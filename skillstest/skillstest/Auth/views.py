# Django specific imports...
from django.conf import settings
from skillstest import settings as mysettings
from django.views.decorators.csrf import csrf_exempt, csrf_protect
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

#from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
#from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import get_current_site

# Standard libraries...
import os, sys, re, time, datetime
import cPickle, urlparse
import decimal, math

# Application specific libraries...
from skillstest.Auth.models import User, Session

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
    
def login(request):
    try:
        fp = open(mysettings.PROJECT_ROOT + "/templates/authentication/login.html")
        html = fp.read()
        fp.close()
    except:
        return HttpResponse("Crapped!")
    t = Template(html)
    c = Context({})
    out = t.render(c)
    return HttpResponse(out)


def isloggedin(user, session):
    pass


