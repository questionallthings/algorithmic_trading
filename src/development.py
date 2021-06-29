from datetime import datetime
import mplfinance as mpf
import re
import strategies
import pandas as pd


def test_strategy(connection, symbol, stock_data, arguments):
    print(f'{datetime.now()} :: Importing test stock data.')
    sql_df = pd.read_sql_query(f'SELECT * FROM daily_bars WHERE symbol=\'{symbol}\'', connection)
    sql_df.set_index(pd.to_datetime(sql_df.date), inplace=True)
    sql_df.sort_index(inplace=True)
    sql_df.drop(columns='symbol', inplace=True)
    stock_data.data = sql_df
    stock_data.set_data()
    stock_data.data = getattr(strategies, arguments['strategy'])((symbol, stock_data), arguments)
    mpf_display_count = 200
    print(stock_data.data.tail(20))
    add_plot_indicators = []
    for each_column in stock_data.data.columns:
        if re.match('^EMA', each_column):
            add_plot_indicators.append(mpf.make_addplot(stock_data.data[each_column][-mpf_display_count:]))
        elif re.match('^SUPERT', each_column):
            add_plot_indicators.append(mpf.make_addplot(stock_data.data['SUPERT_7_3.0'][-mpf_display_count:]))
        elif each_column == 'buy_price':
            add_plot_indicators.append(mpf.make_addplot(stock_data.data['buy_price'][-mpf_display_count:] * .99,
                                                        type='scatter',
                                                        markersize=200,
                                                        marker='^'))
        elif each_column == 'sell_price':
            add_plot_indicators.append(mpf.make_addplot(stock_data.data['sell_price'][-mpf_display_count:] * 1.01,
                                                        type='scatter',
                                                        markersize=200,
                                                        marker='v'))
        elif re.match('^STOCHRSI', each_column):
            add_plot_indicators.append(mpf.make_addplot(stock_data.data[each_column][-mpf_display_count:], panel=2))
        elif each_column == 'backtest_profit':
            add_plot_indicators.append(mpf.make_addplot(stock_data.data[each_column][-mpf_display_count:], panel=2))
        elif each_column == 'ISA_9':
            stock_data.data['ISA_9'].fillna(0.0, inplace=True)
            stock_data.data['ISB_26'].fillna(0.0, inplace=True)
            add_plot_indicators.append(mpf.make_addplot(stock_data.data['ITS_9'][-mpf_display_count:],
                                                        color='lime', width=0.9, alpha=0.75))
            add_plot_indicators.append(mpf.make_addplot(stock_data.data['IKS_26'][-mpf_display_count:],
                                                        color='r', width=0.8, alpha=0.75))
            add_plot_indicators.append(mpf.make_addplot(stock_data.data['ICS_26'][-mpf_display_count:],
                                                        color='black', linestyle='dotted', width=1))
            add_plot_indicators.append(mpf.make_addplot(stock_data.data['ISA_9'][-mpf_display_count:],
                                                        color='y', width=0.5, alpha=0.5))
            add_plot_indicators.append(mpf.make_addplot(stock_data.data['ISB_26'][-mpf_display_count:],
                                                        color='purple', width=0.5, alpha=0.5))
        elif each_column == 'pivots':
            add_plot_indicators.append(mpf.make_addplot(stock_data.data['pivots'][-mpf_display_count:] * 1.05,
                                                        type='scatter',
                                                        markersize=200,
                                                        marker='v'))
    mpf_colors = mpf.make_marketcolors(up='g', down='r', volume='in', edge='k')
    mpf_style = mpf.make_mpf_style(marketcolors=mpf_colors)
    if arguments['strategy'] == 'ichimoku':
        mpf.plot(data=stock_data.data[-mpf_display_count:],
                 style=mpf_style,
                 fill_between={'y1': stock_data.data['ISA_9'][-mpf_display_count:].values,
                               'y2': stock_data.data['ISB_26'][-mpf_display_count:].values,
                               'alpha': 0.25},
                 type='candle',
                 addplot=add_plot_indicators,
                 volume=True,
                 warn_too_much_data=1000000000,
                 title=f'{symbol}')
    else:
        mpf.plot(data=stock_data.data[-mpf_display_count:],
                 style=mpf_style,
                 type='candle',
                 addplot=add_plot_indicators,
                 volume=True,
                 warn_too_much_data=1000000000,
                 title=f'{symbol}')
