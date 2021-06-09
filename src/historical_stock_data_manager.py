from concurrent import futures
import threading
import yfinance as yf
import pandas as pd
import pandas_ta as ta

stock_files_directory = 'stocks/'
stock_list_file = 'stock_list.txt'


def import_stock_data(stock_name):
    dataframe_import = pd.read_csv(filepath_or_buffer=f'{stock_files_directory}{stock_name}_daily_stock_data.txt',
                                   sep=',')
    return dataframe_import


def import_data(stock_list):
    with futures.ProcessPoolExecutor(max_workers=2) as import_executor:
        for each_stock, stock_list_results in zip(stock_list, import_executor.map(import_stock_data, stock_list)):
            stock_list[each_stock].daily_stock_data = stock_list_results


def update_stock_data(stock):
    data = yf.Ticker(stock)
    daily_stock_data = data.history(period='max').round(decimals=5)
    if len(daily_stock_data) > 730:
        daily_stock_data.to_csv(path_or_buf=f'{stock_files_directory}{stock}_daily_stock_data.txt')


def update_data():
    stock_list = []
    with open(stock_list_file, 'r') as file:
        for each_ticker in file:
            stock_list.append(each_ticker.strip('\n'))
    with futures.ThreadPoolExecutor() as update_executor:
        update_executor.map(update_stock_data, stock_list)
