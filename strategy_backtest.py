from get_historical_data import *
from backtest import *
import time
import json
import matplotlib.pyplot as plt
import itertools
import numpy as np


#def plotter(data, ranges):
#    fee = []
#    closes = []
#    amount = []
#    fees = 0
#    times = []
#    for i in range(len(data)):
#        fees = fees + data[i]["feeUSD"]
#        closes.append(data[i]["close"])
#        amount.append(data[i]["amountV"])
#        fee.append(fees)
#        times.append((data[i]["periodStartUnix"] - data[0]["periodStartUnix"]) / (3600 * 24))

def plotter(minRange, maxRange, xMin, xMax, fee, closes, amount, times):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 10))
    ax1.plot(times, fee)
    ax1.set_title("feeUSD")
    if closes[0] < 1:
        ax2.plot(times, [1 / i for i in closes])
    else:
        ax2.plot(times, closes)
    for i in range(len(minRange)):
        ax2.fill_between(np.arange(xMin[i], xMax[i], 1 / 24), minRange[i], maxRange[i], color='r', alpha=.2)
        # ax2.hlines(minRange[i], xMin[i], xMax[i], "r")
        # ax2.hlines(maxRange[i], xMin[i], xMax[i], "r")
    ax2.set_title("closes_price")
    ax3.plot(times, amount, times, np.array(amount) + np.array(fee))
    ax3.set_title("LP_value")
    for ax in (ax1, ax2, ax3):
        ax.grid()
    plt.show()


now = int(time.time())


def DateByDaysAgo(days, endDate=now):
    return endDate - days * 86400


# data, pool, baseID, liquidity, unboundedLiquidity, min, max, customFeeDivisor, leverage, investment, tokenRatio
# Required = Pool ID, investmentAmount (token0 by default), minRange, maxRange, options = { days, protocol, baseToken }
def uniswapStrategyBacktest(pool, investmentAmount, minRange, maxRange, startTimestamp=0, endTimestamp=now, days=30,
                            protocol=0,
                            priceToken=0, period="hourly"):
    poolData = poolById(pool)
    if startTimestamp == 0:
        startTimestamp = DateByDaysAgo(days, endTimestamp)
    backtestData = getPoolHourData(pool, startTimestamp, endTimestamp, protocol)
    if priceToken == 1:
        entryPrice = 1 / float(backtestData[0]["close"])
        # decimal = int(poolData[0]["token0"]["decimals"]) - int(poolData[0]["token1"]["decimals"])
    else:
        entryPrice = float(backtestData[0]["close"])
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
    if period == "daily":
        return pivotFeeData(hourlyBacktest, priceToken, investmentAmount)
    else:
        return hourlyBacktest


def getPrices(pool, from_date, endTimestamp=now, priceToken=0, protocol=0):
    price = getPoolHourData(pool, from_date=from_date, to_date=endTimestamp, protocol=protocol)
    if priceToken == 1:
        for e in price:
            e["close"] = 1 / float(e["close"])
    return price


def _X_percent_ITM_strategy(percent_itm, width, pool, investmentAmount, endTimestamp=now, days=30, protocol=0,
                            priceToken=0):
    from_date = DateByDaysAgo(days, endTimestamp)
    prices = getPrices(pool, from_date, endTimestamp, priceToken, protocol)
    time_itm = 0
    time = 0
    current_price = float(prices[0]["close"])
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
        if (current_price * ((100 - width) / 100)) < float(prices[i]["close"]) < (
                current_price * ((100 + width) / 100)):
            time_itm += 1
        time += 1
        if (time_itm / time) < (percent_itm / 100) or i == (len(prices) - 1):
            minBound.append(current_price * ((100 - width) / 100))
            maxBound.append(current_price * ((100 + width) / 100))
            xMin.append((prices[i - time + 1]["periodStartUnix"] - prices[0]["periodStartUnix"]) / (3600 * 24))
            xMax.append((prices[i]["periodStartUnix"] - prices[0]["periodStartUnix"]) / (3600 * 24))
            backtest_data = uniswapStrategyBacktest(pool, investmentAmount, current_price * ((100 - width) / 100),
                                                    current_price * ((100 + width) / 100),
                                                    prices[i - time + 1]["periodStartUnix"],
                                                    prices[i]["periodStartUnix"],
                                                    protocol=protocol, priceToken=priceToken, period="hourly")
            data.extend(backtest_data)
            fees = 0
            for j in range(len(backtest_data)):
                fees = fees + backtest_data[j]["feeUSD"]
            time = 0
            time_itm = 0
            investmentAmount = data[-1]["amountV"] + fees
            current_price = float(prices[i]["close"])
    fees = 0
    for j in range(len(data)):
        fees = fees + data[j]["feeUSD"]
        closes.append(data[j]["close"])
        amount.append(data[j]["amountV"])
        fee.append(fees)
        times.append((data[j]["periodStartUnix"] - prices[0]["periodStartUnix"]) / (3600 * 24))
    plotter(minBound, maxBound, xMin, xMax, fee, closes, amount, times)


