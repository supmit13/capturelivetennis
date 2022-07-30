#!/bin/bash

# This file starts the execution of getlivestream.py.
# This script is meant to be executed on system bootup.
cd /home/supmit/work/capturelivefeed

curdir=`pwd`

source ./videoenv/bin/activate

# Path to python interpreter in (virtual) environment
pypath=`which python`

# Path to getlivestream.py
getlspath="$curdir/getlivestream.py"

# execute getlivestream.py
`nohup $pypath $getlspath "https://live.itftennis.com/en/live-streams/" &`

# Provide execute permissions to this script:
# chmod 755 /home/supmit/work/capturelivefeed/init_getls.sh
# crontab -e
# @reboot  /home/user/init_getls.sh
# Done!
# Dev: Supriyo

