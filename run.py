COINLIST=set(['DOT','BTM','IOST','KSM','ZEC','BCH','QTUM','STORJ','ONT','ETC','LTC','bETH','bTRX','bDOT','bETC','oONT','oIOST','oDOT','LTC', 'oETH', 'oATOM', 'oDASH', 'oDOT', 'oIOST', 'bLTC', 'bDOT', 'bETH'])
import requests, os, sys, time, pickle, io, traceback, random
from time import sleep
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

def get(url, BASE="https://futures.huobi.com/swap-order/x/v1/", retry=3):
    try:
        x = sess.get(BASE+url, headers={"source":"web"}, timeout=5)
        return x.json()["data"]
    except:
        print(x.text, x, "retry:", retry)
        if retry:
            sleep(random.randint(5,10))
            return get(url, BASE=BASE, retry=retry-1)

def linear_get(url):
    return get(url, BASE="https://futures.hbg.com/linear-swap-order/x/v1/")

from datetime import datetime, timedelta
def d(ts):
    ts = int(ts)
    if len(str(ts))==13:
        ts = ts//1000
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

USDTPRICEDATA=[i for i in sess.get("https://www.huobi.com/-/x/general/exchange_rate/list").json()["data"] if i["name"]=="usdt_cny"][0]
USDTPRICE = "%.4f"%USDTPRICEDATA["rate"]
print("USD Time:", d(USDTPRICEDATA["data_time"]), "Price:", USDTPRICE)

@lru_cache(1000)
def getdata(coin, page=1):
    global warns, status, PRICE
    if coin[0]=="u":
        return linear_getdata(coin[1:], page)
    elif coin[0]=="b":
        return binance_getdata(coin[1:])
    elif coin[0]=="o":
        return okex_getdata(coin[1:])
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

@lru_cache()
def linear_getdata(coin, page=1):
    global warns, status, PRICE
    page = str(page)
    if USECACHE and os.path.isfile("__pycache__/linear_"+coin+page):
        res = pickle.load(open("__pycache__/linear_"+coin+page, "rb"))
        if page=="1":
            PRICE["u"+coin] = res[1][0]
        return res
    data = [Decimal(i['final_funding_rate']) for i in linear_get("linear_swap_funding_rate_page?contract_code="+coin+"-USDT&page_index="+page+"&page_size=100")["settle_logs"]]
    settle = [Decimal(i["instrument_info"][0]["settle_price"]) for i in linear_get("linear_swap_delivery_detail?contract_code="+coin+"-USDT&page_index="+page+"&page_size=100")["delivery"]]
    if page=="1":
        PRICE["u"+coin] = settle[0]
    nextdata = linear_get("linear_swap_funding_rate?contract_code="+coin+"-USDT")
    next1, next2 = Decimal(nextdata["final_funding_rate"]), Decimal(nextdata["funding_rate"])
    if sum(data[:3])<0:
        warns += 1
        status = "warning "+str(warns)
    res = [data, settle, next1, next2]
    if USECACHE:
        open("__pycache__/linear_"+coin+page, "wb").write(pickle.dumps(res))
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

@lru_cache()
def binance_premiumIndex():
    # 币安当前的币本位合约预测资金费率和详情
    # 注意币安下一次的资金费率不像火币（本次+预测）一样固定 而是到结算时才能确定（本次就是预测）
    # {"BTCUSD": [Decimal(""), detail]}
    # 其中detail为原始数据：{"symbol":"BTCUSD_PERP","pair":"BTCUSD","markPrice":"18818.14711725","indexPrice":"18816.79090909","estimatedSettlePrice":"18838.22532679","lastFundingRate":"0.00010000","interestRate":"0.00010000","nextFundingTime":1606896000000,"time":1606874737000}
    global PRICE
    data = sess.get("https://dapi.binance.com/dapi/v1/premiumIndex").json()
    data = [i for i in data if i["symbol"].endswith("_PERP")]
    for i in data:
        PRICE["b"+i["pair"].replace("USD","")] = Decimal(i["markPrice"])
    return {i["pair"]: [Decimal(i["lastFundingRate"]),i] for i in data}

