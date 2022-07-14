from get_historical_data import *
from backtest import *
import time
import json
import matplotlib.pyplot as plt
from levels import *
from volume_data import *
import numpy as np
import calendar
from datetime import datetime

from visualization import *

now = int(time.time())


def DateByDaysAgo(days, endDate=now):
    return endDate - days * 86400


def uniswapStrategyBacktest(pool, investmentAmount, minRange, maxRange, startTimestamp=0, endTimestamp=now, days=30,
                            protocol=0, priceToken=0, period="hourly"):
    poolData = poolById(pool)
    if startTimestamp == 0:
        startTimestamp = DateByDaysAgo(days, endTimestamp)
    backtestData = get_pool_hour_data_from_csv(startTimestamp, endTimestamp)
    if priceToken == 1:
        entryPrice = 1 / float(backtestData["close"].values[0])
        # decimal = int(poolData[0]["token0"]["decimals"]) - int(poolData[0]["token1"]["decimals"])
    else:
        entryPrice = float(backtestData["close"].values[0])
        # decimal = int(poolData[0]["token1"]["decimals"]) - int(poolData[0]["token0"]["decimals"])
    tokens = tokensForStrategy(minRange, maxRange, investmentAmount, float(entryPrice),
                               int(poolData[0]["token1"]["decimals"]) - int(poolData[0]["token0"]["decimals"]))
    liquidity = liquidityForStrategy(float(entryPrice), minRange, maxRange, tokens[0], tokens[1],
                                     int(poolData[0]["token0"]["decimals"]), int(poolData[0]["token1"]["decimals"]))
    unbLiquidity = liquidityForStrategy(float(entryPrice), 1.0001 ** -887220, 1.0001 ** 887220, tokens[0],
                                        tokens[1], int(poolData[0]["token0"]["decimals"]),
                                        int(poolData[0]["token1"]["decimals"]))
    hourlyBacktest = calcFees(backtestData, poolData, priceToken, liquidity, unbLiquidity, investmentAmount, minRange,
                              maxRange)
    return hourlyBacktest


def getPrices(priceToken=0):
    price = pd.read_csv("data/pool_hour_data.csv")
    if priceToken == 1:
        for i in range(len(price)):
            price["close"].values[i] = 1 / float(price["close"].values[i])
    return price


def _X_percent_ITM_strategy(percent_itm, width, pool, investmentAmount, endTimestamp=now, days=30, protocol=0,
                            priceToken=0):
    csv_data_saver(pool, days, endTimestamp, protocol)
    prices = getPrices(priceToken)
    time_itm = 0
    time = 0
    current_price = float(prices["close"].values[0])
    fee = []
    closes = []
    amount = []
    fees = 0
    times = []
    xMin = []
    xMax = []
    minBound = []
    maxBound = []
    data = []
    for i in range(len(prices)):
        if (current_price * ((100 - width) / 100)) < float(prices["close"].values[i]) < (
                current_price * ((100 + width) / 100)):
            time_itm += 1
        time += 1
        if (time_itm / time) < (percent_itm / 100) or i == (len(prices) - 1):
            minBound.append(current_price * ((100 - width) / 100))
            maxBound.append(current_price * ((100 + width) / 100))
            xMin.append(
                (prices["periodStartUnix"].values[i - time + 1] - prices["periodStartUnix"].values[0]) / (3600 * 24))
            xMax.append((prices["periodStartUnix"].values[i] - prices["periodStartUnix"].values[0]) / (3600 * 24))
            backtest_data = uniswapStrategyBacktest(pool, investmentAmount, current_price * ((100 - width) / 100),
                                                    current_price * ((100 + width) / 100),
                                                    prices["periodStartUnix"].values[i - time + 1],
                                                    prices["periodStartUnix"].values[i],
                                                    protocol=protocol, priceToken=priceToken, period="hourly")
            data.extend(backtest_data)
            fees = 0
            for j in range(len(backtest_data)):
                fees = fees + backtest_data[j]["feeUSD"]
            time = 1
            time_itm = 1
            investmentAmount = data[-1]["amountV"] + fees
            current_price = float(prices["close"].values[i])
    fees = 0
    for j in range(len(data)):
        fees = fees + data[j]["feeUSD"]
        closes.append(data[j]["close"])
        amount.append(data[j]["amountV"])
        fee.append(fees)
        times.append((data[j]["unixDT"] - prices["periodStartUnix"].values[0]) / (3600 * 24))
    plotter(minBound, maxBound, xMin, xMax, fee, closes, amount, times)


