# List of strategies from Trade Pro
'https://docs.google.com/spreadsheets/d/1LQ7lwnvcB5eacK4PxLXnV1mMEIzSxHzD8IZpP2N1oA8/edit#gid=0'
# Multitimeframe + MACD not doable because pandas_ta does not provide MTF indicators.

import pandas_ta as ta
import numpy as np
import logging
from itertools import repeat
from concurrent import futures


def stochastic_supertrend(stock_data, reward):
    bought_price = 0.0
    stock_data[1].data.ta.ema(length=200, append=True)
    stock_data[1].data.ta.supertrend(append=True)
    stock_data[1].data.ta.stochrsi(append=True)
    for i in range(-len(stock_data[1].data) + 300, 0):
        stock_data[1].data.backtest_profit_percentage.iat[i] = stock_data[1].data.backtest_profit_percentage.iloc[i - 1]
        if bought_price != 0.0:
            stock_data[1].data.risk.iat[i] = stock_data[1].data.risk.iloc[i - 1]
            stock_data[1].data.reward.iat[i] = stock_data[1].data.reward.iloc[i - 1]
            if stock_data[1].data.low.iloc[i] < stock_data[1].data.risk.iloc[i]:
                stock_data[1].data.loss.iat[i] = True
                stock_data[1].data.sell_price.iat[i] = stock_data[1].data.risk.iloc[i]
                stock_data[1].data.backtest_profit_percentage.iat[i] -= ((bought_price /
                                                                          stock_data[1].data.sell_price.iloc[i])
                                                                         - 1) * 100
                stock_data[1].data.risk.iat[i] = 0.0
                stock_data[1].data.reward.iat[i] = 0.0
                bought_price = 0.0
            elif stock_data[1].data.high.iloc[i] > stock_data[1].data.reward.iloc[i]:
                stock_data[1].data.win.iat[i] = True
                stock_data[1].data.sell_price.iat[i] = stock_data[1].data.reward.iloc[i]
                stock_data[1].data.backtest_profit_percentage.iat[i] += ((stock_data[1].data.sell_price.iloc[i] /
                                                                          bought_price) - 1) * 100
                stock_data[1].data.risk.iat[i] = 0.0
                stock_data[1].data.reward.iat[i] = 0.0
                bought_price = 0.0
            elif stock_data[1].data['SUPERTd_7_3.0'].iloc[i] < 1:
                stock_data[1].data.loss.iat[i] = True
                stock_data[1].data.sell_price.iat[i] = stock_data[1].data.close.iloc[i]
                stock_data[1].data.backtest_profit_percentage.iat[i] -= ((bought_price /
                                                                          stock_data[1].data.sell_price.iloc[i])
                                                                         - 1) * 100
                stock_data[1].data.risk.iat[i] = 0.0
                stock_data[1].data.reward.iat[i] = 0.0
                bought_price = 0.0
        else:
            # Cross Up w/ Strategy
            if (stock_data[1].data.STOCHRSIk_14_14_3_3.iloc[i] - stock_data[1].data.STOCHRSId_14_14_3_3.iloc[i] >
                0.0 >
                stock_data[1].data.STOCHRSIk_14_14_3_3.iloc[i - 1] - stock_data[1].data.STOCHRSId_14_14_3_3.iloc[i - 1]) \
                    and (stock_data[1].data.EMA_200.iloc[i] < stock_data[1].data.close.iloc[i]) \
                    and (stock_data[1].data['SUPERTd_7_3.0'].iloc[i] == 1) \
                    and (stock_data[1].data.STOCHRSId_14_14_3_3.iloc[i] < 50) \
                    and (stock_data[1].data.STOCHRSIk_14_14_3_3.iloc[i] < 50):
                stock_data[1].data.strategy.iat[i] = True
                bought_price = stock_data[1].data.close.iloc[i]
                stock_data[1].data.buy_price.iat[i] = bought_price
                stock_data[1].data.risk.iat[i] = stock_data[1].data.risk.iloc[i - 1]
                stock_data[1].data.reward.iat[i] = ((1 + reward) * bought_price) - \
                                                   (reward * stock_data[1].data.risk.iloc[i])
            # Cross Up w/o Strategy
            elif (stock_data[1].data.STOCHRSIk_14_14_3_3.iloc[i] - stock_data[1].data.STOCHRSId_14_14_3_3.iloc[i] >
                  0.0 >
                  stock_data[1].data.STOCHRSIk_14_14_3_3.iloc[i - 1] - stock_data[1].data.STOCHRSId_14_14_3_3.iloc[i - 1]) \
                    and ((stock_data[1].data.EMA_200.iloc[i] > stock_data[1].data.close.iloc[i])
                         or (stock_data[1].data['SUPERTd_7_3.0'].iloc[i] != 1)
                         or (stock_data[1].data.STOCHRSIk_14_14_3_3.iloc[i] >= 50)
                         or (stock_data[1].data.STOCHRSId_14_14_3_3.iloc[i] >= 50)):
                stock_data[1].data.risk.iat[i] = 0.0
                stock_data[1].data.reward.iat[i] = 0.0
            # Cross Down
            elif stock_data[1].data.STOCHRSIk_14_14_3_3.iloc[i] - stock_data[1].data.STOCHRSId_14_14_3_3.iloc[i] < \
                    0.0 < \
                    stock_data[1].data.STOCHRSIk_14_14_3_3.iloc[i - 1] - stock_data[1].data.STOCHRSId_14_14_3_3.iloc[i - 1]:
                stock_data[1].data.risk.iat[i] = stock_data[1].data.low.iloc[i]
            # Cross Down Continues
            elif stock_data[1].data.STOCHRSIk_14_14_3_3.iloc[i] - stock_data[1].data.STOCHRSId_14_14_3_3.iloc[i] < 0.0 \
                    and stock_data[1].data.risk.iloc[i - 1] != 0.0:
                stock_data[1].data.risk.iat[i] = min(stock_data[1].data.risk.iloc[i - 1], stock_data[1].data.low.iloc[i])
            else:
                stock_data[1].data.risk.iat[i] = stock_data[1].data.risk.iloc[i - 1]
                stock_data[1].data.reward.iat[i] = stock_data[1].data.reward.iloc[i - 1]

    return stock_data[1].data


