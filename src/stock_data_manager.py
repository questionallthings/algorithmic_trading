from concurrent import futures
from itertools import repeat
import yahooquery as yq
import pandas as pd
import json
import datetime

stock_files_directory = 'stocks/'
stock_list_file = 'stock_list.txt'


def import_stock_data(stock_name, arguments):
    print(f'{datetime.datetime.now()} :: Importing {stock_name} historical stock data.')
    dataframe_import = pd.read_csv(filepath_or_buffer=f'{stock_files_directory}{stock_name}_'
                                                      f'{arguments.timeframe}_stock_data.txt',
                                   sep=',')
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
                                                interval=arguments.timeframe).round(5)
    if len(daily_stock_data) > 730:
        print(f'{datetime.datetime.now()} :: Updating {stock} historical stock data.')
        print(daily_stock_data)
        daily_stock_data.set_index('date', inplace=True)
        print('hello')
        #print(daily_stock_data)
        #daily_stock_data.to_csv(path_or_buf=f'{stock_files_directory}{stock}_{arguments.timeframe}_stock_data.txt')


def update_data(arguments):
    update_list = []
    print(f'{datetime.datetime.now()} :: Updating historical stock data.')
    with open(stock_list_file) as file:
        ticker_data = json.load(file)
    for each_ticker in ticker_data:
        update_list.append(each_ticker['symbol'])
    with futures.ThreadPoolExecutor() as update_executor:
        update_executor.map(update_stock_data, update_list, repeat(arguments))


def update_stock_list_data(stock):
    print(f'{datetime.datetime.now()} :: Acquiring finance data for {stock}.')
    yahoo_query_data = yq.Ticker(stock)
    stock_info_data = yahoo_query_data.quote_type

    return stock_info_data


def update_stock_list(api):
    yq_stock_data_results = []
    alpaca_tradeable_assets = []
    new_stock_data = []
    print(f'{datetime.datetime.now()} :: Updating stock list file.')
    print(f'{datetime.datetime.now()} :: Acquiring list of tradeable assets.')
    for each in api:
        alpaca_tradeable_assets.append(each.symbol)
    print(f'{datetime.datetime.now()} :: Querying finance data on {len(alpaca_tradeable_assets)} assets.')
    with futures.ThreadPoolExecutor() as update_executor:
        for each_stock, update_list_results in zip(alpaca_tradeable_assets,
                                                   update_executor.map(update_stock_list_data,
                                                                       alpaca_tradeable_assets)):
            yq_stock_data_results.append(update_list_results)
    with open(stock_list_file, 'w') as file:
        for each_ticker in yq_stock_data_results:
            for each_value in each_ticker.values():
                if ('exchange' in each_value) and (each_value['exchange'] is not None):
                    new_stock_data.append(each_value)
        print(f'{datetime.datetime.now()} :: Writing found finance data for {len(new_stock_data)} assets.')
        file.writelines(json.dumps(new_stock_data))
