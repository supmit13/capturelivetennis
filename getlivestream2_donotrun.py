# -*- coding: utf-8 -*-
import os, sys, re
import urllib, urllib.request
from bs4 import BeautifulSoup
import unicodedata
import io
import gzip
import time
import simplejson as json
import datetime
import string
import requests
from urllib.parse import urlencode, quote_plus, urlparse
import html
import numpy as np
import cv2
from multiprocessing import Process, Pool, Queue
import multiprocessing as mp
from threading import Thread
import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb

from avcapturer import *




partialUrlPattern = re.compile("^/\w+")

def decodeHtmlEntities(content):
    entitiesDict = {'&nbsp;' : ' ', '&quot;' : '"', '&lt;' : '<', '&gt;' : '>', '&amp;' : '&', '&apos;' : "'", '&#160;' : ' ', '&#60;' : '<', '&#62;' : '>', '&#38;' : '&', '&#34;' : '"', '&#39;' : "'"}
    for entity in entitiesDict.keys():
        content = content.replace(entity, entitiesDict[entity])
    return(content)


# Implement signal handler for ctrl+c here.
def setSignal():
    pass

class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        infourl = urllib.response.addinfourl(fp, headers, req.get_full_url())
        infourl.status = code
        infourl.code = code
        return infourl

    http_error_300 = http_error_302
    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302


def unicodefraction_to_decimal(v):
    fracPattern = re.compile("(\d*)\s*([^\s\.\,;a-zA-Z]+)")
    fps = re.search(fracPattern, v)
    if fps:
        fpsg = fps.groups()
        wholenumber = fpsg[0]
        fraction = fpsg[1]
        decimal = round(unicodedata.numeric(fraction), 3)
        if wholenumber:
            decimalstr = str(decimal).replace("0.", ".")
        else:
            decimalstr = str(decimal)
        value = wholenumber + decimalstr
        return value
    return v


