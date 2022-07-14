from binance.client import Client

import json
import time

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import colors as mcolors
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.lines import TICKLEFT, TICKRIGHT, Line2D
from matplotlib.patches import Rectangle
from matplotlib.transforms import Affine2D


def get_klines(client, symbol, interval, date_from, date_to) -> str:
    while True:
        try:
            #             klines = client.get_historical_klines("BNBBTC", Client.KLINE_INTERVAL_1MINUTE, "1 day ago UTC")
            #             klines = client.get_historical_klines("ETHBTC", Client.KLINE_INTERVAL_30MINUTE, "1 Dec, 2017", "1 Jan, 2018")
            #             klines = client.get_historical_klines("NEOBTC", Client.KLINE_INTERVAL_1WEEK, "1 Jan, 2017")
            klines = client.get_historical_klines(symbol, interval, date_from, date_to)
            return split_db_klines_basic_data(klines, 0)
        except Exception as e:
            print(e)
            time.sleep(1)


class spiltedKlines:
    def __init__(self):
        self.ids = []
        self.timestamp = []
        self.open = []
        self.high = []
        self.low = []
        self.close = []
        self.total_deals = []
        self.base_buy_vol = []
        self.base_sell_vol = []
        self.quote_buy_vol = []
        self.quote_sell_vol = []


def split_db_klines_basic_data(db_klines, ts_pos):
    # datetime:open:high:low:close
    splited_data = spiltedKlines()

    for kline in db_klines:

        splited_data.ids.append(int(kline[0]))  # kline_id

        if kline[ts_pos] > 2147483647:  # timestamp
            splited_data.timestamp.append(int(kline[ts_pos] / 1000))
        else:
            splited_data.timestamp.append(int(kline[ts_pos]))
        splited_data.open.append(float(kline[ts_pos + 1]))  # open
        splited_data.high.append(float(kline[ts_pos + 2]))
        splited_data.low.append(float(kline[ts_pos + 3]))
        splited_data.close.append(float(kline[ts_pos + 4]))

        splited_data.total_deals.append(float(kline[ts_pos + 5]))  # total deals

        splited_data.base_buy_vol.append(float(kline[ts_pos + 6]))  # base buy
        splited_data.base_sell_vol.append(float(kline[ts_pos + 7]))  # base sell

        splited_data.quote_buy_vol.append(float(kline[ts_pos + 8]))  # quote buy
        splited_data.quote_sell_vol.append(float(kline[ts_pos + 9]))  # quote sell

    return splited_data


def get_price_step(splited_klines):
    klines_min = min(splited_klines.close)
    klines_max = max(splited_klines.close)

    percent_diff = (klines_max - klines_min) / klines_min
    steps = 300

    #     price_step = (klines_max - klines_min) / percent_diff / 5 #step is 0.2%
    price_step = (klines_max - klines_min) / steps
    perc_price_step = percent_diff / steps
    return price_step, perc_price_step


def group_lvls(levels, grouping_percent):
    percent = grouping_percent
    copy = levels[:]
    new_copy = []
    filtered = []

    # limit top 10 lvls
    for j in range(len(levels)):
        if len(copy) < 1:
            break
        top_lvl = copy[0]
        filtered.append(top_lvl)

        for elem in copy[1:]:
            if (elem[0] >= top_lvl[0] and top_lvl[0] + top_lvl[0] * percent >= elem[0]) or \
                    (elem[0] <= top_lvl[0] and top_lvl[0] - top_lvl[0] * percent <= elem[0]):
                continue
            else:
                new_copy.append(elem)

        copy = new_copy[:]
        new_copy = []

    return filtered


def measure_price_as_level(price, price_step, splited_klines):
    level_points = 0
    breakdown_num = 0

    for i in range(len(splited_klines.close)):
        # пробой уровня телом зелёной свечи
        price_step_multipliers = [0.5, 1, 2]
        rewards = [-2, -3, -5]
        for mul, reward in zip(price_step_multipliers, rewards):
            if splited_klines.close[i] > price > splited_klines.open[i] and \
                    splited_klines.close[i] - price_step * mul < price:
                level_points += reward
                breakdown_num += 1
                continue

                # ограниченный пробой уровня телом красной свечи
        price_step_multipliers = [0.5, 1, 2]
        rewards = [-2, -3, -5]
        for mul, reward in zip(price_step_multipliers, rewards):
            if splited_klines.close[i] < price < splited_klines.open[i] and \
                    splited_klines.close[i] + price_step * mul > price:
                level_points += reward
                continue

        # неограниченный пробой уровня телом свечи
        if splited_klines.open[i] < price < splited_klines.close[i]:
            level_points += -8
            breakdown_num += 1
            continue

        if splited_klines.close[i] < price < splited_klines.open[i]:
            level_points += -8
            breakdown_num += 1
            continue

        # high недобой до уровня
        price_step_multipliers = [0.1, 0.3, 0.5, 1, 2]
        rewards = [10, 9, 8, 6, 3]

        for mul, reward in zip(price_step_multipliers, rewards):
            if splited_klines.high[i] < price < splited_klines.high[i] + price_step * mul:
                level_points += reward
                continue

        for mul, reward in zip(price_step_multipliers, rewards):
            if splited_klines.low[i] > price > splited_klines.low[i] - price_step * mul:
                level_points += reward
                continue

        # пробой high уровня снизу вверз
        price_step_multipliers = [0.1, 0.3, 0.5, 1, 2]
        rewards = [8, 6, 5, 3, 1]

        for mul, reward in zip(price_step_multipliers, rewards):
            if splited_klines.high[i] > price > splited_klines.high[i] - price_step * mul:
                level_points += reward
                continue

        if splited_klines.high[i] > price > splited_klines.open[i]:
            breakdown_num += 1
            level_points += -4

        # пробой low уровня сверзу вниз
        for mul, reward in zip(price_step_multipliers, rewards):
            if splited_klines.low[i] < price < splited_klines.low[i] + price_step * mul:
                level_points += reward
                continue

        if splited_klines.low[i] < price < splited_klines.open[i]:
            breakdown_num += 1
            level_points += -4

        # недобой close до уровня
        price_step_multipliers = [0.3, 0.5, 1, 2]
        rewards = [6, 4, 2, 1]
        for mul, reward in zip(price_step_multipliers, rewards):
            if splited_klines.open[i] < splited_klines.close[i] < price < splited_klines.close[i] + price_step * mul:
                level_points += reward
                continue

            if splited_klines.open[i] > splited_klines.close[i] > price > splited_klines.close[
                i] - price_step * mul:
                level_points += reward
                continue

                # пробой уровня свечой с выходом разной силы
    #        price_step_multipliers = [5, 4, 3, 2, 1, 0]
    #        rewards = [-10, -9, -7, -5, -3, -2]
    #
    #        for mul, reward in zip(price_step_multipliers, rewards)
    #            if splited_klines.open[i] + price_step*mul < price and splited_klines.close[i] - mul*price_step > price:
    #                level_points += reward
    #                continue
    return level_points, breakdown_num


