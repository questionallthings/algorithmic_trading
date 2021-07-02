from datetime import datetime
import mplfinance as mpf
import re
import strategies
import pandas as pd
import logging


def test_strategy(symbol, stock_data, arguments):
    logging.info(f'{datetime.now()} :: Importing test stock data.')
    stock_data[symbol].data.set_index(pd.to_datetime(stock_data[symbol].data.date), inplace=True)
    stock_data[symbol].data.sort_index(inplace=True)
    stock_data[symbol].data.drop(columns='symbol',
                                 inplace=True)
    strategies.run_strategy(arguments['strategy'], stock_data, arguments['reward'])
    mpf_display_count = 0
    print(stock_data[symbol].data.tail(40))
    add_plot_indicators = []
    for each_column in stock_data[symbol].data.columns:
        if re.match('^EMA', each_column):
            add_plot_indicators.append(mpf.make_addplot(stock_data[symbol].data[each_column][-mpf_display_count:]))
        elif re.match('^SUPERT', each_column):
            add_plot_indicators.append(mpf.make_addplot(stock_data[symbol].data['SUPERT_7_3.0'][-mpf_display_count:]))
        elif each_column == 'buy_price':
            add_plot_indicators.append(mpf.make_addplot(stock_data[symbol].data['buy_price'][-mpf_display_count:] * .99,
                                                        type='scatter',
                                                        markersize=200,
                                                        marker='^'))
        elif each_column == 'sell_price':
            add_plot_indicators.append(mpf.make_addplot(stock_data[symbol].data['sell_price'][-mpf_display_count:] * 1.01,
                                                        type='scatter',
                                                        markersize=200,
                                                        marker='v'))
        elif re.match('^STOCHRSI', each_column):
            add_plot_indicators.append(mpf.make_addplot(stock_data[symbol].data[each_column][-mpf_display_count:],
                                                        panel=2))
        elif each_column == 'backtest_profit_percentage':
            add_plot_indicators.append(mpf.make_addplot(stock_data[symbol].data[each_column][-mpf_display_count:],
                                                        panel=2))
        elif each_column == 'ATRr_14':
            add_plot_indicators.append(mpf.make_addplot(stock_data[symbol].data[each_column][-mpf_display_count:],
                                                        panel=3))
        elif each_column == 'ISA_9':
            stock_data[symbol].data['ISA_9'].fillna(0.0, inplace=True)
            stock_data[symbol].data['ISB_26'].fillna(0.0, inplace=True)
            add_plot_indicators.append(mpf.make_addplot(stock_data[symbol].data['ITS_9'][-mpf_display_count:],
                                                        color='lime', width=0.9, alpha=0.75))
            add_plot_indicators.append(mpf.make_addplot(stock_data[symbol].data['IKS_26'][-mpf_display_count:],
                                                        color='r', width=0.8, alpha=0.75))
            add_plot_indicators.append(mpf.make_addplot(stock_data[symbol].data['ICS_26'][-mpf_display_count:],
                                                        color='black', linestyle='dotted', width=1))
            add_plot_indicators.append(mpf.make_addplot(stock_data[symbol].data['ISA_9'][-mpf_display_count:],
                                                        color='y', width=0.5, alpha=0.5))
            add_plot_indicators.append(mpf.make_addplot(stock_data[symbol].data['ISB_26'][-mpf_display_count:],
                                                        color='purple', width=0.5, alpha=0.5))
    mpf_colors = mpf.make_marketcolors(up='g', down='r', volume='in', edge='k')
    mpf_style = mpf.make_mpf_style(marketcolors=mpf_colors)
    if arguments['strategy'] == 'ichimoku':
        mpf.plot(data=stock_data[symbol].data[-mpf_display_count:],
                 style=mpf_style,
                 fill_between={'y1': stock_data[symbol].data['ISA_9'][-mpf_display_count:].values,
                               'y2': stock_data[symbol].data['ISB_26'][-mpf_display_count:].values,
                               'alpha': 0.25},
                 type='candle',
                 addplot=add_plot_indicators,
                 volume=True,
                 warn_too_much_data=1000000000,
                 title=f'{symbol}')
    else:
        mpf.plot(data=stock_data[symbol].data[-mpf_display_count:],
                 style=mpf_style,
                 type='candle',
                 addplot=add_plot_indicators,
                 volume=True,
                 warn_too_much_data=1000000000,
                 title=f'{symbol}')
