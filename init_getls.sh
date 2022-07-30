#!/bin/bash

# This file starts the execution of getlivestream.py.
# This script is meant to be executed on system bootup.

curdir=`pwd`

# Path to python interpreter in (virtual) environment
pypath="python"

# Path to getlivestream.py
getlspath="getlivestream.py"

# execute getlivestream.py
`nohup $pypath $getlspath "https://live.itftennis.com/en/live-streams/" &`

# Provide execute permissions to this script:
# chmod 755 /home/supmit/work/capturelivefeed/init_getls.sh
# crontab -e
# @reboot  /home/user/init_getls.sh
# Done!
# Dev: Supriyo

