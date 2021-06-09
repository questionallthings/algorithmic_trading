#!/usr/bin/env python3

# Imports
from argparse import ArgumentParser, RawTextHelpFormatter
import json

# Command Line Arguments to Introduce Later
strategy_options = {'ss': 'stochastic_supertrend',
                    'tet': 'three_eight_trap',
                    'ec': 'ema_crossover'}


def set_parser():
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
    arguments = set_parser()


if __name__ == "__main__":
    main()
