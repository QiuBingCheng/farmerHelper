from config import Config
import requests
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')

config = Config()
api = {"fruit":config.fruit_api,
       "vegetable":config.vegetable_api
       }


USER_AGENT = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}

def get_transaction_info(date,type_,market_no,product_no):
    """成功爬取回傳列表 否則字串"""

    print(date,type_,product_no,market_no)
    
    values = {}
    values['__EVENTTARGET'] = "ctl00$contentPlaceHolder$btnQuery"
    values['__EVENTARGUMENT'] = ''
    values['ctl00$contentPlaceHolder$txtSTransDate'] = date
    values['ctl00$contentPlaceHolder$hfldMarketNo'] = market_no
    values['ctl00$contentPlaceHolder$ucDateScope$rblDateScope'] = 'D'
    values['ctl00$contentPlaceHolder$ucSolarLunar$radlSolarLunar']= "S"
    values['ctl00$contentPlaceHolder$hfldProductNo'] = product_no
    values['__VIEWSTATE'],values['__EVENTVALIDATION'] = get_viewstate_and_event(api[type_])
    
    
    try:
        response = requests.post(api[type_],values,headers = USER_AGENT,verify=False,timeout=2).text
    except requests.exceptions.Timeout as e: 
        return "出現錯誤！奴才辦事無力，請通知秉誠大大"
    
    soup = BeautifulSoup(response,features = 'html.parser')
    table = soup.find_all("table")[-1]
    content = table.find(class_="main_main")
   
    if not content:
        return "當天沒有交易紀錄 請主子恕罪"
    content = content.get_text().split("\n")
    content = [s.strip()  for s in content if s ]
    item = ["產品","上價","中價","下價","平均價","跟前一日交易日比較%","交易量(公斤)","跟前一日交易日比較%"]
    

    content = [ [k,v] for k,v in zip(item,content)]

    return content

def get_viewstate_and_event(url):
    req = requests.get(url,headers = USER_AGENT,verify=False)
    data = req.text
    bs = BeautifulSoup(data,features="html.parser")

    return (bs.find("input", {"id": "__VIEWSTATE"}).attrs['value'],
            bs.find("input", {"id": "__EVENTVALIDATION"}).attrs['value'])
