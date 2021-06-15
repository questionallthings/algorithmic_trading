#!/usr/bin/env python3

# Imports
from argparse import ArgumentParser, RawTextHelpFormatter
import datetime
import sys
import os
import math
import json

import alpaca_trade_api
import pandas as pd

import historical_stock_data_manager
import strategies
from tests import testing


stock_data = {}
stock_files_directory = 'stocks/'
backtest_results_directory = 'backtest_results/'
stock_list_file = 'stock_list.txt'
trade_api = alpaca_trade_api.REST()
account = trade_api.get_account()

pd.set_option('max_columns', 999)
pd.set_option('max_colwidth', 999)
pd.set_option('max_rows', 999)
pd.set_option('display.expand_frame_repr', False)


class StockData:
    def __init__(self):
        self.stock_data = ''
        self.quote_type = ''


def set_parser():
    strategy_options = ['stochastic_supertrend']
    money_management_options = ['ratio_1_1',
                                'ratio_1_1.5',
                                'ratio_1_2',
                                'take_profit_1_1',
                                'take_profit_1_1.5',
                                'take_profit_1_2']
    period_options = ['1mo',
                      '1y',
                      'max']
    timeframe_options = ['5m',
                         '60m',
                         '1d']
    parser = ArgumentParser(formatter_class=RawTextHelpFormatter)
    subparsers = parser.add_subparsers()
    run_parser = subparsers.add_parser('run', help='run -h')
    run_exclusive_group = run_parser.add_mutually_exclusive_group()
    run_exclusive_group.add_argument('-b', '--backtest_results',
                                     action='store_const', dest='run', const='backtest_results',
                                     help='This will force a backtest_results of any strategy selected.')
    run_exclusive_group.add_argument('-u', '--update',
                                     action='store_const', dest='run', const='update',
                                     help='This will force an update of the historical daily stock data.')
    run_exclusive_group.add_argument('-l', '--live',
                                     action='store_const', dest='run', const='live',
                                     help='This will run the program live with no back testing or update.')
    parser.add_argument('-m', '--manage', choices=money_management_options,
                        help='\n'.join(f'{manage_item}' for manage_item in money_management_options),
                        metavar='M')
    parser.add_argument('-s', '--strategy', choices=strategy_options,
                        help='\n'.join(f'{strategy_item}' for strategy_item in strategy_options),
                        metavar='S')
    parser.add_argument('-p', '--period', choices=period_options,
                        help='\n'.join(f'{period_item}' for period_item in period_options),
                        metavar='P')
    parser.add_argument('-t', '--timeframe', choices=timeframe_options,
                        help='\n'.join(f'{timeframe_item}' for timeframe_item in timeframe_options),
                        metavar='T')
    parser.add_argument('-v', '--version', action='version', version='Algorithmic Trading 0.0.1')
    filter_parser = subparsers.add_parser('filter', help='filter -h')
    filter_parser.add_argument('-min', dest='close_min', type=int,
                               help='Minimum current closing value.')
    filter_parser.add_argument('-max', dest='close_max', type=int,
                               help='Maximum current closing value.')
    filter_parser.add_argument('-avg_30', dest='avg_30_volume', type=int,
                               help='Average volume over 30 days.')
    filter_parser.add_argument('-quote_type', dest='quote_type', type=str,
                               help='What type of stock to filter for.')
    parser.set_defaults(run='live',
                        period=period_options[2],
                        timeframe=timeframe_options[2],
                        manage=money_management_options[1],
                        strategy=strategy_options[0],
                        close_min=5,
                        close_max=100,
                        avg_30_volume=1000000,
                        quote_type='EQUITY')

    return parser.parse_args()


def filter_stock_list(filter_options):
    print(f'{datetime.datetime.now()} :: Importing stock data files.')
    historical_stock_data_manager.import_data(stock_data, filter_options)
    print(f'{datetime.datetime.now()} :: Imported {len(stock_data)} files.')
    with open(stock_list_file) as file:
        ticker_data = json.load(file)
    for each_ticker in ticker_data:
        if each_ticker['symbol'] in stock_data:
            stock_data[each_ticker['symbol']].quote_type = each_ticker['quoteType']
    for key, value in list(stock_data.items()):
        if (value.stock_data.volume.iloc[-31:-1].min() < filter_options.avg_30_volume) or \
                (value.stock_data.close.iloc[-1] > filter_options.close_max) or \
                (value.stock_data.close.iloc[-1] < filter_options.close_min) or \
                (value.quote_type != 'EQUITY'):
            del stock_data[key]


def run_backtest(strategy_stock_data):
    pass


def run_strategy(strategy, arguments):
    getattr(strategies, strategy)(stock_data, arguments)


def order(stock_data_order):
    test = trade_api.get_last_trade(symbol=stock_data_order.symbol)
    if stock_data_order.buy_price > test.price > stock_data_order.risk:
        print(f'Stock - {stock_data_order.symbol} :: '
              f'Risk - {stock_data_order.risk} :: '
              f'Price - {stock_data_order.buy_price} :: '
              f'Last Trade - {test.price}:: '
              f'Reward - {stock_data_order.reward}')
        trade_api.submit_order(symbol=stock_data_order.symbol,
                               side='buy',
                               type='stop',
                               stop_price=stock_data_order.buy_price,
                               qty=math.floor((float(account.cash) * .01) / stock_data_order.buy_price),
                               time_in_force='day',
                               order_class='bracket',
                               take_profit=dict(limit_price=stock_data_order.reward),
                               stop_loss=dict(stop_price=stock_data_order.risk,
                                              limit_price=str(round(stock_data_order.risk * .99, 2))))


def main():
    print(f'{datetime.datetime.now()} :: Starting')
    arguments = set_parser()
    for each_stock in os.listdir(stock_files_directory):
        stock_data[each_stock.split('_')[0]] = StockData()
    print(f'{datetime.datetime.now()} :: Using the following arguments: {arguments}.')
    if arguments.run == 'update':
        print(f'{datetime.datetime.now()} :: Running {arguments.run}.')
        historical_stock_data_manager.update_stock_list(trade_api.list_assets())
        historical_stock_data_manager.update_data(arguments)
        print(f'Program took {datetime.datetime.now() - start_time} to run.')
        sys.exit()
    else:
        print(f'{datetime.datetime.now()} :: Running {arguments.run}.')
        filter_stock_list(arguments)
        print(f'{datetime.datetime.now()} :: Filtered down to {len(stock_data)} stocks.')
        run_strategy(arguments.strategy, arguments)
        if arguments.run == 'backtest_results':
            for each_stock in stock_data:
                run_backtest(stock_data[each_stock].stock_data)
        elif arguments.run == 'live':
            print(f'{datetime.datetime.now()} :: Strategy \'{arguments.strategy}\' filtered list down to '
                  f'{len(stock_data)} stock(s).')
            for each_stock in stock_data:
                order(stock_data[each_stock].stock_data.iloc[-1])


if __name__ == "__main__":
    start_time = datetime.datetime.now()
    main()
    print(f'Program took {datetime.datetime.now() - start_time} to complete.')
