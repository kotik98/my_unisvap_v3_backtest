from get_historical_data import *
from backtest import *
import time
import json
import matplotlib.pyplot as plt
import itertools
import numpy as np


def plotter(data, minRange, maxRange, xMin, xMax):
    fee = []
    closes = []
    amount = []
    fees = 0
    times = []
    for i in range(len(data)):
        fees = fees + data[i]["feeUSD"]
        closes.append(data[i]["close"])
        amount.append(data[i]["amountV"])
        fee.append(fees)
        times.append((data[i]["periodStartUnix"] - data[0]["periodStartUnix"]) / (3600 * 24))
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


def getFullPoolHourData(pool, days, endTimestamp=now, protocol=0):
    startTimestamp = DateByDaysAgo(days, endTimestamp)
    if days > 41:
        hours_num = days * 24
        request_quantity = math.ceil(hours_num / 1000)
        backtestData = []
        current_start_Timestamp = startTimestamp
        current_end_Timestamp = startTimestamp + 1000 * 3600
        for i in range(request_quantity):
            backtestData.extend((getPoolHourData(pool, current_start_Timestamp, current_end_Timestamp, protocol)))

            current_start_Timestamp = current_end_Timestamp
            if hours_num - len(backtestData) < 1000:
                current_end_Timestamp = endTimestamp
            else:
                current_end_Timestamp = current_end_Timestamp + 1000 * 3600
    else:
        backtestData = getPoolHourData(pool, startTimestamp, endTimestamp, protocol)
    return backtestData


# data, pool, baseID, liquidity, unboundedLiquidity, min, max, customFeeDivisor, leverage, investment, tokenRatio
# Required = Pool ID, investmentAmount (token0 by default), minRange, maxRange, options = { days, protocol, baseToken }
def uniswapStrategyBacktest(pool, investmentAmount, minRange, maxRange, endTimestamp=now, days=30, protocol=0,
                            priceToken=0, period="hourly"):
    poolData = poolById(pool)
    startTimestamp = DateByDaysAgo(days, endTimestamp)
    backtestData = getFullPoolHourData(pool, days, endTimestamp, protocol)
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


def getPrices(pool, days, endTimestamp=now, protocol=0):
    price = getFullPoolHourData("0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36".lower(), period)
    if priceToken == 1:
        for e in price:
            e["close"] = 1 / float(e["close"])
    return price


def _X_percent_ITM_strategy(x, pool, investmentAmount, minRange, maxRange, endTimestamp=now, days=30, protocol=0,
                            priceToken=0):
    pass


if __name__ == "__main__":
    period = 30
    priceToken = 1
    minRange = 1000
    maxRange = 5000
    investmentAmount = 1000
    price = getPrices("0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36".lower(), period)
    if priceToken == 1:
        for e in price:
            e["close"] = 1 / float(e["close"])
    backtest1 = uniswapStrategyBacktest("0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36".lower(), investmentAmount,
                                        minRange, maxRange, days=period, priceToken=priceToken, period="hourly")
    print(json.dumps(backtest1, indent=2))
    plotter(backtest1, [minRange], [maxRange], [5], [15])

# 0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36  USDT / WETH 0.3
# 0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640  WETH / USDC 0.05
# 0xCBCdF9626bC03E24f779434178A73a0B4bad62eD  WBTC / ETH  0.3%
