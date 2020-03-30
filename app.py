# -*- coding: utf-8 -*-
import os
import requests
from bs4 import BeautifulSoup
from config import Config
from flask import Flask, request, abort
from linebot import (LineBotApi, WebhookHandler, exceptions)
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, JoinEvent, LeaveEvent, TextMessage, LocationSendMessage,
    TextSendMessage, TemplateSendMessage, CarouselTemplate,
    CarouselColumn, MessageTemplateAction, ButtonsTemplate,
    PostbackTemplateAction
)
from datetime import datetime
from crawl_price import get_transaction_info
from crawl_weather import get_weather, get_AQI
import re
import jieba
import redis
from parse_weather import parse_weather_info
from parse_price import parse_transation_info
from parse_air_quality import get_sitename_in_the_county, parse_air_quality
jieba.load_userdict('dict.txt')

app = Flask(__name__)
config = Config()
line_bot_api = config.line_bot_api
handler = config.handler

#初始化資料庫
pool = redis.ConnectionPool(host=config.db["host"], 
                            port=config.db["port"],
                            password=config.db["password"])

R = redis.Redis(connection_pool=pool)

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


@handler.add(JoinEvent, message=TextMessage)
def handle_join(event):
    newcoming_text = "主人好，奴才願意為您肝腦塗地!"

    line_bot_api.reply_message(
        event.reply_token,
        TextMessage(text=newcoming_text)
    )


