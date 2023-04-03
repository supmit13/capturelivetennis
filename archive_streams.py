import os, sys, re, time
import datetime
import docker


def copy_from_container(container, dest, src, logfp):
    filenamepattern = re.compile("\/([^\/]+\.avi)\s*")
    fps = re.search(filenamepattern, src)
    if fps is None:
        return None
    filename = fps.groups()[0]
    pathendpattern = re.compile("\/$")
    if not re.search(pathendpattern, dest):
        dest += "/"
    f = open(dest + filename, 'wb')
    bits, stat = container.get_archive(src)
    for chunk in bits:
        f.write(chunk)
    f.close()
    
def get_files_by_date(container, curdate, logfp):
    filepattern = curdate.strftime("%Y%m%d*.avi")
    response = container.exec_run("/bin/bash -c 'ls /home/supmit/work/capturelivefeed/tennisvideos/final/%s'"%filepattern)
    if response[0] != 0: # Error occurred while executing the ls command above
        logfp.write("%s - Error executing ls in container: %s\n\n"%(currdate.strftime("%d %b, %Y %H:%M:%S"), str(response[0])))
        return []
    cmdoutput = str(response[1])
    whitespacepattern = re.compile("\s+", re.DOTALL)
    fileslist = re.split(whitespacepattern, cmdoutput)
    filepaths = []
    for filename in fileslist:
        filename = str(filename).replace("\\n", "")
        filename = filename.replace("b'", "").replace("'", "")
        filepaths.append(filename)
    return filepaths

if __name__ == "__main__":
    container_name = 'capturetennisfeeds_v2'
    if sys.argv.__len__() > 1:
        container_name = sys.argv[1]
    logfp = open("./archive_streams.log", "a")
    currdate = datetime.datetime.now()
    #destdir = "/volume1/TennisVideos/final/"
    destdir = "/opt/home/edge/videocapture/tennisvideos/final/"
    #client = docker.from_env()
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    containerslist = client.containers.list(filters={'ancestor': "%s:latest"%container_name})
    if containerslist.__len__() < 1:
        logfp.write("%s - No containers are running at the moment.\n"%currdate.strftime("%d %b, %Y %H:%M:%S"))
        logfp.close()
        sys.exit()
    container_id = str(containerslist[0].id)[:12] # Could have just accessed the 'short_id'
    container = client.containers.get(container_id)
    files_list = get_files_by_date(container, currdate, logfp)
    filescount = 0
    for filepath in files_list:
        copy_from_container(container, destdir, filepath, logfp)
        filescount += 1
    logfp.write("%s - Done copying %s files.\n%s"%(currdate.strftime("%d %b, %Y %H:%M:%S"), filescount, "\n".join(files_list)))
    sys.exit()
    
    