def _2_pos_strategy(percent_itm, width, pool, investmentAmount, endTimestamp=now, days=30, protocol=0, priceToken=0):
    csv_data_saver(pool, days, endTimestamp, protocol)
    prices = getPrices(priceToken)
    time_itm = 0
    time = 0
    current_price = float(prices["close"].values[0])
    fee = []
    closes = []
    amount = []
    fees = 0
    times = []
    xMin = []
    xMax = []
    minBound = []
    maxBound = []
    data_top = []
    relocations = []
    actual_fee = []
    data_bottom = []
    for i in range(len(prices)):
        if (current_price - width) < float(prices["close"].values[i]) < (current_price + width):
            time_itm += 1
        time += 1
        if (time_itm / time) < (percent_itm / 100) or i == (len(prices) - 1):
            minBound.append(current_price - width)
            maxBound.append(current_price)
            xMin.append(
                (prices["periodStartUnix"].values[i - time + 1] - prices["periodStartUnix"].values[0]) / (3600 * 24))
            xMax.append((prices["periodStartUnix"].values[i] - prices["periodStartUnix"].values[0]) / (3600 * 24))
            bottom = uniswapStrategyBacktest(pool, investmentAmount / 2,
                                             current_price - width, current_price,
                                             prices["periodStartUnix"].values[i - time + 1],
                                             prices["periodStartUnix"].values[i],
                                             protocol=protocol, priceToken=priceToken, period="hourly")
            minBound.append(current_price)
            maxBound.append(current_price + width)
            xMin.append(
                (prices["periodStartUnix"].values[i - time + 1] - prices["periodStartUnix"].values[0]) / (3600 * 24))
            xMax.append((prices["periodStartUnix"].values[i] - prices["periodStartUnix"].values[0]) / (3600 * 24))
            top = uniswapStrategyBacktest(pool, investmentAmount / 2,
                                          current_price, current_price + width,
                                          prices["periodStartUnix"].values[i - time + 1],
                                          prices["periodStartUnix"].values[i],
                                          protocol=protocol, priceToken=priceToken, period="hourly")
            data_top.extend(top)
            data_bottom.extend(bottom)
            relocations.append(i + 1)
            fees = 0
            for j in range(len(top)):
                fees += top[j]["feeUSD"]
            for j in range(len(bottom)):
                fees += bottom[j]["feeUSD"]
            time = 1
            time_itm = 1
            investmentAmount = top[-1]["amountV"] + bottom[-1]["amountV"] + fees
            if float(prices["close"].values[i]) > current_price:
                current_price = current_price + width
            else:
                current_price = current_price - width
    fees = 0
    actual_fees = 0
    k = 0
    for j in range(len(data_top)):
        if j == relocations[k]:
            k += 1
            actual_fees = 0
        fees = fees + data_top[j]["feeUSD"] + data_bottom[j]["feeUSD"]
        actual_fees = actual_fees + data_top[j]["feeUSD"] + data_bottom[j]["feeUSD"]
        closes.append(data_top[j]["close"])
        amount.append(data_top[j]["amountV"] + data_bottom[j]["amountV"])
        fee.append(fees)
        actual_fee.append(actual_fees)
        times.append((data_top[j]["unixDT"] - prices["periodStartUnix"].values[0]) / (3600 * 24))
    plotter_for_2_pos_strategy(minBound, maxBound, xMin, xMax, fee, closes, amount, times, actual_fee)


