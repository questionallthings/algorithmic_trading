#!/usr/bin/env python3

# Imports
from argparse import ArgumentParser, RawTextHelpFormatter
import datetime
import sys

import historical_stock_data_manager


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


def main():
    print(f'{datetime.datetime.now()} :: Starting')
    arguments = set_parser()
    if arguments.run == 'backtest':
        print(f'{datetime.datetime.now()} :: Running {arguments.run}.')
    elif arguments.run == 'update':
        print(f'{datetime.datetime.now()} :: Running {arguments.run}.')
        print(f'{datetime.datetime.now()} :: Updating data files.')
        historical_stock_data_manager.update_data()
        print(f'Program took {datetime.datetime.now() - start_time} to run.')
        sys.exit()
    elif arguments.run == 'live':
        print(f'{datetime.datetime.now()} :: Running {arguments.run}.')
    else:
        print(f'No running state defined.')
    print(arguments)


if __name__ == "__main__":
    start_time = datetime.datetime.now()
    main()
    print(f'Program took {datetime.datetime.now() - start_time} to complete.')
