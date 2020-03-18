from crawl_weather import get_AQI
import json
from config import Config
config = Config()
data_path = config.data_path

def get_all_sites():
    with open(data_path+'AQI_observation_station.json','r',encoding='utf-8',errors='ignore') as f:
        all_sites = json.loads(f.read())
    return all_sites

def get_county_sitename(all_sites,county_name):
    return [site["SiteName"] for site in all_sites if site["County"]==county_name]

def parse_air_quality(cut_text):
    all_sites = get_all_sites()
    sitenames = [site["SiteName"] for site in all_sites]

    output = ""
    #station
    for possible_site in cut_text:
        #比對sitename
        possible_site = possible_site.replace("台","臺")
        if possible_site in sitenames:
            content = get_AQI(possible_site)
            return content

        #比對county
        for site in all_sites:
            county_name = site["County"]
            if county_name [:2] == possible_site[:2]:
                sites_in_the_county = get_county_sitename(all_sites,county_name)
                output = f"{county_name }有很多觀測站呢!\n"
                output += "\n".join(sites_in_the_county)
                return output

    else:
        output = "沒有指定的觀測站~"
    
    return output

def get_sitename_in_the_county(cut_text):
    all_sites = get_all_sites()
    for possible_site in cut_text:
        possible_site = possible_site.replace("台","臺")
        for site in all_sites:
            county_name = site["County"]
            if county_name [:2] == possible_site[:2]:
                sites_in_the_county = get_county_sitename(all_sites,county_name)
                output = f"這些是{county_name}的觀測站~\n"
                output += "\n".join(sites_in_the_county)
                return output
    else:
        return "這裡沒有觀測站~"