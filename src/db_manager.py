import pymysql
import os


class Database:
    def __init__(self, database_name):
        self.memsql_host = os.environ['memsql_ip']
        self.memsql_port = os.environ['memsql_port']
        self.memsql_user = os.environ['memsql_user']
        self.memsql_password = os.environ['memsql_password']
        self.database_name = database_name
        self.database = pymysql.connect(host=self.memsql_host,
                                   user=self.memsql_user,
                                   password=self.memsql_password,
                                   port=int(self.memsql_port))
        cursor = self.database.cursor()
        cursor.execute(f'CREATE DATABASE IF NOT EXISTS {self.database_name}')
        cursor.execute(f'USE {self.database_name}')

    def create_tables(self, table_data):
        pass

    def update_tables(self):
        pass

