# -*- coding: utf-8 -*-
"""
Created on Sat Feb 29 09:38:14 2020

@author: Jerry
"""

from bs4 import BeautifulSoup
import requests
import json
import pandas as pd
USER_AGENT = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}
url = "https://opendata.epa.gov.tw/api/v1/AQI?skip=0&top=1000&format=json"

response = requests.get(url,headers = USER_AGENT,verify=False).json()
response[0]
a = pd.DataFrame(response)

#存取空氣品質觀測站的info
num = len(response)
remove_key = set(response[0].keys())-set(["SiteName","County","Longitude",'Latitude','SiteId'])
for i in range(num):
    for key in remove_key :
            del response[i][key]
    
with open ('AQI_observation_station.json','w') as f:
    json.dump(response ,f)
   
data = json.load(open('AQI_observation_station.json'))

#存取AQI現況
get_AQI("312")

def get_AQI(site_name):
    response = requests.get(url,headers = USER_AGENT,verify=False).json()
    for site in response:
        if site["SiteName"] == site_name:
            return [["測站",site["SiteName"]],
                    ["縣市",site["County"]],
                    ["AQI",site["AQI"]],
                    ["狀態",site["Status"]],
                    "發布時間",site["PublishTim"]]
                    

get_AQI("前鎮")      
        
a.columns
data
def get_county_sitename(county):
    return [site["SiteName"] for site in data if site["County"]==county]

import time 


"1"[:3]

"\n".join(["A","B","c"])
