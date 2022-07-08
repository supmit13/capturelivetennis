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


@login_required(login_url='/feedauth/showlogin/')
def listfeeds(request):
    return HttpResponse("")


@login_required(login_url='/feedauth/showlogin/')
def editfeed(request):
    pass


@login_required(login_url='/feedauth/showlogin/')
@csrf_protect
def savefeed(request):
    pass


@login_required(login_url='/feedauth/showlogin/')
@csrf_protect
def deletefeed(request):
    pass



