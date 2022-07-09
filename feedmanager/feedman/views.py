import os, sys, re, time
from datetime import datetime
import shutil
import string, random
import urllib.parse
import urllib
import simplejson as json

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.http import HttpResponse
from django.template import loader
from django.conf import settings
from feedman.models import Feed

from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.http import FileResponse


@login_required(login_url='/feedauth/showlogin/')
def listfeeds(request):
    if request.method != 'GET':
        return HttpResponse("Invalid method of call")
    context = {}
    username = ""
    if request.user.is_authenticated:
        username = request.user.username
    else:
        return HttpResponseRedirect("/feedauth/showlogin/")
    context['username'] = username
    context['pagetitle'] = "Feeds List"
    feedslist = []
    chunksize = int(settings.CHUNKSIZE)
    page = 1
    if 'page' in request.GET.keys():
        page = int(request.GET['page'])
    startid = page * chunksize - chunksize
    endid = page * chunksize
    allfeedsqset = Feed.objects.filter(deleted=False).order_by('-id')[startid:endid]
    for feedobj in allfeedsqset:
        d = {}
        d['title'] = feedobj.feedtitle
        d['fid'] = feedobj.id
        d['player1'] = feedobj.feedeventteam1.replace(",", "<br/>")
        d['player2'] = feedobj.feedeventteam2.replace(",", "<br/>")
        d['matchdate'] = feedobj.feedstart
        d['matchtype'] = feedobj.eventtype
        d['result'] = feedobj.eventresult
        d['status'] = feedobj.feedstatus # If this is a live event, we display it in green.
        feedslist.append(d)
    context['feedslist'] = feedslist
    nextpage = page + 1
    prevpage = page - 1
    context['nextpage'] = nextpage
    context['prevpage'] = prevpage
    context['showpagination'] = 0
    if page > 1 and allfeedsqset.__len__() >= chunksize:
        context['showpagination'] = 1
    template = loader.get_template('feedslisting.html')
    return HttpResponse(template.render(context, request))


@login_required(login_url='/feedauth/showlogin/')
def editfeed(request):
    if request.method != 'POST':
        return HttpResponse(json.dumps({'error' : 'Invalid method of call'}))
    if not request.user.is_authenticated:
        return HttpResponse(json.dumps({'error' : 'user is not authenticated'}))
    userid = request.user.id
    feedid = ""
    requestbody = str(request.body)
    bodycomponents = requestbody.split("&")
    requestdict = {}
    for comp in bodycomponents:
        compparts = comp.split("=")
        if compparts.__len__() > 1:
            compparts[0] = compparts[0].replace("b'", "")
            requestdict[compparts[0]] = urllib.parse.unquote(compparts[1])
    if 'feedid' not in requestdict.keys():
        message = "Could not find feed Id as an argument of the request"
        return HttpResponse(json.dumps({'error' : message}))
    feedid = requestdict['feedid']
    feedobj = None
    try:
        feedobj = Feed.objects.get(id=int(feedid))
    except:
        message = "Feed ID %s error: %s"%(feedid, sys.exc_info()[1].__str__())
        return HttpResponse(json.dumps({'error' : message}))
    feed = {}
    feed['title'] = feedobj.feedtitle
    feed['fid'] = feedobj.id
    feed['player1'] = feedobj.feedeventteam1
    feed['player2'] = feedobj.feedeventteam2
    startdate = str(feedobj.feedstart).split("+")[0].replace(" ", "T").replace("Z", "")
    feed['startdate'] = startdate
    enddate = str(feedobj.feedend).split("+")[0].replace(" ", "T").replace("Z", "")
    feed['enddate'] = enddate
    if enddate == "None":
        feed['enddate'] = ""
    feed['eventtype'] = feedobj.eventtype
    feed['result'] = feedobj.eventresult
    feed['status'] = feedobj.feedstatus
    feed['deleted'] = feedobj.deleted
    feed['feedpath'] = feedobj.feedpath
    feed['resultoptions'] = [feedobj.feedeventteam1, feedobj.feedeventteam2, "tie", "unknown"]
    feed['error'] = ""
    feedstr = json.dumps(feed)
    return HttpResponse(feedstr)


