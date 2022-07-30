<<<<<<< HEAD
#syntax=docker/dockerfile:1

# Dockerfile for getlivestream.py standalone app

From python:3.6.9

WORKDIR /home/supmit/work/capturelivefeed

MAINTAINER supmit@mail.com

RUN apt-get update
RUN apt-get -y install zsh htop
RUN apt-get install ffmpeg libsm6 libxext6  -y

COPY getlivestream.py .
=======
# syntax=docker/dockerfile:1

# Dockerfile for getlivestream.py standalone app
# getlivestream.py is a component of "capturetennisfeed" suite.

FROM ubuntu:18.04

RUN apt-get update
RUN apt-get -y install zsh htop

# Set up global dependencies - mysql container
#From mysql
#ENV MYSQL_ROOT_PASSWORD spmprx
#ADD db_install.sql /docker-entrypoint-initdb.d

WORKDIR /home/supmit/work/capturelivefeed

COPY feeddb.sql .
COPY db_install.sh .
COPY setup_nginx.sh .
COPY mysqld.cnf .
COPY nginx.conf .

RUN chmod 755 db_install.sh
RUN ./db_install.sh

# Start mysql server (mysqld)
CMD ["/etc/init.d/mysql", "start"]

EXPOSE 33060

# Set up global dependencies - nginx container
RUN chmod 755 setup_nginx.sh
RUN ./setup_nginx.sh

CMD ["/etc/init.d/nginx", "start"]

EXPOSE 8001

From python:3.6.9 AS builder

MAINTAINER supmit@mail.com

# Set WORKDIR in python image
WORKDIR /home/supmit/work/capturelivefeed

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
>>>>>>> e1b8464e9c9a6b539a8d213a7bcea7099fc711e4

# In case we need to upgrade pip before running requirements.txt
RUN pip install --upgrade pip

COPY requirements.txt .
RUN chmod 644 requirements.txt
RUN pip install -r requirements.txt
# uwsgi is not included in requirements.txt since it wasn't used during development.
RUN pip install uwsgi

# Need to install PyAudio module - this doesn't get installed by pip (throws error)
#RUN easy_install pyaudio

<<<<<<< HEAD
=======
COPY getlivestream.py .
#COPY init_getls.sh .

>>>>>>> e1b8464e9c9a6b539a8d213a7bcea7099fc711e4
RUN mkdir tennisvideos
RUN chmod 777 tennisvideos

# Start the scraper
CMD ["python", "getlivestream.py", "https://live.itftennis.com/en/live-streams/"]

<<<<<<< HEAD
=======
# Run image as: docker run -it --rm -v $(pwd)/tennisvideos:/home/supmit/work/capturelivefeed/tennisvideos capturetennisfeed --add-host="livestreamhost:192.168.1.11"
# Run this as: docker build -t capturetennisfeed .
# docker run -it -d --privileged=true capturetennisfeed /sbin/init
# docker run --privileged -v /run/systemd/system:/run/systemd/system -v /var/run/dbus/system_bus_socket:/var/run/dbus/system_bus_socket -it ubuntu:18.04 systemctl

>>>>>>> e1b8464e9c9a6b539a8d213a7bcea7099fc711e4

