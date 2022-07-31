import os, sys, re, time
import subprocess


if __name__ == "__main__":
    dumppath = "/var/livefeed"
    if sys.argv.__len__() > 1:
        dumppath = sys.argv[1]
    subdirname = time.strftime("%Y-%m-%d", time.localtime())
    dumppath = dumppath + os.path.sep + subdirname
    if not os.path.isdir(dumppath):
        os.makedirs(dumppath, 0o777)
    cmdout = subprocess.check_output(["docker", "ps"]).decode('utf-8')
    alllines = cmdout.split("\n")
    targetpattern = re.compile("ubuntu_python*")
    spacepattern = re.compile("\s+")
    containerid = ""
    for line in alllines:
        lps = re.search(targetpattern, line)
        if lps:
            lineparts = re.split(spacepattern, line)
            containerid = lineparts[0]
            break
    if containerid is not None and containerid != "":
        dcontents = subprocess.check_output(["docker", "exec", containerid, "ls", "/home/supmit/work/capturelivefeed/tennisvideos/"]).decode('utf-8')
        dlines = dcontents.split("\n")
        avipattern = re.compile("\.avi")
        for l in dlines:
            if re.search(avipattern, l):
                backupcmd = ["docker", "cp", "%s:/home/supmit/work/capturelivefeed/tennisvideos/%s"%(containerid, l), "%s"%dumppath]
                subprocess.Popen(backupcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        print("Could not find the container. Please make sure it is running.")
        sys.exit()
    print("All backed up for now.")
    

