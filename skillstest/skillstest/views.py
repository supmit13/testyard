from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.http import HttpResponseBadRequest, HttpResponse , HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson

# Standard libraries...
import os, sys, re, time, datetime
import cPickle
import decimal, math

# Application specific libraries...
from skillstest.Auth.models import User, Session


"""
Dashboard will consist of 2 parts - 1) Details of tests conducted by the user
and 2) details of the tests taken by the user. Also, views will be based on
the privileges of the user. 'Admin' users will be able  to view and access every
bit of information pertaining to the user, users with lesser rights will be able
to view lesser info.
"""
def dashboard(request):
    return HttpResponse()


def home(request):
    return HttpResponse()



