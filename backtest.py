from calc import *
import numpy as np
import math
from datetime import datetime


# calculate the amount of fees earned in 1 period by 1 unit of unbounded liquidity
# fg0 represents the amount of token 0, fg1 represents the amount of token1
def calcUnboundedFees(globalfee0, prevGlobalfee0, globalfee1, prevGlobalfee1, poolSelected):
    fg0_0 = ((int(globalfee0)) / pow(2, 128)) / (pow(10, int(poolSelected[0]["token0"]["decimals"])))
    fg0_1 = (((int(prevGlobalfee0))) / pow(2, 128)) / (pow(10, int(poolSelected[0]["token0"]["decimals"])))
    fg1_0 = ((int(globalfee1)) / pow(2, 128)) / (pow(10, int(poolSelected[0]["token1"]["decimals"])))
    fg1_1 = (((int(prevGlobalfee1))) / pow(2, 128)) / (pow(10, int(poolSelected[0]["token1"]["decimals"])))

    fg0 = (fg0_0 - fg0_1)
    fg1 = (fg1_0 - fg1_1)

    return [fg0, fg1]


# calculate the liquidity tick at a specified price
def getTickFromPrice(price, pool, baseSelected=0):
    if baseSelected == 1:
        decimal0 = int(pool[0]["token1"]["decimals"])
        decimal1 = int(pool[0]["token0"]["decimals"])
    else:
        decimal0 = int(pool[0]["token0"]["decimals"])
        decimal1 = int(pool[0]["token1"]["decimals"])

    valToLog = float(price) * pow(10, (decimal0 - decimal1))
    tickIDXRaw = logWithBase(valToLog, 1.0001)

    return round(tickIDXRaw, 0)


# estimate the percentage of active liquidity for 1 period for a strategy based on min max bounds
# low and high are the period's candle low / high values
def activeLiquidityForCandle(minimum, maximum, low, high):
    if (high - low) != 0:
        divider = high - low
        ratioTrue = (min(maximum, high) - max(minimum, low)) / divider
    else:
        divider = 1
        ratioTrue = 1

    if high > minimum and low < maximum:
        ratio = ratioTrue * 1000
    else:
        ratio = 0

    if np.isnan(ratio):
        return 0
    else:
        return ratio


# Calculate the number of tokens for a Strategy at a specific amount of liquidity & price
def tokensFromLiquidity(price, low, high, liquidity, decimal0, decimal1):
    decimal = decimal1 - decimal0
    lowHigh = [(math.sqrt(low * pow(10, decimal))) * pow(2, 96), (math.sqrt(high * pow(10, decimal))) * pow(2, 96)]
    sPrice = (math.sqrt(price * pow(10, decimal))) * pow(2, 96)

    sLow = min(lowHigh)

    sHigh = max(lowHigh)

    if (sPrice <= sLow):

        amount1 = ((liquidity * pow(2, 96) * (sHigh - sLow) / sHigh / sLow) / pow(10, decimal0))
        return [0, amount1]

    elif (sPrice < sHigh and sPrice > sLow):
        amount0 = liquidity * (sPrice - sLow) / pow(2, 96) / pow(10, decimal1)
        amount1 = ((liquidity * pow(2, 96) * (sHigh - sPrice) / sHigh / sPrice) / pow(10, decimal0))
        return [amount0, amount1]

    else:
        amount0 = liquidity * (sHigh - sLow) / pow(2, 96) / pow(10, decimal1)
        return [amount0, 0]


# Calculate the number of Tokens a strategy owns at a specific price
def tokensForStrategy(minRange, maxRange, investment, price, decimal):
    sqrtPrice = math.sqrt(price * (pow(10, decimal)))
    sqrtLow = math.sqrt(minRange * (pow(10, decimal)))
    sqrtHigh = math.sqrt(maxRange * (pow(10, decimal)))

    if (sqrtPrice > sqrtLow and sqrtPrice < sqrtHigh):

        delta = investment / (
                ((sqrtPrice - sqrtLow)) + (((1 / sqrtPrice) - (1 / sqrtHigh)) * (price * pow(10, decimal))))
        amount1 = delta * (sqrtPrice - sqrtLow)
        amount0 = delta * ((1 / sqrtPrice) - (1 / sqrtHigh)) * pow(10, decimal)

    elif (sqrtPrice < sqrtLow):
        delta = investment / ((((1 / sqrtLow) - (1 / sqrtHigh)) * price))
        amount1 = 0
        amount0 = delta * ((1 / sqrtLow) - (1 / sqrtHigh))

    else:
        delta = investment / ((sqrtHigh - sqrtLow))
        amount1 = delta * (sqrtHigh - sqrtLow)
        amount0 = 0

    return [amount0, amount1]