def binance_fundingRate(pair):
    # 币安资金费率历史
    # 注意api调用是按时间asc的， 我们需要desc的数据
    # 没有结算价格数据
    # 返回 [(时间戳, 资金费率)]
    data = sess.get("https://dapi.binance.com/dapi/v1/fundingRate?symbol="+pair+"_PERP&limit=1000").json()
    return [(i["fundingTime"]//1000, Decimal(i["fundingRate"])) for i in data][::-1]

def binance_markPriceKlines(pair):
    # 币安标记价格K线4小时数据，返回{时间戳: 当时开盘价格}
    data = sess.get("https://dapi.binance.com/dapi/v1/markPriceKlines?symbol="+pair+"_PERP&interval=4h&limit=1500").json()
    #data = [i for i in data if i[0]%28800==0]
    #return [Decimal(i[1]) for i in data][::-1]
    return {i[0]//1000: Decimal(i[1]) for i in data}

@lru_cache()
def binance_openInterest(pair):
    data = sess.get("https://dapi.binance.com/dapi/v1/openInterest?symbol="+pair+"_PERP").json()
    return int(data["openInterest"])

def binance_getdata(coin):
    # 返回 [资金费率历史列表, 资金费率收取是的价格列表, 本次预测, 下一次0]
    pair = coin+"USD"
    binance_openInterest(pair)
    frhistory = binance_fundingRate(pair)
    klines = binance_markPriceKlines(pair)
    next1 = binance_premiumIndex()[pair][0]
    next2 = 0
    
    data = []
    settle = []
    for ts, fr in frhistory:
        if ts not in klines:
            continue
        data.append(fr)
        settle.append(klines[ts])
    return [data, settle, next1, next2]

def okex_get(url):
    return sess.get("https://www.okex.com/api/swap/v3/"+url).json()

def okex_instruments():
    return okex_get("instruments")

def okex_historical_funding_rate(coin):
    data = okex_get("instruments/"+coin+"-USD-SWAP/historical_funding_rate")
    return [(i['funding_time'], Decimal(i["realized_rate"])) for i in data]

def okex_history_candles(coin):
    data = sess.get("https://www.okex.com/v2/perpetual/pc/public/instruments/"+coin+"-USD-SWAP/candles?granularity=14400&size=1000").json()["data"]
    #print(data)
    return {i[0]:Decimal(i[1]) for i in data}

def okex_funding_time(coin):
    return okex_get("instruments/"+coin+"-USD-SWAP/funding_time")

@lru_cache()
def okex_open_interest(coin):
    data = okex_get("instruments/"+coin+"-USD-SWAP/open_interest")
    return int(data["amount"])

def okex_getdata(coin):
    okex_open_interest(coin)
    frhistory = okex_historical_funding_rate(coin)
    klines = okex_history_candles(coin)
    ft = okex_funding_time(coin)
    next1 = Decimal(ft["funding_rate"])
    next2 = Decimal(ft["estimated_rate"])
    
    data = []
    settle = []
    for ts, fr in frhistory:
        if ts not in klines:
            continue
        data.append(fr)
        settle.append(klines[ts])
    PRICE["o"+coin] = settle[0]
    return [data, settle, next1, next2]

if __name__ == "__main__":
    from pprint import pprint
    import threading
    threads = []
    for idx, coin in enumerate(COINLIST):
        t = threading.Thread(target=getdata, args=[coin])
        t.start()
        threads.append(t)
    [t.join() for t in threads]
    text = "USDT: "+USDTPRICE+"\n币种| 昨日 | 预测 |7日年化\n"
    t = []
    for coin in COINLIST:
      try:
        t.append([" | ".join(
            [
                coin+(" " if len(coin)==3 else ""),
                calcprofit(coin,1, yearly=False),
                "%.2f‰"%((getdata(coin)[2]+getdata(coin)[3])*1000),
                calcprofit(coin,7),
            ]), 
            calcprofit(coin,1, yearly=False, returndata=True),
        ])
      except Exception as e:
        print("error:", coin, e)
        continue
    t.sort(key=lambda i:i[1])
    text += "\n".join([i[0] for i in t])
    text = text.replace("\n","\n\n")
    print(text.replace("\n\n","\n").strip())
    title = "[套利收益率] "+status
    if os.environ.get("DINGTOKEN", False):
        b.markdown(title,text)
    
    t = []
    #print(PRICE)
    
    try:
        swap_index = get("swap_index")
        ALLCOINS = [i["contract_code"].replace("-USD","") for i in swap_index if i["contract_code"].endswith("-USD")]
    except:
        ALLCOINS = []
    
    try:
        linear_swap_index = linear_get("linear_swap_index")
        linear_ALLCOINS = ["u"+i["contract_code"].replace("-USDT","") for i in linear_swap_index if i["contract_code"].endswith("-USDT")]
    except:
        linear_ALLCOINS = []
    
    bCOINS = ["b"+i.replace("USD","") for i in binance_premiumIndex().keys()]
    oCOINS = ["o"+i["instrument_id"].split("-")[0] for i in okex_instruments() if i["instrument_id"].endswith("-USD-SWAP")]
    
    coin_series = ALLCOINS+linear_ALLCOINS+bCOINS+oCOINS
    random.shuffle(coin_series)
    #print(coin_series)
    #pprint(swap_index)
    #pprint(linear_swap_index)
    threads = []
    for idx, coin in enumerate(coin_series):
        th = threading.Thread(target=getdata, args=[coin])
        th.start()
        if idx%30==0:
            #print("fetching", idx, coin)
            sleep(1)
        threads.append(th)
    [th.join() for th in threads]
    #print("th finished")
    
    swap_open_interest = {}
    try:
        swap_open_interest.update({i["symbol"]:int(i["volume"])*(10 if i["symbol"]!="BTC" else 100) for i in get("swap_open_interest")})
    except Exception as e:
        pass
    try:
        swap_open_interest.update({"u"+i["symbol"]:int(i['value']) for i in linear_get("linear_swap_open_interest")})
    except Exception as e:
        pass
    try:
        swap_open_interest.update({i:binance_openInterest(i[1:]+"USD")*(10 if i!="bBTC" else 100) for i in bCOINS})
    except Exception as e:
        pass
    try:
        swap_open_interest.update({i:okex_open_interest(i[1:])*(10 if i!="oBTC" else 100) for i in oCOINS})
    except Exception as e:
        pass
    #print("open_interest finished")

    for coin in coin_series:
        try:
            price = str(round(PRICE[coin],4)).rstrip("0")
            if int(price.split(".")[0])>10 and "." in price:
                price = price.split(".")[0]+"."+price.split(".")[1][:2]
            t.append([
                coin+(" " if len(coin)==3 else ""), 
                "%.2f‰"%(getdata(coin)[2]*1000), 
                "%.2f‰"%(getdata(coin)[3]*1000), 
                calcprofit(coin,1, yearly=False), 
                calcprofit(coin,7), 
                calcprofit(coin,30), 
                "%.2f%%"%increase[coin],
                price, 
                number2chinese(swap_open_interest[coin]),
                getdata(coin)[2]+getdata(coin)[3], #预测收益 用于默认排序
            ])
        except Exception as e:
            print("error:", coin, e)
            traceback.print_exc()
            pass
    t.sort(key=lambda i:i[-1], reverse=True)
    html = """<!doctype html><meta charset="utf-8">\n当前USDT价格：%s 数据更新时间：%s <a onclick="loadbtctable()" oncontextmenu="triggerrefresh();return false">触发更新</a><br>
<table style="line-height: 0.5;"><thead>\n<tr><th class="headcol">币种</th><th>本次收益</th><th>下次预测</th><th>昨日收益</th><th>7日年化</th><th>30日年化</th><th>30日涨幅</th><th>结算价格</th><th>持仓量USD</th></tr></thead>
<tbody id="realtimeprofittbody">\n"""%(USDTPRICE,time.strftime("%Y-%m-%d %H:%M:%S"))
    for data in t:
        html += "<tr><td class='headcol'>" + "</td><td>".join(data[:-1]) + "</td></tr>\n"
    html += """</tbody></table>"""
    if hasless30:
        html += "<blockquote>* 这些币种上线不足30日; u-USDT本位, b-币安币本位, o-OKex币本位</blockquote>"
    print(html)
    html+= """<script>function triggerrefresh(){location.href="https://blog.chenyuan.me/Bitcoin/?refresh#_3"}</script>"""
    if os.environ.get("UPYUN_POLICY", False):
        x = sess.post("https://v0.api.upyun.com/py3iodownload", files={"file": io.BytesIO(html.encode("utf-8")), "policy":os.environ["UPYUN_POLICY"], "signature":os.environ["UPYUN_SIGN"]})
        print(x.text)
