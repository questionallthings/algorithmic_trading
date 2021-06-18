import pymysql
import os
import websocket
import json

websocket_auth = {'action': 'auth',
                  'key': os.environ['APCA_API_KEY_ID'],
                  'secret': os.environ['APCA_API_SECRET_KEY']}
websocket_subscribe = {'action': 'subscribe',
                       'trades': [],
                       'quotes': [],
                       'dailyBars': [],
                       'statuses': [],
                       'bars': ['*']}


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


def on_message(ws, message):
    message_json = json.loads(message)
    for each_message in message_json:
        print(each_message)
        if 'msg' in each_message:
            if each_message['msg'] == 'connected':
                ws.send(data=json.dumps(websocket_auth))
            elif each_message['msg'] == 'authenticated':
                ws.send(data=json.dumps(websocket_subscribe))


def on_error(ws, error):
    print(error)


def on_close(ws):
    print('Websocket Closed')


def on_open(ws):
    print('Websocket Opened')


if __name__ == "__main__":
    db = Database
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp('wss://stream.data.alpaca.markets/v2/iex',
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)

    ws.run_forever()
