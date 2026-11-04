import sys
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import Dict, Any, List, Set

current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent
print(f"parent dir = {parent_dir}")
sys.path.append(str(parent_dir))

from technical.src.lib import signals, indicators, duck_db, trading_execution_tools

class BackTesting():
    perf = {
        'total_trades':0.0,
        'profit_trades':0,
        'loss_trades':0,
        'profit_made':0,
        'loss_made':0,
        'net_profit':0,
    }
    date_format = "%Y-%m-%d %H:%M:%S"



    def __init__(self, ):
        self.signals = signals.SignalGenerator()
        self.indicators = indicators.Indicators()
        self.exec_tools = trading_execution_tools.TradingEngineRegistry()
        self.data_db = duck_db.Duck()

    def get_start_end_date(self, total_years):
        today = datetime.now()
        past_date = today - relativedelta(years=total_years)
        return past_date.strftime(self.date_format), today.strftime(self.date_format)

    def get_data(self, company, period_years=1, interval='5 minutes'):
        """this is to get data from db based on the period and interval"""
        start_date, end_date = self.get_start_end_date(total_years=period_years)
        return self.data_db.get_company_data(company, start_date, end_date, interval=interval)

    def inspect_strategy_pipeline(self, strategy):
        """
        Generically inspects a strategy dictionary for missing indicators, conditions,
        and signals based on cross-references down the execution pipeline.

        Returns a dictionary containing boolean 'valid', missing component lists,
        and a formatted error message tailored for LLM context correction.
        """
        missing_indicators: Set[str] = set()
        missing_conditions: Set[str] = set()
        missing_signals: Set[str] = set()

        # ------------------------------------------------------------------
        # 1. Collect Declared Component IDs
        # ------------------------------------------------------------------
        indicators_list = strategy.get("indicators", [])
        conditions_list = strategy.get("conditions", [])
        signals_list = strategy.get("signals", [])

        declared_indicators: Set[str] = {
            ind.get("id") if isinstance(ind, dict) else ind.id
            for ind in indicators_list if ind
        }
        
        declared_conditions: Set[str] = {
            cond.get("id") if isinstance(cond, dict) else cond.id
            for cond in conditions_list if cond
        }

        declared_signals: Set[str] = {
            sig.get("id") if isinstance(sig, dict) else sig.id
            for sig in signals_list if sig
        }

        # ------------------------------------------------------------------
        # 2. Inspect Conditions -> Indicators
        # ------------------------------------------------------------------
        for cond in conditions_list:
            cond_dict = cond if isinstance(cond, dict) else cond.model_dump()
            params = cond_dict.get("parameters", {})

            for _, param_value in params.items():
                if isinstance(param_value, str):
                    # Handle multi-output sub-fields (e.g. 'macd_12_26.macd' -> 'macd_12_26')
                    base_id = param_value.split(".")[0]
                    
                    # Check if non-numeric operand is missing from declared indicators
                    if not param_value.replace(".", "", 1).isdigit():
                        if base_id not in declared_indicators:
                            missing_indicators.add(base_id)

        # ------------------------------------------------------------------
        # 3. Inspect Signals -> Conditions (Using updated schema)
        # ------------------------------------------------------------------
        actions = []
        for sig in signals_list:
            sig_dict = sig if isinstance(sig, dict) else sig.model_dump()
            params = sig_dict.get("parameters", {})

            left_ref = params.get("left")
            right_ref = params.get("right")
            actions.append(params.get("action"))

            for ref in [left_ref, right_ref]:
                if ref and isinstance(ref, str):
                    base_id = ref.split(".")[0]
                    if not ref.replace(".", "", 1).isdigit():
                        if base_id not in declared_conditions:
                            missing_conditions.add(base_id)

        # Check output reference
        output_ref = strategy.get("output")
        if output_ref and output_ref not in declared_signals:
            missing_signals.add(output_ref)

        missing_action = False
        if len(set(actions)) != 2:
            missing_action = True

        # ------------------------------------------------------------------
        # 4. Construct LLM Feedback Message
        # ------------------------------------------------------------------
        is_valid = not (missing_indicators or missing_conditions or missing_signals or missing_action)
        llm_feedback_lines = []

        if not is_valid:
            llm_feedback_lines.append(
                "Your generated strategy JSON contains broken component references that prevent execution:\n"
            )

            if 'BUY' not in actions:
                llm_feedback_lines.append("Your generated strategy JSON does not contain BUY signal, this prevents execution\n")

            if 'SELL' not in actions:
                llm_feedback_lines.append("Your generated strategy JSON does not contain SELL signal, this prevents execution\n")
            
            if missing_indicators:
                llm_feedback_lines.append(
                    f"- MISSING INDICATORS: The following indicator IDs were referenced in conditions but never defined in the 'indicators' list: {list(missing_indicators)}"
                )
                
            if missing_conditions:
                llm_feedback_lines.append(
                    f"- MISSING CONDITIONS: The following condition IDs were referenced in signals (left/right) but never defined in the 'conditions' list: {list(missing_conditions)}"
                )

            if missing_signals:
                llm_feedback_lines.append(
                    f"- MISSING SIGNALS: The output signal '{output_ref}' is specified as target output but never defined in the 'signals' list."
                )

            llm_feedback_lines.append(
                "\nPlease regenerate the COMPLETE JSON strategy object, making sure to define all missing IDs inside their respective 'indicators', 'conditions', or 'signals' arrays."
            )

        return {
            "valid": is_valid,
            "missing_indicators": sorted(list(missing_indicators)),
            "missing_conditions": sorted(list(missing_conditions)),
            "missing_signals": sorted(list(missing_signals)),
            "llm_error_message": "\n".join(llm_feedback_lines) if not is_valid else ""
        }

    def execute(self, json_schema):
        print(f"json schema ={json_schema}\n\n\n")
        result = self.inspect_strategy_pipeline(json_schema)
        print(f"validation status = {result}")
        if not result['valid']:
            return result['llm_error_message']
        # return "no code to execute, please inform the user"
        print(f"found the result!!")
        data = self.get_data(company='reliance', period_years=15)
        buy_id = None
        sell_id = None
        for indicator in json_schema['indicators']:
            data[indicator.id] = self.exec_tools.execute_node(
                indicator.type,
                data[indicator.input],
                indicator.parameters.period
            )
            print(data.columns)

        for condition in json_schema['conditions']:
            print(f"condition = {condition}")
            if isinstance(condition.parameters.right, int) or (isinstance(condition.parameters.right, str) and condition.parameters.right.isdigit()):
                right = condition.parameters.right
            else:
                right = data[condition.parameters.right]
            data[condition.id] = self.exec_tools.execute_node(
                condition.type,
                data[condition.parameters.left],
                right,
            )
            print(data.columns)
        for signal in json_schema['signals']:
            print(f"signal. = {signal}")
            if signal.parameters.action == 'BUY':
                buy_id = signal.id
            if signal.parameters.action == 'SELL':
                sell_id = signal.id
            data[signal.id] = self.exec_tools.execute_node(
                                    signal.type,
                                    signal.parameters.condition,
                                    data[signal.parameters.left],
                                    data[signal.parameters.right],
                                    signal.parameters.action,
                                )
            print(data.columns)

        return self.calculate_performance_with_buy_sell_signal(data, buy_id, sell_id)
        # return "still the execution code is not available!"

    def get_signals_for_sma_crossover(self, company, sma_fast, sma_slow):
        data_df = self.get_data(company, period_years=15, interval='5 minutes')
        return self.signals.generate_ma_crossover_signals(
                                                            df=data_df,
                                                            symbol=company,
                                                            fast_len=sma_fast,
                                                            slow_len=sma_slow
                                                        )

    def get_signals_for_ema_crossover(self, company, ema_fast, ema_slow):
        data_df = self.get_data(company, period_years=15, interval='5 minutes')

        return self.signals.generate_ma_crossover_signals(
                                                            df=data_df,
                                                            symbol=company,
                                                            fast_len=ema_fast,
                                                            slow_len=ema_slow
                                                        )
    def calculate_performance_with_buy_sell_signal(self, data, buy_signal, sell_signal):
        entry_price = None
        for price, buy, sell in zip(data['close'], data[buy_signal], data[sell_signal]):

            if buy == 'BUY':
                self.perf['total_trades'] += 0.5
                entry_price = price
                # print(f"buy price at = {entry_price}")
            if sell == 'SELL':
                self.perf['total_trades'] += 0.5
                sell_price = price
                # print(f"sell price = {sell_price}")
                if entry_price:
                    profit = sell_price - entry_price
                    # print(f"profit = {profit}")
                    if profit > 0:
                        self.perf['profit_trades'] += 1
                        self.perf['profit_made'] += profit
                    else:
                        self.perf['loss_trades'] += 1
                        self.perf['loss_made'] += abs(profit)
                    entry_price = None
                # else
                    # print(f"Ignoring SELL trigger without BUY!")
        self.perf['net_profit'] = self.perf['profit_made'] - self.perf['loss_made']
        return self.perf

    def calculate_performance_in_one_signal(self, signals):
        entry_price = None
        for signal in signals:

            if signal.action == 'BUY':
                self.perf['total_trades'] += 0.5
                entry_price = signal.evidence.price
            if signal.action == 'SELL':
                self.perf['total_trades'] += 0.5
                sell_price = signal.evidence.price
                if entry_price:
                    profit = sell_price - entry_price
                    # print(f"profit = {profit}")
                    if profit > 0:
                        self.perf['profit_trades'] += 1
                        self.perf['profit_made'] += profit
                    else:
                        self.perf['loss_trades'] += 1
                        self.perf['loss_made'] += abs(profit)
                else:
                    print(f"Ignoring SELL trigger without BUY!")
        self.perf['net_profit'] = self.perf['profit_made'] - self.perf['loss_made']
        return self.perf

def get_perfomance_of_strategy(company, sma_slow, sma_fast):
    """
    For a given SMA slow and SMA fast numbers for a given company,
    calculates indicator values, finds signals and calculates
    performances
    """
    bt = BackTesting()
    signal_data = bt.get_signals_for_sma_crossover(
                    company=company.lower(),
                    sma_slow=sma_slow,
                    sma_fast=sma_fast
                )
    performance = bt.calculate_performance_in_one_signal(signal_data)
    print(f" performance = {performance}")

def main():
    bt = BackTesting()
    signal_data = bt.get_signals_for_sma_crossover(company="reliance", sma_slow=30, sma_fast=10)
    performance = bt.calculate_performance_with_buy_sell_signal(signal_data, signal_data)
    print(f" performance = {performance}")

if __name__ == "__main__":

    main()