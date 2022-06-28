from get_historical_data import *
from backtest import *
import time
import json
import matplotlib.pyplot as plt


def plotter(data):
    time = []
    fee = []
    closes = []
    amount = []
    fees = 0
    for i in range(len(data)):
        time.append(i)
        fees = fees + data[i]["feeUSD"]
        closes.append(data[i]["close"])
        amount.append(data[i]["amountV"])
        fee.append(fees)
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 10))
    ax1.plot(time, fee)
    ax1.set_title("feeUSD")
    if closes[0] < 1:
        ax2.plot(time, [1 / i for i in closes])
    else:
        ax2.plot(time, closes)
    ax2.hlines(minRange, time[0], time[-1], "r")
    ax2.hlines(maxRange, time[0], time[-1], "r")
    ax2.set_title("closes_price")
    ax3.plot(time, amount)
    ax3.set_title("LP_value")
    for ax in (ax1, ax2, ax3):
        ax.grid()
    plt.show()


now = int(time.time())


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
        entryPrice = 1 / float(backtestData[0]["close"])
        decimal = int(poolData[0]["token0"]["decimals"]) - int(poolData[0]["token1"]["decimals"])
    else:
        entryPrice = float(backtestData[0]["close"])
        decimal = int(poolData[0]["token1"]["decimals"]) - int(poolData[0]["token0"]["decimals"])
    tokens = tokensForStrategy(minRange, maxRange, investmentAmount, float(entryPrice), decimal)
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


if __name__ == "__main__":
    minRange = 800
    maxRange = 1200
    investmentAmount = 100000
    backtest1 = uniswapStrategyBacktest("0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36".lower(), investmentAmount,
                                        minRange, maxRange, days=15, priceToken=1, period="daily")
    print(json.dumps(backtest1, indent=2))
    plotter(backtest1)

# 0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36  USDT / WETH 0.3
# 0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640  WETH / USDC 0.05
