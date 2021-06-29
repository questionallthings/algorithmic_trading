from concurrent import futures
from datetime import datetime, timedelta, date
from itertools import repeat
import math
import logging

import alpaca_trade_api
import numpy as np
import pandas as pd
import pymysql

import strategies
import db_manager
import alpaca_socket_manager
import development
import backtest

logging.basicConfig(format='%(asctime)s :: %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%dT%H:%M:%S',
                    level=logging.INFO)
logging.info('Started logging')

run_options = ['development', 'backtest', 'live']
strategy_options = ['stochastic_supertrend', 'rsi_stochastic_200ema', 'ichimoku']
period_options = ['1mo', '1y', 'max']
timeframe_options = ['5m', '60m', '1d']
type_options = ['ALL', 'EQUITY', 'ETF']

arguments = {'run': run_options[2],
             'strategy': strategy_options[2],
             'period': period_options[2],
             'timeframe': timeframe_options[2],
             'quote_type': type_options[1],
             'close_min': 1,
             'close_max': 200,
             'avg_30_volume': 1000000,
             'trade_cash_risk': 100}

logging.info(f'Using the following arugments: {arguments}')

stock_data = {}
stock_files_directory = 'stocks/'
backtest_results_directory = 'backtest_results/'
trade_api = alpaca_trade_api.REST()
account = trade_api.get_account()
development_stock_test = 'HPQ'  # HPQ is used due to highest amount of data.

pd.set_option('max_columns', 999)
pd.set_option('max_colwidth', 999)
pd.set_option('max_rows', 999)
pd.set_option('display.expand_frame_repr', False)


class Stock:
    def __init__(self, data=None, info=None):
        self.data = data
        self.info = info
        self.minutes = ''

    def set_data(self):
        self.data['strategy'] = False
        self.data['backtest_profit'] = 0.0
        self.data['buy_price'] = np.nan
        self.data['sell_price'] = np.nan
        self.data['risk'] = 0.0
        self.data['reward'] = 0.0


def import_filter_stocks(connection):
    logging.info(f'Importing stock data.')
    stock_list = []
    with connection.cursor() as filter_query:
        filter_query.execute(f'SELECT symbol FROM daily_bars '
                             f'WHERE date BETWEEN '
                             f'\'{datetime.strftime(datetime.today() - timedelta(days=30), "%Y-%m-%d")}\' '
                             f'AND \'{datetime.strftime(datetime.today() - timedelta(days=1), "%Y-%m-%d")}\' '
                             f'AND close BETWEEN {arguments["close_min"]} AND {arguments["close_max"]} '
                             f'GROUP BY symbol HAVING AVG(volume) > {arguments["avg_30_volume"]}')
        filter_query_results = filter_query.fetchall()
    for filter_stock in filter_query_results:
        if filter_stock['symbol'] in stock_data:
            stock_list.append(filter_stock['symbol'])
    sql_df = pd.read_sql_query(f'SELECT * FROM daily_bars WHERE symbol in {tuple(stock_list)}', connection)
    sql_grouped_df = list(sql_df.groupby('symbol'))
    for sql_group_stock in sql_grouped_df:
        if len(sql_group_stock[1]) > 400:
            stock_data[sql_group_stock[0]].data = sql_group_stock[1]
            stock_data[sql_group_stock[0]].data.set_index(pd.to_datetime(stock_data[sql_group_stock[0]].data.date),
                                                          inplace=True)
            stock_data[sql_group_stock[0]].data.sort_index(inplace=True)
            stock_data[sql_group_stock[0]].data.drop(columns='symbol', inplace=True)
            stock_data[sql_group_stock[0]].set_data()
    for each_key in list(stock_data):
        if stock_data[each_key].data is None or len(stock_data[each_key].data) < 400:
            del(stock_data[each_key])


def run_strategy(strategy):
    with futures.ProcessPoolExecutor() as indicator_executor:
        for each_symbol, stock_data_results in zip(stock_data, indicator_executor.map(getattr(strategies, strategy),
                                                                                      stock_data.items(),
                                                                                      repeat(arguments))):
            stock_data[each_symbol].data = stock_data_results
    if arguments['run'] == 'live':
        for each_symbol in list(stock_data.keys()):
            if not stock_data[each_symbol].data.strategy.iloc[-1] or \
                    stock_data[each_symbol].data.risk.iloc[-1] == 0.0 or \
                    stock_data[each_symbol].data.reward.iloc[-1] == 0.0:
                del stock_data[each_symbol]


