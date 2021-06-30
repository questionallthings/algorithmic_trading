import pandas
from itertools import repeat
from concurrent import futures
import numpy as np
import logging
import strategies


def run_backtest(stock_data, arguments):
    logging.info('Starting backtest')
    logging.info(f'Running {arguments["strategy"]}')
    wins = 0
    losses = 0
    profits = 0.0
    with futures.ProcessPoolExecutor() as indicator_executor:
        for each_symbol, stock_data_results in zip(stock_data, indicator_executor.map(getattr(strategies,
                                                                                              arguments['strategy']),
                                                                                      stock_data.items(),
                                                                                      repeat(arguments))):
            stock_data[each_symbol].data = stock_data_results
    for each in stock_data:
        last_valid_profit_index = stock_data[each].data.backtest_profit_percentage.last_valid_index()
        profits += stock_data[each].data.backtest_profit_percentage.loc[last_valid_profit_index]
        if True in stock_data[each].data.value_counts(subset="win"):
            wins += stock_data[each].data.value_counts(subset="win")[True]
        if True in stock_data[each].data.value_counts(subset="loss"):
            losses += stock_data[each].data.value_counts(subset="loss")[True]
    print(f'Stock Count: {len(stock_data)}')
    print(f'Win(s): {wins}')
    print(f'Average Win(s): {round(wins / len(stock_data), 2)}')
    print(f'Loss(es): {losses}')
    print(f'Average Loss(es): {round(losses / len(stock_data), 2)}')
    print(f'Win/Loss Ratio: {round(wins / losses, 2)}')
    print(f'Profit Percentage: {profits}')
    print(f'Average Percentage: {round(profits / len(stock_data), 2)}')
