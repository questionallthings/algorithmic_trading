import os
import json
import websocket
from datetime import datetime


socket_auth = {'action': 'auth',
               'key': os.environ['APCA_API_KEY_ID'],
               'secret': os.environ['APCA_API_SECRET_KEY']}
socket_subscribe = {'action': 'subscribe',
                    'trades': [],
                    'quotes': [],
                    'dailyBars': [],
                    'statuses': [],
                    'lulds': []
                    'bars': ['*']}


def on_message(ws, message):
    print(f'{datetime.now()} :: {message}')
    message_json = json.loads(message)
    for each_message in message_json:
        print(each_message)
        if each_message['T'] == 'success':
            if each_message['msg'] == 'connected':
                ws.send(json.dumps(socket_auth))
            elif each_message['msg'] == 'authenticated':
                ws.send(json.dumps(socket_subscribe))



def on_error(ws, error):
    print(f'{datetime.now()} :: {error}')


def on_close(ws, close_status_code, close_msg):
    print(f'{datetime.now()} :: Socket Closed')


def on_open(ws):
    print(f'{datetime.now()} :: Socket Opened')


def alpaca_socket():
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp('wss://stream.data.alpaca.markets/v2/iex',
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.run_forever()
