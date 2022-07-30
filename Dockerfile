#syntax=docker/dockerfile:1

# Dockerfile for getlivestream.py standalone app

From python:3.6.9

WORKDIR /home/supmit/work/capturelivefeed

MAINTAINER supmit@mail.com

RUN apt-get update
RUN apt-get -y install zsh htop
RUN apt-get install ffmpeg libsm6 libxext6  -y

COPY getlivestream.py .

# In case we need to upgrade pip before running requirements.txt
RUN pip install --upgrade pip

COPY requirements.txt .
RUN chmod 644 requirements.txt
RUN pip install -r requirements.txt
# uwsgi is not included in requirements.txt since it wasn't used during development.
RUN pip install uwsgi

# Need to install PyAudio module - this doesn't get installed by pip (throws error)
#RUN easy_install pyaudio

RUN mkdir tennisvideos
RUN chmod 777 tennisvideos

# Start the scraper
CMD ["python", "getlivestream.py", "https://live.itftennis.com/en/live-streams/"]


