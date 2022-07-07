import csv
from binance.client import Client

symbol = 'ETHUSDT'
interval = "1h"
date_from = "1 Jul 2020"
date_to = "1 Jul 2022"
client = Client()

columns = [
    'open_time', 'open', 'high', 'low', 'close', 'volume',
    'close_time', 'quote_asset_volume', 'number_of_trades',
    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume',
    'ignore'
]

klines = client.get_historical_klines(symbol, interval, date_from, date_to)

with open('data/{} {} klines from {} to {}.csv'.format(symbol, interval, date_from, date_to), 'w') as f:
    write = csv.writer(f)
    write.writerow(columns)
    write.writerows(klines)
