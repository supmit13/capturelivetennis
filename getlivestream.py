# -*- coding: utf-8 -*-
import os, sys, re
import urllib, urllib.request
from bs4 import BeautifulSoup
import unicodedata
import io
import gzip
import time
import signal, readchar
import simplejson as json
import datetime
import string
import requests
from urllib.parse import urlencode, quote_plus, urlparse
import html
import numpy as np
import cv2
#import pyaudio
import ffmpeg
import subprocess
import wave
from multiprocessing import Process, Pool, Queue
import multiprocessing as mp
from threading import Thread
import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb
#import psycopg2





# Basic utility functions and variables
partialUrlPattern = re.compile("^/\w+")

def decodeHtmlEntities(content):
    entitiesDict = {'&nbsp;' : ' ', '&quot;' : '"', '&lt;' : '<', '&gt;' : '>', '&amp;' : '&', '&apos;' : "'", '&#160;' : ' ', '&#60;' : '<', '&#62;' : '>', '&#38;' : '&', '&#34;' : '"', '&#39;' : "'"}
    for entity in entitiesDict.keys():
        content = content.replace(entity, entitiesDict[entity])
    return(content)


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

# Signal handler to handle ctrl+c interrupt
def handler(signum, frame):
    msg = "Ctrl-c was pressed. Do you really want to exit? y/n "
    print(msg, end="", flush=True)
    res = readchar.readchar()
    if res == 'y':
        print("")
        exit(1)
    else:
        print("", end="\n", flush=True)
        print(" " * len(msg), end="", flush=True) # clear the printed line
        print("    ", end="\n", flush=True)
 


# Redirects handler, in case we need to handle HTTP redirects.
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


