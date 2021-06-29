import os
import json
import websocket
import logging


class AlpacaSocket:
    def __init__(self, monitoring, stock_data):
        self.socket_auth = {'action': 'auth',
                            'key': os.environ['APCA_API_KEY_ID'],
                            'secret': os.environ['APCA_API_SECRET_KEY']}
        self.socket_subscribe = {'action': 'subscribe',
                                 'trades': [],
                                 'quotes': [],
                                 'dailyBars': [],
                                 'statuses': [],
                                 'lulds': [],
                                 'bars': ['*']}
        self.monitoring = monitoring
        self.stock_data = stock_data

    def on_message(self, ws, message):
        message_json = json.loads(message)
        for each_message in message_json:
            if each_message['T'] == 'success':
                if each_message['msg'] == 'connected':
                    ws.send(json.dumps(self.socket_auth))
                elif each_message['msg'] == 'authenticated':
                    ws.send(json.dumps(self.socket_subscribe))
            elif each_message['T'] == 'b':
                if each_message['S'] in self.monitoring:
                    logging.info(each_message)

    def on_error(self, ws, error):
        logging.error(error)

    def on_close(self, ws, close_status_code, close_msg):
        logging.info('Socket Closed')

    def on_open(self, ws):
        logging.info('Socket Opened')

    def alpaca_socket(self):
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp('wss://stream.data.alpaca.markets/v2/iex',
                                    on_open=self.on_open,
                                    on_message=self.on_message,
                                    on_error=self.on_error,
                                    on_close=self.on_close)
        ws.run_forever()
