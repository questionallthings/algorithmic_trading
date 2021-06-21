# Imports
import sys
from argparse import ArgumentParser, RawTextHelpFormatter
from concurrent import futures
from datetime import datetime, timedelta
import mplfinance as mpf
from itertools import repeat
import math
import re

import alpaca_trade_api
import numpy as np
import pandas as pd
import pymysql

import strategies
import db_manager


stock_data = {}
stock_files_directory = 'stocks/'
backtest_results_directory = 'backtest_results/'
trade_api = alpaca_trade_api.REST()
account = trade_api.get_account()

pd.set_option('max_columns', 999)
pd.set_option('max_colwidth', 999)
pd.set_option('max_rows', 999)
pd.set_option('display.expand_frame_repr', False)


class Stock:
    def __init__(self, data=None, info=None):
        self.data = data
        self.info = info

    def set_data(self):
        self.data.loc[:, 'strategy'] = False
        self.data.loc[:, 'backtest_profit'] = 0.0
        self.data.loc[:, 'buy_price'] = np.nan
        self.data.loc[:, 'sell_price'] = np.nan
        self.data.loc[:, 'risk'] = 0.0
        self.data.loc[:, 'reward'] = 0.0


def set_parser():
    run_options = ['live',
                   'backtest',
                   'strategy']
    strategy_options = ['stochastic_supertrend',
                        'rsi_stochastic_200ema',
                        'ichimoku']
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
    type_options = ['ALL',
                    'EQUITY',
                    'ETF']
    parser = ArgumentParser(formatter_class=RawTextHelpFormatter)
    subparsers = parser.add_subparsers()
    parser.add_argument('-r', '--run', choices=run_options,
                        help='\n'.join(f'{run_item}' for run_item in run_options),
                        metavar='R')
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
    filter_parser.add_argument('-quote_type', '--quote_type', choices=type_options,
                               help='\n'.join(f'{type_item}' for type_item in type_options),
                               metavar='Q')
    parser.set_defaults(run=run_options[2],
                        period=period_options[2],
                        timeframe=timeframe_options[2],
                        manage=money_management_options[2],
                        strategy=strategy_options[2],
                        close_min=5,
                        close_max=100,
                        avg_30_volume=1000000,
                        quote_type=type_options[1])

    return parser.parse_args()


def import_filter_stocks(connection, filter_options):
    print(f'{datetime.now()} :: Importing stock data.')
    stock_list = []
    with connection.cursor() as filter_query:
        filter_query.execute(f'SELECT symbol FROM daily_bars '
                             f'WHERE date BETWEEN '
                             f'\'{datetime.strftime(datetime.today() - timedelta(days=5), "%Y-%m-%d")}\' '
                             f'AND \'{datetime.strftime(datetime.today() - timedelta(days=1), "%Y-%m-%d")}\' '
                             f'AND close BETWEEN {filter_options.close_min} AND {filter_options.close_max} '
                             f'GROUP BY symbol HAVING AVG(volume) > {filter_options.avg_30_volume}')
        filter_query_results = filter_query.fetchall()
    for each_stock in filter_query_results:
        if each_stock['symbol'] in stock_data:
            stock_list.append(each_stock['symbol'])
    sql_df = pd.read_sql_query(f'SELECT * FROM daily_bars WHERE symbol in {tuple(stock_list)}', connection)
    sql_grouped_df = list(sql_df.groupby('symbol'))
    for each_stock in sql_grouped_df:
        if len(each_stock[1]) > 400:
            stock_data[each_stock[0]].data = each_stock[1]
            stock_data[each_stock[0]].data.set_index(pd.to_datetime(stock_data[each_stock[0]].data.date), inplace=True)
            stock_data[each_stock[0]].data.sort_index(inplace=True)
            stock_data[each_stock[0]].data.drop(columns='symbol', inplace=True)
            stock_data[each_stock[0]].set_data()
    for each_key in list(stock_data):
        if stock_data[each_key].data is None or len(stock_data[each_key].data) < 400:
            del(stock_data[each_key])


