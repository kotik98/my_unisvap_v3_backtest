from get_historical_data import *
from backtest import *
import time
import json
import matplotlib.pyplot as plt

now = int(time.time())

THRESHOLD_LOW = 1500
THRESHOLD_UP = 1700
CASH_AMOUNT = 1000

def plotter(data):
    time = []
    fee = []
    closes = []
    amount = []
    fees = 0
    for i in range(len(data)):
        time.append(data[i]["unixDT"])
        fees = fees + data[i]["feeUSD"]
        closes.append(data[i]["close"])
        amount.append(data[i]["amountV"])
        fee.append(fees)
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1)
    ax1.plot(time, fee)
    ax1.set_title("feeUSD")
    ax2.plot(time, closes)
    ax2.hlines(THRESHOLD_LOW, time[0], time[-1],"r")
    ax2.hlines(THRESHOLD_UP, time[0], time[-1], "r")
    ax2.set_title("closes_price")
    ax3.plot(time, amount)
    ax3.set_title("LP_value")
    plt.show()

def DateByDaysAgo(days, endDate=now):
    return endDate - days * 86400


# data, pool, baseID, liquidity, unboundedLiquidity, min, max, customFeeDivisor, leverage, investment, tokenRatio
# Required = Pool ID, investmentAmount (token0 by default), minRange, maxRange, options = { days, protocol, baseToken }
def uniswapStrategyBacktest(pool, investmentAmount, minRange, maxRange, endTimestamp=now, days=30, protocol=0,
                            priceToken=0, period="hourly"):
    poolData = poolById(pool)
    startTimestamp = DateByDaysAgo(days, endTimestamp)
    backtestData = getPoolHourData(pool, startTimestamp, endTimestamp, protocol)
    if priceToken == 1:
        entryPrice = 1 / backtestData[0]["close"]
    else:
        entryPrice = backtestData[0]["close"]
    tokens = tokensForStrategy(minRange, maxRange, investmentAmount, float(entryPrice),
                               int(poolData[0]["token1"]["decimals"]) - int(poolData[0]["token0"]["decimals"]))
    liquidity = liquidityForStrategy(float(entryPrice), minRange, maxRange, tokens[0], tokens[1],
                                     int(poolData[0]["token0"]["decimals"]),
                                     int(poolData[0]["token1"]["decimals"]))
    unbLiquidity = liquidityForStrategy(float(entryPrice), 1.0001 ** -887220, 1.0001 ** 887220, tokens[0],
                                        tokens[1], int(poolData[0]["token0"]["decimals"]),
                                        int(poolData[0]["token1"]["decimals"]))
    hourlyBacktest = calcFees(backtestData, poolData, priceToken, liquidity, unbLiquidity, investmentAmount, minRange,
                              maxRange)
    if period == "daily":
        return pivotFeeData(hourlyBacktest, priceToken, investmentAmount)
    else:
        return hourlyBacktest


if __name__ == "__main__":
    backtest1 = uniswapStrategyBacktest("0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", CASH_AMOUNT, THRESHOLD_LOW,
                                        THRESHOLD_UP, days=45,
                                        period="daily")
    print(backtest1)
    plotter(backtest1)
