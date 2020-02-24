import requests
from bs4 import BeautifulSoup
import urllib.parse
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
from data import MARKET_NO_NAME,PRODUCT_NO_NAME
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


USER_AGENT = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}

def search(date,market_no=104,product_no="FV4"):
    """成功爬取回傳列表 否則字串"""

    print(date,product_no,market_no)
    
    url = "https://amis.afa.gov.tw/veg/VegProdDayTransInfo.aspx"
    
    values = {}
    values['__EVENTTARGET'] = "ctl00$contentPlaceHolder$btnQuery"
    values['__EVENTARGUMENT'] = ''
    values['ctl00$contentPlaceHolder$txtSTransDate'] = date
    values['ctl00$contentPlaceHolder$hfldMarketNo'] = market_no
    values['ctl00$contentPlaceHolder$ucDateScope$rblDateScope'] = 'D'
    values['ctl00$contentPlaceHolder$ucSolarLunar$radlSolarLunar']= "S"
    values['ctl00$contentPlaceHolder$hfldProductNo'] = product_no
    values['__VIEWSTATE'],values['__EVENTVALIDATION'] = get_viewstate_and_event()
    
    data = urllib.parse.urlencode(values).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers = USER_AGENT)
    response = urllib.request.urlopen(req, data,context=ctx).read().decode("utf-8")   
    soup = BeautifulSoup(response,'html.parser')
    table = soup.find_all("table")[-1]
    content = table.find(class_="main_main")
    if not content:
        return "當天沒有交易紀錄 請主子恕罪"
    content = content.get_text().split("\n")
    content = [s.strip()  for s in content if s ]
    return content

def get_viewstate_and_event():
    url = "https://amis.afa.gov.tw/veg/VegProdDayTransInfo.aspx"
    req = requests.get(url,headers = USER_AGENT,verify=False)
    data = req.text
    bs = BeautifulSoup(data,features="html.parser")

    return (bs.find("input", {"id": "__VIEWSTATE"}).attrs['value'],
            bs.find("input", {"id": "__EVENTVALIDATION"}).attrs['value'])

def get_product_no(name):
    """回傳字串代號 或者細項列表"""
    matched = [p for p in PRODUCT_NO_NAME if name in p]
    if len(matched)>=2:
        return [item[-1] for item in matched]
    else:
        return matched[0][0]

