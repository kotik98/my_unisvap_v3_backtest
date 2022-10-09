import requests
import pandas as pd
import time

now = int(time.time())


def DateByDaysAgo(days, endDate=now):
    return endDate - days * 86400


def urlForProtocol(protocol):
    if protocol == 1:
        return "https://api.thegraph.com/subgraphs/name/ianlapham/optimism-post-regenesis"
    elif protocol == 2:
        return "https://api.thegraph.com/subgraphs/name/ianlapham/arbitrum-minimal"
    elif protocol == 3:
        return "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-polygon"
    elif protocol == 4:
        return "https://api.thegraph.com/subgraphs/name/perpetual-protocol/perpetual-v2-optimism"
    return "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"


def getPoolHourData(pool, from_date, to_date, protocol=0):
    try:
        res = []
        url = urlForProtocol(protocol)
        while True:
            query = '''
                  query PoolHourDatas {
                poolHourDatas ( where:{ pool: "%s" periodStartUnix_gte:%i periodStartUnix_lte:%i close_gt: 0}, orderBy:periodStartUnix, orderDirection:asc, first:1000) {
                    periodStartUnix
                    liquidity
                    high
                    low
                    pool {
                      id
                      totalValueLockedUSD
                      totalValueLockedToken1
                      totalValueLockedToken0
                      token0
                        {decimals}
                      token1
                        {decimals}
                    }
                    close
                    feeGrowthGlobal0X128
                    feeGrowthGlobal1X128
                    }
                }
                ''' % (pool, from_date, to_date)
            request = requests.post(url, json={'query': query})
            data = request.json()
            from_date = data["data"]["poolHourDatas"][len(data["data"]["poolHourDatas"]) - 1]["periodStartUnix"] + 1
            res.extend(data["data"]["poolHourDatas"])
            if len(data["data"]["poolHourDatas"]) < 1000:
                break
        return pd.DataFrame(res)

    except Exception as e:
        print(e)
        return


def csv_data_saver(pool, days, end_timestamp=now, protocol=0):
    from_date = DateByDaysAgo(days, end_timestamp)
    data = pd.DataFrame(getPoolHourData(pool, from_date, end_timestamp, protocol))
    data.to_csv("data/pool_hour_data.csv")


def process_historical_data(path):
    decimals0 = 18
    decimals1 = 6
    data = pd.read_csv(path)
    data.insert(0, 'close', [
            int(data['sqrtPriceX96'].values[i]) * int(data['sqrtPriceX96'].values[i]) * (10 ** decimals0) / (
            10 ** decimals1) / 2 ** 192 for i in range(len(data))])
    data.insert(0, 'high', data['close'])
    data.insert(0, 'low', data['close'])
    data.insert(0, 'periodStartUnix', [int(data['UnixTime'].values[i]) // 1000 for i in range(len(data))])
    data.insert(0, 'pool', [{'totalValueLockedToken0': int(data['balanceToken0'].values[i]) / (10 ** decimals0),
                             'totalValueLockedToken1': int(data['balanceToken1'].values[i]) / (10 ** decimals1),
                             'totalValueLockedUSD': (int(data['balanceToken0'].values[i]) / (10 ** decimals0) * (
                                     int(data['sqrtPriceX96'].values[i]) * int(data['sqrtPriceX96'].values[i]) * (
                                     10 ** decimals0) / (
                                             10 ** decimals1) / 2 ** 192)) + int(data['balanceToken1'].values[
                                                                                     i]) / (10 ** decimals1)} for i in
                            range(len(data))])
    data.to_csv('data/history_data.csv')
    return data.iloc[-1]


def get_historical_data_from_csv(startTimestamp, endTimestamp):
    data = pd.read_csv("data/history_data.csv")
    start = False
    for i in range(len(data)):
        if int(data["periodStartUnix"].values[i]) > startTimestamp and not start:
            start = True
            low_index = i
        if abs(endTimestamp - int(data["periodStartUnix"].values[i])) < 15:
            high_index = i
    return data[low_index:high_index]


def get_pool_hour_data_from_csv(startTimestamp, endTimestamp):
    data = pd.read_csv("data/pool_hour_data.csv")
    for i in range(len(data)):
        if data["periodStartUnix"].values[i] == startTimestamp:
            low_index = i
        if abs(endTimestamp - data["periodStartUnix"].values[i]) < 3600:  # округление до ближайшего часа
            high_index = i
    return data[low_index:high_index]


def poolById(pool, protocol=0):
    try:
        query = '''
            query Pools { id: pools(where: { id: "%s" } orderBy:totalValueLockedETH, orderDirection:desc)
            {
              id
              feeTier
              totalValueLockedUSD
              totalValueLockedETH
              token0Price
              token1Price  
              token0 {
                id
                symbol
                name
                decimals
              }
              token1 {
                id
                symbol
                name
                decimals
              }
              poolDayData(orderBy: date, orderDirection:desc,first:1)
              {
                date
                volumeUSD
                tvlUSD
                feesUSD
                liquidity
                high
                low
                volumeToken0
                volumeToken1
                close
                open
              }
            }
            }
        ''' % pool

        url = urlForProtocol(protocol)

        request = requests.post(url, json={'query': query})
        data = request.json()

        if data["data"]["id"]:
            return data["data"]["id"]
        else:
            print("nothing returned from poolById")
            return None

    except Exception as e:
        print(e)
        return


if __name__ == "__main__":
    pool_id = "0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36".lower()
    from_date = 1651611600
    to_date = 1654290000
    # csv_data_saver("0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36".lower(), from_date, to_date)
    print(process_historical_data('data/history_data.csv'))
