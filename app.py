from flask import Flask, request, abort
from linebot import (LineBotApi, WebhookHandler, exceptions)
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, JoinEvent, LeaveEvent, TextMessage, TextSendMessage
)
from datetime import datetime
from crawl_price import search
from crawl_weather import get_weather
import re
import jieba
from data import MARKET_NO_NAME,PRODUCT_NO_NAME,COUNTRIES
import configparser
jieba.load_userdict('dict.txt')

app = Flask(__name__)
config = configparser.ConfigParser()
config.read("config.ini")

line_bot_api = LineBotApi(config.get('line_bot','Channel_Access_Token'))
handler = WebhookHandler(config.get('line_bot','Channel_Secret'))


# 監聽所有來自 /callback 的 Post Request
@app.route("/index", methods=['GET'])
def Hello():
    return 'SUCCESS!'

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(JoinEvent,message=TextMessage)
def handle_join(event):
    newcoming_text = "主人好，奴才願意為您肝腦塗地!"

    line_bot_api.reply_message(
            event.reply_token,
            TextMessage(text=newcoming_text)
        )

def parse_country(cut_text):
    for text in cut_text:
        if text in COUNTRIES:
            return text
    return None


def is_product(name):
    if [ p for p in PRODUCT_NO_NAME if name in p]:
        return True
    else:
        False

def parse_date(text):

    date = re.search("\d{1,2}\/\d{1,2}",text).group(0)
    return "/".join([f"0{d}" if len(d)==1 else d for d in date.split("/")])
  

def parse_market(cut_text):
    for text in cut_text:
        if text in MARKET_NO_NAME:
            return MARKET_NO_NAME[text]
    return None

def get_specific_product_no(name):
    """取得吻合的細項名稱編號"""
    return [p[0] for p in PRODUCT_NO_NAME if p[-1]==name]

def get_same_category_item(name):
    """辣椒=>朝天椒..."""
    return [p[2] for p in PRODUCT_NO_NAME if (len(p)==3) and (p[1]==name)]

def parse_product(cut_text):
    """回傳市場"""
    for text in cut_text:
        product_no = get_specific_product_no(text)
        if product_no:
            return product_no[0]

        item_list = get_same_category_item(text)
        if item_list:
            return item_list
    return ""
        
#訊息傳遞區塊
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):  

    def reply(text):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text)
        )

    def push(id_, text):
        line_bot_api.push_message(id_,TextSendMessage(text))

    ###抓到顧客的資料 ###
    #profile = line_bot_api.get_profile(event.source.user_id)
    #nameid = profile.display_name #使用者名稱
    #uid = profile.user_id #使用者ID

    #群組聊天
    #uid = event.source.group_id
    if hasattr(event.source, 'group_id'):
        uid = event.source.group_id

    elif hasattr(event.source, 'room_id'):
        uid = event.source.room_id
        
    else:
        uid = event.source.user_id

    userspeak=str(event.message.text).strip() #使用者講的話
    cut_text = jieba.lcut(userspeak, cut_all=False)


    if "天氣" in cut_text:
        country = parse_country(cut_text)
        if not country:
            country = "雲林縣"
            
        country = country.replace("台","臺")
        period_list = get_weather(country)
        if period_list:
            info = ["從","到","天氣現象","最低溫度","最高溫度","降雨機率"]
            output = ""
            for period in period_list:
                for i,ele in enumerate(period):
                   output += f"{info[i]}：{ele}\n"
                output += "\n"
            push(uid,  output)
        else:
            push(uid,  "查無紀錄，主人饒命阿!!")


    if "價格" in cut_text:
        product_no = parse_product(cut_text)
        if isinstance(product_no, list):
            msg = f"好多種呀 請主子責罰\n"+"\n".join(product_no)
            push(uid,  msg)
            return 

        if product_no:

            #日期預設今天
            dt =datetime.now()
            m = str(dt.month) if dt.month>=10 else f"0{dt.month}"
            d = str(dt.day) if dt.day>=10 else f"0{dt.day}"
            date = f"109/{m}/{d}"
            if re.search("\d+/\d+",userspeak):
                date = f"109/{parse_date(userspeak)}"

            print (date)
          
            #市場
            market_no = parse_market(cut_text) if  parse_market(cut_text) else 109
            
            #搜尋
            content = search(date,market_no=109,product_no=product_no)
            print (content)
            item = ["產品","上價","中價","下價","平均價","跟前一日交易日比較%","交易量(公斤)","跟前一日交易日比較%"]

            if isinstance(content, str):
                push(uid,content)
                return 
                
            output = ""
            for i,it in enumerate(item):
                output = output+f'{it}:{content[i]}\n'

            push(uid,output)
            return 

    elif userspeak == "小琳":
        push(uid, "主子有什麼吩咐?")

    elif userspeak == "可以幫我嗎":
        push(uid, "奴才甘願為主人肝腦塗地！")


    elif userspeak in ["謝謝","謝了"]:
        push(uid,"奴才不敢當")

    elif userspeak in ["小琳再見"]:
        push(uid,"奴才告退")



import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 27017))
    app.run(host='0.0.0.0', port=port)
    #app.run(debug=True,port=5000)





