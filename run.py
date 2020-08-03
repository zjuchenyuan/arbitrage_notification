COINLIST=["EOS", "IOTA", "ZEC", "BSV", "BCH", "ONT", "NEO", "BTC", "LINK", "LTC", "XMR"]
import requests, os, sys, time
from decimal import Decimal
from functools import lru_cache
from dtb.config import WebhookConfig
from dtb import Bot

if not os.environ.get("NODING", False):
    b=Bot(WebhookConfig("https://oapi.dingtalk.com/robot/send?access_token="+os.environ["DINGTOKEN"]))
sess = requests.session()

status = "ok"
warns = 0

@lru_cache()
def getdata(coin, page=1):
    global warns, status
    page = str(page)
    data = [Decimal(i['final_funding_rate']) for i in sess.get("https://futures.huobi.com/swap-order/x/v1/swap_funding_rate_page?contract_code="+coin+"-USD&page_index="+page+"&page_size=100", headers={"source":"web"}).json()["data"]["settle_logs"]]
    settle = [Decimal(i["instrument_info"][0]["settle_price"]) for i in sess.get("https://futures.huobi.com/swap-order/x/v1/swap_delivery_detail?symbol="+coin+"&page_index="+page+"&page_size=100", headers={"source":"web"}).json()["data"]["delivery"]]
    if sum(data[:3])<0:
        warns += 1
        status = "warning "+str(warns)
    return data, settle

def calcprofit(coin, days, yearly=True, returndata=False):
    fulldata, fullsettle = getdata(coin)
    data, settle = fulldata[:days*3], fullsettle[:days*3]
    profit_coin = sum([k/settle[i] for i,k in enumerate(data)]) #1美元在结算中能挣到多少币
    profit_usd = profit_coin*settle[0] #按最近一次结算价格 这些挣到的币现在值多少USD
    #print(coin, "profit_usd:", profit_usd)
    
    suffix = ""
    if len(data)<days*3:
        suffix = " *"
    if not yearly:
        if returndata:
            return profit_usd
        return "%.2f"%(profit_usd*100)+ "%"
    #return "%.2f"%(sum(data)/len(data)*3*365*100) + "%"+suffix
    return "%6.2f"%(profit_usd/len(data)*3*365*100) + "%"+suffix

def calc_fullprofit(coin):
    data, settle = [], []
    page = 1
    x = getdata(coin)
    while len(x[0]):
        data.extend(x[0])
        settle.extend(x[1])
        page+=1
        x = getdata(coin, page)
    profit_coin = sum([k/settle[i] for i,k in enumerate(data)])
    profit_usd = profit_coin*settle[0]
    return "%.2f"%(profit_usd/len(data)*3*365*100) + "%", len(data)

if __name__ == "__main__":
    #main()
    if 0:
        data=[]
        for i in "BTC ETH EOS LINK BCH BSV LTC XRP ETC TRX ADA ATOM IOTA NEO ONT XLM XMR DASH ZEC".split(" "):
            profit, length = calc_fullprofit(i)
            data.append([i, profit, length])
        data.sort(key=lambda i:i[1], reverse=True)
        for i,profit,length in data:
            print("",i, profit, length,"", sep="|")
        exit()
    from pprint import pprint
    text = "|币种|昨日 |7日年化|月年化|\n"
    t = []
    for coin in COINLIST:
        t.append(["|".join(
            [
                "",
                coin+(" " if len(coin)==3 else ""),
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
    print(text.replace("\n\n","\n").strip())
    title = "[套利收益率] "+status
    if not os.environ.get("NODING", False):
        b.markdown(title,text)