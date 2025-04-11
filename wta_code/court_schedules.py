# -*- coding: utf-8 -*-
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


def get_tournament_group_ids():
    # https://api.wtatennis.com/tennis/tournaments/?page=0&pageSize=100&excludeLevels=ITF&from=2025-04-01&to=2025-04-30
    curmonth = str(datetime.datetime.now().month)
    curyear = str(datetime.datetime.now().year)
    if str(curmonth).__len__() < 2:
        curmonth = "0" + curmonth
    startdate = "%s-%s-01"%(curyear, curmonth)
    enddate = "%s-%s-30"%(curyear, curmonth)
    if int(curmonth) <= 6 and int(curmonth) % 2 == 1:
        enddate = "%s-%s-31"%(curyear, curmonth)
    elif int(curmonth) > 7 and int(curmonth) % 2 == 0:
        enddate = "%s-%s-31"%(curyear, curmonth)
    elif int(curmonth) == 7:
        enddate = "%s-%s-31"%(curyear, curmonth)
    elif int(curmonth) == 2:
        enddate = "%s-%s-28"%(curyear, curmonth)
    else:
        enddate = "%s-%s-30"%(curyear, curmonth)
    headers = {'accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 'accept-encoding' : 'gzip, deflate', 'accept-language' : 'en-GB,en-US;q=0.9,en;q=0.8', 'account' : 'wta', 'if-none-match' : 'W/"0bc70c948c40a474abb90c3de03ef9891"', 'origin' : 'https://www.wtatennis.com', 'referer' : 'https://www.wtatennis.com/', 'user-agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
    response = requests.get("https://api.wtatennis.com/tennis/tournaments/?page=0&pageSize=100&excludeLevels=ITF&from=%s&to=%s"%(startdate, enddate), headers=headers)
    content = response.text
    contentdict = json.loads(content)
    tournamentgroups = contentdict['content']
    datalist = []
    for tg in tournamentgroups:
        title = tg['title']
        startdt = tg['startDate']
        enddt = tg['endDate']
        tgid = tg['tournamentGroup']['id']
        level = tg['tournamentGroup']['level']
        d = {'title' : title, 'startdate' : startdt, 'enddate' : enddt, 'tournamentgroupid' : tgid, 'level' : level}
        datalist.append(d)
    return datalist



def get_court_schedules(playerslist, datalist):
    # https://api.wtatennis.com/tennis/tournaments/1125/2025/matches?states=L , 1125 is the tournament group Id from "get_tournament_group_ids.
    curyear = datetime.datetime.now().year
    headers = {'accept' : '*/*', 'accept-encoding' : 'gzip, deflate', 'accept-language' : 'en-GB,en-US;q=0.9,en;q=0.8', 'account' : 'wta', 'if-none-match' : 'W/"0bc70c948c40a474abb90c3de03ef9891"', 'origin' : 'https://www.wtatennis.com', 'referer' : 'https://www.wtatennis.com/', 'user-agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
    # Create a list of regexes of player names from playerslist
    playerregexes = []
    for player in playerslist:
        if player == "":
            continue
        playerregex = re.compile(player, re.IGNORECASE|re.DOTALL)
        playerregexes.append(playerregex)
    matcheslist = []
    for dobj in datalist:
        tgid = dobj['tournamentgroupid']
        #targeturl = "https://api.wtatennis.com/tennis/tournaments/%s/%s/matches?states=L"%(tgid, curyear)
        #targeturl = "https://api.wtatennis.com/tennis/tournaments/%s/%s/matches?states=C"%(tgid, curyear)
        targeturl = "https://api.wtatennis.com/tennis/tournaments/" + str(tgid) + "/" + str(curyear) + "/matches?states=L%2C+C"
        print(targeturl)
        response = requests.get(targeturl, headers=headers)
        content = response.text
        #print(content)
        contentdict = json.loads(content)
        matches = contentdict['matches']
        #print(matches.__len__())
        for match in matches:
            courtid = str(match['CourtID'])
            playernameA = match['PlayerNameFirstA'] + " " + match['PlayerNameLastA']
            playernameB = match['PlayerNameFirstB'] + " " + match['PlayerNameLastB']
            #print(playernameA)
            found = False
            for pprx in playerregexes:
                if re.search(pprx, match['PlayerNameLastA']) or re.search(pprx, match['PlayerNameLastB']):
                    found = True
                    break
            if found is True:
                matchts = match['MatchTimeStamp']
                matchdt = matchts.split("T")[0]
                matchdate = datetime.datetime.strptime(matchdt, "%Y-%m-%d")
                tournamenttitle = dobj['title']
                d = {'courtid' : courtid, 'matchdate' : matchdate, 'tournamenttitle' : tournamenttitle, 'playernameA' : playernameA, 'playernameB' : playernameB}
                matcheslist.append(d)
    return matcheslist



if __name__ == "__main__":
    playerslist = []
    pfp = open("/home/supmit/work/capturelivefeed/players.list", "r")
    playerscontent = pfp.read()
    pfp.close()
    playerslist = playerscontent.split("\n")
    datalist = get_tournament_group_ids()
    matcheslist = get_court_schedules(playerslist, datalist)
    for matchobj in matcheslist:
        for k in matchobj.keys():
            print("%s ====>> %s"%(k, matchobj[k]))
        print("\n ----------------------------------------- \n")
    

