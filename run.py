COINLIST=["EOS", "IOTA", "ZEC", "BSV", "BCH"]
import requests, os, sys, time
from decimal import Decimal
from functools import lru_cache
from dtb.config import WebhookConfig
from dtb import Bot

b=Bot(WebhookConfig("https://oapi.dingtalk.com/robot/send?access_token="+os.environ["DINGTOKEN"]))
sess = requests.session()

status = "ok"
warns = 0

@lru_cache()
def getdata(coin):
    data = [Decimal(i['final_funding_rate']) for i in sess.get("https://futures.huobi.com/swap-order/x/v1/swap_funding_rate_page?contract_code="+coin+"-USD&page_index=0&page_size=100", headers={"source":"web"}).json()["data"]["settle_logs"]]
    if sum(data[:3])<0:
        warns += 1
        status = "warning "+str(warns)
    return data

def calcprofit(coin, days, yearly=True, returndata=False):
    fulldata = getdata(coin)
    data = fulldata[:days*3]
    suffix = ""
    if len(data)<days*3:
        suffix = " *"
    if not yearly:
        if returndata:
            return sum(data)
        return "%.2f"%(sum(data)*100)+ "%"
    return "%.2f"%(sum(data)/len(data)*3*365*100) + "%"+suffix

if __name__ == "__main__":
    #main()
    from pprint import pprint
    text = "|币种|昨日收益率|七日年化|月年化|\n"
    t = []
    for coin in COINLIST:
        t.append(["|".join(
            [
                "",
                coin+("　" if len(coin)==3 else ""),
                calcprofit(coin,1, yearly=False),
                calcprofit(coin,7),
                calcprofit(coin,30),
                ""
            ]), 
            calcprofit(coin,1, yearly=False, returndata=True),
        ])
    t.sort(key=lambda i:i[1])
    text += "\n".join([i[0] for i in t])
    text = text.replace("|"," | ").replace("----","").replace(" \n ","\n\n")
    print(text.replace("\n\n","\n"))
    title = "[套利收益率] "+status
    b.markdown(title,text)