@login_required(login_url='/feedauth/showlogin/')
@csrf_protect
def savefeed(request):
    if request.method != 'POST':
        return HttpResponse("Invalid method of call")
    if not request.user.is_authenticated:
        return HttpResponse("Your session is invalid. Please login to perform this operation")
    requestbody = str(request.body)
    requestdict = urllib.parse.parse_qs(requestbody)
    #print(requestdict)
    # Convert all double quotes in input to single quotes... pain! Also, urllib.parse.parse_qs leaves "b'" in the keys in some cases.
    newrequestdict = {}
    for k in requestdict.keys():
        newk = k.replace("b'", "")
        newrequestdict[newk] = requestdict[k][0].replace('"', "'")
    # Now save the data.
    feedid, feedtitle, feedplayer1, feedplayer2, eventtype, feedpath, feedstart, feedend, deleted, feedresult, feedstatus = -1, "", "", "", "", "", "", "", 0, "", ""
    print(newrequestdict.keys())
    if 'feedid' in newrequestdict.keys():
        feedid = newrequestdict['feedid']
    if 'title' in newrequestdict.keys():
        feedtitle = newrequestdict['title']
    if 'player1' in newrequestdict.keys():
        feedplayer1 = newrequestdict['player1']
    if 'player2' in newrequestdict.keys():
        feedplayer2 = newrequestdict['player2']
    if 'eventtype' in newrequestdict.keys():
        eventtype = newrequestdict['eventtype']
    if 'feedpath' in newrequestdict.keys():
        feedpath = newrequestdict['feedpath']
    if 'startdate' in newrequestdict.keys():
        feedstart = newrequestdict['startdate']
    if 'enddate' in newrequestdict.keys():
        feedend = newrequestdict['enddate']
    if 'deleted' in newrequestdict.keys():
        deleted = newrequestdict['deleted']
    if 'result' in newrequestdict.keys():
        feedresult = newrequestdict['result']
    if 'status' in newrequestdict.keys():
        feedstatus = newrequestdict['status']
    # Convert dates to python datetime values
    mszPattern = re.compile("\.\d+Z", re.IGNORECASE)
    feedstart = mszPattern.sub("", feedstart)
    feedend = mszPattern.sub("", feedend)
    #print(feedstart)
    if feedstart != "":
        feedstart = datetime.strptime(feedstart, "%Y-%m-%dT%H:%M:%S")
    if feedend != "":
        feedend = datetime.strptime(feedend, "%Y-%m-%dT%H:%M:%S")
    feedobj = None
    try:
        feedobj = Feed.objects.get(id=feedid)
    except:
        message = "Could not identify the feed object (%s) uniquely"%feedid
        return HttpResponse(message)
    feedobj.feedtitle = feedtitle
    feedobj.feedeventteam1 = feedplayer1
    feedobj.feedeventteam2 = feedplayer2
    feedobj.feedstart = feedstart
    feedobj.feedend = feedend
    feedobj.eventtype = eventtype
    feedobj.eventresult = feedresult
    feedobj.feedstatus = feedstatus
    feedobj.feedpath = feedpath
    if int(deleted) == 0:
        feedobj.deleted = False
    else:
        feedobj.deleted = True
    feedobj.updatetime = datetime.now()
    feedobj.updateuser = request.user
    try:
        feedobj.save()
    except:
        message = "Error occurred while saving the changes: %s"%sys.exc_info()[1].__str__()
    message = 'Successfully saved changes to the feed'
    return HttpResponse(message)


