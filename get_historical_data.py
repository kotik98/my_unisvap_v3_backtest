import requests

pool_id = "0x4e68Ccd3E89f51C3074ca5072bbAC773960dFa36".lower()
from_date = 1656612000
to_date = 1625202000


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
        return res

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
    data = getPoolHourData(pool_id, from_date, to_date)
    print(data)