def order(stock_data_order, symbol):
    status = False
    last_trade = trade_api.get_last_trade(symbol=symbol)
    if stock_data_order.buy_price >= last_trade.price > stock_data_order.risk:
        order_results = trade_api.submit_order(symbol=symbol,
                                               side='buy',
                                               type='stop',
                                               stop_price=stock_data_order.buy_price,
                                               qty=math.floor(arguments['trade_cash_risk'] /
                                                              (stock_data_order.buy_price -
                                                               stock_data_order.risk)),
                                               time_in_force='gtc',
                                               order_class='bracket',
                                               take_profit=dict(limit_price=stock_data_order.reward),
                                               stop_loss=dict(stop_price=stock_data_order.risk,
                                                              limit_price=str(round(stock_data_order.risk * .99, 2))))
        # '''
        if order_results.status == 'accepted':
            status = True
            logging.info({'symbol': symbol,
                          'quantity': order_results.qty,
                          'price': round(stock_data_order.buy_price, 4),
                          'risk': round(stock_data_order.buy_price - stock_data_order.risk, 4),
                          'reward': round(stock_data_order.reward - stock_data_order.buy_price, 4),
                          'volume': stock_data_order.volume})
        # '''

    return status


if __name__ == "__main__":
    start_time = datetime.now()
    logging.info('Started main function')
    database = db_manager.Database()
    memsql_server = pymysql.connect(host=database.memsql_host,
                                    user=database.memsql_user,
                                    password=database.memsql_password,
                                    port=int(database.memsql_port),
                                    database=database.database_name,
                                    cursorclass=pymysql.cursors.DictCursor)
    if arguments['run'] == 'development':
        development.test_strategy(connection=memsql_server,
                                  symbol=development_stock_test,
                                  stock_data=Stock(),
                                  arguments=arguments)
    else:
        with memsql_server.cursor() as db_query:
            db_query.execute('SELECT * FROM stock_info')
            memsql_stock_list_result = db_query.fetchall()
        if arguments['quote_type'] != 'ALL':
            for each_result in memsql_stock_list_result:
                if each_result['quoteType'] == arguments['quote_type']:
                    stock_data[each_result['symbol']] = Stock(info=each_result)
        import_filter_stocks(memsql_server)
        logging.info(f'Filtered down to {len(stock_data)} stock(s).')
        if arguments['run'] == 'backtest':
            backtest.run_backtest(stock_data=stock_data,
                                  arguments=arguments)
        else:
            run_strategy(arguments['strategy'])
            logging.info(f'Strategy \'{arguments["strategy"]}\' filtered list down to {len(stock_data)} stock(s).')
            orders = []
            current_orders = trade_api.list_orders()
            for each_order in current_orders:
                orders.append(each_order.symbol)
            for each_stock in list(stock_data.keys()):
                order_status = False
                if each_stock not in orders:
                    for date_range in range(1, 4):
                        if datetime.strftime(datetime.today() -
                                             timedelta(days=date_range), '%Y-%m-%d') in stock_data[each_stock].data:
                            if date.timetuple(datetime.today() - timedelta(days=date_range)).tm_wday not in [5, 6] and \
                                    (stock_data[each_stock].data.buy_price.loc[
                                         datetime.strftime(datetime.today() - timedelta(days=date_range),
                                                           '%Y-%m-%d')] > 0):
                                order_status = order(stock_data[each_stock].data.loc[datetime.strftime(
                                    datetime.today() - timedelta(days=date_range), '%Y-%m-%d')], each_stock)
                elif each_stock in orders:
                    order_status = True
                if not order_status:
                    del stock_data[each_stock]
            logging.info(f'Monitoring from stream {len(stock_data)} stock(s).')
            alpaca_socket_run = alpaca_socket_manager.AlpacaSocket(stock_data)
            alpaca_socket_run.alpaca_socket()

    logging.info(f'Program took {datetime.now() - start_time} to complete.')
