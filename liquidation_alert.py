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

import sys
sys.path.append("/home/api.chenyuan.me")
from qieman import *

ht_price, bag_price = graphql_token_price("0xa042fb0e60125a4022670014ac121931e7501af4", HECO_GRAPH)
ht_price, bags_price = graphql_token_price("0x6868d406a125eb30886a6dd6b651d81677d1f22c", HECO_GRAPH)
if bag_price<0.7 or bags_price<150:
    send("bag已经暴跌", "BAG %(bag_price).3f BAGS %(bags_price).2f"%(locals()))
if bag_price>1:
    send("已恢复bag", "BAG %(bag_price).3f BAGS %(bags_price).2f"%(locals()))
ht_price, mdx_price = graphql_token_price("0x25d2e80cb6b86881fd7e07dd263fb79f4abe033c", HECO_GRAPH)
if mdx_price < 2.21:
    send("mdx跌幅大于30%", "MDX %(mdx_price).3f"%(locals()))
