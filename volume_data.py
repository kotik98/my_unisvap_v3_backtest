from binance.client import Client
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def getData(client, symbol, interval, date_from, date_to):
    frame = pd.DataFrame(client.get_historical_klines(symbol, interval, date_from, date_to))
    frame = frame.iloc[:, :6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    return frame


def volume_for_bounds(trading_volume, bounds_min, bounds_max):
    volume = 0
    for i in range(len(trading_volume[1])):
        if bounds_max > trading_volume[1][i] > bounds_min:
            volume = volume + trading_volume[0][i]
    return volume


def volume_visualization(trading_volume, bins_num):
    price_min = min(trading_volume[1])
    price_max = max(trading_volume[1])
    bins_bounds = np.linspace(price_min, price_max, bins_num + 1)
    volume = np.zeros(bins_num)
    bins_bounds_visualization = np.zeros(bins_num)
    for j in range(bins_num):
        volume[j] = volume_for_bounds(trading_volume, bins_bounds[j], bins_bounds[j + 1])
        bins_bounds_visualization[j] = (bins_bounds[j] + bins_bounds[j + 1]) / 2
    bin_width = (bins_bounds_visualization[0] - bins_bounds[0]) * 2
    plt.bar(bins_bounds_visualization, volume, width=bin_width)
    with open("data/levels.txt", "r+") as file1:
        for l in file1.readlines():
            plt.axvline(float(l), linewidth=1, color='r')
    plt.show()


def get_volume_data(symbol, interval, date_from, date_to):
    client = Client()
    df = getData(client, symbol, interval, date_from, date_to)
    trading_volume = np.ndarray((2, len(df)))
    for i in range(len(df)):
        trading_volume[0][i] = df.Volume[i] * df.Close[i]
        trading_volume[1][i] = df.Close[i]
    return trading_volume


def relative_volume_plot(trading_volume):
    levels = []
    fig, ax = plt.subplots(figsize=(15, 15))
    with open("data/levels.txt", "r+") as file1:
        for l in file1.readlines():
            levels.append(float(l))
            plt.axvline(float(l), linewidth=1, color='r')
    levels.sort()
    for j in range(len(levels) - 1):
        rel_volume = volume_for_bounds(trading_volume, levels[j], levels[j + 1]) / abs(levels[j + 1] - levels[j])
        ax.fill_between(np.arange(levels[j], levels[j + 1], 1), 0, rel_volume, color='b', alpha=.5)
    plt.show()


def relative_volume(symbol, interval, date_from, date_to, levels):
    trading_volume = get_volume_data(symbol, interval, date_from, date_to)
    rel_vol = []
    for j in range(len(levels) - 1):
        rel_vol.append(volume_for_bounds(trading_volume, levels[j][0], levels[j + 1][0]) / abs(levels[j + 1][0] - levels[j][0]))
    return rel_vol


if __name__ == "__main__":
    trading_volume = get_volume_data("ETHUSDT", "1h", "1 Jul 2021", "1 Jul 2022")
    volume_visualization(trading_volume, 80)
    relative_volume_plot(trading_volume)
