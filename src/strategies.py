# List of strategies from Trade Pro
'https://docs.google.com/spreadsheets/d/1LQ7lwnvcB5eacK4PxLXnV1mMEIzSxHzD8IZpP2N1oA8/edit#gid=0'
# Multitimeframe + MACD not doable because pandas_ta does not provide MTF indicators.

import pandas_ta as ta
import numpy as np


def stochastic_supertrend(stock, arguments):
    bought_price = 0.0
    stock[1].data.ta.ema(length=200, append=True)
    if arguments.run == 'live' and stock[1].data.EMA_200.iloc[-1] > stock[1].data.close.iloc[-1]:
        return stock[1].data
    stock[1].data.ta.supertrend(append=True)
    if arguments.run == 'live' and stock[1].data['SUPERTd_7_3.0'].iloc[-1] < 1:
        return stock[1].data
    stock[1].data.ta.stochrsi(append=True)
    for i in range(-len(stock[1].data) + 300, 0):
        stock[1].data.backtest_profit.iat[i] = stock[1].data.backtest_profit.iloc[i - 1]
        if bought_price != 0.0:
            stock[1].data.risk.iat[i] = stock[1].data.risk.iloc[i - 1]
            stock[1].data.reward.iat[i] = stock[1].data.reward.iloc[i - 1]
            if stock[1].data.low.iloc[i] < stock[1].data.risk.iloc[i]:
                stock[1].data.sell_price.iat[i] = stock[1].data.risk.iloc[i]
                stock[1].data.backtest_profit.iat[i] -= bought_price - \
                    stock[1].data.sell_price.iloc[i]
                stock[1].data.risk.iat[i] = 0.0
                stock[1].data.reward.iat[i] = 0.0
                bought_price = 0.0
            elif stock[1].data.high.iloc[i] > stock[1].data.reward.iloc[i]:
                stock[1].data.sell_price.iat[i] = stock[1].data.reward.iloc[i]
                stock[1].data.backtest_profit.iat[i] -= bought_price - \
                    stock[1].data.sell_price.iloc[i]
                stock[1].data.risk.iat[i] = 0.0
                stock[1].data.reward.iat[i] = 0.0
                bought_price = 0.0
            elif stock[1].data['SUPERTd_7_3.0'].iloc[i] < 1:
                stock[1].data.sell_price.iat[i] = stock[1].data.close.iloc[i]
                stock[1].data.backtest_profit.iat[i] -= bought_price - \
                    stock[1].data.sell_price.iloc[i]
                stock[1].data.risk.iat[i] = 0.0
                stock[1].data.reward.iat[i] = 0.0
                bought_price = 0.0
        else:
            # Cross Up w/ Strategy
            if (stock[1].data.STOCHRSIk_14_14_3_3.iloc[i] - stock[1].data.STOCHRSId_14_14_3_3.iloc[i] >
                    0.0 >
                    stock[1].data.STOCHRSIk_14_14_3_3.iloc[i - 1] - stock[1].data.STOCHRSId_14_14_3_3.iloc[i - 1])\
                    and (stock[1].data.EMA_200.iloc[i] < stock[1].data.close.iloc[i])\
                    and (stock[1].data['SUPERTd_7_3.0'].iloc[i] == 1)\
                    and (stock[1].data.STOCHRSId_14_14_3_3.iloc[i] < 50)\
                    and (stock[1].data.STOCHRSIk_14_14_3_3.iloc[i] < 50):
                stock[1].data.strategy.iat[i] = True
                bought_price = stock[1].data.close.iloc[i]
                stock[1].data.buy_price.iat[i] = bought_price
                stock[1].data.risk.iat[i] = stock[1].data.risk.iloc[i - 1]
                stock[1].data.reward.iat[i] = (2.5 * bought_price) - (1.5 * stock[1].data.risk.iloc[i])
            # Cross Up w/o Strategy
            elif (stock[1].data.STOCHRSIk_14_14_3_3.iloc[i] - stock[1].data.STOCHRSId_14_14_3_3.iloc[i] >
                    0.0 >
                    stock[1].data.STOCHRSIk_14_14_3_3.iloc[i - 1] - stock[1].data.STOCHRSId_14_14_3_3.iloc[i - 1])\
                    and ((stock[1].data.EMA_200.iloc[i] > stock[1].data.close.iloc[i])
                         or (stock[1].data['SUPERTd_7_3.0'].iloc[i] != 1)
                         or (stock[1].data.STOCHRSIk_14_14_3_3.iloc[i] >= 50)
                         or (stock[1].data.STOCHRSId_14_14_3_3.iloc[i] >= 50)):
                stock[1].data.risk.iat[i] = 0.0
                stock[1].data.reward.iat[i] = 0.0
            # Cross Down
            elif stock[1].data.STOCHRSIk_14_14_3_3.iloc[i] - stock[1].data.STOCHRSId_14_14_3_3.iloc[i] < \
                    0.0 < \
                    stock[1].data.STOCHRSIk_14_14_3_3.iloc[i - 1] - stock[1].data.STOCHRSId_14_14_3_3.iloc[i - 1]:
                stock[1].data.risk.iat[i] = stock[1].data.low.iloc[i]
            # Cross Down Continues
            elif stock[1].data.STOCHRSIk_14_14_3_3.iloc[i] - stock[1].data.STOCHRSId_14_14_3_3.iloc[i] < 0.0 \
                    and stock[1].data.risk.iloc[i - 1] != 0.0:
                stock[1].data.risk.iat[i] = min(stock[1].data.risk.iloc[i - 1], stock[1].data.low.iloc[i])
            else:
                stock[1].data.risk.iat[i] = stock[1].data.risk.iloc[i - 1]
                stock[1].data.reward.iat[i] = stock[1].data.reward.iloc[i - 1]

    return stock[1].data


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


