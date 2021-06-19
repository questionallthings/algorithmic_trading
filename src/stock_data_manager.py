from concurrent import futures
from itertools import repeat
import os
import pymysql
import yahooquery as yq
import pandas as pd
import json
import datetime
import db_manager

stock_files_directory = 'stocks/'
stock_list_file = 'stock_list.txt'


def import_stock_data(stock_name, arguments):
    print(f'{datetime.datetime.now()} :: Importing {stock_name} historical stock data.')
    dataframe_import = pd.read_csv(filepath_or_buffer=f'{stock_files_directory}{stock_name}_'
                                                      f'{arguments.timeframe}_stock_data.txt',
                                   sep=',',
                                   index_col='date',
                                   parse_dates=True)
    dataframe_import['strategy'] = False
    dataframe_import['backtest_profit'] = 0.0
    dataframe_import['buy_price'] = 0.0
    dataframe_import['sell_price'] = 0.0
    dataframe_import['risk'] = 0.0
    dataframe_import['reward'] = 0.0

    return dataframe_import


def import_data(stock_data, arguments):
    print(f'{datetime.datetime.now()} :: Importing historical stock data.')
    with futures.ProcessPoolExecutor(max_workers=2) as import_executor:
        for each_stock, stock_list_results in zip(stock_data, import_executor.map(import_stock_data,
                                                                                  stock_data,
                                                                                  repeat(arguments))):
            stock_data[each_stock].stock_data = stock_list_results


def update_stock_data(stock, arguments):
    yahoo_query_data = yq.Ticker(stock)
    daily_stock_data = yahoo_query_data.history(period=arguments.period,
                                                interval=arguments.timeframe).round(4)
    print(f'{datetime.datetime.now()} :: Updating {stock} historical stock data.')
    daily_stock_data.reset_index(level=[0, 1], inplace=True)
    daily_stock_data.set_index('date', inplace=True)
    daily_stock_data.to_csv(path_or_buf=f'{stock_files_directory}{stock}_{arguments.timeframe}_stock_data.txt')


def update_data(arguments):
    update_list = []
    memsql_host = os.environ['memsql_ip']
    memsql_port = os.environ['memsql_port']
    memsql_user = os.environ['memsql_user']
    memsql_password = os.environ['memsql_password']
    database_name = 'stock_data'
    memsql_server = pymysql.connect(host=memsql_host,
                                    user=memsql_user,
                                    password=memsql_password,
                                    port=int(memsql_port),
                                    database=database_name,
                                    cursorclass=pymysql.cursors.DictCursor)

    with memsql_server.cursor() as db_query:
        db_query.execute('SELECT SYMBOL FROM stock_info')
        memsql_stock_list_result = db_query.fetchall()
    print(f'{datetime.datetime.now()} :: Updating historical stock data.')
    for each_ticker in memsql_stock_list_result:
        update_list.append(each_ticker['SYMBOL'])
    with futures.ThreadPoolExecutor() as update_executor:
        update_executor.map(update_stock_data, update_list, repeat(arguments))