def ichimoku(stock_data, reward):
    bought_price = 0.0
    ichimoku_df = stock_data[1].data.ta.ichimoku(append=True)
    stock_data[1].data = stock_data[1].data.append(ichimoku_df[1])
    stock_data[1].data.drop(columns='date', inplace=True)
    stock_data[1].data.ta.atr(append=True)
    for i in range(-len(stock_data[1].data) + 300, -26):
        stock_data[1].data.backtest_profit_percentage.iat[i] = stock_data[1].data.backtest_profit_percentage.iloc[i - 1]
        if bought_price != 0.0:
            stock_data[1].data.risk.iat[i] = stock_data[1].data.risk.iloc[i - 1]
            stock_data[1].data.reward.iat[i] = stock_data[1].data.reward.iloc[i - 1]
            if stock_data[1].data.low.iloc[i] < stock_data[1].data.risk.iloc[i]:
                stock_data[1].data.loss.iat[i] = True
                stock_data[1].data.sell_price.iat[i] = stock_data[1].data.risk.iloc[i]
                stock_data[1].data.backtest_profit_percentage.iat[i] -= ((bought_price /
                                                                          stock_data[1].data.sell_price.iloc[i])
                                                                         - 1) * 100
                stock_data[1].data.risk.iat[i] = 0.0
                stock_data[1].data.reward.iat[i] = 0.0
                bought_price = 0.0
            elif stock_data[1].data.high.iloc[i] > stock_data[1].data.reward.iloc[i]:
                stock_data[1].data.win.iat[i] = True
                stock_data[1].data.sell_price.iat[i] = stock_data[1].data.reward.iloc[i]
                stock_data[1].data.backtest_profit_percentage.iat[i] += ((stock_data[1].data.sell_price.iloc[i] /
                                                                          bought_price) - 1) * 100
                stock_data[1].data.risk.iat[i] = 0.0
                stock_data[1].data.reward.iat[i] = 0.0
                bought_price = 0.0
        else:
            if (stock_data[1].data.close.iloc[i] > stock_data[1].data.ISA_9.iloc[i]) and \
                    (stock_data[1].data.close.iloc[i] > stock_data[1].data.open.iloc[i]) and \
                    (stock_data[1].data.close.iloc[i] > stock_data[1].data.ISB_26.iloc[i]) and \
                    (stock_data[1].data.ISA_9.iloc[i + 26] > stock_data[1].data.ISB_26.iloc[i + 26]) and \
                    (stock_data[1].data.ICS_26.iloc[i - 26] > stock_data[1].data.ISA_9.iloc[i - 26]) and \
                    (stock_data[1].data.ICS_26.iloc[i - 26] > stock_data[1].data.ISB_26.iloc[i - 26]) and \
                    (stock_data[1].data.ITS_9.iloc[i] > stock_data[1].data.IKS_26.iloc[i]) and \
                    (stock_data[1].data.close.iloc[i] > stock_data[1].data.IKS_26.iloc[i]) and \
                    bought_price == 0.0:
                stock_data[1].data.strategy.iat[i] = True
                bought_price = stock_data[1].data.close.iloc[i]
                stock_data[1].data.buy_price.iat[i] = bought_price
                stock_data[1].data.risk.iat[i] = max(stock_data[1].data.IKS_26.iloc[i],
                                                     (min(stock_data[1].data.low.iloc[i - 5:i - 1])))
                stock_data[1].data.reward.iat[i] = ((1 + reward) * bought_price) - \
                                                   (reward * stock_data[1].data.risk.iloc[i])

    return stock_data[1].data


