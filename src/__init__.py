# Imports
from argparse import ArgumentParser, RawTextHelpFormatter
from concurrent import futures
from datetime import datetime, timedelta
import mplfinance as mpf
from itertools import repeat
import math

import alpaca_trade_api
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
        self.data.loc[:, 'buy_price'] = 0.0
        self.data.loc[:, 'sell_price'] = 0.0
        self.data.loc[:, 'risk'] = 0.0
        self.data.loc[:, 'reward'] = 0.0


def set_parser():
    run_options = ['backtest',
                   'strategy',
                   'live']
    strategy_options = ['stochastic_supertrend',
                        'rsi_stochastic_200ema']
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
    parser.set_defaults(run=run_options[1],
                        period=period_options[2],
                        timeframe=timeframe_options[2],
                        manage=money_management_options[1],
                        strategy=strategy_options[0],
                        close_min=3,
                        close_max=4,
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
            stock_data[each_stock[0]].data.set_index('date', inplace=True)
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
    strategy_df = getattr(strategies, strategy)((stock, stock_df), arguments)
    print(strategy_df.tail())
    print(f'{datetime.now()} :: Displaying finance chart window.')
    mpf.plot(sql_df[-400:],
             type='candle',
             warn_too_much_data=1000000)


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


def order(stock_data_order):
    test = trade_api.get_last_trade(symbol=stock_data_order.symbol)
    if stock_data_order.buy_price >= test.price > stock_data_order.risk:
        print(f'Stock - {stock_data_order.symbol} :: '
              f'Risk - {stock_data_order.risk} :: '
              f'Price - {stock_data_order.buy_price} :: '
              f'Last Trade - {test.price}:: '
              f'Reward - {stock_data_order.reward}')
        # '''
        trade_api.submit_order(symbol=stock_data_order.symbol,
                               side='buy',
                               type='stop',
                               stop_price=stock_data_order.buy_price,
                               qty=math.floor((float(account.cash) * .01) / stock_data_order.buy_price),
                               time_in_force='gtc',
                               order_class='bracket',
                               take_profit=dict(limit_price=stock_data_order.reward),
                               stop_loss=dict(stop_price=stock_data_order.risk,
                                              limit_price=str(round(stock_data_order.risk * .99, 2))))
        # '''


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
                      stock='HPQ',
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
                order(stock_data[each_stock].data.iloc[-1])


if __name__ == "__main__":
    start_time = datetime.now()
    main()
    print(f'Program took {datetime.now() - start_time} to complete.')
