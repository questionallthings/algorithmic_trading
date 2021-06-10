from concurrent import futures
import yahooquery as yq
import pandas as pd

stock_files_directory = 'stocks/'
stock_list_file = 'stock_list.txt'


def import_stock_data(stock_name):
    dataframe_import = pd.read_csv(filepath_or_buffer=f'{stock_files_directory}{stock_name}_daily_stock_data.txt',
                                   sep=',')
    return dataframe_import


def import_data(stock_data):
    with futures.ProcessPoolExecutor(max_workers=2) as import_executor:
        for each_stock, stock_list_results in zip(stock_data, import_executor.map(import_stock_data, stock_data)):
            stock_data[each_stock].daily_stock_data = stock_list_results


def update_stock_data(stock):
    yahoo_query_data = yq.Ticker(stock)
    daily_stock_data = yahoo_query_data.history(period='max').round(5)
    if len(daily_stock_data) > 730:
        daily_stock_data.to_csv(path_or_buf=f'{stock_files_directory}{stock}_daily_stock_data.txt')


def update_data():
    update_list = []
    with open(stock_list_file, 'r') as file:
        for each_ticker in file:
            update_list.append(each_ticker.strip('\n'))
    with futures.ThreadPoolExecutor() as update_executor:
        update_executor.map(update_stock_data, update_list)


def update_stock_list_data():
    pass


def update_stock_list():
    pass

