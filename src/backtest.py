import pandas
from concurrent import futures


class Backtest:
    def __init__(self):
        pass

    def run_test(self, data):
        print(data[0])
        print(data[1].data)


def run_backtest(stock_data):
    backtesting = Backtest()
    with futures.ProcessPoolExecutor() as backtest_executor:
        backtest_executor.map(backtesting.run_test, list(stock_data.items()))
