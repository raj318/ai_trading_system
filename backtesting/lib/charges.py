class Charges():
    stt_delivery: float = 0.001       # 0.1% on Buy & Sell
    stt_intraday_sell: float = 0.00025 # 0.025% on Sell only

    exchange_txn_rate: float = 0.0000297 # NSE: 0.00297%
    sebi_fee_rate: float = 0.000001      # ₹10 / Crore (0.0001%)

    stamp_duty_delivery: float = 0.00015  # 0.015%
    stamp_duty_intraday: float = 0.00003  # 0.003%

    gst_rate: float = 0.18
    def __init__(self):
        pass