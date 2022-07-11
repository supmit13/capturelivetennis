#!/usr/bin/env python
# -*- coding: utf-8 -*-
# VideoRecorder.py

from __future__ import print_function, division
import numpy as np
import cv2
import pyaudio
import wave
import threading
import time
import subprocess
import os

class VideoRecorder():  
    "Video class based on openCV"
    def __init__(self, streamsource, outvideofile, feedid):
        self.open = True
        self.streamsource = streamsource
        self.fps = 25
        self.fourcc = "MJPG" # capture images (with no decrease in speed over time; testing is required)
        self.frameSize = (320, 180) # video formats and sizes also depend and vary according to the camera used
        self.video_filename = outvideofile
        self.video_cap = cv2.VideoCapture(streamsource)
        self.video_writer = cv2.VideoWriter_fourcc(*'MJPG')
        self.video_out = cv2.VideoWriter(self.video_filename, self.video_writer, self.fps, self.frameSize)
        self.frame_counts = 1
        self.start_time = time.time()
        self.feedid = feedid

    def record(self):
        "Video starts being recorded"
        # counter = 1
        timer_start = time.time()
        timer_current = 0
        while self.open:
            ret, video_frame = self.video_cap.read()
            if ret:
                self.video_out.write(video_frame)
                # print(str(counter) + " " + str(self.frame_counts) + " frames written " + str(timer_current))
                self.frame_counts += 1
                # counter += 1
                # timer_current = time.time() - timer_start
                time.sleep(1/self.fps)
                # gray = cv2.cvtColor(video_frame, cv2.COLOR_BGR2GRAY)
                # cv2.imshow('video_frame', gray)
                # cv2.waitKey(1)
            else:
                retval = self.verifystream()
                if not retval:
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
                    break

    def verifystream(self):
        cap = cv2.VideoCapture(self.streamsource)
        if not self.video_cap.isOpened():
            return False
        self.video_cap.release()
        return True

    def stop(self):
        "Finishes the video recording therefore the thread too"
        if self.open:
            self.open=False
            self.video_out.release()
            self.video_cap.release()
            cv2.destroyAllWindows()

    def start(self):
        "Launches the video recording function using a thread"
        video_thread = threading.Thread(target=self.record)
        video_thread.start()

class AudioRecorder():
    "Audio class based on pyAudio and Wave"
    def __init__(self, streamsource, outaudiofile):
        self.open = True
        self.rate = 44100
        self.frames_per_buffer = 1024
        self.streamsource = streamsource
        self.channels = 2
        self.format = pyaudio.paInt16
        self.audio_filename = outaudiofile
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=self.format, channels=self.channels, rate=self.rate, input=True, frames_per_buffer=self.frames_per_buffer)
        self.audio_frames = []

    def record(self):
        "Audio starts being recorded"
        self.stream.start_stream()
        while self.open:
            data = self.stream.read(self.frames_per_buffer) 
            self.audio_frames.append(data)
            if not self.open:
                break

    def stop(self):
        "Finishes the audio recording therefore the thread too"
        if self.open:
            self.open = False
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()
            waveFile = wave.open(self.audio_filename, 'wb')
            waveFile.setnchannels(self.channels)
            waveFile.setsampwidth(self.audio.get_sample_size(self.format))
            waveFile.setframerate(self.rate)
            waveFile.writeframes(b''.join(self.audio_frames))
            waveFile.close()

    def start(self):
        "Launches the audio recording function using a thread"
        audio_thread = threading.Thread(target=self.record)
        audio_thread.start()

def start_AVrecording(argslist):
    streamsource, outvideofile, outaudiofile, feedid = argslist[0], argslist[1], argslist[2], argslist[3]
    global video_thread
    global audio_thread
    video_thread = VideoRecorder(streamsource, outvideofile, feedid)
    audio_thread = AudioRecorder(streamsource, outaudiofile)
    audio_thread.start()
    video_thread.start()
    return (outvideofile,outaudiofile)

def start_video_recording(streamsource):
    global video_thread
    video_thread = VideoRecorder(streamsource)
    video_thread.start()
    return filename

def start_audio_recording(streamsource, outfilename="test"):
    global audio_thread
    audio_thread = AudioRecorder(streamsource)
    audio_thread.start()
    return filename

def stop_AVrecording(filename="test"):
    audio_thread.stop() 
    frame_counts = video_thread.frame_counts
    elapsed_time = time.time() - video_thread.start_time
    recorded_fps = frame_counts / elapsed_time
    print("total frames " + str(frame_counts))
    print("elapsed time " + str(elapsed_time))
    print("recorded fps " + str(recorded_fps))
    video_thread.stop() 

    # Makes sure the threads have finished
    while threading.active_count() > 1:
        time.sleep(1)

    # Merging audio and video signal
    if abs(recorded_fps - 6) >= 0.01:    # If the fps rate was higher/lower than expected, re-encode it to the expected
        print("Re-encoding")
        cmd = "ffmpeg -r " + str(recorded_fps) + " -i temp_video.avi -pix_fmt yuv420p -r 6 temp_video2.avi"
        subprocess.call(cmd, shell=True)
        print("Muxing")
        cmd = "ffmpeg -y -ac 2 -channel_layout stereo -i temp_audio.wav -i temp_video2.avi -pix_fmt yuv420p " + filename + ".avi"
        subprocess.call(cmd, shell=True)
    else:
        print("Normal recording\nMuxing")
        cmd = "ffmpeg -y -ac 2 -channel_layout stereo -i temp_audio.wav -i temp_video.avi -pix_fmt yuv420p " + filename + ".avi"
        subprocess.call(cmd, shell=True)
        print("..")

def file_manager(filename="test"):
    "Required and wanted processing of final files"
    local_path = os.getcwd()
    if os.path.exists(str(local_path) + "/temp_audio.wav"):
        os.remove(str(local_path) + "/temp_audio.wav")
    if os.path.exists(str(local_path) + "/temp_video.avi"):
        os.remove(str(local_path) + "/temp_video.avi")
    if os.path.exists(str(local_path) + "/temp_video2.avi"):
        os.remove(str(local_path) + "/temp_video2.avi")
    # if os.path.exists(str(local_path) + "/" + filename + ".avi"):
    #     os.remove(str(local_path) + "/" + filename + ".avi")

"""
if __name__ == '__main__':
    start_AVrecording(streamsource, outvideofile, outaudiofile)
    time.sleep(5)
    stop_AVrecording()
    file_manager()
"""