def _simple_bounds_strategy(width, pool_id, Amount, days, priceToken, endTimestamp=now, protocol=0,
                            fee_reinvesting=False):
    csv_data_saver(pool_id, days, endTimestamp, protocol)
    bounds_width = width / 100
    from_date = DateByDaysAgo(days, endTimestamp)
    prices = getPrices(priceToken)
    up_bound = np.zeros(len(prices))
    down_bound = np.zeros(len(prices))
    start_timestamps = []
    end_timestamps = []
    low_b = []
    high_b = []
    down_bound[0] = prices["close"].values[0] * (1 - bounds_width)
    up_bound[0] = prices["close"].values[0] * (1 + bounds_width)
    bounds_change_index = 0
    start_timestamps.append(prices["periodStartUnix"].values[0])

    low_b.append(down_bound[0])
    high_b.append(up_bound[0])

    for i in range(1, len(prices)):
        if prices["close"].values[i] <= up_bound[i - 1] and prices["close"].values[i] >= down_bound[i - 1]:
            down_bound[i] = down_bound[i - 1]
            up_bound[i] = up_bound[i - 1]
        else:
            end_timestamps.append(prices["periodStartUnix"].values[i])
            start_timestamps.append(prices["periodStartUnix"].values[i + 1])
            down_bound[i] = prices["close"].values[i] * (1 - bounds_width)
            up_bound[i] = prices["close"].values[i] * (1 + bounds_width)
            low_b.append(down_bound[i])
            high_b.append(up_bound[i])
            bounds_change_index = bounds_change_index + 1
    end_timestamps.append(prices["periodStartUnix"].values[-1])

    bounds_for_plot = [up_bound, down_bound]
    timestamps = [start_timestamps, end_timestamps]
    bounds = [high_b, low_b]

    backtest = []
    length = 0
    for j in range(len(timestamps[0])):
        backtest.extend(uniswapStrategyBacktest(pool_id, Amount,
                                                maxRange=bounds[0][j], minRange=bounds[1][j],
                                                startTimestamp=timestamps[0][j],
                                                endTimestamp=timestamps[1][j], priceToken=priceToken, period="hourly"))
        Amount = backtest[-1]["amountV"]

        if fee_reinvesting == True:
            fee_r = 0
            for q in range(len(backtest) - length):
                fee_r = fee_r + backtest[q]["feeUSD"]
            length = len(backtest)
            Amount = Amount + fee_r
    fees = 0
    closes = []
    amount = []
    fee = []
    times = []
    for j in range(len(backtest)):
        fees = fees + backtest[j]["feeUSD"]
        closes.append(backtest[j]["close"])
        amount.append(backtest[j]["amountV"])
        fee.append(fees)
        times.append((backtest[j]["unixDT"] - prices["periodStartUnix"].values[0]) / (3600 * 24))
    plotter(low_b, high_b, (np.array(start_timestamps) - start_timestamps[0]) / (3600 * 24),
            (np.array(end_timestamps) - start_timestamps[0]) / (3600 * 24), fee, closes, amount, times, fee_reinvesting)


def normal_distribution_strategy(sigma, pool_id, Amount, days, priceToken, endTimestamp=now, protocol=0,
                                 fee_reinvesting=False, positions_num=25):
    prices = getPrices(priceToken)
    current_price = prices["close"].values[0]
    start_timestamp = prices["periodStartUnix"].values[0]
    max_prices_range = 30  # в процентах от данной цены
    prices_range = np.linspace(current_price * (100 - max_prices_range) / 100,
                               current_price * (100 + max_prices_range) / 100, num=positions_num)

    relative_liquidity_range = 1 / (sigma * np.sqrt(2 * np.pi)) * np.exp(
        - (prices_range - current_price) ** 2 / (2 * sigma ** 2))
    max_bin = max(relative_liquidity_range)
    liquidity = np.zeros_like(relative_liquidity_range)
    full_liquidity_multiplier = sum(relative_liquidity_range)
    for i in range(len(relative_liquidity_range)):
        liquidity[i] = relative_liquidity_range[i] * Amount / full_liquidity_multiplier
    # temp = sum(liquidity)
    # plt.bar(prices_range, liquidity,
    #         width=(prices_range[1] - prices_range[0]) * 2, color='b')
    # plt.show()
    bound_width = (prices_range[1] - prices_range[0]) * 2
    times = prices["periodStartUnix"].values
    amount = np.zeros(days * 24 - 1)
    closes = prices["close"].values
    fee = np.zeros(days * 24 - 1)
    fees = np.zeros(days * 24 - 1)
    low_bound = []
    high_bound = []
    end = np.zeros_like(liquidity)
    start = np.zeros_like(liquidity)
    for j in range(len(liquidity)):
        data = uniswapStrategyBacktest(pool_id, liquidity[j], prices_range[j] - bound_width / 2,
                                       prices_range[j] + bound_width / 2, start_timestamp, days=days,
                                       priceToken=priceToken)
        low_bound.append(prices_range[j] - bound_width / 4)
        high_bound.append(prices_range[j] + bound_width / 4)
        end[j] = ((endTimestamp - start_timestamp) * liquidity[j] / max(liquidity)) + start_timestamp
        start[j] = 0.
        end[j] = end[j] - start_timestamp
        for q in range(len(data)):
            amount[q] = amount[q] + data[q]["amountV"]
            fee[q] = fee[q] + data[q]["feeUSD"]
    for i in range(len(fee)):
        times[i] = times[i] - data[0]["unixDT"]
        fees[i] = sum(fee[:i])

    plotter(low_bound, high_bound, start / (3600 * 24), end / (3600 * 24), fees, closes, amount, times / (3600 * 24))


