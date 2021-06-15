#!/usr/bin/env python3

"""
This script is used to test various ideas from internal/external sources before implementing in development code.
This will not be part of final package.
"""
from concurrent import futures
from itertools import repeat
import pandas_ta as ta


def stochastic_supertrend_concurrent(stock, arguments):
    stock[1].stock_data['cross_up'] = False
    stock[1].stock_data['cross_down'] = False
    stock[1].stock_data['ema_200_trend'] = stock[1].stock_data.ta.ema(length=200) < stock[1].stock_data.close
    if arguments.run == 'live' and not stock[1].stock_data['ema_200_trend'].iloc[-1]:
        return stock[1].stock_data
    stock[1].stock_data.ta.supertrend(append=True)
    if arguments.run == 'live' and stock[1].stock_data['SUPERTd_7_3.0'].iloc[-1] < 1:
        return stock[1].stock_data
    stock[1].stock_data['stoch_trend'] = stock[1].stock_data.ta.stochrsi().STOCHRSIk_14_14_3_3 - \
        stock[1].stock_data.ta.stochrsi().STOCHRSId_14_14_3_3
    stock[1].stock_data.ta.atr(append=True)
    for i in range(600, len(stock[1].stock_data)):
        stock[1].stock_data.backtest_profit.iat[i] = stock[1].stock_data.backtest_profit.iat[i - 1]
        if stock[1].stock_data['SUPERTd_7_3.0'].iloc[i] > 0:
            if (stock[1].stock_data.stoch_trend.iloc[i] <= 0 < stock[1].stock_data.stoch_trend.iloc[i - 1]) and \
                    (stock[1].stock_data.risk.iat[i - 1] == 0.0 or
                     stock[1].stock_data.reward.iat[i - 1] == 0.0):
                stock[1].stock_data.cross_down.iat[i] = True
                stock[1].stock_data.cross_up.iat[i] = False
                stock[1].stock_data.risk.iat[i] = stock[1].stock_data.low.iloc[i]
            elif (stock[1].stock_data.stoch_trend.iloc[i] > 0 >= stock[1].stock_data.stoch_trend.iloc[i - 1]) and \
                    (stock[1].stock_data.risk.iat[i - 1] == 0.0 or
                     stock[1].stock_data.reward.iat[i - 1] == 0.0):
                stock[1].stock_data.cross_up.iat[i] = True
                stock[1].stock_data.cross_down.iat[i] = False
                stock[1].stock_data.strategy.iat[i] = True
                if i < len(stock[1].stock_data) - 1:
                    stock[1].stock_data.buy_price.iat[i] = stock[1].stock_data.open.iloc[i + 1]
                else:
                    stock[1].stock_data.buy_price.iat[i] = stock[1].stock_data.close.iloc[i]
                stock[1].stock_data.risk.iat[i] = max(stock[1].stock_data.low.iloc[i],
                                                      stock[1].stock_data.risk.iloc[i - 1],
                                                      (stock[1].stock_data.buy_price.iloc[i] -
                                                       stock[1].stock_data.ATRr_14.iloc[i]))
                stock[1].stock_data.reward.iat[i] = stock[1].stock_data.buy_price.iloc[i] + \
                                                    ((stock[1].stock_data.buy_price.iloc[i] -
                                                      stock[1].stock_data.risk.iloc[i]) *
                                                     float(arguments.manage.split('_')[-1]))
            else:
                stock[1].stock_data.buy_price.iat[i] = stock[1].stock_data.buy_price.iloc[i - 1]
                stock[1].stock_data.cross_down.iat[i] = stock[1].stock_data.cross_down.iat[i - 1]
                stock[1].stock_data.cross_up.iat[i] = stock[1].stock_data.cross_up.iat[i - 1]
                stock[1].stock_data.risk.iat[i] = stock[1].stock_data.risk.iloc[i - 1]
                stock[1].stock_data.reward.iat[i] = stock[1].stock_data.reward.iloc[i - 1]
        else:
            if stock[1].stock_data.buy_price.iloc[i - 1] != 0.0:
                stock[1].stock_data.backtest_profit.iat[i] = \
                    stock[1].stock_data.backtest_profit.iloc[i - 1] + \
                    stock[1].stock_data.close.iloc[i - 1] - \
                    stock[1].stock_data.buy_price.iloc[i - 1]
                stock[1].stock_data.sell_price.iat[i] = stock[1].stock_data.close.iloc[i - 1]
            elif (stock[1].stock_data.risk.iloc[i] < stock[1].stock_data.low.iloc[i]) and \
                    (stock[1].stock_data.reward.iloc[i] < stock[1].stock_data.high.iloc[i]):
                pass
            elif stock[1].stock_data.risk.iloc[i] < stock[1].stock_data.low.iloc[i]:
                stock[1].stock_data.backtest_profit.iat[i] = \
                    stock[1].stock_data.backtest_profit.iloc[i - 1] - \
                    (stock[1].stock_data.buy_price.iloc[i] - stock[1].stock_data.risk.iloc[i])
                stock[1].stock_data.sell_price.iat[i] = stock[1].stock_data.risk.iloc[i]
            elif stock[1].stock_data.reward.iloc[i] < stock[1].stock_data.high.iloc[i]:
                stock[1].stock_data.backtest_profit.iat[i] = \
                    stock[1].stock_data.backtest_profit.iloc[i - 1] + \
                    (stock[1].stock_data.reward.iloc[i] - stock[1].stock_data.buy_price.iloc[i])
                stock[1].stock_data.sell_price.iat[i] = stock[1].stock_data.reward.iloc[i]
            else:
                stock[1].stock_data.cross_down.iat[i] = False
                stock[1].stock_data.cross_up.iat[i] = False
                stock[1].stock_data.risk.iat[i] = 0.0
                stock[1].stock_data.reward.iat[i] = 0.0
                stock[1].stock_data.buy_price.iat[i] = 0.0

    if arguments.run == 'backtest':
        stock[1].stock_data.to_csv(path_or_buf=f'backtest_results/{stock[0]}_backtest.csv', na_rep='n/a', index=False)

    print(stock[1].stock_data)

    return stock[1].stock_data


def stochastic_supertrend(stock_data, arguments):
    with futures.ProcessPoolExecutor(max_workers=2) as indicator_executor:
        for each_stock, stock_list_results in zip(stock_data,
                                                  indicator_executor.map(stochastic_supertrend_concurrent,
                                                                         stock_data.items(),
                                                                         repeat(arguments))):
            stock_data[each_stock].stock_data = stock_list_results
    if arguments.run == 'live':
        for each_stock, value in list(stock_data.items()):
            if not stock_data[each_stock].stock_data.strategy.iloc[-1] or \
                    stock_data[each_stock].stock_data.risk.iloc[-1] == 0.0 or \
                    stock_data[each_stock].stock_data.reward.iloc[-1] == 0.0:
                del stock_data[each_stock]
