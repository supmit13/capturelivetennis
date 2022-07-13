from threading import Thread
import cv2
import multiprocessing as mp

class VideoWritingThreading(object):
    def __init__(self, src=0):
        # Create a VideoCapture object
        self.capture = cv2.VideoCapture(src)

        # Default resolutions of the frame are obtained (system dependent)
        self.frame_width = int(self.capture.get(3))
        self.frame_height = int(self.capture.get(4))

        # Set up codec and output video settings
        self.codec = cv2.VideoWriter_fourcc(*'XVID')
        self.output_video = cv2.VideoWriter('/home/supmit/work/capturelivefeed/tennisvideos/output2.avi', self.codec, 25, (self.frame_width, self.frame_height))
        self.framenumber = 0
        self.lastframenumberwritten = 0
        mgr = mp.Manager()
        self.processq = mgr.Queue(maxsize=10000)
        # Start the thread to read frames from the video stream
        self.thread = Thread(target=self.update, args=())
        self.thread.daemon = True
        self.thread.start()

    def update(self):
        # Read the next frame from the stream in a different thread
        while True:
            if self.capture.isOpened():
                (self.status, self.frame) = self.capture.read()
                if self.status == True:
                    self.framenumber += 1
                    self.processq.put(self.frame)

    def show_frame(self):
        # Display frames in main program
        if self.status:
            cv2.imshow('frame', self.frame)

        # Press Q on keyboard to stop recording
        key = cv2.waitKey(1)
        if key == ord('q'):
            self.capture.release()
            self.output_video.release()
            cv2.destroyAllWindows()
            exit(1)

    def save_frame(self):
        # Save obtained frame into video output file
        if self.lastframenumberwritten < self.framenumber:
            frame = self.processq.get()
            self.output_video.write(frame)
            self.lastframenumberwritten += 1
            print("Wrote frame number %s"%self.lastframenumberwritten)

if __name__ == '__main__':
    capture_src = 'https://lc-live-http.akamaized.net/at/14879/2450989/mobile/master_delayed.m3u8?cid=14879&mid=34675721&ecid=2450989&pid=6&dtid=1&sid=727479094321&hdnts=ip=2401:4900:1c5d:4175:9cbd:4f8:920d:b415~exp=1657814473~acl=%2Fat%2F14879%2F2450989%2Fmobile%2F%2A~hmac=efabd3955e67167d90e9f06fcbbc4736e3ab618f00f5cbb5acd8d1ba013bbf18'
    video_writing = VideoWritingThreading(capture_src)
    while True:
        try:
            #video_writing.show_frame()
            video_writing.save_frame()
        except AttributeError:
            pass


""" {
    "streamUrl": "https://lc-live-http.akamaized.net/at/14879/2450989/mobile/master_delayed.m3u8?cid=14879&mid=34675721&ecid=2450989&pid=6&dtid=1&sid=727479094321&hdnts=ip=2401:4900:1c5d:4175:9cbd:4f8:920d:b415~exp=1657814473~acl=%2Fat%2F14879%2F2450989%2Fmobile%2F%2A~hmac=efabd3955e67167d90e9f06fcbbc4736e3ab618f00f5cbb5acd8d1ba013bbf18",
    "isLiveStream": true,
    "codecs": {
        "vcodec": "avc1.42c00d",
        "acodec": "mp4a.40.5"
    },
    "playState": "playing",
    "resolution": "320x180",
    "playbackrate": 1,
    "quality": 375.475,
    "currentTime": 96.457067,
    "fps": null,
    "droppedFrames": null,
    "volume": 50
} """