def get_lvls_and_rel_vol(symbol, from_date, days_ago=365):
    curr_date = datetime.fromtimestamp(from_date)
    past_date = datetime.fromtimestamp(from_date - (days_ago * 24 * 3600))
    past_month_name = calendar.month_abbr[past_date.month]
    current_month_name = calendar.month_abbr[curr_date.month]
    levels, _ = get_levels(symbol, "1h", "{} {} {}".format(past_date.day, past_month_name, past_date.year),
                           "{} {} {}".format(curr_date.day, current_month_name, curr_date.year))
    rel_vol = relative_volume(symbol, "1h", "{} {} {}".format(past_date.day, past_month_name, past_date.year),
                              "{} {} {}".format(curr_date.day, current_month_name, curr_date.year), levels)
    return levels, rel_vol


def analyzer(z1, z2, z1_width, z2_width, symbol, from_date, current_price, days, update_z1, update_z2):
    levels, rel_vol = get_lvls_and_rel_vol(symbol, from_date, days)
    if current_price < levels[1][0] or current_price > levels[len(levels) - 2][0]:
        if update_z2:
            z2["bottom"] = current_price * ((100 - z2_width) / 100)
            z2["top"] = current_price * ((100 + z2_width) / 100)
        if update_z1:
            z1["bottom"] = current_price * ((100 - z1_width) / 100)
            z1["top"] = current_price * ((100 + z1_width) / 100)
        return
    k = -1
    while current_price > levels[k + 1][0]:
        k += 1
    right_max = k + 1
    while right_max < len(rel_vol) - 1 and rel_vol[right_max] < rel_vol[right_max + 1]:
        right_max += 1
    left_max = k
    while left_max > 0 and rel_vol[left_max] < rel_vol[left_max - 1]:
        left_max -= 1
    if update_z1:
        z1["bottom"] = levels[k][0]
        z1["top"] = levels[k + 1][0]
    if update_z2:
        z2["bottom"] = levels[left_max][0]
        z2["top"] = levels[right_max][0]


