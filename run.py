COINLIST=["EOS", "IOTA", "ZEC", "BSV", "BCH", "ONT", "NEO", "BTC", "LINK", "LTC", "XMR"]
import requests, os, sys, time, pickle, io
from decimal import Decimal
from functools import lru_cache
from dtb.config import WebhookConfig
from dtb import Bot

if os.environ.get("DINGTOKEN", False):
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
hasless30 = False #是否有上线少于30天的币种
increase = {} #30日涨幅

def get(url):
    return sess.get("https://futures.huobi.com/swap-order/x/v1/"+url, headers={"source":"web"}).json()["data"]

from datetime import datetime, timedelta
def d(ts):
    ts = int(ts)
    if len(str(ts))==13:
        ts = ts//1000
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
USDTPRICEDATA=[i for i in sess.get("https://www.huobi.com/-/x/general/exchange_rate/list").json()["data"] if i["name"]=="usdt_cny"][0]
USDTPRICE = "%.4f"%USDTPRICEDATA["rate"]
print("USD Time:", d(USDTPRICEDATA["data_time"]), "Price:", USDTPRICE)

@lru_cache()
def getdata(coin, page=1):
    global warns, status, PRICE
    page = str(page)
    if USECACHE and os.path.isfile("__pycache__/"+coin+page):
        res = pickle.load(open("__pycache__/"+coin+page, "rb"))
        if page=="1":
            PRICE[coin] = res[1][0]
        return res
    data = [Decimal(i['final_funding_rate']) for i in get("swap_funding_rate_page?contract_code="+coin+"-USD&page_index="+page+"&page_size=100")["settle_logs"]]
    settle = [Decimal(i["instrument_info"][0]["settle_price"]) for i in get("swap_delivery_detail?symbol="+coin+"&page_index="+page+"&page_size=100")["delivery"]]
    if page=="1":
        PRICE[coin] = settle[0]
    nextdata = get("swap_funding_rate?contract_code="+coin+"-USD")
    next1, next2 = Decimal(nextdata["final_funding_rate"]), Decimal(nextdata["funding_rate"])
    if sum(data[:3])<0:
        warns += 1
        status = "warning "+str(warns)
    res = [data, settle, next1, next2]
    if USECACHE:
        open("__pycache__/"+coin+page, "wb").write(pickle.dumps(res))
    return res

def calcprofit(coin, days, yearly=True, returndata=False):
    global hasless30
    fulldata, fullsettle, next1, next2 = getdata(coin)
    data, settle = fulldata[:days*3], fullsettle[:days*3]
    if days==30: #使用30天开始和结束的结算价格计算涨幅
        increase[coin] = (settle[0]/settle[-1]-1)*100
    profit_coin = sum([k/settle[i] for i,k in enumerate(data)]) #1美元在结算中能挣到多少币
    profit_usd = profit_coin*settle[0] #按最近一次结算价格 这些挣到的币现在值多少USD
    #print(coin, "profit_usd:", profit_usd)
    
    suffix = ""
    if len(data)<days*3:
        suffix = " *"
        hasless30 = True
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

def number2chinese(d):
    n = str(d)
    digits = len(n)
    if digits<=3: #123 -> "123"
        return str(n)
    elif digits<=8: #1234 -> "0.123万"
        return "%.2f"%(d/10000)+"万"
    else:
        return "%.2f"%(d/100000000)+"亿"

if __name__ == "__main__":
    from pprint import pprint
    import threading
    threads = []
    for coin in COINLIST:
        t = threading.Thread(target=getdata, args=[coin])
        t.start()
        threads.append(t)
    [t.join() for t in threads]
    text = "USDT: "+USDTPRICE+"\n币种| 昨日 | 预测 |7日年化\n"
    t = []
    for coin in COINLIST:
        t.append([" | ".join(
            [
                coin+(" " if len(coin)==3 else ""),
                calcprofit(coin,1, yearly=False),
                "%.2f‰"%((getdata(coin)[2]+getdata(coin)[3])*1000),
                calcprofit(coin,7),
            ]), 
            calcprofit(coin,1, yearly=False, returndata=True),
        ])
    t.sort(key=lambda i:i[1])
    text += "\n".join([i[0] for i in t])
    text = text.replace("\n","\n\n")
    print(text.replace("\n\n","\n").strip())
    title = "[套利收益率] "+status
    if os.environ.get("DINGTOKEN", False):
        b.markdown(title,text)
    
    t = []
    print(PRICE)
    swap_index = get("swap_index")
    ALLCOINS = [i["contract_code"].replace("-USD","") for i in swap_index if i["contract_code"].endswith("-USD")]
    print(ALLCOINS)
    pprint(swap_index)
    threads = []
    for coin in ALLCOINS:
        th = threading.Thread(target=getdata, args=[coin])
        th.start()
        threads.append(th)
    [th.join() for t in threads]
    
    swap_open_interest = {i["symbol"]:int(i["volume"]) for i in get("swap_open_interest")}
    
    for coin in ALLCOINS:
        try:
            t.append([
                coin+(" " if len(coin)==3 else ""), 
                "%.2f‰"%((getdata(coin)[2]+getdata(coin)[3])*1000), 
                calcprofit(coin,1, yearly=False), 
                calcprofit(coin,7), 
                calcprofit(coin,30), 
                "%.2f%%"%increase[coin],
                str(round(PRICE[coin],6)).rstrip("0"), 
                number2chinese(swap_open_interest[coin]*(10 if coin!="BTC" else 100)),
                getdata(coin)[2]+getdata(coin)[3], #预测收益 用于默认排序
            ])
        except:
            print("error:", coin)
            pass
    t.sort(key=lambda i:i[-1], reverse=True)
    html = """<!doctype html><meta charset="utf-8">\n当前USDT价格：%s 数据更新时间：%s <a onclick="loadbtctable()" oncontextmenu="triggerrefresh();return false">触发更新</a><br>
<table style="line-height: 0.5;"><thead>\n<tr><th class="headcol">币种</th><th>预测收益</th><th>昨日收益</th><th>7日年化</th><th>30日年化</th><th>30日涨幅</th><th>结算价格</th><th>持仓量USD</th></tr></thead>
<tbody id="realtimeprofittbody">\n"""%(USDTPRICE,time.strftime("%Y-%m-%d %H:%M:%S"))
    for data in t:
        html += "<tr><td class='headcol'>" + "</td><td>".join(data[:-1]) + "</td></tr>\n"
    html += """</tbody></table>"""
    if hasless30:
        html += "<blockquote>* 这些币种上线不足30日</blockquote>"
    print(html)
    html+= """<script>function triggerrefresh(){location.href="https://blog.chenyuan.me/Bitcoin/?refresh#_3"}</script>"""
    if os.environ.get("UPYUN_POLICY", False):
        x = sess.post("https://v0.api.upyun.com/py3iodownload", files={"file": io.BytesIO(html.encode("utf-8")), "policy":os.environ["UPYUN_POLICY"], "signature":os.environ["UPYUN_SIGN"]})
        print(x.text)