@login_required(login_url='/feedauth/showlogin/')
@csrf_protect
def deletefeed(request):
    if request.method != 'POST':
        return HttpResponse("Invalid method of call")
    if not request.user.is_authenticated:
        return HttpResponseRedirect("/feedauth/showlogin/")
    userid = request.user.id
    feedid = ""
    requestbody = str(request.body)
    bodycomponents = requestbody.split("&")
    requestdict = {}
    for comp in bodycomponents:
        compparts = comp.split("=")
        if compparts.__len__() > 1:
            compparts[0] = compparts[0].replace("b'", "")
            requestdict[compparts[0]] = urllib.parse.unquote(compparts[1])
    if 'feedid' not in requestdict.keys():
        message = "Could not find feed Id as an argument of the request"
        return HttpResponse(message)
    feedid = requestdict['feedid']
    feedobj = None
    try:
        feedobj = Feed.objects.get(id=int(feedid))
    except:
        message = "Feed ID %s error: %s"%(feedid, sys.exc_info()[1].__str__())
        return HttpResponse(message)
    feedobj.deleted = True
    feedobj.save()
    message = "The selected feed was successfully deleted"
    return HttpResponse(message)
    


@login_required(login_url='/feedauth/showlogin/')
@csrf_protect
def searchfeeds(request):
    if request.method != 'POST':
        message = "Invalid method of call"
        context = {'error' : message}
        return HttpResponse(json.dumps(context))
    if not request.user.is_authenticated:
        message = "Your session is invalid. Please login to perform this operation"
        context = {'error' : message}
        return HttpResponse(json.dumps(context))
    requestbody = str(request.body)
    requestdict = urllib.parse.parse_qs(requestbody)
    #print(requestdict)
    # Convert all double quotes in input to single quotes... pain! Also, urllib.parse.parse_qs leaves "b'" in the keys in some cases.
    newrequestdict = {}
    for k in requestdict.keys():
        newk = k.replace("b'", "")
        newrequestdict[newk] = requestdict[k][0].replace('"', "'")
    page = 1
    if 'page' in newrequestdict.keys():
        page = int(newrequestdict['page'])
    searchtext = ""
    if 'q' in newrequestdict.keys():
        searchtext = newrequestdict['q']
    whitespacePattern = re.compile("^\s*$")
    if re.search(whitespacePattern, searchtext):
        message = "You did not specify any meaningful text"
        context = {'error' : message}
        return HttpResponse(json.dumps(context))
    chunksize = int(settings.CHUNKSIZE)
    startid = page * chunksize - chunksize
    endid = page * chunksize
    context = {}
    # If we reached here, then we may conduct the search.
    feedsqset = Feed.objects.filter(feedtitle__icontains=searchtext).order_by('-id')[startid:endid]
    feedslist = []
    for feedobj in feedsqset:
        d = {}
        d['title'] = feedobj.feedtitle
        d['fid'] = feedobj.id
        d['player1'] = feedobj.feedeventteam1.replace(",", "<br/>")
        d['player2'] = feedobj.feedeventteam2.replace(",", "<br/>")
        d['matchdate'] = str(feedobj.feedstart)
        d['matchtype'] = feedobj.eventtype
        d['result'] = feedobj.eventresult
        d['status'] = feedobj.feedstatus # If this is a live event, we display it in green.
        feedslist.append(d)
    context['feedslist'] = feedslist
    nextpage = page + 1
    prevpage = page - 1
    context['nextpage'] = nextpage
    context['prevpage'] = prevpage
    context['showpagination'] = 0
    if page > 1 and allfeedsqset.__len__() >= chunksize:
        context['showpagination'] = 1
    context['error'] = ""
    return HttpResponse(json.dumps(context))


@login_required(login_url='/feedauth/showlogin/')
@csrf_protect
def feedsettings(request):
    pass


@login_required(login_url='/feedauth/showlogin/')
@csrf_protect
def sendmail(request):
    pass






