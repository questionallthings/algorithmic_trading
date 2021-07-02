from datetime import datetime, timedelta, date
import math
import logging

import numpy as np
import pandas as pd
import pymysql

import stock
import strategies
import db_manager
import alpaca_manager
import develop
import backtest

run_options = ['development', 'backtest', 'live']
strategy_options = ['stochastic_supertrend', 'ichimoku']
timeframe_options = ['minute', 'day']
type_options = ['ALL', 'EQUITY', 'ETF']

arguments = {'run': run_options[2],
             'strategy': strategy_options[1],
             'timeframe': timeframe_options[1],
             'quote_type': type_options[1],
             'reward': 2,
             'close_min': 1,
             'close_max': 200,
             'avg_30_volume': 1000000,
             'trade_cash_risk': 100}

stock_data = {}
account = alpaca_manager.trade_api.get_account()
development_stock_test = 'HPQ'  # HPQ is used due to highest amount of data.

pd.set_option('max_columns', 999)
pd.set_option('max_colwidth', 999)
pd.set_option('max_rows', 999)
pd.set_option('display.expand_frame_repr', False)


def import_filter_stocks(filter_data):
    logging.info(f'Importing stock data.')
    sql_grouped_df = list(filter_data.groupby('symbol'))
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


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s :: %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%dT%H:%M:%S',
                        level=logging.INFO)
    logging.info('Started logging')
    logging.info(f'Using the following arguments: {arguments}')
    start_time = datetime.now()
    logging.info('Started main function')
    database = db_manager.Database()
    with pymysql.connect(host=database.memsql_host,
                         user=database.memsql_user,
                         password=database.memsql_password,
                         port=int(database.memsql_port),
                         database=database.database_name,
                         cursorclass=pymysql.cursors.DictCursor) as memsql_connection:
        if arguments['run'] == 'development':
            logging.info('Querying memsql for development data')
            stock_data[development_stock_test] = stock.Stock()
            stock_data[development_stock_test].data = pd.read_sql_query(
                f'SELECT * FROM daily_bars WHERE symbol=\'{development_stock_test}\'',
                memsql_connection)
            stock_data[development_stock_test].set_data()
        else:
            logging.info('Querying memsql for stock info data')
            with memsql_connection.cursor() as memsql_query:
                memsql_query.execute('SELECT * FROM stock_info')
                memsql_stock_info_results = memsql_query.fetchall()
            logging.info('Querying memsql for stock daily data')
            with memsql_connection.cursor() as filter_query:
                if arguments['quote_type'] != 'ALL':
                    for each_result in memsql_stock_info_results:
                        if each_result['quoteType'] == arguments['quote_type']:
                            stock_data[each_result['symbol']] = stock.Stock(info=each_result)
                stock_list = []
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
                filter_df = pd.read_sql_query(f'SELECT * FROM daily_bars WHERE symbol in {tuple(stock_list)}',
                                              memsql_connection)
    if arguments['run'] == 'development':
        develop.test_strategy(symbol=development_stock_test, stock_data=stock_data, arguments=arguments)
    else:
        import_filter_stocks(filter_df)
        logging.info(f'Filtered down to {len(stock_data)} stock(s).')
        if arguments['run'] == 'backtest':
            backtest.run_backtest(stock_data=stock_data,
                                  arguments=arguments)
        else:
            logging.info(f'Getting Alpaca Account')
            logging.info(f'Getting Alpaca Positions')
            alpaca_positions = alpaca_manager.trade_api.list_positions()
            current_positions = []
            for each_position in alpaca_positions:
                current_positions.append(each_position.symbol)
            logging.info(f'Current Positions:\n{current_positions}')
            logging.info(f'Getting Alpaca Orders')
            alpaca_orders = alpaca_manager.trade_api.list_orders()
            current_orders = []
            for each_order in alpaca_orders:
                current_orders.append(each_order.symbol)
            logging.info(f'Current Orders:\n{current_orders}')
            strategies.run_strategy(arguments['strategy'], stock_data, arguments['reward'])
            if arguments['run'] == 'live':
                for each_symbol in list(stock_data.keys()):
                    if not stock_data[each_symbol].data.strategy.iloc[-1] or \
                            stock_data[each_symbol].data.risk.iloc[-1] == 0.0 or \
                            stock_data[each_symbol].data.reward.iloc[-1] == 0.0:
                        del stock_data[each_symbol]
            pending_orders = {}
            date_offset = 1
            if date.timetuple(datetime.today()).tm_wday == 0:
                date_offset += 2
            for each_stock in list(stock_data.keys()):
                if datetime.strftime(datetime.today() -
                                     timedelta(days=date_offset), '%Y-%m-%d') in stock_data[each_stock].data.index:
                    pending_orders[each_stock] = stock_data[each_stock].data.loc[datetime.strftime(
                        datetime.today() - timedelta(days=date_offset), '%Y-%m-%d')]
                if np.isnan(pending_orders[each_stock].buy_price):
                    del pending_orders[each_stock]
            logging.info(f'Reviewing {len(pending_orders)} stock order(s)')
            for each_position in current_positions:
                if each_position in pending_orders:
                    del pending_orders[each_position]
            for each_order in current_orders:
                if each_order in pending_orders:
                    del pending_orders[each_order]
            logging.info(f'Attempting {len(pending_orders)} order(s)')
            for each_order in list(pending_orders):
                order_status = alpaca_manager.order(pending_orders[each_order],
                                                    each_order,
                                                    arguments['trade_cash_risk'])
                if not order_status:
                    del pending_orders[each_order]
            monitor_stocks = []
            for each_order in pending_orders:
                monitor_stocks.append(each_order)
            for each_position in current_positions:
                monitor_stocks.append(each_position)
            for each_order in current_orders:
                monitor_stocks.append(each_order)
            logging.info(f'Monitoring from stream {len(monitor_stocks)} stock(s).')
            alpaca_socket_run = alpaca_manager.AlpacaSocket(monitor_stocks, stock_data)
            alpaca_socket_run.alpaca_socket()

    logging.info(f'Program took {datetime.now() - start_time} to complete.')