# Class to handle video/audio capture and write to a file on disk. 
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
        self.statusq = []
        for i in range(10000):
            self.statusq.append(1) # Default status is active
        self.size = (320, 180)
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        # itftennis streams have a rate of 25 fps.
        self.FPS = 1/25 # This is the delay that would be applied after every read(). This would 'normalize' the frame rate and handle frame loss jitters.
        self.FPS_MS = int(self.FPS * 1000) # Same delay as above, in milliseconds.
        # Audio parameters:
        self.rate = 44100
        self.frames_per_buffer = 1024
        self.channels = 1
        #self.format = pyaudio.paInt16
        self.devices_state = {}
        # Other params
        self.DEBUG = 1 # TODO: Remember to set it to 0 (or False) before deploying somewhere.
        self.dbuser = "feeduser"
        self.dbpasswd = "feedpasswd"
        self.dbname = "feeddb"
        self.dbhost = "localhost" # Since this will be connecting to the mysql db inside the docker container
        self.dbport = 3306
        #self.dbport = 5432 # for postgresql
        

    def checkforlivestream(self):
        self.pageRequest = urllib.request.Request(self.siteUrl, headers=self.httpHeaders)
        try:
            self.pageResponse = self.opener.open(self.pageRequest)
            headers = self.pageResponse.getheaders()
            if "Location" in headers:
                self.requestUrl = headers["Location"]
                self.pageRequest = urllib.request.Request(self.requestUrl, headers=self.httpHeaders)
                try:
                    self.pageResponse = self.no_redirect_opener.open(self.pageRequest)
                except:
                    print ("Error. %s"%sys.exc_info()[1].__str__())
                    return []
        except:
            print ("Error: %s"%sys.exc_info()[1].__str__())
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


    def verifystream(self, videolink):
        cap = cv2.VideoCapture(videolink)
        if not cap.isOpened():
            return False
        cap.release()
        return True


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


    def captureaudiostream_pyaudio(self, stream, twf):
        while True:
            try:
                audiodata = stream.read(self.frames_per_buffer)
                twf.writeframes(audiodata)
            except:
                print("Error reading audio stream: %s"%sys.exc_info()[1].__str__())
                break
        return None # Just to satisfy the Thread module's need for explicitly ending the thread


    def captureaudiostream(self, streamurl, tempaudiofile, qctr):
        try:
            info = ffmpeg.probe(streamurl, select_streams='a')
        except:
            sys.stderr.buffer.write(sys.exc_info()[1].__str__())
            sys.exit() # End the thread.
        streams = info.get('streams', [])
        if len(streams) == 0:
            print('There are no streams available')
            sys.exit()
        stream = streams[0]
        if stream.get('codec_type') != 'audio':
            for stream in streams:
                if stream.get('codec_type') != 'audio':
                    continue
                else:
                    break
        channels = stream['channels']
        samplerate = float(stream['sample_rate'])
        blocksize = 1024
        buffersize = 20
        try:
            print('Opening stream ...')
            #channels = 1 # Hard code to 1
            process = ffmpeg.input(streamurl).output('pipe:', format='s16le', acodec='pcm_s16le', ac=channels, ar=samplerate, loglevel='quiet',).run_async(pipe_stdout=True)
            read_size = blocksize * channels * 8
            tmpframes = None
            if os.path.exists(tempaudiofile):
                ftmp = wave.open(tempaudiofile, "rb")
                frmcnt = ftmp.getnframes()
                tmpframes = ftmp.readframes(frmcnt)
                ftmp.close()
            twf = wave.open(tempaudiofile, 'wb') # Opening in append mode as we might need to append if the stream is dropped
            twf.setnchannels(channels)
            twf.setsampwidth(2) # Is this good enough?
            twf.setframerate(samplerate)
            if tmpframes is not None:
                twf.writeframes(tmpframes)
            lastread = time.time()
            while True:
                if self.statusq[qctr] == 0:
                    break
                aframes = process.stdout.read(read_size)
                if aframes.__len__() == 0:
                    time.sleep(5) # A five second sleep.
                    curtime = time.time()
                    if curtime - lastread > 60: # We haven't received a frame for the past 1 minute
                        try:
                            process = ffmpeg.input(streamurl).output('pipe:', format='s16le', acodec='pcm_s16le', ac=channels, ar=samplerate, loglevel='quiet',).run_async(pipe_stdout=True) # So we try to reconnect...
                            aframes = process.stdout.read(read_size) # Try to read one more time...
                            if aframes.__len__() == 0: # If we still can't get any frames...
                                break  # ... then quit.
                        except:
                            break # ... failing which, we break.
                        if not process: # If we somehow failed to create a stream, we quit.
                            break
                    continue
                lastread = time.time()
                twf.writeframes(aframes)
            twf.close()
        except Exception as e:
            print(type(e).__name__ + ': ' + str(e))
            sys.exit()
        return None


    def capturelivestream(self, argslist):
        streamurl, outnum, feedid, outfilename = argslist[0], argslist[1], argslist[2], argslist[3]
        cap = cv2.VideoCapture(streamurl)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 30)
        # check the incoming frame rate if we are in DEBUG mode
        if self.DEBUG:
            fps_in = cap.get(cv2.CAP_PROP_FPS)
            print("Incoming frame rate: %s"%fps_in)
        #cap.set(cv2.CAP_PROP_FPS, 20) # Should we alter the frames rate and set it to 20 fps?
        # Get audio stream...
        ta = None
        fpath = os.path.dirname(outfilename)
        fnamefext = os.path.basename(outfilename)
        fname = fnamefext.split(".")[0]
        tempaudiofile = fpath + os.path.sep + fname + ".wav"
        self.statusq[outnum] = 1
        ta = Thread(target=self.captureaudiostream, args=(streamurl, tempaudiofile, outnum))
        ta.daemon = True
        ta.start()
        lastcaptured = time.time()
        while True:
            if cap.isOpened():
                ret, frame = cap.read()
                if ret == True:
                    lastcaptured = time.time()
                    self.processq.put([outnum, frame])
                    if self.DEBUG == 2:
                        print("Put a frame in queue for out writer %s"%outnum)
                    #    self.show_frame(frame)
                    time.sleep(self.FPS)
                else:
                    if self.DEBUG:
                        print("Could not read frame for feed ID %s"%feedid)
                    t = time.time()
                    if t - lastcaptured > 5: # If the frames can't be read for more than 5 seconds, reopen the stream
                        print("Reopening feed identified by feed ID %s"%feedid)
                        cap.release()
                        cap = cv2.VideoCapture(streamurl)
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 30)
                    continue
            else: # Check if the streamurl is still having the feed
                if self.DEBUG:
                    print("Feed identified by ID %s has closed. Verifying availability of feed."%feedid)
                retval = self.verifystream(streamurl)
                if retval: # retval is True, so reconnect to the stream...
                    cap = cv2.VideoCapture(streamurl)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 30)
                    if self.DEBUG: # Check incoming frame rate if DEBUG mode is set
                        fps_in = cap.get(cv2.CAP_PROP_FPS)
                        print("Feed %s reconnected. Incoming frame rate: %s"%(feedid, fps_in))
                    # Reconnect audio stream...
                    if ta is not None:
                        ta.join() # End the previous thread
                    ta = Thread(target=self.captureaudiostream, args=(streamurl, tempaudiofile, outnum))
                    ta.daemon = True
                    ta.start()
                else: # Stream is not available anymore, so update feed record in DB
                    if self.DEBUG:
                        print("Stream %s is no longer available."%streamurl)
                    curdatetime = datetime.datetime.now()
                    pdbconn = MySQLdb.connect(host=self.dbhost, port=self.dbport, user=self.dbuser, passwd=self.dbpasswd, db=self.dbname)
                    #pdbconn = psycopg2.connect(database=self.dbname, user=self.dbuser, password=self.dbpasswd, host=self.dbhost, port=self.dbport)
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
        # End audio thread.
        self.statusq[outnum] = 0 # Signal the audio capture thread to quit.
        if ta is not None:
            if self.DEBUG:
                print("Joining thread... ")
            ta.join()
            if self.DEBUG:
                print("Thread joined... ")
        if not os.path.isdir(fpath+os.path.sep+"final"):
            os.makedirs(fpath+os.path.sep+"final")
        combinedfile = fpath + os.path.sep + "final" + os.path.sep + fname + "_combined.avi"
        print("Normal recording\nMuxing")
        muxcmd = "ffmpeg -y -ac 1 -channel_layout mono -i %s -i %s -pix_fmt yuv420p %s"%(tempaudiofile, outfilename, combinedfile)
        subprocess.call(muxcmd, shell=True)
        # Exit process
        #sys.exit()
        return None


    def capturelivestream_pyaudio(self, argslist):
        streamurl, outnum, feedid, deviceindex, outfilename = argslist[0], argslist[1], argslist[2], argslist[3], argslist[4]
        cap = cv2.VideoCapture(streamurl)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 30)
        # check the incoming frame rate if we are in DEBUG mode
        if self.DEBUG:
            fps_in = cap.get(cv2.CAP_PROP_FPS)
            print("Incoming frame rate: %s"%fps_in)
        #cap.set(cv2.CAP_PROP_FPS, 20) # Should we alter the frames rate and set it to 20 fps?
        # Get audio stream, only if we received a valid device index
        ta = None
        if deviceindex >= 0:
            audio = pyaudio.PyAudio()
            #stream = audio.open(input_device_index=deviceindex, format=self.format, channels=self.channels, rate=self.rate, input=True, frames_per_buffer=self.frames_per_buffer)
            stream = audio.open(format=self.format, channels=self.channels, rate=self.rate, input=True, frames_per_buffer=self.frames_per_buffer)
            stream.start_stream()
            # Create a temporary file to write the frames periodically
            fpath = os.path.dirname(outfilename)
            fnamefext = os.path.basename(outfilename)
            fname = fnamefext.split(".")[0]
            tempaudiofile = fpath + os.path.sep + fname + ".wav"
            twf = wave.open(tempaudiofile, 'wb')
            twf.setnchannels(self.channels)
            twf.setsampwidth(audio.get_sample_size(self.format))
            twf.setframerate(self.rate)
            # Read audio since we received a valid device index. Start a thread to block on audio read.
            ta = Thread(target=self.captureaudiostream, args=(stream, twf))
            ta.daemon = True
            ta.start()
        lastcaptured = time.time()
        while True:
            if cap.isOpened():
                ret, frame = cap.read()
                if ret == True:
                    lastcaptured = time.time()
                    self.processq.put([outnum, frame])
                    if self.DEBUG == 2:
                        print("Put a frame in queue for out writer %s"%outnum)
                    #    self.show_frame(frame)
                    time.sleep(self.FPS)
                else:
                    if self.DEBUG:
                        print("Could not read frame for feed ID %s"%feedid)
                    t = time.time()
                    if t - lastcaptured > 5: # If the frames can't be read for more than 5 seconds, reopen the stream
                        print("Reopening feed identified by feed ID %s"%feedid)
                        cap.release()
                        cap = cv2.VideoCapture(streamurl)
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 30)
                    continue
            else: # Check if the streamurl is still having the feed
                if self.DEBUG:
                    print("Feed identified by ID %s has closed. Verifying availability of feed."%feedid)
                retval = self.verifystream(streamurl)
                if retval: # retval is True, so reconnect to the stream...
                    cap = cv2.VideoCapture(streamurl)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 30)
                    if self.DEBUG: # Check incoming frame rate if DEBUG mode is set
                        fps_in = cap.get(cv2.CAP_PROP_FPS)
                        print("Feed %s reconnected. Incoming frame rate: %s"%(feedid, fps_in))
                    # Reconnect audio stream...
                    ta = Thread(target=self.captureaudiostream, args=(stream, twf))
                    ta.daemon = True
                    ta.start()
                else: # Stream is not available anymore, so update feed record in DB
                    if self.DEBUG:
                        print("Stream %s is no longer available."%streamurl)
                    curdatetime = datetime.datetime.now()
                    pdbconn = MySQLdb.connect(host=self.dbhost, port=self.dbport, user=self.dbuser, passwd=self.dbpasswd, db=self.dbname)
                    #pdbconn = psycopg2.connect(database=self.dbname, user=self.dbuser, password=self.dbpasswd, host=self.dbhost, port=self.dbport)
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
        # End audio stream if we opened one, i.e., if we received a valid device index.
        if deviceindex >= 0:
            if ta is not None:
                if self.DEBUG:
                    print("Joining thread... ")
                ta.join()
            if self.DEBUG:
                print("Closing strean... ")
            stream.stop_stream()
            stream.close()
            audio.terminate()
            twf.close() # Temporary audio file closed.
            combinedfile = fpath + os.path.sep + fname + "_combined.avi"
            print("Normal recording\nMuxing")
            muxcmd = "ffmpeg -y -ac 1 -channel_layout mono -i %s -i %s -pix_fmt yuv420p %s"%(tempaudiofile, outfilename, combinedfile)
            subprocess.call(muxcmd, shell=True)
            self.devices_state[str(deviceindex)] = 0 # Device status is set to 0 - free
            #print("..")
        if self.DEBUG:
            cv2.destroyAllWindows()
        # Exit process
        sys.exit()

    
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
        if playersspans.__len__() > 2:
            team1_2 = playersspans[1].renderContents().decode('utf-8')
            team1_2 = team1_2.replace("\n", "").replace("\r", "")
            team1_2 = htmltagPattern.sub("", team1_2)
            team1_2 = beginspacePattern.sub("", team1_2)
            team1_2 = endspacePattern.sub("", team1_2)
            team1 = team1 + ", " + team1_2
            team2 = playersspans[2].renderContents().decode('utf-8')
            team2 = team2.replace("\n", "").replace("\r", "")
            team2 = htmltagPattern.sub("", team2)
            team2 = beginspacePattern.sub("", team2)
            team2 = endspacePattern.sub("", team2)
            if playersspans.__len__() > 3:
                team2_2 = playersspans[3].renderContents().decode('utf-8')
                team2_2 = team2_2.replace("\n", "").replace("\r", "")
                team2_2 = htmltagPattern.sub("", team2_2)
                team2_2 = beginspacePattern.sub("", team2_2)
                team2_2 = endspacePattern.sub("", team2_2)
                team2 = team2 + ", " + team2_2
        else:
            team2 = ""
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
    signal.signal(signal.SIGINT, handler)
    siteurl = sys.argv[1]
    itftennis = VideoBot(siteurl)
    outlist = []
    t = Thread(target=itftennis.framewriter, args=(outlist,))
    t.daemon = True
    t.start()
    # Create a database connection and as associated cursor object. We will handle database operations from main thread only.
    dbconn = MySQLdb.connect(host=itftennis.dbhost, port=itftennis.dbport, user=itftennis.dbuser, passwd=itftennis.dbpasswd, db=itftennis.dbname)
    #dbconn = psycopg2.connect(database=itftennis.dbname, user=itftennis.dbuser, password=itftennis.dbpasswd, host=itftennis.dbhost, port=itftennis.dbport)
    cursor = dbconn.cursor()
    feedidlist = []
    vidsdict = {}
    streampattern = re.compile("\?vid=(\d+)$")
    processeslist = []
    while True:
        streampageurls = itftennis.checkforlivestream()
        if itftennis.DEBUG:
            print("Checking for new urls...")
            print(streampageurls.__len__())
        if streampageurls.__len__() > 0:
            argslist = []
            newurlscount = 0
            for streampageurl in streampageurls:
                sps = re.search(streampattern, streampageurl)
                if sps:
                    streamnum = sps.groups()[0]
                    if streamnum not in vidsdict.keys(): # Check if this stream has already been processed.
                        vidsdict[streamnum] = 1
                        newurlscount += 1
                    else:
                        continue
                else:
                    continue
                print("Detected new live stream... Getting it.")
                streamurl = itftennis.getstreamurlfrompage(streampageurl)
                print("Adding %s to list..."%streamurl)
                if streamurl is not None:
                    outfilename = time.strftime("./tennisvideos/" + "%Y%m%d%H%M%S",time.localtime())+".avi" # Please change this as per your system.
                    fpath = os.path.dirname(outfilename)
                    fnamefext = os.path.basename(outfilename)
                    fname = fnamefext.split(".")[0]
                    combinedfile = fpath + os.path.sep + "final" + os.path.sep + fname + "_combined.avi"
                    out = cv2.VideoWriter(outfilename, itftennis.fourcc, 1/itftennis.FPS, itftennis.size)
                    outlist.append(out) # Save it in the list and take down the number for usage in framewriter
                    outnum = outlist.__len__() - 1
                    # Now, get feed metadata...
                    metadata = itftennis.getfeedmetadata(streampageurl)
                    # Save metadata in DB
                    feedinsertsql = "insert into feedman_feeds (feedtitle, feedeventteam1, feedeventteam2, feedstart, feedend, eventtype, feedstatus, feedpath, deleted, updatetime, updateuser_id) values ('%s', '%s', '%s', '%s', null, '%s', 'live', '%s', FALSE, '%s', 1)"%(metadata['FeedTitle'], metadata['FeedEventTeam1'], metadata['FeedEventTeam2'], metadata['FeedStartTime'], metadata['FeedEventType'], combinedfile, datetime.datetime.now()) # The supplied user Id value of 1 is reserved for this script.
                    try:
                        cursor.execute(feedinsertsql)
                        dbconn.commit() # Just in case autocommit is not set.
                    except:
                        print("Error in data insertion to DB: %s\nErroneous SQL: %s"%(sys.exc_info()[1].__str__(), feedinsertsql))
                    feedid = -1
                    try:
                        # Get the Id of the inserted feed
                        feedidsql = "select max(id) from feedman_feeds"
                        cursor.execute(feedidsql)
                        feedrecs = cursor.fetchall()
                        feedid = int(feedrecs[0][0])
                    except:
                        pass # Leave it if we can't get it. We can get it from the management interface.
                    argslist.append([streamurl, outnum, feedid, outfilename])   
                else:
                    print("Couldn't get the stream url from page")
            if newurlscount > 0:
                #p = Pool(newurlscount)
                #p.map(itftennis.capturelivestream, argslist) 
                # With the above code the main process stalls. Should be investigated later.
                for args in argslist:
                    p = Process(target=itftennis.capturelivestream, args=(args,))
                    p.start()
                    processeslist.append(p)
                    if itftennis.DEBUG:
                        print("Started process with args %s"%args)
                print("Created processes, continuing now...")
                continue
        time.sleep(itftennis.livestreamcheckinterval)
    t.join()
    for out in outlist:
        out.release()
    dbconn.close() # Close and keep environment clean.


