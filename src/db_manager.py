import pymysql
import os
import datetime


class Database:
    def __init__(self):
        self.memsql_host = os.environ['memsql_ip']
        self.memsql_port = os.environ['memsql_port']
        self.memsql_user = os.environ['memsql_user']
        self.memsql_password = os.environ['memsql_password']
        self.database_name = 'stock_data'
        self.memsql_server = pymysql.connect(host=self.memsql_host,
                                             user=self.memsql_user,
                                             password=self.memsql_password,
                                             port=int(self.memsql_port),
                                             database=self.database_name)
        self.cursor = self.memsql_server.cursor()
        self.cursor.execute(f'CREATE DATABASE IF NOT EXISTS {self.database_name}')

    def update_stock_info(self, data):
        try:
            for each in data.values():
                columns = []
                for each_value in each:
                    columns.append(each_value)
                if 'exchange' in each:
                    query_text = f'INSERT INTO stock_info ('
                    for each_value in columns[:-1]:
                        query_text += f'{each_value}, '
                    query_text += f'{columns[-1]}) VALUES ('
                    for each_value in columns[:-1]:
                        #if each_value in ['exchange', 'quoteType', 'symbol', 'underlyingSymbol', 'shortName', 'longName', 'firstTradeDateEpochUtc', 'timeZoneFullName', 'timeZoneShortName', 'uuid', 'messageBoardId']:
                        query_text += f'\"{each[each_value]}", '
                        #else:
                        #    query_text += f'{each[each_value]}, '
                    query_text += f'{each[columns[-1]]})'
                    print(query_text)
                    self.cursor.execute(f'{query_text}')
            self.memsql_server.commit()
        except:
            pass

    def update_tables(self, data):
        data.fillna('')
        columns = data.columns
        for each_date in data.index:
            query_text = f'INSERT INTO daily_bars (date, '
            for each_column in columns[:-1]:
                query_text += f'{each_column}, '
            query_text += f'{columns[-1]}) VALUES (\'{datetime.datetime.strftime(each_date, "%Y-%m-%d")}\', '
            for each_column in columns[:-1]:
                if each_column == 'symbol':
                    query_text += f'\'{data.loc[each_date].loc[each_column]}\', '
                else:
                    query_text += f'{data.loc[each_date].loc[each_column]}, '
            query_text += f'{data.loc[each_date].loc[columns[-1]]})'
            print(query_text)
            self.cursor.execute(f'{query_text}')
        self.memsql_server.commit()
