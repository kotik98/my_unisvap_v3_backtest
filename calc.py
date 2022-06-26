import math

def my_round(number, decimalPlaces):
    factorOfTen = 10 ** decimalPlaces
    return round(number * factorOfTen) / factorOfTen


def sumArray(arr):
    return sum(arr)


def parsePrice(price, percent):

    if percent:
        rounder = 2
    else:
        rounder = 4

    if price == 0:
        return 0
    elif price > 1000000:
        return int(price)
    elif price > 1:
        return my_round(price, 2)
    else:
        m = -math.floor(math.log(abs(price)) / math.log(10) + 1)
        return my_round(price, m + rounder)


def logWithBase(y, x):
    return math.log(y) / math.log(x)