def run_backtest(strategy_stock_data):
    print(f'{datetime.now()} :: Saving backtest results.')
    strategy_stock_data.to_csv(path_or_buf=f'backtest_results/{strategy_stock_data.symbol.iloc[-1]}_backtest.csv',
                               na_rep='n/a',
                               index=False)


def test_strategy(connection, stock, strategy, arguments):
    print(f'{datetime.now()} :: Importing test stock data.')
    sql_df = pd.read_sql_query(f'SELECT * FROM daily_bars WHERE symbol=\'{stock}\'', connection)
    sql_df.set_index(pd.to_datetime(sql_df.date), inplace=True)
    sql_df.sort_index(inplace=True)
    sql_df.drop(columns='symbol', inplace=True)
    stock_df = Stock(data=sql_df)
    stock_df.set_data()
    stock_df.data = getattr(strategies, strategy)((stock, stock_df), arguments)
    mpf_display_count = 200
    print(stock_df.data.tail(80))
    add_plot_indicators = []
    for each_column in stock_df.data.columns:
        if re.match('^EMA', each_column):
            add_plot_indicators.append(mpf.make_addplot(stock_df.data[each_column][-mpf_display_count:]))
        elif re.match('^SUPERT', each_column):
            add_plot_indicators.append(mpf.make_addplot(stock_df.data['SUPERT_7_3.0'][-mpf_display_count:]))
        #elif each_column == 'buy_price':
        #    add_plot_indicators.append(mpf.make_addplot(stock_df.data['buy_price'][-mpf_display_count:] * .99,
        #                                                type='scatter',
        #                                                markersize=200,
        #                                                marker='^'))
        #elif each_column == 'sell_price':
        #    add_plot_indicators.append(mpf.make_addplot(stock_df.data['sell_price'][-mpf_display_count:] * 1.01,
        #                                                type='scatter',
        #                                                markersize=200,
        #                                                marker='v'))
        elif re.match('^STOCHRSI', each_column):
            add_plot_indicators.append(mpf.make_addplot(stock_df.data[each_column][-mpf_display_count:], panel=2))
        elif each_column == 'backtest_profit':
            add_plot_indicators.append(mpf.make_addplot(stock_df.data[each_column][-mpf_display_count:], panel=2))
        elif each_column == 'ISA_9':
            stock_df.data['ISA_9'].fillna(0.0, inplace=True)
            stock_df.data['ISB_26'].fillna(0.0, inplace=True)
            add_plot_indicators.append(mpf.make_addplot(stock_df.data['ITS_9'][-mpf_display_count:],
                                                        color='lime', width=0.9, alpha=0.75))
            add_plot_indicators.append(mpf.make_addplot(stock_df.data['IKS_26'][-mpf_display_count:],
                                                        color='r', width=0.8, alpha=0.75))
            add_plot_indicators.append(mpf.make_addplot(stock_df.data['ICS_26'][-mpf_display_count:],
                                                        color='black', linestyle='dotted', width=1))
            add_plot_indicators.append(mpf.make_addplot(stock_df.data['ISA_9'][-mpf_display_count:],
                                                        color='y', width=0.5, alpha=0.5))
            add_plot_indicators.append(mpf.make_addplot(stock_df.data['ISB_26'][-mpf_display_count:],
                                                        color='purple', width=0.5, alpha=0.5))
    mpf_colors = mpf.make_marketcolors(up='g', down='r', volume='in', edge='k')
    mpf_style = mpf.make_mpf_style(marketcolors=mpf_colors)
    mpf.plot(data=stock_df.data[-mpf_display_count:],
             style=mpf_style,
             fill_between={'y1': stock_df.data['ISA_9'][-mpf_display_count:].values,
                           'y2': stock_df.data['ISB_26'][-mpf_display_count:].values,
                           'alpha': 0.25},
             type='candle',
             addplot=add_plot_indicators,
             volume=True,
             warn_too_much_data=1000000000,
             title=f'{stock}')