# 訊息傳遞區塊
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    def reply_text_message(text):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text)
        )

    def reply_location_message(lat, lng, title, address):
        line_bot_api.reply_message(event.reply_token, 
                                   LocationSendMessage( title=title,
                                                        address=address,
                                                        latitude=lat,
                                                        longitude=lng))

    def reply_menu_message(template):
        line_bot_api.reply_message(
            event.reply_token,
            template
        )

    def make_template(text, labels, texts, title="快速選單", postback=False):
        if postback:
            actions = [PostbackTemplateAction(
                label=label, text=text, data='postback1') for label, text in zip(labels, texts)]
        else:
            actions = [MessageTemplateAction(
                label=label, text=text) for label, text in zip(labels, texts)]

        buttons_template = TemplateSendMessage(
            itle='Menu',
            text='Please select option',
            alt_text='Buttons Template',
            template=ButtonsTemplate(
                title=title,
                text=text,
                actions=actions
            )
        )
        return buttons_template

    def send_text_message(id_, text):
        line_bot_api.push_message(id_, TextSendMessage(text))

    ###抓到顧客的資料 ###
    # profile = line_bot_api.get_profile(event.source.user_id)
    # nameid = profile.display_name #使用者名稱
    # uid = profile.user_id #使用者ID

    # 群組聊天
    # uid = event.source.group_id
    if hasattr(event.source, 'group_id'):
        group_id = event.source.group_id
        if R.llen(f"group:{group_id}")>0:
            R.blpop(f"group:{group_id}")

        try:
            group = line_bot_api.get_group_member_ids(group_id)
            for id_ in group.member_ids:
                R.rpush(f"group:{group_id}",id_)
        except:
            pass

    elif hasattr(event.source, 'room_id'):
        room_id = event.source.room_id
        if R.llen(f"room:{room_id}")>0:
            R.blpop(f"room:{room_id}")

        try:
            room = line_bot_api.get_room_member_ids(room_id)
            for id_ in room.member_ids:
                R.rpush(f"room:{room_id}",id_)
        except:
            pass

    else:
        uid = event.source.user_id
        profile = line_bot_api.get_profile(event.source.user_id)

        display_name = profile.display_name if profile.display_name else ""
        picture_url = profile.picture_url if profile.picture_url else ""
        status_message = profile.status_message if profile.status_message else ""

        R.hset(f"user:{uid}","display_name",display_name)
        R.hset(f"user:{uid}","picture_url",picture_url)
        R.hset(f"user:{uid}","status_message",status_message)

    reply_text_message("0x100078".encode("utf-32"))
    userspeak = str(event.message.text).strip()  # 使用者講的話
    cut_text = jieba.lcut(userspeak, cut_all=False)
    print(cut_text)

    if re.search("聽.{2,5}的.+", userspeak):
        keyword = re.search("聽.{2,5}的.+", userspeak).group(0).replace("聽", "")
        #print (keyword)
        search_url = f"https://www.youtube.com/results?search_query={keyword}"
        # print search_url
        # reply_text_message(keyword+"\n"+search_url)
        # return
        response = requests.get(search_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        url = soup.select('.yt-lockup-title')[0].find('a')['href']
        reply_text_message(f"https://www.youtube.com{url}")

    elif re.search("(.*)在[哪何][裡邊處]?|(.*)的地址", userspeak):

        def get_information_of_address(keyword, google_key, basic=True):
            print ("get_information_of_address is called")
            """basic不用收費 進階資訊如照片等則要"""
            if basic:
                address_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={keyword}&key={google_key}&language=zh-TW"
            else:
                fields = "photos,formatted_address,geometry"
                address_url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={keyword}&inputtype=textquery&fields={fields}&key={google_key}&language=zh-TW"

            response = requests.get(address_url).json()
            info = {}
            if response["status"] == "OK":
                info["keyword"] =  keyword

                result = response["results"][0]
                #Latitude and longitude
                info["lat"] = result["geometry"]["location"]["lat"]
                info["lng"] = result["geometry"]["location"]["lng"]
                info["address"] = result['formatted_address']
                if "photo_reference" in result:
                    info["photo_reference"] = result['photo_reference']

            return info

        def download_photo(name,photo_reference,google_key):
            photo_url=f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=1600&photoreference={photo_reference}&key={google_key}"
            response = requests.get(photo_url)
            with open(name, 'wb') as f:
                for chunk in response:
                    if chunk:
                        f.write(chunk)

        keyword = re.search("(.*)在[哪何][裡邊處]?|(.*)的地址", userspeak).group(1)

        #先從資料庫搜索
        if R.hexists(f"address_keyword:{keyword}","lat"):
            info = R.hgetall(f"address_keyword:{keyword}")
            reply_location_message(title=keyword,
                                   lat=float(info[b"lat"]),
                                   lng=float(info[b"lng"]),
                                   address=str(info[b"address"],encoding="utf-8"))
            return

        info = get_information_of_address(keyword, config.google_key)
        if info:
            dic={"lat":info["lat"],"lng":info["lng"],"address":info["address"]}
            R.hmset(f"address_keyword:{keyword}",dic)
            reply_location_message(
                lat=info["lat"], lng=info["lng"], title=info["keyword"], address=info["address"])
        else:
            reply_text_message(f"嗚嗚 抱歉 我找不到{keyword}在哪邊")

    elif "天氣" in cut_text:
        content = parse_weather_info(cut_text)
        reply_text_message(content)

    elif "空氣" in userspeak:
        type_, content = parse_air_quality(cut_text)
        if type_ == "success":
            reply_text_message(content)

        elif type_ == "sites":
            # api最多只能四個選單
            county = content[0]
            sites = content[1:]

            if len(sites) <= 4:
                texts = [site+"的空氣品質" for site in sites]
                buttons_template = make_template(
                    text=county+"有很多觀測站呢!", labels=sites, texts=texts)
                reply_menu_message(buttons_template)
            else:
                output = county+"有很多觀測站呢!\n請重新輸入 *站名* 空氣品質~\n"
                output += "\n".join(sites)
                reply_text_message(output)

        elif type_ == "fail":
            reply_text_message(content)

    elif "觀測站" in userspeak:
        content = get_sitename_in_the_county(cut_text)
        if content:
            output = f"這些是{content[0]}的觀測站~\n"
            output += "\n".join(content[1:])
            reply_text_message(output)
        else:
            reply_text_message("查不到該地方的觀測站哦~")

    elif "價格" in userspeak:
        type_, content = parse_transation_info(userspeak, cut_text)
        print(type_, content)
        if type_ == "success":
            reply_text_message(content)

        elif type_ == "fail":
            reply_text_message(content)

        elif type_ == "items":
            output = content[0]+"有很多種類呢! 請重新輸入 *品項*價格~\n"
            reply_text_message(output+"\n".join(content[1:]))

    elif re.search("教學|使用說明", userspeak):
        text = "哈囉~我是小蓉bot，可以點擊下方選單來查看怎麼使用我噢><\n"

        labels = ["天氣預報", "空氣品質查詢", "蔬果價格查詢", "地標查詢"]
        texts = ["天氣預報功能說明\n輸入 縣市名稱+天氣\n例如 台北市天氣如何呢?",
                 """空氣品質查詢功能說明\n輸入 觀測站名稱+空氣品質\n 例如 斗六的空氣品質\n欲搜尋縣市的觀測站 輸入 縣市名稱+觀測站 例如桃園觀測站""",
                 "蔬果價格查詢功能說明\n輸入 蔬果名稱+價格\n例如 朝天椒價格多少啊?",
                 "地標查詢功能說明\n努力實現中~~"]
        buttons_template = make_template(
            title="簡易教學", text=text, labels=labels, texts=texts, postback=True)
        reply_menu_message(buttons_template)

    elif userspeak == "小蓉":
        # send_text_message(uid, "主子有什麼吩咐?")
        reply_text_message("哈囉")

    elif userspeak in ["謝謝", "謝了"]:
        # send_text_message(uid,"奴才不敢當")
        reply_text_message("不客氣>///<")

    elif "再見" in userspeak :
        # send_text_message(uid,"奴才告退")
        reply_text_message("拜拜囉")
    else:
        return

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 27017))
    app.run(host='0.0.0.0', port=port)
    # app.run(debug=True,port=5000)
