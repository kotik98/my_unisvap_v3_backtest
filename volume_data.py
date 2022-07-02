import config
from binance.client import Client
from binance.enums import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

TRADE_SYMBOL = 'ETHUSDT'

client = Client(config.ApiKey, config.SecretKey, tld='com')


def getMinuteData(client, symbol, interval, lookback):
    frame = pd.DataFrame(client.get_historical_klines(symbol, interval, lookback + 'day ago UTC'))
    frame = frame.iloc[:, :6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    return frame


def get_volume_for_bounds(trading_volume, bounds_min, bounds_max):
    volume = 0
    for i in range(len(trading_volume[1])):
        if trading_volume[1][i] < bounds_max and trading_volume[1][i] > bounds_min:
            volume = volume + trading_volume[0][i]
    return volume


def get_volume_visualization(trading_volume, bins_num):
    price_min = min(trading_volume[1])
    price_max = max(trading_volume[1])
    bins_bounds = np.linspace(price_min, price_max, bins_num + 1)
    volume = np.zeros(bins_num)
    bins_bounds_visualization = np.zeros(bins_num)
    for j in range(bins_num):
        volume[j] = get_volume_for_bounds(trading_volume, bins_bounds[j], bins_bounds[j + 1])
        bins_bounds_visualization[j] = (bins_bounds[j] + bins_bounds[j + 1]) / 2
    bin_width = (bins_bounds_visualization[0] - bins_bounds[0]) * 2
    plt.bar(bins_bounds_visualization, volume, width=bin_width)
    plt.show()


df = getMinuteData(client, TRADE_SYMBOL, '15m', '100')
trading_volume = np.ndarray((2, len(df)))
for i in range(len(df)):
    trading_volume[0][i] = df.Volume[i] * df.Close[i]
    trading_volume[1][i] = df.Close[i]

print(get_volume_for_bounds(trading_volume, 1000, 1200))
get_volume_visualization(trading_volume, 80)
