#!/usr/bin/env python3

"""
This script is used to test various ideas from internal/external sources before implementing in development code.
This will not be part of final package.
"""

from concurrent import futures
import yfinance as yf
import yahooquery as yq
import json
import os
import datetime

stock_list_file = '../src/stock_list.txt'
stock_files_directory = '../src/stocks/'


def update_stock_data(stock):
    yahoo_query_data = yq.Ticker(stock)
    stock_info_data = yahoo_query_data.quote_type

    return stock_info_data


def update_data():
    new_stock_data = []
    update_list = []
    with open(stock_list_file, 'r') as file:
        for each_ticker in file:
            ticker_data = json.loads(each_ticker)
            if 'symbol' in ticker_data:
                update_list.append(ticker_data['symbol'])
    with futures.ThreadPoolExecutor() as update_executor:
        for each_stock, update_list_results in zip(update_list, update_executor.map(update_stock_data, update_list)):
            new_stock_data.append(update_list_results)
    with open(stock_list_file, 'w') as file:
        for each_ticker in new_stock_data:
            for each_value in each_ticker.values():
                file.writelines(f'{json.dumps(each_value)}\n')


start_time = datetime.datetime.now()
update_data()
print(datetime.datetime.now() - start_time)
