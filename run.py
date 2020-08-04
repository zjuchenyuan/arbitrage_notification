COINLIST=["EOS", "IOTA", "ZEC", "BSV", "BCH", "ONT", "NEO", "BTC", "LINK", "LTC", "XMR"]
ALLCOINS="BTC ETH EOS LINK BCH BSV LTC XRP ETC TRX ADA ATOM IOTA NEO ONT XLM XMR DASH ZEC XTZ".split(" ")
import requests, os, sys, time, pickle, io
from decimal import Decimal
from functools import lru_cache
from dtb.config import WebhookConfig
from dtb import Bot

if not os.environ.get("NODING", False):
    b=Bot(WebhookConfig("https://oapi.dingtalk.com/robot/send?access_token="+os.environ["DINGTOKEN"]))
sess = requests.session()

status = "ok"
warns = 0
USECACHE=os.environ.get("CACHE", False)
os.environ['TZ'] = "UTC-8"
try:
    time.tzset()
except:
    pass

PRICE={} #最近一次结算的USD计价价格

@lru_cache()
def getdata(coin, page=1):
    global warns, status, PRICE
    page = str(page)
    if USECACHE and os.path.isfile("__pycache__/"+coin+page):
        res = pickle.load(open("__pycache__/"+coin+page, "rb"))
        if page=="1":
            PRICE[coin] = res[1][0]
        return res
    data = [Decimal(i['final_funding_rate']) for i in sess.get("https://futures.huobi.com/swap-order/x/v1/swap_funding_rate_page?contract_code="+coin+"-USD&page_index="+page+"&page_size=100", headers={"source":"web"}).json()["data"]["settle_logs"]]
    settle = [Decimal(i["instrument_info"][0]["settle_price"]) for i in sess.get("https://futures.huobi.com/swap-order/x/v1/swap_delivery_detail?symbol="+coin+"&page_index="+page+"&page_size=100", headers={"source":"web"}).json()["data"]["delivery"]]
    if page=="1":
        PRICE[coin] = settle[0]
    nextdata = sess.get("https://futures.huobi.com/swap-order/x/v1/swap_funding_rate?contract_code="+coin+"-USD", headers={"source":"web"}).json()["data"]
    next1, next2 = Decimal(nextdata["final_funding_rate"]), Decimal(nextdata["funding_rate"])
    if sum(data[:3])<0:
        warns += 1
        status = "warning "+str(warns)
    res = [data, settle, next1, next2]
    if USECACHE:
        open("__pycache__/"+coin+page, "wb").write(pickle.dumps(res))
    return res

def calcprofit(coin, days, yearly=True, returndata=False):
    fulldata, fullsettle, next1, next2 = getdata(coin)
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
        return "%.2f‰"%(profit_usd*1000)
    #return "%.2f"%(sum(data)/len(data)*3*365*100) + "%"+suffix
    return "%6.2f"%(profit_usd/len(data)*3*365*100) + "%"+suffix

def getfulldata(coin):
    data, settle = [], []
    page = 1
    x = getdata(coin)
    while len(x[0]):
        data.extend(x[0])
        settle.extend(x[1])
        page+=1
        x = getdata(coin, page)
    return data, settle
    
def calc_fullprofit(coin):
    data, settle = getfulldata(coin)
    profit_coin = sum([k/settle[i] for i,k in enumerate(data)])
    profit_usd = profit_coin*settle[0]
    return "%.2f"%(profit_usd/len(data)*3*365*100) + "%", len(data)

def calc_fullprofit_curve(coin):
    data, settle = getfulldata(coin)
    data, settle = data[::-1], settle[::-1] #本来是逆序现在改成顺序 从第一次结算净值为1开始计算
    curve = []
    for i, item in enumerate(data):
        profit_coin = sum([k/settle[j] for j,k in enumerate(data[:i+1])])
        profit_usd = profit_coin*settle[i]
        curve.append(profit_usd)
    return curve

if __name__ == "__main__":
    #main()
    if 0:
        data=[]
        for i in ALLCOINS:
            profit, length = calc_fullprofit(i)
            data.append([i, profit, length])
        data.sort(key=lambda i:i[1], reverse=True)
        for i,profit,length in data:
            print("",i, profit, length,"", sep="|")
        exit()
    from pprint import pprint
    text = "币种| 预测 | 昨日 |7日年化\n"
    t = []
    for coin in COINLIST:
        t.append([" | ".join(
            [
                coin+(" " if len(coin)==3 else ""),
                "%.2f‰"%((getdata(coin)[2]+getdata(coin)[3])*1000),
                calcprofit(coin,1, yearly=False),
                calcprofit(coin,7),
            ]), 
            calcprofit(coin,1, yearly=False, returndata=True),
        ])
    t.sort(key=lambda i:i[1])
    text += "\n".join([i[0] for i in t])
    text = text.replace("\n","\n\n")
    print(text.replace("\n\n","\n").strip())
    title = "[套利收益率] "+status
    if not os.environ.get("NODING", False):
        b.markdown(title,text)
    
    t = []
    print(PRICE)
    for coin in ALLCOINS:
        t.append([coin+(" " if len(coin)==3 else ""), "%.2f‰"%((getdata(coin)[2]+getdata(coin)[3])*1000), calcprofit(coin,1, yearly=False), calcprofit(coin,7), calcprofit(coin,30), str(round(PRICE[coin],6)).rstrip("0"), getdata(coin)[2]+getdata(coin)[3]])
    t.sort(key=lambda i:i[-1])
    html = """<!doctype html><meta charset="utf-8">\n数据更新时间：%s<br>\n<table><thead>\n<tr><th>币种</th><th>预测收益</th><th>昨日收益</th><th>7日年化</th><th>30日年化</th><th>最近结算价格USD</th></tr></thead><tbody>\n"""%(time.strftime("%Y-%m-%d %H:%M:%S"))
    for data in t:
        html += "<tr><td>" + "</td><td>".join(data[:-1]) + "</td></tr>\n"
    html += "</tbody></table><blockquote>* 这些币种上线不足30日</blockquote>"
    print(html)
    x = sess.post("https://v0.api.upyun.com/py3iodownload", files={"file": io.BytesIO(html.encode("utf-8")), "policy":os.environ["UPYUN_POLICY"], "signature":os.environ["UPYUN_SIGN"]})
    print(x.text)