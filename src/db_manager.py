import pymysql
import pandas
import os
from datetime import datetime
from concurrent import futures
import alpaca_trade_api
import yahooquery as yq


class Database:
    def __init__(self):
        self.memsql_host = os.environ['memsql_ip']
        self.memsql_port = os.environ['memsql_port']
        self.memsql_user = os.environ['memsql_user']
        self.memsql_password = os.environ['memsql_password']
        self.database_name = 'stock_data'

    def update_stock_info(self, stock):
        try:
            yahoo_query_data = yq.Ticker(stock)
            stock_info_data = yahoo_query_data.quote_type
            if 'exchange' in stock_info_data[stock]:
                if stock_info_data[stock]['exchange'] is not None:
                    print(stock_info_data[stock])
                    columns = []
                    for each_column in stock_info_data[stock]:
                        columns.append(each_column)
                    query_text = f'INSERT INTO stock_info ('
                    for each_column in columns[:-1]:
                        query_text += f'{each_column}, '
                    query_text += f'{columns[-1]}) VALUES ('
                    for each_column in columns[:-1]:
                        if stock_info_data[stock][each_column] is None:
                            stock_info_data[stock][each_column] = 'NULL'
                        if each_column in ['gmtOffSetMilliseconds', 'maxAge']:
                            query_text += f'{stock_info_data[stock][each_column]}, '
                        else:
                            query_text += f'\"{stock_info_data[stock][each_column]}", '
                    query_text += f'{stock_info_data[stock][columns[-1]]})'
                    print(query_text)
                    sql_server = pymysql.connect(host=self.memsql_host,
                                                 user=self.memsql_user,
                                                 password=self.memsql_password,
                                                 port=int(self.memsql_port),
                                                 database=self.database_name,
                                                 cursorclass=pymysql.cursors.DictCursor)
                    with sql_server.cursor() as stock_info_post:
                        stock_info_post.execute(f'{query_text}')
                    sql_server.commit()
        except pymysql.err.IntegrityError as error:
            print(f'Stock returned error: {error}')

    def update_daily_bars(self, stock):
        yahoo_query_data = yq.Ticker(stock)
        daily_stock_data = yahoo_query_data.history(period='1mo',
                                                    interval='1d').round(4)
        sql_server = pymysql.connect(host=self.memsql_host,
                                     user=self.memsql_user,
                                     password=self.memsql_password,
                                     port=int(self.memsql_port),
                                     database=self.database_name,
                                     cursorclass=pymysql.cursors.DictCursor)
        daily_stock_data.reset_index(level=[0, 1], inplace=True)
        daily_stock_data.set_index('date', inplace=True)
        daily_stock_data.fillna('NULL')
        columns = daily_stock_data.columns
        for each_date in daily_stock_data.index:
            query_text = f'INSERT INTO daily_bars (date, '
            for each_column in columns[:-1]:
                query_text += f'{each_column}, '
            query_text += f'{columns[-1]}) VALUES (\'{datetime.strftime(each_date, "%Y-%m-%d")}\', '
            for each_column in columns[:-1]:
                if each_column == 'symbol':
                    query_text += f'\'{daily_stock_data.loc[each_date].loc[each_column]}\', '
                else:
                    query_text += f'{daily_stock_data.loc[each_date].loc[each_column]}, '
            query_text += f'{daily_stock_data.loc[each_date].loc[columns[-1]]})'
            print(query_text)
            with sql_server.cursor() as daily_bars_post:
                daily_bars_post.execute(f'{query_text}')
        sql_server.commit()

    def update_minute_bars(self, stock):
        pass


if __name__ == '__main__':
    start_time = datetime.now()
    database = Database()
    alpaca_tradeable_assets = []
    memsql_stock_info_list = []
    api = alpaca_trade_api.REST()
    stock_info_update_list = []
    daily_bars_update_list = []

    tradeable_assets = api.list_assets()
    memsql_server = pymysql.connect(host=database.memsql_host,
                                    user=database.memsql_user,
                                    password=database.memsql_password,
                                    port=int(database.memsql_port),
                                    database=database.database_name,
                                    cursorclass=pymysql.cursors.DictCursor)
    with memsql_server.cursor() as db_query:
        db_query.execute('SELECT symbol FROM stock_info')
        memsql_stock_list_result = db_query.fetchall()
    for each in memsql_stock_list_result:
        memsql_stock_info_list.append(each['symbol'])

    # # # UPDATING STOCK INFO
    for each in tradeable_assets:
        alpaca_tradeable_assets.append(each.symbol)
    for each_stock in alpaca_tradeable_assets:
        if each_stock not in memsql_stock_info_list:
            stock_info_update_list.append(each_stock)
    with futures.ThreadPoolExecutor() as info_executor:
        info_executor.map(database.update_stock_info, stock_info_update_list)

    # # # UPDATING DAILY BARS
    with futures.ThreadPoolExecutor() as daily_executor:
        daily_executor.map(database.update_daily_bars, memsql_stock_info_list)

    print(f'Total time for updating: {datetime.now() - start_time}')