def rsi_stochastic_200ema(stock_data, reward):
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


class Strategy:
    def __init__(self, stock_data, reward, strategy):
        self.symbol = stock_data[0]
        self.data = stock_data[1]
        self.reward = reward
        self.strategy = strategy
        self.bought_price = 0.0
        self.iteration_start = -len(self.data) + 300
        self.iteration_stop = 0

    def stochastic_supertrend_setup(self):
        self.data.ta.ema(length=200, append=True)
        self.data.ta.supertrend(append=True)
        self.data.ta.stochrsi(append=True)

    def stochastic_supertrend_sold(self, i):
        pass

    def ichimoku_setup(self):
        ichimoku_df = self.data.ta.ichimoku(append=True)
        self.data = self.data.append(ichimoku_df[1])
        self.data.drop(columns='date', inplace=True)
        self.iteration_stop = -26

    def ichimoku_sold(self, i):
        pass

    def iterate_through(self):
        eval(f'{self.strategy}_setup')
        for i in range(self.iteration_start, self.iteration_stop):
            self.data.backtest_profit_percentage.iat[i] = self.data.backtest_profit_percentage.iloc[i - 1]
            self.data.risk.iat[i] = self.data.risk.iloc[i - 1]
            self.data.reward.iat[i] = self.data.reward.iloc[i - 1]
            if self.bought_price != 0.0:
                if self.data.low.iloc[i] < self.data.risk.iloc[i]:
                    self.data.loss.iat[i] = True
                    self.data.sell_price.iat[i] = self.data.risk.iloc[i]
                    self.data.backtest_profit_percentage.iat[i] -= ((self.bought_price /
                                                                              self.data.sell_price.iloc[i])
                                                                             - 1) * 100
                    self.data.risk.iat[i] = 0.0
                    self.data.reward.iat[i] = 0.0
                    self.bought_price = 0.0
                elif self.data.high.iloc[i] > self.data.reward.iloc[i]:
                    self.data.win.iat[i] = True
                    self.data.sell_price.iat[i] = self.data.reward.iloc[i]
                    self.data.backtest_profit_percentage.iat[i] += ((self.data.sell_price.iloc[i] /
                                                                              self.bought_price) - 1) * 100
                    self.data.risk.iat[i] = 0.0
                    self.data.reward.iat[i] = 0.0
                    self.bought_price = 0.0
            else:
                eval(f'{self.strategy}_sold(i)')


def run_strategy(strategy, stock_data, reward):
    logging.info(f'Running {strategy}')
    with futures.ProcessPoolExecutor() as indicator_executor:
        for each_symbol, stock_data_results in zip(stock_data, indicator_executor.map(eval(strategy),
                                                                                      stock_data.items(),
                                                                                      repeat(reward))):
            stock_data[each_symbol].data = stock_data_results
    logging.info(f'Initial strategy run filters down to {len(stock_data)} stock(s)')
