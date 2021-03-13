#!/usr/bin/python3
import requests, time
print("time:", time.strftime("%Y%m%d %H%M%S"))
from decimal import Decimal
pricedata = {i["symbol"]:Decimal(i["price"]) for i in requests.get("https://api.binance.com/api/v3/ticker/price").json()}
from config import WATCHER_UP, WATCHER_DOWN, send

for flag, data in {1:WATCHER_UP, -1:WATCHER_DOWN}.items():
    for coin,price,note in data:
        nowprice = pricedata[coin.upper()+"USDT"]
        diff = flag*(price-nowprice)/nowprice
        print(coin, str(nowprice).rstrip("0"), price, "%.2f%%"%(diff*100), note, sep="\t")
        if diff<0.1:
            send(coin+" "+note+" 爆仓预警", str(nowprice).rstrip("0")+"->"+str(price)+" "+"%.2f%%"%(diff*100))


