# Django specific imports...
from django.conf import settings

from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.core.context_processors import csrf
from django.views.generic import View
from django.http import HttpResponseBadRequest, HttpResponse , HttpResponseRedirect, QueryDict
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.template.response import TemplateResponse
from django.utils.http import base36_to_int, is_safe_url
from django.utils.translation import ugettext as _
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.template import Template, Context
from django.template.loader import get_template

#from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
#from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, PasswordChangeForm
#from django.contrib.auth.models import User as djangoUser
#from django.contrib.auth.models import Session as djangoSession
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import get_current_site
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth.hashers import make_password # We will use this to generate a hash from csrftoken and user Id.
# We will use that as our sessionid.

# Standard libraries...
import os, sys, re, time, datetime
import cPickle, urlparse
import decimal, math

# Application specific libraries...
from skillstest.Auth.models import User, Session
from skillstest import settings as mysettings
from skillstest.errors import error_msg

"""
@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request, template_name='authentication/login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm,
          current_app=None, extra_context=None):
    
    #Displays the login form and handles the login action.
    
    redirect_to = request.REQUEST.get(redirect_field_name, '')

    if request.method == "POST":
        form = authentication_form(data=request.POST)
        if form.is_valid():
            # Ensure the user-originating redirection url is safe.
            if not is_safe_url(url=redirect_to, host=request.get_host()):
                redirect_to = settings.LOGIN_REDIRECT_URL

            # Okay, security check complete. Log the user in.
            auth_login(request, form.get_user())

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()

            return HttpResponseRedirect(redirect_to)
    else:
        form = authentication_form(request)

    request.session.set_test_cookie()

    current_site = get_current_site(request)

    context = {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context,
                            current_app=current_app)
"""

def authenticate(uname, passwd):
    try:
        user = User.objects.get(displayname=uname)
        if passwd == user.password:
            return user
        else:
            return None
    except:
        return None


def generatesessionid(username, csrftoken, userip):
    hashstr = make_password(username + csrftoken + userip)
    return hashstr


@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request):
    if request.method == "GET":
        msg = None
        if request.META.has_key('QUERY_STRING'):
            msg = request.META.get('QUERY_STRING', '')
        if msg is not None and msg != '':
            var, msg = msg.split("=")
            for hexkey in mysettings.HEXCODE_CHAR_MAP.keys():
                msg = msg.replace(hexkey, mysettings.HEXCODE_CHAR_MAP[hexkey])
            msg = "<p style=\"color:#FF0000;font-size:14;font-face:'helvetica neue';font-style:bold;\">%s</p>"%msg
        else:
            msg = ""
        # Display login form
        curdate = datetime.datetime.now()
        tmpl = get_template("authentication/login.html")
        c = {'curdate' : curdate, 'msg' : msg, }
        c.update(csrf(request))
        cxt = Context(c)
        loginhtml = tmpl.render(cxt)
        for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
            loginhtml = loginhtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
        return HttpResponse(loginhtml)
    elif request.method == "POST":
        username = request.POST.get('username') or ""
        password = request.POST.get('password') or ""
        keeploggedin = request.POST.get('keepmeloggedin') or 0
        csrfmiddlewaretoken = request.POST.get('csrfmiddlewaretoken', "")
        userobj = authenticate(username, password)
        if not userobj: # Incorrect password - return user to login screen with an appropriate message.
            message = error_msg('1002')
            return HttpResponseRedirect("/" + mysettings.LOGIN_URL + "?msg=" + message)
        else: # user will be logged in after checking the 'active' field
            if userobj.active:
                sessobj = Session()
                clientip = request.META['REMOTE_ADDR']
                sesscode = generatesessionid(username, csrfmiddlewaretoken, clientip)
                request.COOKIES['sessioncode'] = sesscode
                sessobj.sessioncode = sesscode
                sessobj.user = userobj
                # sessobj.starttime should get populated on its own when we save this session object.
                sessobj.endtime = None
                sessobj.sourceip = clientip
                if userobj.istest: # This session is being performed by a test user, so this must be a test session.
                    sessobj.istest = True
                elif mysettings.TEST_RUN: # This is a test run as mysettings.TEST_RUN is set to True
                    sessobj.istest = True
                else:
                    sessobj.istest = False
                sessobj.useragent = request.META['HTTP_USER_AGENT']
                # Now save the session...
                sessobj.save()
                # ... and redirect to landing page.
                return HttpResponseRedirect("/" + mysettings.LOGIN_REDIRECT_URL)
            else:
                message = error_msg('1003')
                return HttpResponseRedirect("/" + mysettings.LOGIN_URL + "?msg=" + message)
    else:
        message = error_msg('1001')
        return HttpResponseRedirect("/" + mysettings.LOGIN_URL + "?msg=" + message)


def isloggedin(user, session):
    pass


