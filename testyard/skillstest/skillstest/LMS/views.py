# Django specific imports...
from django.conf import settings

from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.core.context_processors import csrf
from django.views.generic import View
from django.http import HttpResponseBadRequest, HttpResponse , HttpResponseRedirect, QueryDict
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
#from django.utils import simplejson # Since django no longer ships simplejson as a part of it.
import simplejson as json
from django.template.response import TemplateResponse
from django.utils.http import base36_to_int, is_safe_url
from django.utils.translation import ugettext as _
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.template import Template, Context
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import get_current_site
from django.contrib.sessions.backends.db import SessionStore
from passlib.hash import pbkdf2_sha256 # To create hash of passwords
# We will use that as our sessionid.

# Standard libraries...
import os, sys, re, time, datetime
import cPickle, urlparse
import decimal, math, base64
import requests, shutil
import urllib, urllib2
import logging

from skillsteach.views import *
from skillsauth.models import *
from skillsteach.models import *
import teachyard.utils as teachutils


def returnRedirect(request):
    requestline = request.build_absolute_uri()
    logger = logging.getLogger(__name__)
    logger.debug("REQUEST LINE: %s"%requestline)
    httpPattern = re.compile(r"^http:")
    if httpPattern.search(requestline):
        redirectUrl = "%s/%s"%("", settings.LOGIN_URL)
        redirectUrlParts = redirectUrl.split("//")
        urlPathPart = redirectUrlParts[redirectUrlParts.__len__() - 1]
        urlPathPart = teachutils.gethosturl(request) + "/" + urlPathPart
        print("URLPATH: " + urlPathPart)
        urlPathPart = urlPathPart.replace("https://", "", 1)
        return HttpResponseRedirect(urlPathPart)
    #redirectUrl = "%s/%s"%("", settings.MANAGE_TEST_URL)
    redirectUrl = "%s/%s"%("", settings.INDEX_URL)
    if not teachutils.isloggedin(request):
        loginredirect = True
        for pathpattern in settings.UNAUTHENTICATED_ACCESS_PATH_PATTERNS:
            if re.search(pathpattern, request.path):
                loginredirect = False
                break
        if loginredirect is True:
            redirectUrl = "%s/%s"%("", settings.LOGIN_URL)
    redirectUrlParts = redirectUrl.split("//")
    urlPathPart = redirectUrlParts[redirectUrlParts.__len__() - 1]
    urlPathPart = settings.URL_PROTOCOL + teachutils.gethosturl(request) + urlPathPart
    urlPathPart = urlPathPart.replace("https://", "", 1)
    return HttpResponseRedirect(urlPathPart)


def handler404(request):	
    return HttpResponseRedirect("%s/%s"%("", settings.LOGIN_URL))



def dashboard(request):
    pass


def index(request):
    pass


def showteachinterface(request):
    if request.method != 'GET':
        return HttpResponse("Invalid method of call")
    teach_interface_dict = {}
    
    tmpl = get_template("skillsteach/teach_interface.html")
    teach_interface_dict.update(csrf(request))
    cxt = Context(teach_interface_dict)
    teachinterfacehtml = tmpl.render(cxt)
    return HttpResponse(teachinterfacehtml)


