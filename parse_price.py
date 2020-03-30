from crawl_price import get_transaction_info
from datetime import datetime
from util import parse_date
import re
import json
from config import Config

config = Config()
data_path = config.data_path
with open(data_path+'crop_item.json','r',encoding='utf-8',errors='ignore') as f:
        crop_item = json.loads(f.read())

VEGETABLE_NO_NAME = crop_item["vegetable_no_name"]
FRUIT_NO_NAME = crop_item["fruit_no_name"]

with open(data_path+'crop_market.json','r',encoding='utf-8',errors='ignore') as f:
        MARKET_NO_NAME = json.loads(f.read())

def parse_market(cut_text,type_):
    MARKET_NO_NAME = json.loads(open(config.data_path+'/crop_market.json',encoding='utf-8',errors='ignore').read())
    if type_ == "fruit":
        for text in cut_text:
            if text in MARKET_NO_NAME["fruit"]:
                return text

    if type_ == "vegetable":
        for text in cut_text:
            if text in MARKET_NO_NAME["vegetable"]:
                return text
    return None

def get_product_no(name,type_):
    if type_ == "fruit":
        return [p[0] for p in FRUIT_NO_NAME  if p[-1]==name]
    if type_ == "vegetable":
        return [p[0] for p in VEGETABLE_NO_NAME  if p[-1]==name]

def get_category_item(name,type_):
    """辣椒=>朝天椒..."""
    if type_ == "vegetable":
        return [p[2] for p in VEGETABLE_NO_NAME  if (len(p)==3) and (p[1]==name)]
    
    if type_ == "fruit":
        return [p[2] for p in FRUIT_NO_NAME  if (len(p)==3) and (p[1]==name)]

def parse_product(cut_text):
    """先完全比對品名 爾後比對種類"""
    for text in cut_text:
        vegetable_no = get_product_no(text,type_="vegetable")
        if vegetable_no:
            return ("vegetable",vegetable_no[0])

        fruit_no = get_product_no(text,type_="fruit")
        if fruit_no:
            return ("fruit", fruit_no[0])

        item_list = get_category_item(text,type_="vegetable")
        if item_list:
            item_list.insert(0,text)
            return item_list

        item_list = get_category_item(text,type_="fruit")
        if item_list:
            item_list.insert(0,text)
            return item_list

    return False

def parse_transation_info(userspeak,cut_text):
    """extract trading informtion from message

    Returns: 
        tuple:(result,info)
    """
    product_type_no = parse_product(cut_text)

    if isinstance(product_type_no, list):
        return ("items",product_type_no)
        
    if isinstance(product_type_no, tuple):
        product_type, product_no = product_type_no

        y,m,d = parse_date(userspeak.replace(" ",""))
        if m <=9:
            m = f"0{m}"
        if d <=9:
            d = f"0{d}"
            
        date = f"{y}/{m}/{d}"

        market_name = parse_market(cut_text,product_type)
        if not market_name:
            market_name = "台北一"

        market_no = MARKET_NO_NAME[product_type][market_name]
        
        #搜尋
        content = get_transaction_info(date,type_= product_type,market_no=market_no,product_no=product_no)
        
        if isinstance(content, str):
            #send_text_message(uid,content)
            return ("fail",content)

        output = f"日期:{date}\n市場:{market_name}\n"

        for item in content:
            output += f'{item[0]}:{item[1]}\n'

        return ("success",output)