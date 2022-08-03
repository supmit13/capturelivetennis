This script gets the live feeds from itftennis website and stores them on your disk.
It should be run from the command line as follows: 
python getlivestream.py https://live.itftennis.com/en/live-streams/
Tested on Ubuntu 18.04 and 20.04. However, it should work with little or no change on other linux distros.

Issues: 
#1. Feeds captured have breaks in them and are sometimes jittery. Separating the writing of frames from the frame capture logic using separate threads has improved the situation, but some breaks still remain. Working on fixing this issue. [Resolved - this was happening because the network connection was not good enough]
#2. Sometimes, a feed stops and the associated file doesn't get updated. Investigating why this happens.  [Resolved - issue with the camera capturing the feed. Sometimes the camera stops capturing and sends back no frames or data whatsoever]
#3. Issue with capturing sound: Synology host has no sound card. Investigating how to mitigate the effects of this scenario.

# supmit

