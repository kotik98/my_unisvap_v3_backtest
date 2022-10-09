import ta.trend as trend
import pandas as pd
from binance.client import Client
from datetime import datetime
import calendar

client = Client()


def getATR(symbol, interval, window, startTimestamp, endTimestamp):
    curr_date = datetime.fromtimestamp(endTimestamp)
    past_date = datetime.fromtimestamp(startTimestamp)
    past_month_name = calendar.month_abbr[past_date.month]
    current_month_name = calendar.month_abbr[curr_date.month]
    frame = pd.DataFrame(client.get_historical_klines(symbol, interval,
                                                      "{} {} {}".format(past_date.day, past_month_name, past_date.year),
                                                      "{} {} {}".format(curr_date.day, current_month_name,
                                                                        curr_date.year)))
    frame = frame.iloc[:, :6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    tr = pd.Series([max(frame.iloc[i][1] - frame.iloc[i][2], frame.iloc[i][1] - frame.iloc[i - 1][3],
                        frame.iloc[i - 1][3] - frame.iloc[i][2]) for i in range(1, len(frame.index))])
    return trend.ema_indicator(tr, window).iloc[-1]