def relative_volume_strategy(z1_width, z2_width, percent_itm, symbol, pool, investmentAmount, endTimestamp=now, days=30,
                             protocol=0, priceToken=0):
    from_date = DateByDaysAgo(days, endTimestamp)
    csv_data_saver(pool, days, endTimestamp, protocol)
    prices = getPrices(priceToken)
    time_itm = 0
    time1 = 0
    time2 = 0
    fee = []
    closes = []
    amount = []
    fees = 0
    times = []
    xMin = []
    xMax = []
    minBound = []
    maxBound = []
    data1 = []
    data2 = []
    z1 = {
        "proportion": .5,
        "bottom": None,
        "top": None
    }
    z2 = {
        "proportion": .5,
        "bottom": None,
        "top": None
    }
    analyzer(z1, z2, z1_width, z2_width, symbol, from_date, float(prices["close"].values[0]), 365, True, True)
    for i in range(len(prices)):
        if z1["bottom"] < float(prices["close"].values[i]) < z1["top"]:
            time_itm += 1
        time1 += 1
        time2 += 1

        if i == (len(prices) - 1) or (time_itm / time1) < (percent_itm / 100) or z2["bottom"] > float(
                prices["close"].values[i]) or float(prices["close"].values[i]) > z2["top"]:

            update_z1 = False
            update_z2 = False

            if (time_itm / time1) < (percent_itm / 100) or i == (len(prices) - 1):

                minBound.append(z1["bottom"])
                maxBound.append(z1["top"])
                xMin.append(
                    (prices["periodStartUnix"].values[i - time1 + 1] - prices["periodStartUnix"].values[0]) / (
                            3600 * 24))
                xMax.append((prices["periodStartUnix"].values[i] - prices["periodStartUnix"].values[0]) / (3600 * 24))
                backtest_z1 = uniswapStrategyBacktest(pool, z1["proportion"] * investmentAmount,
                                                      z1["bottom"], z1["top"],
                                                      prices["periodStartUnix"].values[i - time1 + 1],
                                                      prices["periodStartUnix"].values[i],
                                                      protocol=protocol, priceToken=priceToken, period="hourly")
                data1.extend(backtest_z1)
                time1 = 1
                time_itm = 1
                fees = 0
                for j in range(len(backtest_z1)):
                    fees += backtest_z1[j]["feeUSD"]
                investmentAmount = backtest_z1[-1]["amountV"] + fees
                update_z1 = True

            if z2["bottom"] > float(prices["close"].values[i]) or float(prices["close"].values[i]) > z2["top"] or i == (
                    len(prices) - 1):

                minBound.append(z2["bottom"])
                maxBound.append(z2["top"])
                xMin.append(
                    (prices["periodStartUnix"].values[i - time2 + 1] - prices["periodStartUnix"].values[0]) / (
                            3600 * 24))
                xMax.append((prices["periodStartUnix"].values[i] - prices["periodStartUnix"].values[0]) / (3600 * 24))
                backtest_z2 = uniswapStrategyBacktest(pool, z2["proportion"] * investmentAmount,
                                                      z2["bottom"], z2["top"],
                                                      prices["periodStartUnix"].values[i - time2 + 1],
                                                      prices["periodStartUnix"].values[i],
                                                      protocol=protocol, priceToken=priceToken, period="hourly")
                data2.extend(backtest_z2)
                time2 = 1
                fees = 0
                for j in range(len(backtest_z2)):
                    fees += backtest_z2[j]["feeUSD"]
                investmentAmount = backtest_z2[-1]["amountV"] + fees
                update_z2 = True

            if i == (len(prices) - 1):
                break

            analyzer(z1, z2, z1_width, z2_width, symbol, prices["periodStartUnix"].values[i],
                     float(prices["close"].values[i]), 365, update_z1, update_z2)

    fees = 0
    for j in range(len(data1)):
        fees = fees + data1[j]["feeUSD"] + data2[j]["feeUSD"]
        closes.append(data1[j]["close"])
        amount.append(data1[j]["amountV"] + data2[j]["amountV"])
        fee.append(fees)
        times.append((data1[j]["unixDT"] - prices["periodStartUnix"].values[0]) / (3600 * 24))
    plotter(minBound, maxBound, xMin, xMax, fee, closes, amount, times)


if __name__ == "__main__":
    days = 60
    priceToken = 1
    minRange = 1900
    maxRange = 2100
    investmentAmount = 100000
    pool = "0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36".lower()
    # data = uniswapStrategyBacktest(pool, investmentAmount,
    #                                     minRange, maxRange, days=days, priceToken=priceToken, period="hourly")

    # fee = []
    # closes = []
    # amount = []
    # fees = 0
    # times = []
    # for i in range(len(data)):
    #     fees = fees + data[i]["feeUSD"]
    #     closes.append(data[i]["close"])
    #     amount.append(data[i]["amountV"])
    #     fee.append(fees)
    #     times.append((data[i]["periodStartUnix"] - data[0]["periodStartUnix"]) / (3600 * 24))
    # plotter([minRange], [maxRange], [0], [days], fee, closes, amount, times)
    # print(json.dumps(data, indent=2))

    # _2_pos_strategy(100, 250, "0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36".lower(), investmentAmount, days=days,
    #                         priceToken=1)

    _X_percent_ITM_strategy(65, 12, pool, investmentAmount, days=days,
                            priceToken=1)

    # relative_volume_strategy(z1_width=5, z2_width=10, percent_itm=100, symbol="ETHUSDT", pool=pool,
    #                          investmentAmount=investmentAmount, endTimestamp=now, days=days,
    #                          protocol=0, priceToken=1)

    # normal_distribution_strategy(100, "0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36".lower(), investmentAmount, days, priceToken)

# 0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36  USDT / WETH 0.3
# 0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640  WETH / USDC 0.05
# 0xCBCdF9626bC03E24f779434178A73a0B4bad62eD  WBTC / ETH  0.3%
