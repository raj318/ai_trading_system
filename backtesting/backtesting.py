import sys
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta

current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent
print(f"parent dir = {parent_dir}")
sys.path.append(str(parent_dir))

from technical.src.lib import signals, indicators, duck_db

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

    def __init__(self):
        self.signals = signals.SignalGenerator()
        self.indicators = indicators.Indicators()
        self.data_db = duck_db.Duck()

    def get_start_end_date(self, total_years):
        today = datetime.now()
        past_date = today - relativedelta(years=total_years)
        return past_date.strftime(self.date_format), today.strftime(self.date_format)

    def get_data(self, company, period_years=1, interval='5 minutes'):
        """this is to get data from db based on the period and interval"""
        start_date, end_date = self.get_start_end_date(total_years=period_years)
        return self.data_db.get_company_data(company, start_date, end_date, interval=interval)

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

    def calculate_performance(self, signals):
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
    bt = BackTesting()
    signal_data = bt.get_signals_for_sma_crossover(
                    company="reliance",
                    sma_slow=sma_slow,
                    sma_fast=sma_fast
                )
    performance = bt.calculate_performance(signal_data)
    print(f" performance = {performance}")

def main():
    bt = BackTesting()
    signal_data = bt.get_signals_for_sma_crossover(company="reliance", sma_slow=30, sma_fast=10)
    performance = bt.calculate_performance(signal_data)
    print(f" performance = {performance}")

if __name__ == "__main__":

    main()