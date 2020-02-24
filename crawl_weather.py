import requests
from config import Config
config = Config()
open_data_url = config.weather_url
member_token = config.member_token

def get_weather(locationName):
    payload = {"Authorization":member_token,
               "locationName":locationName,
               }
    r = requests.get(open_data_url, params=payload)
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

    return period_list