# Calculate the liquidity share for a strategy based on the number of tokens owned
def liquidityForStrategy(price, low, high, tokens0, tokens1, decimal0, decimal1):
    decimal = decimal1 - decimal0
    lowHigh = [(math.sqrt(low * pow(10, decimal))) * pow(2, 96), (math.sqrt(high * pow(10, decimal))) * pow(2, 96)]
    sPrice = (math.sqrt(price * pow(10, decimal))) * pow(2, 96)
    sLow = min(lowHigh)
    sHigh = max(lowHigh)

    if (sPrice <= sLow):

        return tokens0 / ((pow(2, 96) * (sHigh - sLow) / sHigh / sLow) / pow(10, decimal0))

    elif (sPrice <= sHigh and sPrice > sLow):

        liq0 = tokens0 / ((pow(2, 96) * (sHigh - sPrice) / sHigh / sPrice) / pow(10, decimal0))
        liq1 = tokens1 / ((sPrice - sLow) / pow(2, 96) / pow(10, decimal1))
        return min(liq1, liq0)
    else:
        return tokens1 / ((sHigh - sLow) / pow(2, 96) / pow(10, decimal1))


# Calculate estimated fees
def calcFees(data, pool, priceToken, liquidity, unboundedLiquidity, investment, min, max):
    for i in range(len(data)):
        if i == 0:
            fg = [0, 0]
        else:
            fg = calcUnboundedFees(float(data[i]["feeGrowthGlobal0X128"]), float(data[(i - 1)]["feeGrowthGlobal0X128"]),
                                   float(data[i]["feeGrowthGlobal1X128"]), float(data[(i - 1)]["feeGrowthGlobal1X128"]),
                                   pool)

        if float(data[i]["low"]) == 0:
            dtemp = 1
        else:
            dtemp = float(data[i]["low"])
        if priceToken == 0:
            low = float(data[i]["low"])
        else:
            low = dtemp

        if float(data[i]["high"]) == 0:
            dtemp1 = 1
        else:
            dtemp1 = float(data[i]["high"])
        if priceToken == 0:
            high = float(data[i]["high"])
        else:
            high = dtemp1

        lowTick = getTickFromPrice(low, pool, priceToken)
        highTick = getTickFromPrice(high, pool, priceToken)
        minTick = getTickFromPrice(min, pool, priceToken)
        maxTick = getTickFromPrice(max, pool, priceToken)

        activeLiquidity = activeLiquidityForCandle(minTick, maxTick, lowTick, highTick)

        if priceToken == 1:
            price = 1 / float(data[i]["close"])
            firstClose = 1 / float(data[0]["close"])
        else:
            price = float(data[i]["close"])
            firstClose = float(data[0]["close"])

        tokens = tokensFromLiquidity(price, min, max, liquidity, int(pool[0]["token0"]["decimals"]),
                                     int(pool[0]["token1"]["decimals"]))

        if i == 0:
            feeToken0 = 0
            feeUnb0 = 0
        else:
            feeToken0 = fg[0] * liquidity * activeLiquidity / 100
            feeUnb0 = fg[0] * unboundedLiquidity

        if i == 0:
            feeToken1 = 0
            feeUnb1 = 0
        else:
            feeToken1 = fg[1] * liquidity * activeLiquidity / 100
            feeUnb1 = fg[0] * unboundedLiquidity

        latestRec = data[(len(data) - 1)]

        tokenRatioFirstClose = tokensFromLiquidity(firstClose, min, max, liquidity, int(pool[0]["token0"]["decimals"]),
                                                   int(pool[0]["token1"]["decimals"]))

        x0 = tokenRatioFirstClose[1]
        y0 = tokenRatioFirstClose[0]

        if (priceToken == 0):
            if i == 0:
                fgV = 0
                feeV = 0
                feeUnb = 0
            else:
                fgV = fg[0] + (fg[1] * float(data[i]["close"]))
                feeV = feeToken0 + (feeToken1 * float(data[i]["close"]))
                feeUnb = feeUnb0 + (feeUnb1 * float(data[i]["close"]))

            amountV = tokens[0] + (tokens[1] * float(data[i]["close"]))
            feeUSD = feeV * float(latestRec["pool"]["totalValueLockedUSD"]) / (
                    (float(latestRec["pool"]["totalValueLockedToken1"]) * float(latestRec["close"])) + float(
                latestRec["pool"]["totalValueLockedToken0"]))
            amountTR = investment + (amountV - ((x0 * float(data[i]["close"])) + y0))

        elif (priceToken == 1):

            if i == 0:
                fgV = 0
                feeV = 0
                feeUnb = 0
            else:
                fgV = fg[0] + (fg[1] * float(data[i]["close"]))
                feeV = feeToken0 + (feeToken1 * float(data[i]["close"]))
                feeUnb = feeUnb0 + (feeUnb1 * float(data[i]["close"]))

            amountV = (tokens[1] / float(data[i]["close"])) + tokens[0]
            feeUSD = feeV * float(latestRec["pool"]["totalValueLockedUSD"]) / (
                    float(latestRec["pool"]["totalValueLockedToken1"]) + (
                    float(latestRec["pool"]["totalValueLockedToken0"]) / float(latestRec["close"])))
            amountTR = investment + (amountV - ((x0 * (1 / float(data[i]["close"]))) + y0))

        date = data[i]["periodStartUnix"]

        data[i].update({
            "unixDT": date,
            "fg0": fg[0],
            "fg1": fg[1],
            "activeliquidity": activeLiquidity,
            "feeToken0": feeToken0,
            "feeToken1": feeToken1,
            "tokens": tokens,
            "fgV": fgV,
            "feeV": feeV,
            "feeUnb": feeUnb,
            "amountV": amountV,
            "amountTR": amountTR,
            "feeUSD": feeUSD,
            "close": float(data[i]["close"]),
            "baseClose": float(data[i]["close"])
        })
    return data


