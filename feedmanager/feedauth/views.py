import os, sys, re, time
from datetime import datetime
import shutil
import string, random
import urllib.parse
import urllib

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



def showlogin(request):
    if request.method != 'GET':
        return HttpResponse("Invalid method of call")
    context = {}
    template = loader.get_template('login.html')
    return HttpResponse(template.render(context, request))

@csrf_protect
def dologin(request):
    if request.method != 'POST':
        return HttpResponse("Invalid method of call")
    username, password = "", ""
    requestbody = str(request.body)
    bodycomponents = requestbody.split("&")
    requestdict = {}
    for comp in bodycomponents:
        compparts = comp.split("=")
        if compparts.__len__() > 1:
            compparts[0] = compparts[0].replace("b'", "")
            requestdict[compparts[0]] = urllib.parse.unquote(compparts[1])
    username = requestdict['uname']
    password = requestdict['psw']
    password = password.replace("'", "")
    userqset = User.objects.filter(username=username)
    if userqset.__len__() > 0:
        userobj = userqset[0]
        if userobj.check_password(password):
            login(request, userobj)
            return HttpResponseRedirect("/feedman/listfeeds/")
        else:
            return HttpResponseRedirect("/feedauth/showlogin/?err=2") # err=2 - incorrect password
    else:
        return HttpResponseRedirect("/feedauth/showlogin/?err=1") # err=1 - username doesn't exist.
    """
    authuser = authenticate(username=username, password=password)
    if authuser is not None:
        login(request, authuser)
        # Redirect to run scraper page
        return HttpResponseRedirect("/feedman/listfeeds/")
    else:
        return HttpResponseRedirect("/feedauth/showlogin/")
    """


def dologout(request):
    logout(request)
    return HttpResponseRedirect("/feedauth/showlogin/")



