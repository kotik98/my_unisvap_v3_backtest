# Uniswap V3 LP Strategy BackTester

Strategy Backtester for providing liquidity to a Uniswap V3 Pool. Inspired by:
[Historical Performances of Uniswap V3 Pools](https://defi-lab.medium.com/historical-performances-of-uniswap-l3-pools-2de713f7c70f)

## Usage

Inside "main" area in strategy_backtest.py file

```python
# put 1000$ for last 25 days from 2120.09 to 2662.99 price limits in ETH / USD 0.05% pool
uniswapStrategyBacktest("0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", 1000, 2120.09, 2662.99, days=25, period="daily")

# get results from start timestamp for lp from quote token 
uniswapStrategyBacktest("0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", 1, 1 / 2662.99, 1 / 2120.09,
                        startTimestamp=1653364800, period="daily", priceToken=1)

# get results from start timestamp to end timestamp for lp from quote token 
uniswapStrategyBacktest("0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", 1, 1 / 2662.99, 1 / 2120.09,
                              startTimestamp=1653364800, endTimestamp=1653374800, period="daily", priceToken=1)

# get results for n days before end timestamp for lp from quote token 
uniswapStrategyBacktest("0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", 1, 1 / 2662.99, 1 / 2120.09,
                              endTimestamp=1653364800, days=1, period="daily", priceToken=1)
```

## **uniswapStrategyBacktest() input**

uniswapStrategyBacktest() should be called with the following arguments:

```
uniswapStrategyBacktest(    
  poolID,    
  investmentAmount,    
  minRange,    
  maxRange,    
  endTimestamp,
  days,
  protocol,
  priceToken,
  period
)
```

**poolID** = the ID of the pool you'd like to run the backtest for. Example
for [ETH / USD 0.05%](https://info.uniswap.org/#/pools/0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640) would be "
0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"

**investmentAmount** = the initial amount invested in the LP strategy. This value is presumed to be denominated in the
base token of the pair (Token0) but can be overridden to use the quote token with the options argument.

**minRange** = the lower bound of the LP Strategy. As with investmentAmount, presumed to be in base but can be
overridden to use quote.

**maxRange** = the upper bound of the LP Strategy. As with investmentAmount, presumed to be in base but can be
overridden to use quote.

**days**= number of days to run the backtest from todays date. Defaults to 30, Currently maxed to 30. Optional. 

**startTimestamp** = timestamp in seconds for LP start. Optional.     

**endTimestamp** = timestamp in seconds for LP end. Optional. If used with *days* provides results for `n` days before
timestamp. Optional.

**priceToken** = 0: values in baseToken, 1: values in quoteToken (Token0, Token1). Default is 0. Optional.

**period** = Calculate fees "daily" or "hourly", defaults to "hourly". Optional.

**protocol**: Optional. Which chain, sidechain or L2 to use:  
0 = Ethereum (default)    
1 = Optimism    
2 = Arbitrum   
3 = Polygon

## **uniswapStrategyBacktest() output**

**amountV** = the total value of the LP position for the specified period.    
**feeV** = the fees generated for the specified period.    
**activeliquidity** = the % of the strategies liquidity that was active within the specified period.    
**feeUSD** = the total fees in USD   

## **Check out our new strategies in strategy_backtest.py !**
  



