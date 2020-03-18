import json
from crawl_weather import get_weather
from config import Config
config = Config()
data_path = config.data_path

def parse_county(cut_text):
    with open(data_path+'weather.json','r',encoding='utf-8',errors='ignore') as f:
        COUNTIES = json.loads(f.read())["COUNTIES"]

    for possible_county in cut_text:
        possible_county = possible_county.replace("台","臺")
        for county in COUNTIES:
            if possible_county[:2] == county[:2]:
                return county
    return None

def parse_weather_info(cut_text):
    county = parse_county(cut_text)
    if not county:
        county = "雲林縣"
    output = get_weather(county)
    return output