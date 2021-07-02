# List of strategies from Trade Pro
'https://docs.google.com/spreadsheets/d/1LQ7lwnvcB5eacK4PxLXnV1mMEIzSxHzD8IZpP2N1oA8/edit#gid=0'
# Multitimeframe + MACD not doable because pandas_ta does not provide MTF indicators.
import concurrent.futures

import pandas_ta as ta
import numpy as np
import logging
from itertools import repeat
from concurrent import futures


class Strategy:
    def __init__(self, stock_data, reward, strategy):
        self.symbol = stock_data[0]
        self.data = stock_data[1].data
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
            self.data.reward.iat[i] = ((1 + self.reward) * self.bought_price) - \
                                               (self.reward * self.data.risk.iloc[i])
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

    def ichimoku_setup(self):
        ichimoku_df = self.data.ta.ichimoku(append=True)
        self.data = self.data.append(ichimoku_df[1])
        self.data.drop(columns='date', inplace=True)
        self.iteration_stop = -26

    def ichimoku_sold(self, i):
        if (self.data.close.iloc[i] > self.data.ISA_9.iloc[i]) and \
                (self.data.close.iloc[i] > self.data.open.iloc[i]) and \
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
            self.data.risk.iat[i] = max(self.data.IKS_26.iloc[i],
                                        (min(self.data.low.iloc[i - 5:i - 1])))
            self.data.reward.iat[i] = ((1 + self.reward) * self.bought_price) - \
                                      (self.reward * self.data.risk.iloc[i])

    def iterate_through(self):
        eval(f'self.{self.strategy}_setup()')
        for i in range(self.iteration_start, self.iteration_stop):
            self.data.backtest_profit_percentage.iat[i] = self.data.backtest_profit_percentage.iloc[i - 1]
            self.data.risk.iat[i] = self.data.risk.iloc[i - 1]
            self.data.reward.iat[i] = self.data.reward.iloc[i - 1]
            if self.bought_price != 0.0:
                if self.data.low.iloc[i] < self.data.risk.iloc[i]:
                    self.data.loss.iat[i] = True
                    self.data.sell_price.iat[i] = self.data.risk.iloc[i]
                    self.data.backtest_profit_percentage.iat[i] -= ((self.bought_price / self.data.sell_price.iloc[i])
                                                                    - 1) * 100
                    self.data.risk.iat[i] = 0.0
                    self.data.reward.iat[i] = 0.0
                    self.bought_price = 0.0
                elif self.data.high.iloc[i] > self.data.reward.iloc[i]:
                    self.data.win.iat[i] = True
                    self.data.sell_price.iat[i] = self.data.reward.iloc[i]
                    self.data.backtest_profit_percentage.iat[i] += ((self.data.sell_price.iloc[i] / self.bought_price)
                                                                    - 1) * 100
                    self.data.risk.iat[i] = 0.0
                    self.data.reward.iat[i] = 0.0
                    self.bought_price = 0.0
            else:
                eval(f'self.{self.strategy}_sold(i)')

        return self.data


def run_strategy(strategy, stock_data, reward):
    logging.info(f'Running {strategy}')
    with futures.ProcessPoolExecutor() as indicator_executor:
        strategy_results = {indicator_executor.submit(Strategy(data, reward, strategy).iterate_through()):
                            data for data in stock_data.items()}
        for future in concurrent.futures.as_completed(strategy_results):
            print(strategy_results[future])
    logging.info(f'Initial strategy run filters down to {len(stock_data)} stock(s)')


'''
def run_strategy(strategy, stock_data, reward):
    logging.info(f'Running {strategy}')
    with futures.ProcessPoolExecutor() as indicator_executor:
        for each_symbol, stock_data_results in zip(stock_data, indicator_executor.map(
                getattr(Strategy,
                        'iterate_through'),stock_data.items(), repeat(reward), repeat(strategy))):
            stock_data[each_symbol].data = stock_data_results
    logging.info(f'Initial strategy run filters down to {len(stock_data)} stock(s)')
'''
