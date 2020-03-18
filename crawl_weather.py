import requests
from config import Config
config = Config()
weather_api = config.weather_api
AQI_api = config.AQI_api
member_token = config.member_token

def get_weather(locationName):
    payload = {"Authorization":member_token,
               "locationName":locationName,
               }
    r = requests.get(weather_api, params=payload)
    json_data = r.json()["records"]["location"] 

    if not json_data:
        return None

    wea_ele = json_data[0]["weatherElement"]

    wx = [i['time'] for i in wea_ele if i["elementName"]=="Wx"][0]
    period_list = [[w["startTime"],w["endTime"],w['parameter']['parameterName']] for w in wx]

    mint = [i['time'] for i in wea_ele if i["elementName"]=="MinT"][0]
    for i,item in enumerate(period_list):
        for m in mint:
            if (m["startTime"]==item[0])&(m["endTime"]==item[1]):
                period_list [i].append(m["parameter"]["parameterName"])
                
    maxt = [i['time'] for i in wea_ele if i["elementName"]=="MaxT"][0]
    for i,item in enumerate(period_list ):
        for m in maxt:
            if (m["startTime"]==item[0])&(m["endTime"]==item[1]):
                period_list[i].append(m["parameter"]["parameterName"])

    pop = [i['time'] for i in wea_ele if i["elementName"]=="PoP"][0]
    for i,item in enumerate(period_list):
        for p in pop:
            if (p["startTime"]==item[0])&(p["endTime"]==item[1]):
                period_list [i].append(p["parameter"]["parameterName"])
    #簡化時間
    for period in period_list:
        period[0] = period[0][5:-3].replace("-","/")
        period[1] = period[1][5:-3].replace("-","/")

    output = ""
    info = ["從","到","天氣現象","最低溫度","最高溫度","降雨機率"]
    for period in period_list:
        for i,ele in enumerate(period):
           output += f"{info[i]}：{ele}\n"
        output += "\n"
    return output


def get_AQI(site_name):

    try :
        response = requests.get(AQI_api,verify=False,timeout=2).json()
    except requests.exceptions.Timeout as e:
        return "出現錯誤！奴才辦事無力，請通知秉誠大大"

    for site in response:
        if site["SiteName"] == site_name:
            content = [f"測站:{site['SiteName']}",
                       f"縣市:{site['County']}",
                       f"AQI:{site['AQI']}",
                       f"狀態:{site['Status']}",
                       f"發布時間:{site['PublishTime']}"]
            return "\n".join(content)
            

def get_county_sitename(county):
    return [site["SiteName"] for site in data if site["County"]==county]
