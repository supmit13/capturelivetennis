import time
import requests
from selenium import webdriver 

def download_stream(url):
    r1 = requests.get(url, stream=True)
    with open('/home/supmit/work/capturelivefeed/tennisvideos/testvid.mp4','ab') as f:
        for chunk in r1.iter_content(chunk_size=1024):
            f.write(chunk)

# Create a new instance of the Chrome driver
driver = webdriver.Chrome()

# Go to the Google home page
driver.get('https://lc-live-http.akamaized.net/at/14879/2449791/mobile/master_delayed.m3u8?cid=14879&mid=34650587&ecid=2449791&pid=6&dtid=1&sid=418717373730&hdnts=ip=2401:4900:1c5d:4175:9cbd:4f8:920d:b415~exp=1657820393~acl=%2Fat%2F14879%2F2449791%2Fmobile%2F%2A~hmac=fcde40ecd71dacdf8011c62c04628174a8ba4d3437e94052085159c5aed1465f')

# Access requests via the `requests` attribute
tslist = []
while True:
    for request in driver.requests:
        if request.url.endswith(".ts"):
            if request.url not in tslist:
                tslist.append(request.url)
                download_stream(request.url)


"""
{
    "streamUrl": "https://lc-live-http.akamaized.net/at/14879/2449791/mobile/master_delayed.m3u8?cid=14879&mid=34650587&ecid=2449791&pid=6&dtid=1&sid=418717373730&hdnts=ip=2401:4900:1c5d:4175:9cbd:4f8:920d:b415~exp=1657820393~acl=%2Fat%2F14879%2F2449791%2Fmobile%2F%2A~hmac=fcde40ecd71dacdf8011c62c04628174a8ba4d3437e94052085159c5aed1465f",
    "isLiveStream": true,
    "codecs": {
        "vcodec": "avc1.42c00d",
        "acodec": "mp4a.40.5"
    },
    "playState": "paused",
    "resolution": "320x180",
    "playbackrate": 1,
    "quality": 375.475,
    "currentTime": 22.047559,
    "fps": null,
    "droppedFrames": null,
    "volume": 50
}

"""