def ichimoku(stock, arguments):
    bought_price = 0.0
    ichimoku_df = stock[1].data.ta.ichimoku(append=True)
    stock[1].data = stock[1].data.append(ichimoku_df[1])
    stock[1].data.drop(columns='date', inplace=True)
    for i in range(-len(stock[1].data) + 300, -26):
        stock[1].data.backtest_profit.iat[i] = stock[1].data.backtest_profit.iloc[i - 1]
        if bought_price != 0.0:
            stock[1].data.risk.iat[i] = stock[1].data.risk.iloc[i - 1]
            stock[1].data.reward.iat[i] = stock[1].data.reward.iloc[i - 1]
            if stock[1].data.low.iloc[i] < stock[1].data.risk.iloc[i]:
                stock[1].data.sell_price.iat[i] = stock[1].data.risk.iloc[i]
                stock[1].data.backtest_profit.iat[i] -= bought_price - \
                    stock[1].data.sell_price.iloc[i]
                stock[1].data.risk.iat[i] = 0.0
                stock[1].data.reward.iat[i] = 0.0
                bought_price = 0.0
            elif stock[1].data.high.iloc[i] > stock[1].data.reward.iloc[i]:
                stock[1].data.sell_price.iat[i] = stock[1].data.reward.iloc[i]
                stock[1].data.backtest_profit.iat[i] -= bought_price - \
                    stock[1].data.sell_price.iloc[i]
                stock[1].data.risk.iat[i] = 0.0
                stock[1].data.reward.iat[i] = 0.0
                bought_price = 0.0
        else:
            if (stock[1].data.close.iloc[i] > stock[1].data.ISA_9.iloc[i]) and \
                    (stock[1].data.close.iloc[i] > stock[1].data.ISB_26.iloc[i]) and \
                    (stock[1].data.ISA_9.iloc[i + 26] > stock[1].data.ISB_26.iloc[i + 26]) and \
                    (stock[1].data.ICS_26.iloc[i - 26] > stock[1].data.ISA_9.iloc[i - 26]) and \
                    (stock[1].data.ICS_26.iloc[i - 26] > stock[1].data.ISB_26.iloc[i - 26]) and \
                    (stock[1].data.ITS_9.iloc[i] > stock[1].data.IKS_26.iloc[i]) and \
                    bought_price == 0.0:
                stock[1].data.strategy.iat[i] = True
                bought_price = stock[1].data.close.iloc[i]
                stock[1].data.buy_price.iat[i] = bought_price
                stock[1].data.risk.iat[i] = stock[1].data.IKS_26.iloc[i]
                stock[1].data.reward.iat[i] = (3 * bought_price) - (2 * stock[1].data.risk.iloc[i])

    return stock[1].data
