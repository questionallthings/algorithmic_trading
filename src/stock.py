import numpy as np


class Stock:
    def __init__(self, data=None, info=None):
        self.data = data
        self.info = info
        self.minutes = ''

    def set_data(self):
        self.data['strategy'] = False
        self.data['backtest_profit_percentage'] = 0.0
        self.data['buy_price'] = np.nan
        self.data['sell_price'] = np.nan
        self.data['risk'] = 0.0
        self.data['reward'] = 0.0
        self.data['win'] = False
        self.data['loss'] = False