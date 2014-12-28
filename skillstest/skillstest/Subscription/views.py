from django.conf import settings
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.generic import View
from django.http import HttpResponseBadRequest, HttpResponse , HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.db.models import Q

# Standard libraries...
import os, sys, re, time, datetime
import cPickle
import decimal, math

# Application specific libraries...
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
from skillstest import settings as mysettings
from skillstest.errors import error_msg
import skillstest.utils as skillutils

@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def subscriptions(request):
    pass
