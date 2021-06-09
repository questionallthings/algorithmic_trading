#!/usr/bin/env python3

# Imports
from argparse import ArgumentParser, RawTextHelpFormatter
import datetime
import sys
import os

import historical_stock_data_manager
import strategies

stock_data = {}
stock_files_directory = 'stocks/'


class StockData:
    def __init__(self):
        self.daily_stock_data = ''
        self.strategies = {}
        self.strategy_orders = []


def set_parser():
    strategy_options = {'ss': 'stochastic_supertrend',
                        'tet': 'three_eight_trap',
                        'ec': 'ema_crossover'}
    parser = ArgumentParser(formatter_class=RawTextHelpFormatter)
    subparsers = parser.add_subparsers()
    run_parser = subparsers.add_parser('run', help='run -h')
    exclusive_group = run_parser.add_mutually_exclusive_group()
    exclusive_group.add_argument('-b', '--backtest',
                                 action='store_const', dest='run', const='backtest',
                                 help='This will force a backtest of any strategy selected.')
    exclusive_group.add_argument('-u', '--update',
                                 action='store_const', dest='run', const='update',
                                 help='This will force an update of the historical daily stock data.')
    exclusive_group.add_argument('-l', '--live',
                                 action='store_const', dest='run', const='live',
                                 help='This will run the program live with no back testing or update.')
    parser.add_argument('-s', '--strategy', choices=strategy_options, default='ss', nargs='*',
                        help='\n'.join(f'{key}: {value}' for key, value in strategy_options.items()),
                        metavar='S')
    parser.add_argument('-v', '--version', action='version', version='Algorithmic Trading 0.0.1')
    filter_parser = subparsers.add_parser('filter', help='filter -h')
    filter_parser.add_argument('-min', dest='close_min', type=int,
                               help='Minimum current closing value.')
    filter_parser.add_argument('-max', dest='close_max', type=int,
                               help='Maximum current closing value.')
    filter_parser.add_argument('-avg_30', dest='avg_30_volume', type=int,
                               help='Average volume over 30 days.')
    parser.set_defaults(run='live',
                        close_min=5,
                        close_max=100,
                        avg_30_volume=1000000)

    return parser.parse_args()


def filter_stock_list(filter_options):
    print(f'{datetime.datetime.now()} :: Importing stock data files.')
    historical_stock_data_manager.import_data(stock_data)
    print(f'{datetime.datetime.now()} :: Imported {len(stock_data)} files.')
    for key, value in list(stock_data.items()):
        if (value.daily_stock_data.Volume.iloc[-31:-1].min() < filter_options.avg_30_volume) or \
                (value.daily_stock_data.Close.iloc[-1] > filter_options.close_max) or \
                (value.daily_stock_data.Close.iloc[-1] < filter_options.close_min):
            del stock_data[key]


def run_backtest(strategy):
    if strategy == 'ss':
        strategies.stochastic_supertrend(stock_data, backtest=True)
    elif strategy == 'tet':
        strategies.three_eight_trap(stock_data, backtest=True)
    elif strategy == 'ec':
        strategies.ema_crossover(stock_data, backtest=True)
    else:
        print(f'No strategy defined for backtest run.')


def run_live(strategy):
    if strategy == 'ss':
        strategies.stochastic_supertrend(stock_data)
    elif strategy == 'tet':
        strategies.three_eight_trap(stock_data)
    elif strategy == 'ec':
        strategies.ema_crossover(stock_data)
    else:
        print(f'No strategy defined for live run.')


def main():
    print(f'{datetime.datetime.now()} :: Starting')
    arguments = set_parser()
    for each_stock in os.listdir(stock_files_directory):
        stock_data[each_stock.split('_')[0]] = StockData()
    if arguments.run == 'backtest':
        print(f'{datetime.datetime.now()} :: Running {arguments.run}.')
        filter_stock_list(arguments)
        print(f'{datetime.datetime.now()} :: Filtered down to {len(stock_data)} stocks.')
        run_backtest(arguments.strategy)
    elif arguments.run == 'update':
        print(f'{datetime.datetime.now()} :: Running {arguments.run}.')
        print(f'{datetime.datetime.now()} :: Updating data files.')
        historical_stock_data_manager.update_data()
        print(f'Program took {datetime.datetime.now() - start_time} to run.')
        sys.exit()
    elif arguments.run == 'live':
        print(f'{datetime.datetime.now()} :: Running {arguments.run}.')
        filter_stock_list(arguments)
        print(f'{datetime.datetime.now()} :: Filtered down to {len(stock_data)} stocks.')
        run_live(arguments.strategy)
        print(f'{datetime.datetime.now()} :: Strategies filtered down to {len(stock_data)} stocks.')
        for each_stock in stock_data:
            if stock_data[each_stock].strategies['stochastic_supertrend']:
                print(stock_data[each_stock].strategy_orders)
    else:
        print(f'No running state defined.')


if __name__ == "__main__":
    start_time = datetime.datetime.now()
    main()
    print(f'Program took {datetime.datetime.now() - start_time} to complete.')