"""
References:
https://ffmpeg.org/ffmpeg-all.html
https://en.wikipedia.org/wiki/Video_compression_picture_types
https://www.geeksforgeeks.org/saving-operated-video-from-a-webcam-using-opencv/
https://stackoverflow.com/questions/58293187/opencv-real-time-streaming-video-capture-is-slow-how-to-drop-frames-or-get-sync
https://www.fourcc.org/downloads/
https://stackoverflow.com/questions/55828451/video-streaming-from-ip-camera-in-python-using-opencv-cv2-videocapture
https://stackoverflow.com/questions/55099413/python-opencv-streaming-from-camera-multithreading-timestamps
https://stackoverflow.com/questions/58592291/how-to-capture-multiple-camera-streams-with-opencv
https://www.it-jim.com/blog/practical-aspects-of-real-time-video-pipelines/
https://code-maven.com/catch-control-c-in-python
https://www.baeldung.com/linux/run-script-on-startup
https://stackoverflow.com/questions/36894315/how-to-select-a-specific-input-device-with-pyaudio
https://stackoverflow.com/questions/48561981/activate-python-virtualenv-in-dockerfile
https://www.docker.com/blog/containerized-python-development-part-1/
https://stackoverflow.com/questions/72468361/docker-cant-find-python-venv-executable
https://blog.carlesmateo.com/2021/07/07/a-small-python-mysql-docker-program-as-a-sample/
https://stackoverflow.com/questions/27947865/docker-how-to-restart-process-inside-of-container
https://towardsdatascience.com/extracting-audio-from-video-using-python-58856a940fd
https://kkroening.github.io/ffmpeg-python/
"""
# Dev: Supriyo Mitra
# Date: 28-07-2022
# Run: python getlivestream.py https://live.itftennis.com/en/live-streams/

