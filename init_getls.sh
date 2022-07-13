#!/bin/bash

# This file starts the execution of getlivestream.py.
# This script is meant to be executed on system bootup.

# crontab -e
# @reboot  /home/user/init_getls.sh

# Path to python interpreter in (virtual) environment
pypath="/home/user/videocapture/pyenv/bin/python3"

# Path to getlivestream.py
getlspath="/home/user/videocapture/getlivestream.py"

# execute getlivestream.py
`nohup $pypath $getlspath "https://live.itftennis.com/en/live-streams/" &`

# Done!
# Dev: supmit

