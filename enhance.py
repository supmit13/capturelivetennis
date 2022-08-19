import os, sys, re, time
import datetime

# load the required packages
import cv2
import numpy as np


def enhance(mp4_or_avi_input, mp4_or_avi_output, fps=25, fourcc=cv2.VideoWriter_fourcc(*'XVID'), size=(1920, 1080), DEBUG=False):
    cap = cv2.VideoCapture(mp4_or_avi_input)
    out = cv2.VideoWriter(mp4_or_avi_output, fourcc, fps, size)
    cap.set(cv2.CAP_PROP_FPS, fps)
    #cap.set(cv2.CAP_PROP_BUFFERSIZE, 30) # Set buffersize=30 frames
    fsrcnn_model = "/home/supmit/work/capturelivefeed/resources/models/FSRCNN_x3.pb"
    modelname = fsrcnn_model.split(os.path.sep)[-1].split("_")[0].lower()
    modelscale = fsrcnn_model.split("_x")[-1]
    modelscale = int(modelscale[:modelscale.find(".")])
    print("%s %s"%(modelname, modelscale))
    sr = cv2.dnn_superres.DnnSuperResImpl_create()
    sr.readModel(fsrcnn_model)
    sr.setModel(modelname, modelscale)
    lastread = time.time()
    curframeid = 0
    while True:
        if cap.isOpened():
            ret, frame = cap.read()
            if ret == False:
                if DEBUG:
                    print("Could not read frame")
                # Need to do something... possibly a good idea is to reopen the cap if we did a successful read in the last 30 seconds.
                now = time.time()
                if now - lastread > 30:
                    break
                else:
                    cap = cv2.VideoCapture(mp4_or_avi_input)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, curframeid) # Go to the last frame read.
                    cap.set(cv2.CAP_PROP_FPS, fps)
                    #cap.set(cv2.CAP_PROP_BUFFERSIZE, 30)
            else:
                if DEBUG:
                    print("Read a frame with Id %s"%curframeid)
                lastread = time.time()
                curframeid += 1
                # Process the frame        
                frame_resized = cv2.resize(frame, size, fx = 0, fy = 0, interpolation = cv2.INTER_CUBIC)
                frame_sharp = sr.upsample(frame_resized)  
                # Write the frame back
                if out.isOpened():
                    out.write(frame_sharp)
                    if DEBUG:
                        print("Wrote a frame with Id %s"%curframeid)
                else:
                    if DEBUG:
                        print("VideoWriter object has closed. Need to re-process the video")
                    break
        else:
            if DEBUG:
                print("cap is closed")
            now = time.time()
            if now - lastread > 30:
                break
            else:
                cap = cv2.VideoCapture(mp4_or_avi_input)
                cap.set(cv2.CAP_PROP_POS_FRAMES, curframeid) # Go to the last frame read.
                cap.set(cv2.CAP_PROP_FPS, fps)
                #cap.set(cv2.CAP_PROP_BUFFERSIZE, 30)
    cap.release() # Done!
    out.release()


if __name__ == "__main__":
    enhance("/home/supmit/work/capturelivefeed/tennisvideos/20220817154915_combined.avi", "/home/supmit/work/capturelivefeed/tennisvideos/20220817154915_final.avi")
    print("Done")


