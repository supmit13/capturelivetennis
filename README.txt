This script gets the live feeds from itftennis website and stores them on your disk.
It should be run from the command line as follows: 
python getlivestream.py https://live.itftennis.com/en/live-streams/
Tested on Ubuntu 18.04 and 20.04. However, it should work with little or no change on other linux distros.

Issues: 
#1. Feeds captured have breaks in them and are sometimes jittery. Separating the writing of frames from the frame capture logic using separate threads has improved the situation, but some breaks still remain. Working on fixing this issue.
#2. Sometimes, a feed stops and the associated file doesn't get updated. Investigating why this happens. 

# supmit