class VideoBot(object):
    htmltagPattern = re.compile("\<\/?[^\<\>]*\/?\>", re.DOTALL)
    pathEndingWithSlashPattern = re.compile(r"\/$")

    htmlEntitiesDict = {'&nbsp;' : ' ', '&#160;' : ' ', '&amp;' : '&', '&#38;' : '&', '&lt;' : '<', '&#60;' : '<', '&gt;' : '>', '&#62;' : '>', '&apos;' : '\'', '&#39;' : '\'', '&quot;' : '"', '&#34;' : '"'}

    def __init__(self, siteurl):
        # Create the opener object(s). Might need more than one type if we need to get pages with unwanted redirects.
        self.opener = urllib.request.build_opener(urllib.request.HTTPHandler(), urllib.request.HTTPSHandler()) # This is my normal opener....
        self.no_redirect_opener = urllib.request.build_opener(urllib.request.HTTPHandler(), urllib.request.HTTPSHandler(), NoRedirectHandler()) # ... and this one won't handle redirects.
        #self.debug_opener = urllib.request.build_opener(urllib.request.HTTPHandler(debuglevel=1))
        # Initialize some object properties.
        self.sessionCookies = ""
        self.httpHeaders = { 'User-Agent' : r'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',  'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language' : 'en-us,en;q=0.5', 'Accept-Encoding' : 'gzip,deflate', 'Accept-Charset' : 'ISO-8859-1,utf-8;q=0.7,*;q=0.7', 'Keep-Alive' : '115', 'Connection' : 'keep-alive', }
        self.httpHeaders['cache-control'] = "max-age=0"
        self.httpHeaders['upgrade-insecure-requests'] = "1"
        self.httpHeaders['sec-fetch-dest'] = "document"
        self.httpHeaders['sec-fetch-mode'] = "navigate"
        self.httpHeaders['sec-fetch-site'] = "same-origin"
        self.httpHeaders['sec-fetch-user'] = "?1"
        self.httpHeaders['sec-ch-ua-mobile'] = "?0"
        self.httpHeaders['sec-ch-ua'] = "\".Not/A)Brand\";v=\"99\", \"Google Chrome\";v=\"103\", \"Chromium\";v=\"103\""
        self.httpHeaders['sec-ch-ua-platform'] = "Linux"
        self.httpHeaders['cookie'] = "cookiecheck=1; referer=https%3A%2F%2Flive.itftennis.com%2Fen%2Flive-streams%2F;cookieconsent_status=allow; _gat=1"
        self.httpHeaders['referer'] = "https://live.itftennis.com/en/live-streams/video.php?vid=34421611"
        self.homeDir = os.getcwd()
        self.siteUrl = siteurl
        self.requestUrl = siteurl
        parsedUrl = urlparse(self.requestUrl)
        self.baseUrl = parsedUrl.scheme + "://" + parsedUrl.netloc
        #print(self.requestUrl)
        self.pageRequest = urllib.request.Request(self.requestUrl, headers=self.httpHeaders)
        self.pageResponse = None
        self.requestMethod = "GET"
        self.postData = {}
        self.nolivestreamtext = "There are currently no live streams available"
        try:
            self.pageResponse = self.opener.open(self.pageRequest)
            headers = self.pageResponse.getheaders()
            #print(headers)
            if "Location" in headers:
                self.requestUrl = headers["Location"]
                self.pageRequest = urllib.request.Request(self.requestUrl, headers=self.httpHeaders)
                try:
                    self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
                except:
                    print ("Couldn't fetch page due to limited connectivity. Please check your internet connection and try again. %s"%sys.exc_info()[1].__str__())
                    sys.exit()
        except:
            print ("Couldn't fetch page due to limited connectivity. Please check your internet connection and try again. %s"%sys.exc_info()[1].__str__())
            sys.exit()
        self.httpHeaders["Referer"] = self.requestUrl
        self.sessionCookies = self.__class__._getCookieFromResponse(self.pageResponse)
        self.httpHeaders["Cookie"] = self.sessionCookies
        # Initialize the account related variables...
        self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
        self.livestreamcheckinterval = 10 # 10 seconds.
        self.chunk_size = 1024
        self.time_limit = 86400 # time in seconds (1 day), for recording. Event will end before this, and we need to be able to recognize it.
        mgr = mp.Manager()
        self.processq = mgr.Queue(maxsize=10000)
        self.size = (320, 180)
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        # itftennis streams have a rate of 25 fps.
        self.FPS = 1/25 # This is the delay that would be applied after every read(). This would 'normalize' the frame rate and handle frame loss jitters.
        self.FPS_MS = int(self.FPS * 1000) # Same delay as above, in milliseconds.
        self.DEBUG = 1 # TODO: Remember to set it to 0 (or False) before deploying somewhere.
        self.dbuser = "feeduser"
        self.dbpasswd = "feedpasswd"
        self.dbname = "feeddb"
        self.dbhost = "localhost"
        self.dbport = 3306
        

    def checkforlivestream(self):
        self.pageRequest = urllib.request.Request(self.siteUrl, headers=self.httpHeaders)
        try:
            self.pageResponse = self.opener.open(self.pageRequest)
            headers = self.pageResponse.getheaders()
            #print(headers)
            if "Location" in headers:
                self.requestUrl = headers["Location"]
                self.pageRequest = urllib.request.Request(self.requestUrl, headers=self.httpHeaders)
                try:
                    self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
                except:
                    print ("Error. %s"%sys.exc_info()[1].__str__())
                    sys.exit()
        except:
            print ("Error: %s"%sys.exc_info()[1].__str__())
            #sys.exit()
            return []
        self.currentPageContent = self.__class__._decodeGzippedContent(self.getPageContent())
        livestreamurls = []
        if self.nolivestreamtext in self.currentPageContent:
            print("No live stream is available now")
            return livestreamurls
        else:
            # Get the streamurls from the page
            soup = BeautifulSoup(self.currentPageContent, features="html.parser")
            videodivtags = soup.find_all("div", {'class' : 'video_thumbnail'})
            for videodiv in videodivtags:
                liveitag = videodiv.find("i", {'class' : 'video_is_live'})
                if not liveitag:
                    continue
                else:
                    liveitext = liveitag.renderContents().decode('utf-8')
                    liveitext = liveitext.replace("\n", "").replace("\r", "")
                    if liveitext == "LIVE":
                        livestreamanchor = videodiv.find("a")
                        if livestreamanchor is not None:
                            livestreamurl = livestreamanchor['href']
                            if not livestreamurl.startswith("https://"):
                                livestreamurl = self.baseUrl + livestreamurl
                            livestreamurls.append(livestreamurl)
        # Return all stream urls
        return livestreamurls


    def _decodeGzippedContent(cls, encoded_content):
        response_stream = io.BytesIO(encoded_content)
        decoded_content = ""
        try:
            gzipper = gzip.GzipFile(fileobj=response_stream)
            decoded_content = gzipper.read()
        except: # Maybe this isn't gzipped content after all....
            decoded_content = encoded_content
        decoded_content = decoded_content.decode('utf-8')
        return(decoded_content)

    _decodeGzippedContent = classmethod(_decodeGzippedContent)


    def _getCookieFromResponse(cls, lastHttpResponse):
        cookies = ""
        responseCookies = lastHttpResponse.getheader("Set-Cookie")
        pathPattern = re.compile(r"Path=/;", re.IGNORECASE)
        domainPattern = re.compile(r"Domain=[^;,]+(;|,)", re.IGNORECASE)
        expiresPattern = re.compile(r"Expires=[^;]+;", re.IGNORECASE)
        maxagePattern = re.compile(r"Max-Age=[^;]+;", re.IGNORECASE)
        samesitePattern = re.compile(r"SameSite=[^;]+;", re.IGNORECASE)
        securePattern = re.compile(r"secure;?", re.IGNORECASE)
        httponlyPattern = re.compile(r"HttpOnly;?", re.IGNORECASE)
        if responseCookies and responseCookies.__len__() > 1:
            cookieParts = responseCookies.split("Path=/")
            for i in range(cookieParts.__len__()):
                cookieParts[i] = re.sub(domainPattern, "", cookieParts[i])
                cookieParts[i] = re.sub(expiresPattern, "", cookieParts[i])
                cookieParts[i] = re.sub(maxagePattern, "", cookieParts[i])
                cookieParts[i] = re.sub(samesitePattern, "", cookieParts[i])
                cookieParts[i] = re.sub(securePattern, "", cookieParts[i])
                cookieParts[i] = re.sub(pathPattern, "", cookieParts[i])
                cookieParts[i] = re.sub(httponlyPattern, "", cookieParts[i])
                cookieParts[i] = cookieParts[i].replace(",", "")
                cookieParts[i] = re.sub(re.compile("\s+", re.DOTALL), "", cookieParts[i])
                cookies += cookieParts[i]
        cookies = cookies.replace(";;", ";")
        return(cookies)

    _getCookieFromResponse = classmethod(_getCookieFromResponse)


    def getPageContent(self):
        return(self.pageResponse.read())


    


    def capturelivestream(self, argslist):
        streamurl, outfilename = argslist[0], argslist[1]
        print("Capturing stream...")
        file_handle = open(outfilename, 'wb')
        start_time_in_seconds = time.time()
        time_elapsed = 0
        with requests.Session() as session:
            response = session.get(streamurl, stream=True)
            for chunk in response.iter_content(chunk_size=self.chunk_size):
                if time_elapsed > self.time_limit:
                    break
                # to print time elapsed   
                if int(time.time() - start_time_in_seconds)- time_elapsed > 0 :
                    time_elapsed = int(time.time() - start_time_in_seconds)
                    print(time_elapsed, end='\r', flush=True)
                if chunk:
                    file_handle.write(chunk)
        file_handle.close()


    def capturelivestream_cv2(self, argslist):
        streamurl, outfilename = argslist[0], argslist[1]
        cap = cv2.VideoCapture(streamurl)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) + 0.5)
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) + 0.5)
        if self.DEBUG:
            print("Width: %s"%width)
            print("Height: %s"%height)
            fps_in = cap.get(cv2.CAP_PROP_FPS)
            print("Incoming frame rate: %s"%fps_in)
        size = (width, height)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        #fourcc = -1
        out = cv2.VideoWriter(outfilename, fourcc, 20.0, size)
        while(True):
            ret, frame = cap.read()
            if ret==True:
                out.write(frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                break
        # Done!
        cap.release()
        out.release()
        cv2.destroyAllWindows()


    def capturelivestream_cv2_q(self, argslist):
        streamurl, outnum, feedid = argslist[0], argslist[1], argslist[2]
        cap = cv2.VideoCapture(streamurl)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 250)
        # check the incoming frame rate if we are in DEBUG mode
        if self.DEBUG:
            fps_in = cap.get(cv2.CAP_PROP_FPS)
            print("Incoming frame rate: %s"%fps_in)
        #cap.set(cv2.CAP_PROP_FPS, 20) # Should we alter the frames rate and set it to 20 fps?
        while True:
            if cap.isOpened():
                ret, frame = cap.read()
                if ret == True:
                    self.processq.put([outnum, frame])
                    if self.DEBUG == 2:
                        print("Put a frame in queue for out writer %s"%outnum)
                    #    self.show_frame(frame)
                    time.sleep(self.FPS)
                else:
                    pass
            else: # Check if the streamurl is still having the feed
                retval = self.verifystream(streamurl)
                if retval: # retval is True, so reconnect to the stream...
                    cap = cv2.VideoCapture(streamurl)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 250)
                    if self.DEBUG: # Check incoming frame rate if DEBUG mode is set
                        fps_in = cap.get(cv2.CAP_PROP_FPS)
                        print("Incoming frame rate: %s"%fps_in)
                else: # Stream is not available anymore, so update feed record in DB
                    print("Stream %s is no longer available."%streamurl)
                    curdatetime = datetime.datetime.now()
                    pdbconn = MySQLdb.connect(host=self.dbhost, user=self.dbuser, passwd=self.dbpasswd, db=self.dbname)
                    pcursor = pdbconn.cursor()
                    updatesql = "update feedman_feeds set feedend='%s' where id=%s"%(curdatetime, feedid)
                    if self.DEBUG:
                        print(updatesql)
                    try:
                        pcursor.execute(updatesql)
                        pdbconn.commit()
                    except:
                        print("Could not update db for the feed identified by Id %s"%feedid)
                    pdbconn.close()
                    break # Break out of infinite loop.
        cap.release() # Done!
        if self.DEBUG:
            cv2.destroyAllWindows()

    
    def framewriter(self, outlist):
        isempty = False
        endofrun = False
        while True:
            frame = None
            args = self.processq.get()
            outnum = args[0]
            frame = args[1]
            if outlist.__len__() > outnum:
                out = outlist[outnum]
            else:
                if self.DEBUG == 2:
                    print("Could not get writer %s"%outnum)
                continue
            if frame is not None and out.isOpened():
                out.write(frame)
                #print("Wrote a frame to %s..."%outnum)
                isempty = False
                endofrun = False
            else:
                if self.processq.empty() and not isempty:
                    isempty = True
                elif self.processq.empty() and isempty: # processq queue is empty now and was empty last time
                    print("processq is empty")
                    time.sleep(10) # Sleep for 10 secs.
                    endofrun = True
                elif endofrun and isempty:
                    print("Could not find any frames to process. Quitting")
                    break
        print("Done writing feeds. Quitting.")
        return None


    def show_frame(self, frame):
        cv2.imshow('frame', frame)
        cv2.waitKey(self.FPS_MS)


    def getstreamurlfrompage(self, streampageurl):
        pagerequest = urllib.request.Request(streampageurl, headers=self.httpHeaders)
        try:
            pageresponse = self.opener.open(pagerequest)
            pagecontent = self.__class__._decodeGzippedContent(pageresponse.read())
        except:
            print("Error: %s"%sys.exc_info()[1].__str__())
            pagecontent = ""
        pagePattern = re.compile("\"streamUrl\"\: \"(.*?)\"", re.DOTALL)
        pps = re.search(pagePattern, pagecontent)
        if pps:
            streamurl = pps.groups()[0]
        else:
            streamurl = None
        return streamurl


    def getfeedmetadata(self, pageurl):
        """
        Returns the following metadata as a dict:
        FeedTitle, FeedEventTeam1 (name of participating player(s) separated by commas),
        FeedEventTeam2 (name of participating player(s) separated by commas), FeedStartTime,
        FeedEndTime (both datetime values), FeedEventType (MEN - Singles, WOMEN - Doubles, etc),
        FeedEventResult (name of team that won, both teams in case of tie), FeedStatus
        (live or past, default is live), FeedDeleted (True if deleted, False if not, default
        is False), FeedPath (location/path of feed on the disk), FeedUpdated (datetime val),
        FeedUpdatedUser (User who last updated the feed, default is 0).
        """
        metadata = {}
        pagerequest = urllib.request.Request(pageurl, headers=self.httpHeaders)
        try:
            pageresponse = self.opener.open(pagerequest)
            headers = pageresponse.getheaders()
            #print(headers)
            if "Location" in headers:
                requesturl = headers["Location"]
                pagerequest = urllib.request.Request(requesturl, headers=self.httpHeaders)
                try:
                    pageresponse = self.no_redirect_opener.open(pagerequest)
                except:
                    print ("Error. %s"%sys.exc_info()[1].__str__())
                    return {'FeedTitle' : '', 'FeedEventTeam1' : '', 'FeedEventTeam2' : '', 'FeedStartTime' : '', 'FeedEventType' : ''}
        except:
            print ("Error: %s"%sys.exc_info()[1].__str__())
            return {'FeedTitle' : '', 'FeedEventTeam1' : '', 'FeedEventTeam2' : '', 'FeedStartTime' : '', 'FeedEventType' : ''}
        streampagecontent = self.__class__._decodeGzippedContent(pageresponse.read())
        soup = BeautifulSoup(streampagecontent, features="html.parser")
        htmltagPattern = re.compile("<\/?[^>]+>", re.DOTALL)
        beginspacePattern = re.compile("^\s+")
        endspacePattern = re.compile("\s+$")
        eventtitle, team1, team2, eventtype, startdate, enddate, eventstatus, deleted = "", "", "", "", "", "", "live", 0
        subtitlespan = soup.find("span", {'class' : 'sub_title'})
        if subtitlespan is not None:
            eventtype = subtitlespan.renderContents().decode('utf-8')
            eventtype = eventtype.replace("\n", "").replace("\r", "")
            eventtype = htmltagPattern.sub("", eventtype)
            eventtype = beginspacePattern.sub("", eventtype)
            eventtype = endspacePattern.sub("", eventtype)
        h1tags = soup.find_all("h1")
        if h1tags.__len__() > 0:
            eventtitle = h1tags[0].renderContents().decode('utf-8')
            eventtitle = eventtitle.replace("\n", "").replace("\r", "")
            eventtitle = htmltagPattern.sub("", eventtitle)
            eventtitle = eventtitle.replace("LIVESTREAM:", "")
            eventtitle = beginspacePattern.sub("", eventtitle)
            eventtitle = endspacePattern.sub("", eventtitle)
        datetimediv = soup.find("div", {'class' : 'video_date'})
        if datetimediv is not None:
            datetimecontents = datetimediv.renderContents().decode('utf-8')
            datetimecontents = datetimecontents.replace("\n", "").replace("\r", "")
            datePattern = re.compile("(\d{4}\-\d{1,2}\-\d{1,2})\s+starts\s+at\s+(\d{1,2}\:?\d{0,2})", re.IGNORECASE|re.DOTALL)
            dps = re.search(datePattern, datetimecontents)
            if dps:
                datestr = dps.groups()[0]
                timestr = dps.groups()[1]
                if ":" not in timestr:
                    timestr += ":00:00"
                else:
                    timestr += ":00"
                dtstr = datestr + " " + timestr
                dtstr = htmltagPattern.sub("", dtstr)
                dtstr = beginspacePattern.sub("", dtstr)
                dtstr = endspacePattern.sub("", dtstr)
                startdate = datetime.datetime.strptime(dtstr, "%Y-%m-%d %H:%M:%S")
            else:
                startdate = datetime.datetime.now()
        else:
            startdate = datetime.datetime.now()
        playersspans = soup.find_all("span", {'class' : 'player'})
        if playersspans.__len__() > 0:
            team1 = playersspans[0].renderContents().decode('utf-8')
            team1 = team1.replace("\n", "").replace("\r", "")
            team1 = htmltagPattern.sub("", team1)
            team1 = beginspacePattern.sub("", team1)
            team1 = endspacePattern.sub("", team1)
        if playersspans.__len__() > 1:
            team2 = playersspans[1].renderContents().decode('utf-8')
            team2 = team2.replace("\n", "").replace("\r", "")
            team2 = htmltagPattern.sub("", team2)
            team2 = beginspacePattern.sub("", team2)
            team2 = endspacePattern.sub("", team2)
        metadata['FeedTitle'] = eventtitle
        metadata['FeedEventTeam1'] = team1
        metadata['FeedEventTeam2'] = team2
        metadata['FeedStartTime'] = startdate
        metadata['FeedEventType'] = eventtype
        return metadata


