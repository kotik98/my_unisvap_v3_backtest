from get_historical_data import *
from backtest import *
import time
import json

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
    print(json.dumps(
        uniswapStrategyBacktest("0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", 1000, 2120.09, 2662.99, days=2,
                                period="daily"), indent=2))
