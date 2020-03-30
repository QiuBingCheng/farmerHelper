import re
from datetime import datetime

def parse_date(string):
    """解析年月日 若沒有則是當日日期"""
    result = re.search("(\d{3,4})?[/年]?(\d{1,2})[/月](\d{1,2})",string)
    if result:
        year = result.group(1)
        if year:
            #西元>民國
            if len(year)==3:
                return (int(year),int(result.group(2)),int(result.group(3)))
            else:
                return (int(year)-1911,int(result.group(2)),int(result.group(3)))
        else:
            return (datetime.now().year-1911,int(result.group(2)),int(result.group(3)))
    else:
        dt = datetime.now()
        return (dt.year-1911,dt.month,dt.day)