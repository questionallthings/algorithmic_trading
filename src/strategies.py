# List of strategies from Trade Pro
'https://docs.google.com/spreadsheets/d/1LQ7lwnvcB5eacK4PxLXnV1mMEIzSxHzD8IZpP2N1oA8/edit#gid=0'
# Multitimeframe + MACD not doable because pandas_ta does not provide MTF indicators.

import pandas_ta as ta


def stochastic_supertrend(stock, arguments):
    stock[1].data['ema_200_trend'] = stock[1].data.ta.ema(length=200) < stock[1].data.close
    if arguments.run == 'live' and not stock[1].data['ema_200_trend'].iloc[-1]:
        return stock[1].data
    stock[1].data.ta.supertrend(append=True)
    if arguments.run == 'live' and stock[1].data['SUPERTd_7_3.0'].iloc[-1] < 1:
        return stock[1].data
    stock[1].data['cross_up'] = stock[1].data.ta.stochrsi().STOCHRSIk_14_14_3_3 - \
                                stock[1].data.ta.stochrsi().STOCHRSId_14_14_3_3 > 0
    for i in range(600, len(stock[1].data)):
        stock[1].data.backtest_profit.iat[i] = stock[1].data.backtest_profit.iat[i - 1]
        if stock[1].data['SUPERTd_7_3.0'].iloc[i] > 0:
            if (not stock[1].data.cross_up.iloc[i] and stock[1].data.cross_up.iloc[i - 1]) and \
                    (stock[1].data.risk.iat[i - 1] == 0.0 or
                     stock[1].data.reward.iat[i - 1] == 0.0):
                stock[1].data.risk.iat[i] = stock[1].data.low.iloc[i]
            elif (stock[1].data.cross_up.iloc[i] and not stock[1].data.cross_up.iloc[i - 1]) and \
                    (stock[1].data.risk.iat[i - 1] == 0.0 or
                     stock[1].data.reward.iat[i - 1] == 0.0):
                stock[1].data.cross_up.iat[i] = True
                stock[1].data.strategy.iat[i] = True
                if i < len(stock[1].data) - 1:
                    stock[1].data.buy_price.iat[i] = stock[1].data.open.iloc[i + 1]
                else:
                    stock[1].data.buy_price.iat[i] = stock[1].data.close.iloc[i]
                stock[1].data.risk.iat[i] = max(stock[1].data.low.iloc[i],
                                                stock[1].data.risk.iloc[i - 1],
                                                (stock[1].data.buy_price.iloc[i] -
                                                 stock[1].data.ATRr_14.iloc[i]))
                stock[1].data.reward.iat[i] = stock[1].data.buy_price.iloc[i] + \
                                              ((stock[1].data.buy_price.iloc[i] -
                                                stock[1].data.risk.iloc[i]) *
                                               float(arguments.manage.split('_')[-1]))
            else:
                stock[1].data.buy_price.iat[i] = stock[1].data.buy_price.iloc[i - 1]
                stock[1].data.cross_up.iat[i] = stock[1].data.cross_up.iat[i - 1]
                stock[1].data.risk.iat[i] = stock[1].data.risk.iloc[i - 1]
                stock[1].data.reward.iat[i] = stock[1].data.reward.iloc[i - 1]
        else:
            if stock[1].data.buy_price.iloc[i - 1] != 0.0:
                stock[1].data.backtest_profit.iat[i] = \
                    stock[1].data.backtest_profit.iloc[i - 1] + \
                    stock[1].data.close.iloc[i - 1] - \
                    stock[1].data.buy_price.iloc[i - 1]
                stock[1].data.sell_price.iat[i] = stock[1].data.close.iloc[i - 1]
            elif (stock[1].data.risk.iloc[i] > stock[1].data.low.iloc[i]) and \
                    (stock[1].data.reward.iloc[i] < stock[1].data.high.iloc[i]):
                pass
            elif stock[1].data.risk.iloc[i] > stock[1].data.low.iloc[i]:
                stock[1].data.backtest_profit.iat[i] = \
                    stock[1].data.backtest_profit.iloc[i - 1] - \
                    (stock[1].data.buy_price.iloc[i] - stock[1].data.risk.iloc[i])
                stock[1].data.sell_price.iat[i] = stock[1].data.risk.iloc[i]
            elif stock[1].data.reward.iloc[i] < stock[1].data.high.iloc[i]:
                stock[1].data.backtest_profit.iat[i] = \
                    stock[1].data.backtest_profit.iloc[i - 1] + \
                    (stock[1].data.reward.iloc[i] - stock[1].data.buy_price.iloc[i])
                stock[1].data.sell_price.iat[i] = stock[1].data.reward.iloc[i]
            else:
                stock[1].data.cross_up.iat[i] = False
                stock[1].data.risk.iat[i] = 0.0
                stock[1].data.reward.iat[i] = 0.0
                stock[1].data.buy_price.iat[i] = 0.0

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


