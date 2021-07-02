import os
import math
import json
import websocket
import logging
import alpaca_trade_api

trade_api = alpaca_trade_api.REST()


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


def order(stock_data_order, symbol, cash_risk):
    status = False
    last_trade = trade_api.get_last_trade(symbol=symbol)
    if stock_data_order.buy_price >= last_trade.price > stock_data_order.risk:
        order_results = trade_api.submit_order(symbol=symbol,
                                               side='buy',
                                               type='stop',
                                               stop_price=stock_data_order.buy_price,
                                               qty=math.floor(cash_risk /
                                                              (stock_data_order.buy_price -
                                                               stock_data_order.risk)),
                                               time_in_force='day',
                                               order_class='bracket',
                                               take_profit=dict(limit_price=stock_data_order.reward),
                                               stop_loss=dict(stop_price=stock_data_order.risk,
                                                              limit_price=str(round(stock_data_order.risk * .99, 2))))
        logging.info(f'{symbol} : Order {order_results.status}')
        if order_results.status == 'accepted':
            status = True
            logging.info({'symbol': symbol,
                          'quantity': order_results.qty,
                          'price': round(stock_data_order.buy_price, 4),
                          'risk': round(stock_data_order.buy_price - stock_data_order.risk, 4),
                          'reward': round(stock_data_order.reward - stock_data_order.buy_price, 4),
                          'volume': stock_data_order.volume})
    else:
        logging.info(f'{symbol} : Last trade price not within range')

    return status
