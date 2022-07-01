from get_historical_data import *
from backtest import *
import time
import json
import matplotlib.pyplot as plt
import itertools


def plotter(data, ranges):
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
    ax2.plot(times, ranges[0], 'r', times, ranges[1], 'r')
    # ax2.hlines(minRange[i], xMin[i], xMax[i], "r")
    # ax2.hlines(maxRange[i], xMin[i], xMax[i], "r")
    ax2.set_title("closes_price")
    ax3.plot(times, amount, times, np.array(amount) + np.array(fee))
    ax3.set_title("LP_value")
    for ax in (ax1, ax2, ax3):
        ax.grid()
    plt.show()


now = int(time.time())


def calc_backtests_schedule(prices, width):
    up_bound = np.zeros(len(prices))
    down_bound = np.zeros(len(prices))
    start_timestamps = []
    end_timestamps = []
    low_b = []
    high_b = []
    down_bound[0] = prices[0]["close"] * (1 - bounds_width)
    up_bound[0] = prices[0]["close"] * (1 + bounds_width)
    bounds_change_index = 0
    start_timestamps.append(prices[0]["periodStartUnix"])

    low_b.append(down_bound[0])
    high_b.append(up_bound[0])

    for i in range(1, len(prices)):
        if prices[i]["close"] <= up_bound[i - 1] and prices[i]["close"] >= down_bound[i - 1]:
            down_bound[i] = down_bound[i - 1]
            up_bound[i] = up_bound[i - 1]
        else:

            end_timestamps.append(prices[i]["periodStartUnix"])
            start_timestamps.append(prices[i + 1]["periodStartUnix"])
            down_bound[i] = prices[i]["close"] * (1 - bounds_width)
            up_bound[i] = prices[i]["close"] * (1 + bounds_width)
            low_b.append(down_bound[i])
            high_b.append(up_bound[i])
            bounds_change_index = bounds_change_index + 1
    end_timestamps.append(prices[-1]["periodStartUnix"])
    return [up_bound, down_bound], [start_timestamps, end_timestamps], [high_b, low_b]


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


def getPrices(pool, from_date, endTimestamp=now, protocol=0):
    price = getPoolHourData(pool,
                            from_date=from_date, to_date=endTimestamp,
                            protocol=protocol)
    if priceToken == 1:
        for e in price:
            e["close"] = 1 / float(e["close"])
    return price


def _X_percent_ITM_strategy(percent_itm, width, pool, investmentAmount, endTimestamp=now, days=30, protocol=0,
                            priceToken=0):
    prices = getPrices(pool, days, endTimestamp, protocol)
    time_itm = 0
    time = 0
    current_price = float(prices[0]["close"])
    for i in range(len(prices)):
        if (current_price * ((100 - width) / 100)) < float(prices[i]["close"]) < (
                current_price * ((100 + width) / 100)):
            time_itm += 1
        time += 1
        if (time_itm / time) < ((100 - percent_itm) / 100):
            backtest_data = uniswapStrategyBacktest(pool, investmentAmount, current_price * ((100 - width) / 100),
                                                    current_price * ((100 + width) / 100),
                                                    prices[i - time - 1]["periodStartUnix"],
                                                    prices[i]["periodStartUnix"],
                                                    protocol=protocol, priceToken=priceToken, period="hourly")


def _simple_bounds_strategy(bounds_width, pool_id, Amount, days):
    prices = getPrices(pool_id, DateByDaysAgo(days))

    up_bound = np.zeros(len(prices))
    down_bound = np.zeros(len(prices))
    start_timestamps = []
    end_timestamps = []
    low_b = []
    high_b = []
    down_bound[0] = prices[0]["close"] * (1 - bounds_width)
    up_bound[0] = prices[0]["close"] * (1 + bounds_width)
    bounds_change_index = 0
    start_timestamps.append(prices[0]["periodStartUnix"])

    low_b.append(down_bound[0])
    high_b.append(up_bound[0])

    for i in range(1, len(prices)):
        if prices[i]["close"] <= up_bound[i - 1] and prices[i]["close"] >= down_bound[i - 1]:
            down_bound[i] = down_bound[i - 1]
            up_bound[i] = up_bound[i - 1]
        else:

            end_timestamps.append(prices[i]["periodStartUnix"])
            start_timestamps.append(prices[i + 1]["periodStartUnix"])
            down_bound[i] = prices[i]["close"] * (1 - bounds_width)
            up_bound[i] = prices[i]["close"] * (1 + bounds_width)
            low_b.append(down_bound[i])
            high_b.append(up_bound[i])
            bounds_change_index = bounds_change_index + 1
    end_timestamps.append(prices[-1]["periodStartUnix"])

    bounds_for_plot = [up_bound, down_bound]
    timestamps = [start_timestamps, end_timestamps]
    bounds = [high_b, low_b]

    backtest = []
    for j in range(len(timestamps[0])):
        backtest.extend(uniswapStrategyBacktest(pool_id, Amount,
                                                maxRange=bounds[0][j], minRange=bounds[1][j],
                                                startTimestamp=timestamps[0][j],
                                                endTimestamp=timestamps[1][j], priceToken=priceToken, period="hourly"))
        Amount = backtest[-1]["amountV"]

    return backtest, bounds_for_plot


if __name__ == "__main__":
    days = 15
    priceToken = 1
    minRange = 1000
    maxRange = 5000
    investmentAmount = 1000
    bounds_width = 0.2  # ширина в процентах от цены
    pool_id = "0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36".lower()

    backtest, bounds_for_plot = _simple_bounds_strategy(bounds_width, pool_id, investmentAmount, days)

    print(json.dumps(backtest, indent=2))
    plotter(backtest, bounds_for_plot)

# 0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36  USDT / WETH 0.3
# 0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640  WETH / USDC 0.05
# 0xCBCdF9626bC03E24f779434178A73a0B4bad62eD  WBTC / ETH  0.3%