def _2_pos_strategy(percent_itm, width, pool, investmentAmount, endTimestamp=now, days=30, protocol=0,
                    priceToken=0):
    from_date = DateByDaysAgo(days, endTimestamp)
    prices = getPrices(pool, from_date, endTimestamp, priceToken, protocol)
    time_itm = 0
    time = 0
    current_price = float(prices[0]["close"])
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
    data_bottom = []
    for i in range(len(prices)):
        if (current_price - width) < float(prices[i]["close"]) < (current_price + width):
            time_itm += 1
        time += 1
        if (time_itm / time) < (percent_itm / 100) or i == (len(prices) - 1):
            minBound.append(current_price - width)
            maxBound.append(current_price)
            xMin.append((prices[i - time + 1]["periodStartUnix"] - prices[0]["periodStartUnix"]) / (3600 * 24))
            xMax.append((prices[i]["periodStartUnix"] - prices[0]["periodStartUnix"]) / (3600 * 24))
            bottom = uniswapStrategyBacktest(pool, investmentAmount / 2,
                                                  current_price - width, current_price,
                                                  prices[i - time + 1]["periodStartUnix"],
                                                  prices[i]["periodStartUnix"],
                                                  protocol=protocol, priceToken=priceToken, period="hourly")
            minBound.append(current_price)
            maxBound.append(current_price+ width)
            xMin.append((prices[i - time + 1]["periodStartUnix"] - prices[0]["periodStartUnix"]) / (3600 * 24))
            xMax.append((prices[i]["periodStartUnix"] - prices[0]["periodStartUnix"]) / (3600 * 24))
            top = uniswapStrategyBacktest(pool, investmentAmount / 2,
                                               current_price, current_price + width,
                                               prices[i - time + 1]["periodStartUnix"],
                                               prices[i]["periodStartUnix"],
                                               protocol=protocol, priceToken=priceToken, period="hourly")
            data_top.extend(top)
            data_bottom.extend(bottom)
            fees = 0
            for j in range(len(top)):
                fees += top[j]["feeUSD"]
            for j in range(len(bottom)):
                fees += bottom[j]["feeUSD"]
            time = 0
            time_itm = 0
            investmentAmount = top[-1]["amountV"] + bottom[-1]["amountV"] + fees
            current_price = float(prices[i]["close"])
    fees = 0
    for j in range(len(data_top)):
        fees = fees + data_top[j]["feeUSD"] + data_bottom[j]["feeUSD"]
        closes.append(data_top[j]["close"])
        amount.append(data_top[j]["amountV"] + data_bottom[j]["amountV"])
        fee.append(fees)
        times.append((data_top[j]["periodStartUnix"] - prices[0]["periodStartUnix"]) / (3600 * 24))
    plotter(minBound, maxBound, xMin, xMax, fee, closes, amount, times)



if __name__ == "__main__":
    days = 60
    priceToken = 1
    minRange = 1000
    maxRange = 5000
    investmentAmount = 100000
    # price = getPrices("0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36".lower(), DateByDaysAgo(days, now), now, priceToken)
    # if priceToken == 1:
    #     for e in price:
    #         e["close"] = 1 / float(e["close"])
    # backtest1 = uniswapStrategyBacktest("0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36".lower(), investmentAmount,
    #                                     minRange, maxRange, days=days, priceToken=priceToken, period="hourly")
    # print(json.dumps(backtest1, indent=2))
    # _2_pos_strategy(90, 180, "0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36".lower(), investmentAmount, days=days,
    #                         priceToken=1)
    _X_percent_ITM_strategy(95, 10, "0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36".lower(), investmentAmount, days=days,
                            priceToken=1)

# 0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36  USDT / WETH 0.3
# 0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640  WETH / USDC 0.05
# 0xCBCdF9626bC03E24f779434178A73a0B4bad62eD  WBTC / ETH  0.3%
