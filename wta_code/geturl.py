import os, sys, re
import urllib, urllib.request
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import unicodedata
import io
import gzip
import time
import simplejson as json
import xml.etree.ElementTree as ET
import datetime
import string
import requests
from urllib.parse import urlencode, quote_plus
import html
import csv


if __name__ == "__main__":
    headers = {
        'Host': 'api.wtatennis.com',
        # 'Cookie': 'OptanonAlertBoxClosed=2025-03-04T08:55:53.651Z; __exponea_etc__=17230a4b-290e-4137-b57c-c3a8c53371eb; _fbp=fb.1.1741078560015.764214526706481615; _hjSessionUser_3914023=eyJpZCI6ImE0M2E2NThjLWI5MGQtNTEwZS1iMWM3LWVkMzk5OWUyZTAyNiIsImNyZWF0ZWQiOjE3NDEwNzg1Njc2MzYsImV4aXN0aW5nIjp0cnVlfQ==; _gid=GA1.2.373990136.1742607753; __exponea_time2__=5.295958518981934; _tt_enable_cookie=1; _ttp=01JPYM0V1AJVZJXVEKBBY76G8W_.tt.1; _gcl_au=1.1.1176158351.1741078554.906351405.1742638863.1742638863; __gads=ID=a6bf5c98d15f28a1:T=1741078405:RT=1742638889:S=ALNI_MaWfU-dUxyUBtLYQahKUGbTYuG6Qw; __gpi=UID=00001054b4922fac:T=1741078405:RT=1742638889:S=ALNI_MbU6LiD_xk-Y6QvlvCwCCw_5q9tSA; __eoi=ID=b408ddbfa9a52384:T=1741078405:RT=1742638889:S=AA-AfjaIvE5t90g7GMb4XkMKsqGC; _ga=GA1.2.149211522.1741078400; _ga_N68DS9FZ1P=GS1.2.1742638246.5.1.1742638891.0.0.0; OptanonConsent=isGpcEnabled=0&datestamp=Sat+Mar+22+2025+15%3A51%3A31+GMT%2B0530+(India+Standard+Time)&version=202409.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=176753d3-5dd0-4152-a5b4-82e139b0a352&interactionCount=1&isAnonUser=1&landingPath=NotLandingPage&groups=C0004%3A1%2CC0003%3A1%2CC0002%3A1%2CC0001%3A1&intType=1&geolocation=IN%3BKL&AwaitingReconsent=false; _ga_XYQ4F7ZCP6=GS1.1.1742638246.6.1.1742639224.57.0.0; _ga_RJ0TV0MHZJ=GS1.1.1742636858.4.1.1742639224.0.0.0',
        'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document',
        'accept-language': 'en-IN,en;q=0.9,zh-TW;q=0.8,zh;q=0.7,ml;q=0.6,hi;q=0.5',
        'priority': 'u=0, i',
    }
    
    params = {
        'tagNames': 'live-video',
        'page': '0',
        'pageSize': '100',
    }

    response = requests.get('https://api.wtatennis.com/content/wta/VIDEO/en', params=params,
                            headers=headers,verify=None)

    try:
        jsn = response.json()
        print(jsn)
        """
        sources = jsn['sources']
        for source in sources:
            if source['type'] == 'application/x-mpegURL':
                return source['src']
        """
    except:
        pass
