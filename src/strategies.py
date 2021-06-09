from concurrent import futures
from itertools import repeat
import pandas_ta as ta


def stochastic_supertrend_concurrent(stock, bt=False):
    strategy_orders = []
    strategy_risk = 0
    strategy_reward = 0
    super_stochastic_risk_low_begin = 0
    super_stochastic_risk_low_end = 0
    cross_ups = []
    cross_downs = []
    cross_up_found = False
    cross_down_found = False
    stock[1].daily_stock_data.ta.ema(length=200, append=True)
    if not bt and (stock[1].daily_stock_data.EMA_200.iloc[-1] >= stock[1].daily_stock_data.close.iloc[-1]):
        return False, strategy_orders
    stock[1].daily_stock_data.ta.supertrend(append=True)
    if not bt and (stock[1].daily_stock_data['SUPERTd_7_3.0'].iloc[-1] <= 0):
        return False, strategy_orders
    stock[1].daily_stock_data.ta.stochrsi(append=True)
    if not bt and not ((stock[1].daily_stock_data.STOCHRSIk_14_14_3_3.iloc[-1] >
                        stock[1].daily_stock_data.STOCHRSId_14_14_3_3.iloc[-1]) and
                       (stock[1].daily_stock_data.STOCHRSIk_14_14_3_3.iloc[-2] <
                        stock[1].daily_stock_data.STOCHRSId_14_14_3_3.iloc[-2])):
        return False, strategy_orders
    for i in range(1, len(stock[1].daily_stock_data)):
        if (stock[1].daily_stock_data.STOCHRSIk_14_14_3_3.iloc[-i] >
            stock[1].daily_stock_data.STOCHRSId_14_14_3_3.iloc[-i]) and \
                (stock[1].daily_stock_data.STOCHRSIk_14_14_3_3.iloc[-i - 1] <
                 stock[1].daily_stock_data.STOCHRSId_14_14_3_3.iloc[-i - 1]):
            cross_ups.append(-i)
    for i in range(1, len(stock[1].daily_stock_data)):
        if (stock[1].daily_stock_data.STOCHRSIk_14_14_3_3.iloc[-i] <
            stock[1].daily_stock_data.STOCHRSId_14_14_3_3.iloc[-i]) and \
                (stock[1].daily_stock_data.STOCHRSIk_14_14_3_3.iloc[-i - 1] >
                 stock[1].daily_stock_data.STOCHRSId_14_14_3_3.iloc[-i - 1]):
            cross_downs.append(-i)
    stock[1].daily_stock_data.ta.atr(append=True)
    for i in range(1, len(stock[1].daily_stock_data)):
        if -i in cross_ups and not cross_up_found:
            cross_up_found = True
            super_stochastic_risk_low_end = -i
        elif -i in cross_downs and not cross_down_found:
            cross_down_found = True
            super_stochastic_risk_low_begin = -i - 1
        if cross_up_found and cross_down_found:
            cross_down_found = False
            cross_up_found = False
            strategy_risk = round(stock[1].daily_stock_data.ATRr_14.iloc[super_stochastic_risk_low_end], 4)
            for x in range(super_stochastic_risk_low_begin, super_stochastic_risk_low_end):
                if (stock[1].daily_stock_data.close.iloc[super_stochastic_risk_low_end] >
                        stock[1].daily_stock_data.low.iloc[x]) and \
                        ((stock[1].daily_stock_data.close.iloc[super_stochastic_risk_low_end] -
                          stock[1].daily_stock_data.low.iloc[x]) < strategy_risk):
                    strategy_risk = stock[1].daily_stock_data.close.iloc[super_stochastic_risk_low_end] - \
                                    stock[1].daily_stock_data.low.iloc[x]
            strategy_reward = strategy_risk * 1.5
            strategy_orders.append([stock[1].daily_stock_data.date.iloc[super_stochastic_risk_low_end],
                                    round(stock[1].daily_stock_data.close.iloc[super_stochastic_risk_low_end] -
                                          strategy_risk, 2),
                                    round(stock[1].daily_stock_data.close.iloc[super_stochastic_risk_low_end], 2),
                                    round(stock[1].daily_stock_data.close.iloc[super_stochastic_risk_low_end] +
                                          strategy_reward, 2)])
            if not bt:
                return True, [stock[1].daily_stock_data.date.iloc[super_stochastic_risk_low_end],
                              round(stock[1].daily_stock_data.close.iloc[super_stochastic_risk_low_end] -
                                    strategy_risk, 2),
                              round(stock[1].daily_stock_data.close.iloc[super_stochastic_risk_low_end], 2),
                              round(stock[1].daily_stock_data.close.iloc[super_stochastic_risk_low_end] +
                                    strategy_reward, 2)]

    return True, strategy_orders


def stochastic_supertrend(stock_data, backtest=False):
    with futures.ProcessPoolExecutor(max_workers=2) as indicator_executor:
        for each_stock, stock_list_results in zip(stock_data,
                                                  indicator_executor.map(stochastic_supertrend_concurrent,
                                                                         stock_data.items(),
                                                                         repeat(backtest))):
            stock_data[each_stock].strategies['stochastic_supertrend'], \
            stock_data[each_stock].strategy_orders = stock_list_results
    if not backtest:
        for each_stock, value in list(stock_data.items()):
            if not stock_data[each_stock].strategies['stochastic_supertrend']:
                del stock_data[each_stock]


def three_eight_trap(stock_data, backtest=False):
    stocks_meeting_strategy = []

    return stocks_meeting_strategy


def ema_crossover(stock_data, backtest=False):
    stocks_meeting_strategy = []

    return stocks_meeting_strategy