if __name__ == "__main__":
    if sys.argv.__len__() < 2:
        print("Insufficient parameters")
        sys.exit()
    siteurl = sys.argv[1]
    itftennis = VideoBot(siteurl)
    outlist = []
    #t = Thread(target=itftennis.framewriter, args=(outlist,))
    #t.daemon = True
    #t.start()
    # Create a database connection and as associated cursor object. We will handle database operations from main thread only.
    dbconn = MySQLdb.connect(host=itftennis.dbhost, user=itftennis.dbuser, passwd=itftennis.dbpasswd, db=itftennis.dbname)
    cursor = dbconn.cursor()
    feedidlist = []
    while True:
        streampageurls = itftennis.checkforlivestream()
        if streampageurls.__len__() > 0:
            print("Detected %s new live stream(s)... Getting them."%streampageurls.__len__())
            p = Pool(streampageurls.__len__())
            argslist = []
            for streampageurl in streampageurls:
                streamurl = itftennis.getstreamurlfrompage(streampageurl)
                print("Adding %s to list..."%streamurl)
                if streamurl is not None:
                    filename = time.strftime("/home/supmit/work/capturelivefeed/tennisvideos/" + "%Y%m%d%H%M%S",time.localtime())
                    outvideofilename = filename+".avi" # Please change this as per your system.
                    outaudiofilename = filename+".wav"
                    # Now, get feed metadata...
                    metadata = itftennis.getfeedmetadata(streampageurl)
                    # Save metadata in DB
                    feedinsertsql = "insert into feedman_feeds (feedtitle, feedeventteam1, feedeventteam2, feedstart, feedend, eventtype, feedstatus, feedpath, deleted, updatetime, updateuser_id) values ('%s', '%s', '%s', '%s', null, '%s', 'live', '%s', FALSE, '%s', 1)"%(metadata['FeedTitle'], metadata['FeedEventTeam1'], metadata['FeedEventTeam2'], metadata['FeedStartTime'], metadata['FeedEventType'], outvideofilename, datetime.datetime.now()) # The supplied user Id value of 1 is reserved for this script.
                    try:
                        cursor.execute(feedinsertsql)
                        dbconn.commit() # Just in case autocommit is not set.
                    except:
                        print("Error in data insertion to DB: %s\nErroneous SQL: %s"%(sys.exc_info()[1].__str__(), feedinsertsql))
                    try:
                        # Get the Id of the inserted feed
                        feedid = -1
                        feedidsql = "select max(id) from feedman_feeds"
                        cursor.execute(feedidsql)
                        feedrecs = cursor.fetchall()
                        feedid = int(feedrecs[0][0])
                    except:
                        pass # Leave it if we can't get it. We can get it from the management interface.
                    argslist.append([streamurl, outvideofilename, outaudiofilename, feedid]) 
                else:
                    print("Couldn't get the stream url from page")
                #if itftennis.DEBUG: # Let only a single stream be processed for debugging.
                #    break
            p.map(start_AVrecording, argslist)
        time.sleep(itftennis.livestreamcheckinterval)
    #t.join()
    for out in outlist:
        out.release()
    dbconn.close() # Close and keep environment clean.


# How to run: python getlivestream.py https://live.itftennis.com/en/live-streams/
"""
References:
https://en.wikipedia.org/wiki/Video_compression_picture_types
https://www.geeksforgeeks.org/saving-operated-video-from-a-webcam-using-opencv/
https://stackoverflow.com/questions/58293187/opencv-real-time-streaming-video-capture-is-slow-how-to-drop-frames-or-get-sync
https://www.fourcc.org/downloads/
https://stackoverflow.com/questions/55828451/video-streaming-from-ip-camera-in-python-using-opencv-cv2-videocapture
https://stackoverflow.com/questions/55099413/python-opencv-streaming-from-camera-multithreading-timestamps
https://stackoverflow.com/questions/58592291/how-to-capture-multiple-camera-streams-with-opencv
https://www.it-jim.com/blog/practical-aspects-of-real-time-video-pipelines/
"""
# supmit