# Pivot hourly estimated fee data (generated by calcFees) into daily values
def pivotFeeData(data, priceToken, investment):
    def createPivotRecord(date, data):
        if np.isnan(data["activeliquidity"]):
            activeliquidity = 0
        else:
            activeliquidity = data["activeliquidity"]
        if priceToken == 1:
            baseClose = 1 / data["close"]
        else:
            baseClose = data["close"]
        return {
            "date": datetime.utcfromtimestamp(date).strftime('%Y-%m-%d %H:%M:%S'),
            "unixDT": date,
            "feeToken0": data["feeToken0"],
            "feeToken1": data["feeToken1"],
            "feeV": data["feeV"],
            "feeUnb": data["feeUnb"],
            "fgV": float(data["fgV"]),
            "feeUSD": data["feeUSD"],
            "activeliquidity": activeliquidity,
            "amountV": data["amountV"],
            "amountTR": data["amountTR"],
            "amountVLast": data["amountV"],
            "percFee": data["feeV"] / data["amountV"],
            "close": data["close"],
            "baseClose": baseClose,
            "count": 1
        }

    firstDate = data[0]["periodStartUnix"]
    pivot = [createPivotRecord(firstDate, data[0])]

    for i in range(len(data)):
        if (i > 0):
            currentDate = data[i]["periodStartUnix"]
            currentPriceTick = pivot[(len(pivot) - 1)]

            if datetime.utcfromtimestamp(currentDate).year == datetime.utcfromtimestamp(
                    currentPriceTick["unixDT"]).year and datetime.utcfromtimestamp(
                    currentDate).month == datetime.utcfromtimestamp(
                    currentPriceTick["unixDT"]).month and datetime.utcfromtimestamp(
                    currentDate).day == datetime.utcfromtimestamp(currentPriceTick["unixDT"]).day:

                currentPriceTick["feeToken0"] = currentPriceTick["feeToken0"] + data[i]["feeToken0"]
                currentPriceTick["feeToken1"] = currentPriceTick["feeToken1"] + data[i]["feeToken1"]
                currentPriceTick["feeV"] = currentPriceTick["feeV"] + data[i]["feeV"]
                currentPriceTick["feeUnb"] = currentPriceTick["feeUnb"] + data[i]["feeUnb"]
                currentPriceTick["fgV"] = float(currentPriceTick["fgV"]) + float(data[i]["fgV"])
                currentPriceTick["feeUSD"] = currentPriceTick["feeUSD"] + data[i]["feeUSD"]
                currentPriceTick["activeliquidity"] = currentPriceTick["activeliquidity"] + data[i]["activeliquidity"]
                currentPriceTick["amountVLast"] = data[i]["amountV"]
                currentPriceTick["count"] = currentPriceTick["count"] + 1

                if i == (len(data) - 1):
                    currentPriceTick["activeliquidity"] = currentPriceTick["activeliquidity"] / currentPriceTick[
                        "count"]
                    currentPriceTick["percFee"] = currentPriceTick["feeV"] / currentPriceTick["amountV"] * 100
            else:
                currentPriceTick["activeliquidity"] = currentPriceTick["activeliquidity"] / currentPriceTick["count"]
                currentPriceTick["percFee"] = currentPriceTick["feeV"] / currentPriceTick["amountV"] * 100
                pivot.append(createPivotRecord(currentDate, data[i]))
    return pivot