def run_strategy(strategy, arguments):
    with futures.ProcessPoolExecutor(max_workers=2) as indicator_executor:
        for each_stock, stock_list_results in zip(stock_data,
                                                  indicator_executor.map(getattr(strategies, strategy),
                                                                         stock_data.items(),
                                                                         repeat(arguments))):
            stock_data[each_stock].data = stock_list_results
    if arguments.run == 'live':
        for each_stock, value in list(stock_data.items()):
            if not stock_data[each_stock].data.strategy.iloc[-1] or \
                    stock_data[each_stock].data.risk.iloc[-1] == 0.0 or \
                    stock_data[each_stock].data.reward.iloc[-1] == 0.0:
                del stock_data[each_stock]


def order(stock_data_order, symbol):
    test = trade_api.get_last_trade(symbol=symbol)
    if stock_data_order.buy_price >= test.price > stock_data_order.risk:
        print(f'Stock - {symbol} :: '
              f'Risk - {stock_data_order.risk} :: '
              f'Price - {stock_data_order.buy_price} :: '
              f'Last Trade - {test.price}:: '
              f'Reward - {stock_data_order.reward}')
        '''
        trade_api.submit_order(symbol=symbol,
                               side='buy',
                               type='stop',
                               stop_price=stock_data_order.buy_price,
                               qty=math.floor((float(account.cash) * .01) / stock_data_order.buy_price),
                               time_in_force='gtc',
                               order_class='bracket',
                               take_profit=dict(limit_price=stock_data_order.reward),
                               stop_loss=dict(stop_price=stock_data_order.risk,
                                              limit_price=str(round(stock_data_order.risk * .99, 2))))
        '''


def main():
    print(f'{datetime.now()} :: Starting')
    arguments = set_parser()
    print(f'{datetime.now()} :: Using the following arguments: {arguments}.')
    database = db_manager.Database()
    memsql_server = pymysql.connect(host=database.memsql_host,
                                    user=database.memsql_user,
                                    password=database.memsql_password,
                                    port=int(database.memsql_port),
                                    database=database.database_name,
                                    cursorclass=pymysql.cursors.DictCursor)
    if arguments.run == 'strategy':
        test_strategy(connection=memsql_server,
                      stock='ABEV',
                      strategy=arguments.strategy,
                      arguments=arguments)  # HPQ is used due to largest set
    else:
        with memsql_server.cursor() as db_query:
            db_query.execute('SELECT * FROM stock_info')
            memsql_stock_list_result = db_query.fetchall()
        for each_result in memsql_stock_list_result:
            stock_data[each_result['symbol']] = Stock(info=each_result)
        if arguments.quote_type != 'ALL':
            for each_stock, value in list(stock_data.items()):
                if stock_data[each_stock].info['quoteType'] != arguments.quote_type:
                    del stock_data[each_stock]
        print(f'{datetime.now()} :: Running {arguments.run}.')
        import_filter_stocks(memsql_server, arguments)
        print(f'{datetime.now()} :: Filtered down to {len(stock_data)} stocks.')
        run_strategy(arguments.strategy, arguments)
        print(f'{datetime.now()} :: Strategy \'{arguments.strategy}\' filtered list down to '
              f'{len(stock_data)} stock(s).')
        if arguments.run == 'backtest':
            for each_stock in stock_data:
                run_backtest(stock_data[each_stock].data)
        elif arguments.run == 'live':
            for each_stock in stock_data:
                if stock_data[each_stock].data.buy_price.iloc[-1] > 0:
                    order(stock_data[each_stock].data.iloc[-1], each_stock)


if __name__ == "__main__":
    start_time = datetime.now()
    main()
    print(f'Program took {datetime.now() - start_time} to complete.')
