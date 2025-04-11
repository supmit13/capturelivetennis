import json
import logging
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread, Lock

import datetime

import requests
import concurrent.futures



def get_live_videos(matcheslist):
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

    jsn = json.loads(response.text)
    for item in jsn['content']:
        if item['type'] == 'video':
            _id = item['id']
            titleUrlSegment = item['titleUrlSegment']
            mediaId = item['mediaId']
            dt = item['date'].split("T")[0] # Date for checking with results from extended code.
            found = False
            for matchobj in matcheslist:
                mdate = matchobj['matchdate']
                matchplayers = matchobj['playernameA'].replace(" ", "_") + "_vs_" + matchobj['playernameB'].replace(" ", "_")
                if mdate == dt:
                    found = True
                    break
            if found is True:
                yield dict(
                    id=_id,
                    titleUrlSegment=titleUrlSegment,
                    mediaId=mediaId,
                    matchdate=dt,
                    matchplayers=matchplayers
                )


def get_stream_url(mediaId):
    headers = {
        'Host': 'edge.api.brightcove.com',
        'sec-ch-ua-platform': '"Windows"',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        'accept': 'application/json;pk=BCpkADawqM0zcg_0ZvfWGz7KplqrF6vLHywgyqoukH-6LW3yPthBLN-snb1VI07jhrLNiPMa78U87tX8X2PN6YSoUjOSA9GKl1NjqErawII0fXSP2eZhUPIBBttt9ee5wRSFmUvHfVP73Nx1JRuSFuhP8ZI3zlnL-oar0w',
        'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        'sec-ch-ua-mobile': '?0',
        'origin': 'https://www.wtatennis.com',
        'sec-fetch-site': 'cross-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://www.wtatennis.com/',
        'accept-language': 'en-IN,en;q=0.9',
        'priority': 'u=1, i',
    }

    response = requests.get(
        f'https://edge.api.brightcove.com/playback/v1/accounts/6041795521001/videos/{mediaId}',
        headers=headers,verify=None
    )

    try:
        jsn = response.json()
        sources = jsn['sources']
        for source in sources:
            if source['type'] == 'application/x-mpegURL':
                return source['src']

    except:
        return None



def backgrounddownloader( url, file_path, file_key):
    command = (f'yt-dlp -f "bestvideo[height<=720]+bestaudio/best[height<=720]" "{url}" '
               f'--external-downloader ffmpeg '
               f'--external-downloader-args "ffmpeg:-t 04:00:00" '
               f'--add-header="Accept:*/*" '
               f'--add-header="Origin:https://www.wtatennis.com" '
               f'--add-header="Connection:keep-alive" '
               f'--add-header="Referer:https://www.wtatennis.com/" '
               f'--add-header="User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36" '
               f'--abort-on-unavailable-fragment '
               f'-o "{file_path}.%(ext)s"')
    try:
        process_output = subprocess.check_output(command, shell=True, universal_newlines=True)
        print(f"Downloading finished for {file_key}")
        # Mark as downloaded in the JSON file
    except subprocess.CalledProcessError as e:
        print(f"Download failed for {file_key}: {e}")


def download_video(video):

    stream_url = get_stream_url(video['mediaId'])
    match_date = video['matchdate'].replace("-", "") # Format is yyyymmdd

    if stream_url:


        #file_name = f"{video['titleUrlSegment']}_{video['id']}_{video['mediaId']}"
        file_name = f"{video['matchplayers']}_{video['id']}_{video['mediaId']}"

        Path(
            "wta-videos/%s"%match_date
        ).mkdir(
            parents=True,exist_ok=True
        )


        file_path = Path(f"wta-videos/{match_date}/{file_name}")

        backgrounddownloader(stream_url, file_path, file_name)



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
                #matchdate = datetime.datetime.strptime(matchdt, "%Y-%m-%d")
                tournamenttitle = dobj['title']
                d = {'courtid' : courtid, 'matchdate' : matchdt, 'tournamenttitle' : tournamenttitle, 'playernameA' : playernameA, 'playernameB' : playernameB}
                matcheslist.append(d)
    return matcheslist


def process_matches(matcheslist):
    matches_to_download = list(get_live_videos(matcheslist))

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_match = {}
        for match in matches_to_download:

            print(f"Scheduling download for match: {match}")
            future = executor.submit(download_video, match)
            future_to_match[future] = match
        # Wait for all downloads to complete
        for future in concurrent.futures.as_completed(future_to_match):
            match = future_to_match[future]
            try:
                future.result()
            except Exception as e:
                print(f"Error downloading match : {e}")


if __name__ == '__main__':
    playerslist = []
    pfp = open("/home/supmit/work/capturelivefeed/players.list", "r")
    playerscontent = pfp.read()
    pfp.close()
    playerslist = playerscontent.split("\n")
    datalist = get_tournament_group_ids()
    matcheslist = get_court_schedules(playerslist, datalist)
    process_matches(matcheslist)

