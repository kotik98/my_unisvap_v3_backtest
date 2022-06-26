import requests

pool_id = "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8"
from_date = 1643155200
to_date = 1645833600


def urlForProtocol(protocol=0):
    if protocol == 1:
        return "https://api.thegraph.com/subgraphs/name/ianlapham/optimism-post-regenesis"
    elif protocol == 2:
        return "https://api.thegraph.com/subgraphs/name/ianlapham/arbitrum-minimal"
    elif protocol == 3:
        return "https://api.thegraph.com/subgraphs/name/ianlapham/uniswap-v3-polygon"
    elif protocol == 4:
        return "https://api.thegraph.com/subgraphs/name/perpetual-protocol/perpetual-v2-optimism"
    return "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"


def getPoolHourData(pool, from_date, to_date, protocol=0, skip=0):
    try:
        query = '''
          query PoolHourDatas {
        poolHourDatas ( where:{ pool: "%s" periodStartUnix_gte:%i periodStartUnix_lte:%i close_gt: 0}, orderBy:periodStartUnix, orderDirection:asc, first:1000, skip: %i) {
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
        ''' % (pool, from_date, to_date, skip)

        url = urlForProtocol(protocol)

        request = requests.post(url, json={'query': query})
        data = request.json()

        if data["data"]["poolHourDatas"]:
            return data["data"]["poolHourDatas"]
        else:
            print("nothing returned from getPoolHourData")
            return None

    except Exception as e:
        print(e)
        return


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
    print(poolById(pool_id))
