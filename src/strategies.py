# List of strategies from Trade Pro
'https://docs.google.com/spreadsheets/d/1LQ7lwnvcB5eacK4PxLXnV1mMEIzSxHzD8IZpP2N1oA8/edit#gid=0'
# Multitimeframe + MACD not doable because pandas_ta does not provide MTF indicators.

import pandas_ta as ta
import numpy as np

# ALL TIME FRAMES STRATEGIES

# DAY TIME FRAME STRATEGIES


class Strategy:
    def __init__(self, stock_data, arguments):
        self.symbol = stock_data[0]
        self.data = stock_data[1].data
        self.arguments = arguments
        self.bought_price = 0.0

    def stochastic_supertrend(self):
        self.data.ta.ema(length=200, append=True)
        if self.arguments['run'] == 'live' and self.data.EMA_200.iloc[-1] > self.data.close.iloc[-1]:
            return self.data
        self.data.ta.supertrend(append=True)
        if self.arguments['run'] == 'live' and self.data['SUPERTd_7_3.0'].iloc[-1] < 1:
            return self.data
        self.data.ta.stochrsi(append=True)
        for i in range(-len(self.data) + 300, 0):
            self.data.backtest_profit.iat[i] = self.data.backtest_profit.iloc[i - 1]
            if self.bought_price != 0.0:
                self.data.risk.iat[i] = self.data.risk.iloc[i - 1]
                self.data.reward.iat[i] = self.data.reward.iloc[i - 1]
                if self.data.low.iloc[i] < self.data.risk.iloc[i]:
                    self.data.sell_price.iat[i] = self.data.risk.iloc[i]
                    self.data.backtest_profit.iat[i] -= self.bought_price - self.data.sell_price.iloc[i]
                    self.data.risk.iat[i] = 0.0
                    self.data.reward.iat[i] = 0.0
                    self.bought_price = 0.0
                elif self.data.high.iloc[i] > self.data.reward.iloc[i]:
                    self.data.sell_price.iat[i] = self.data.reward.iloc[i]
                    self.data.backtest_profit.iat[i] -= self.bought_price - self.data.sell_price.iloc[i]
                    self.data.risk.iat[i] = 0.0
                    self.data.reward.iat[i] = 0.0
                    self.bought_price = 0.0
                elif self.data['SUPERTd_7_3.0'].iloc[i] < 1:
                    self.data.sell_price.iat[i] = self.data.close.iloc[i]
                    self.data.backtest_profit.iat[i] -= self.bought_price - self.data.sell_price.iloc[i]
                    self.data.risk.iat[i] = 0.0
                    self.data.reward.iat[i] = 0.0
                    self.bought_price = 0.0
            else:
                # Cross Up w/ Strategy
                if (self.data.STOCHRSIk_14_14_3_3.iloc[i] - self.data.STOCHRSId_14_14_3_3.iloc[i] >
                    0.0 >
                    self.data.STOCHRSIk_14_14_3_3.iloc[i - 1] - self.data.STOCHRSId_14_14_3_3.iloc[i - 1]) \
                        and (self.data.EMA_200.iloc[i] < self.data.close.iloc[i]) \
                        and (self.data['SUPERTd_7_3.0'].iloc[i] == 1) \
                        and (self.data.STOCHRSId_14_14_3_3.iloc[i] < 50) \
                        and (self.data.STOCHRSIk_14_14_3_3.iloc[i] < 50):
                    self.data.strategy.iat[i] = True
                    self.bought_price = self.data.close.iloc[i]
                    self.data.buy_price.iat[i] = self.bought_price
                    self.data.risk.iat[i] = self.data.risk.iloc[i - 1]
                    self.data.reward.iat[i] = (2.5 * self.bought_price) - (1.5 * self.data.risk.iloc[i])
                # Cross Up w/o Strategy
                elif (self.data.STOCHRSIk_14_14_3_3.iloc[i] - self.data.STOCHRSId_14_14_3_3.iloc[i] >
                      0.0 >
                      self.data.STOCHRSIk_14_14_3_3.iloc[i - 1] - self.data.STOCHRSId_14_14_3_3.iloc[i - 1]) \
                        and ((self.data.EMA_200.iloc[i] > self.data.close.iloc[i])
                             or (self.data['SUPERTd_7_3.0'].iloc[i] != 1)
                             or (self.data.STOCHRSIk_14_14_3_3.iloc[i] >= 50)
                             or (self.data.STOCHRSId_14_14_3_3.iloc[i] >= 50)):
                    self.data.risk.iat[i] = 0.0
                    self.data.reward.iat[i] = 0.0
                # Cross Down
                elif self.data.STOCHRSIk_14_14_3_3.iloc[i] - self.data.STOCHRSId_14_14_3_3.iloc[i] < \
                        0.0 < \
                        self.data.STOCHRSIk_14_14_3_3.iloc[i - 1] - self.data.STOCHRSId_14_14_3_3.iloc[i - 1]:
                    self.data.risk.iat[i] = self.data.low.iloc[i]
                # Cross Down Continues
                elif self.data.STOCHRSIk_14_14_3_3.iloc[i] - self.data.STOCHRSId_14_14_3_3.iloc[i] < 0.0 \
                        and self.data.risk.iloc[i - 1] != 0.0:
                    self.data.risk.iat[i] = min(self.data.risk.iloc[i - 1], self.data.low.iloc[i])
                else:
                    self.data.risk.iat[i] = self.data.risk.iloc[i - 1]
                    self.data.reward.iat[i] = self.data.reward.iloc[i - 1]

        return self.data

    def ichimoku(self):
        ichimoku_df = self.data.ta.ichimoku(append=True)
        self.data = self.data.append(ichimoku_df[1])
        self.data.drop(columns='date', inplace=True)
        for i in range(-len(self.data) + 300, -26):
            self.data.backtest_profit.iat[i] = self.data.backtest_profit.iloc[i - 1]
            if self.bought_price != 0.0:
                self.data.risk.iat[i] = self.data.risk.iloc[i - 1]
                self.data.reward.iat[i] = self.data.reward.iloc[i - 1]
                if self.data.low.iloc[i] < self.data.risk.iloc[i]:
                    self.data.sell_price.iat[i] = self.data.risk.iloc[i]
                    self.data.backtest_profit.iat[i] -= self.bought_price - self.data.sell_price.iloc[i]
                    self.data.risk.iat[i] = 0.0
                    self.data.reward.iat[i] = 0.0
                    self.bought_price = 0.0
                elif self.data.high.iloc[i] > self.data.reward.iloc[i]:
                    self.data.sell_price.iat[i] = self.data.reward.iloc[i]
                    self.data.backtest_profit.iat[i] -= self.bought_price - self.data.sell_price.iloc[i]
                    self.data.risk.iat[i] = 0.0
                    self.data.reward.iat[i] = 0.0
                    self.bought_price = 0.0
            else:
                if (self.data.close.iloc[i] > self.data.ISA_9.iloc[i]) and \
                        (self.data.close.iloc[i] > self.data.ISB_26.iloc[i]) and \
                        (self.data.ISA_9.iloc[i + 26] > self.data.ISB_26.iloc[i + 26]) and \
                        (self.data.ICS_26.iloc[i - 26] > self.data.ISA_9.iloc[i - 26]) and \
                        (self.data.ICS_26.iloc[i - 26] > self.data.ISB_26.iloc[i - 26]) and \
                        (self.data.ITS_9.iloc[i] > self.data.IKS_26.iloc[i]) and \
                        (self.data.close.iloc[i] > self.data.IKS_26.iloc[i]) and \
                        self.bought_price == 0.0:
                    self.data.strategy.iat[i] = True
                    self.bought_price = self.data.close.iloc[i]
                    self.data.buy_price.iat[i] = self.bought_price
                    self.data.risk.iat[i] = self.data.IKS_26.iloc[i]
                    self.data.reward.iat[i] = (3 * self.bought_price) - (2 * self.data.risk.iloc[i])

        return self.data


def rsi_stochastic_200ema(stock, arguments):
    pass
    '''
    long
    close above 200 ema
    rsi for divergence
    price higher lows
    rsi lower low
    next cross up on stoch is entry
    risk is nearest swing low
    reward is 2x risk
    '''