def candlestick2_ohlc_binance(ax, binance_klines, width=4, colorup='g', colordown='r', alpha=0.75):
    """Represent the open, close as a bar line and high low range as a
    vertical line.
    NOTE: this code assumes if any value open, low, high, close is
    missing they all are missing
    Parameters
    ----------
    ax : `Axes`
        an Axes instance to plot to
    width : int
        size of open and close ticks in points
    alpha : float
        bar transparency
    Returns
    -------
    ret : tuple
        (lineCollection, barCollection)
    """

    delta = width / 2.
    barVerts = []
    rangeSegments = []
    colors = []

    colorup = mcolors.to_rgba(colorup, alpha)
    colordown = mcolors.to_rgba(colordown, alpha)

    min_y = float(binance_klines.low[0])
    max_y = float(binance_klines.high[0])

    for i in range(len(binance_klines.timestamp)):
        cdl_open = float(binance_klines.open[i])
        cdl_high = float(binance_klines.high[i])
        cdl_low = float(binance_klines.low[i])
        cdl_close = float(binance_klines.close[i])

        if min_y > cdl_low:
            min_y = cdl_low

        if max_y < cdl_high:
            max_y = cdl_high

        #         volume_bought = float(binance_klines[i][10])
        #         total_volume = float(binance_klines[i][7])
        #         volume_sold = total_volume - volume_bought

        top = 0
        bottom = 0

        if cdl_open > cdl_close:
            bottom = cdl_close
            top = cdl_open
            colors.append(colordown)
        else:
            bottom = cdl_open
            top = cdl_close
            colors.append(colorup)

        candle_movement = top - bottom

        barVerts.append(((i - delta, bottom),
                         (i - delta, top),
                         (i + delta, top),
                         (i + delta, bottom))
                        )

        rangeSegments.append(((i, cdl_low), (i, cdl_high)))

    useAA = 0,  # use tuple here
    lw = 1.5,  # and here
    rangeCollection = LineCollection(rangeSegments,
                                     colors=colors,
                                     linewidths=lw,
                                     antialiaseds=useAA,
                                     )

    barCollection = PolyCollection(barVerts,
                                   facecolors=colors,
                                   edgecolors=colors,
                                   antialiaseds=useAA,
                                   linewidths=lw,
                                   )

    min_x, max_x = 0, len(rangeSegments)

    corners = (min_x, min_y), (max_x, max_y)

    ax.update_datalim(corners)
    ax.autoscale_view()

    # add these last
    ax.add_collection(rangeCollection)
    ax.add_collection(barCollection)
    return rangeCollection, barCollection


def get_levels(symbol, interval, date_from, date_to):
    client = Client()
    klines = get_klines(client, symbol, interval, date_from, date_to)
    initial_price = min(klines.close)
    final_price = max(klines.close)
    current_price = initial_price
    price_step, perc_price_step = get_price_step(klines)

    lvls_result = []
    while current_price < final_price:
        price_points, price_breakdowns = measure_price_as_level(current_price, price_step, klines)
        if price_points - price_breakdowns > 0:
            lvls_result.append([current_price, price_points, price_breakdowns])
        current_price += price_step
    result = sorted(lvls_result, key=lambda x: x[1] - x[2], reverse=True)
    filtered = group_lvls(result, 5 * perc_price_step)
    filtered = sorted(filtered, key=lambda x: x[0])
    # filtered = filtered[:int(2/3*len(filtered))]
    return filtered, klines


if __name__ == "__main__":
    data, klines = get_levels("ETHUSDT", "1h", "1 Jul 2021", "1 Jul 2022")
    fig, ax = plt.subplots(figsize=(30, 15))
    with open("data/levels.txt", "w") as file1:
        for lvl in data:
            plt.axhline(lvl[0], linewidth=2, color='b')
            file1.write(str(lvl[0]) + '\n')

    candlestick2_ohlc_binance(ax, klines, width=1, colorup='g', colordown='r', alpha=0.75)
    plt.show()
