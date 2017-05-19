from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.core.context_processors import csrf
from django.views.generic import View
from django.http import HttpResponseBadRequest, HttpResponse , HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.db.models import Q
from django.template.response import TemplateResponse
from django.utils.http import base36_to_int, is_safe_url
from django.template import Template, Context
from django.template.loader import get_template
from django.contrib.sites.models import get_current_site
from django.contrib.sessions.backends.db import SessionStore

# Standard libraries...
import os, sys, re, time, datetime
import cPickle
import decimal, math

# Application specific libraries...
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
from skillstest.Subscription.models import Plan, UserPlan, Transaction
from skillstest.Tests.models import Topic, Subtopic, Evaluator, Test, UserTest, Challenge, UserResponse
from skillstest import settings as mysettings
from skillstest.errors import error_msg
import skillstest.utils as skillutils


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def subscriptions(request):
    message = ''
    if request.method != "GET" and request.method != 'POST': # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.SUBSCRIPTION_URL + "?msg=%s"%message)
        return response
    # If request method is 'GET', then retrieve Session and User info from the DB
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    plans = Plan.objects.all() # Getting all Plans.
    current_plans_dict = {}
    past_plans_dict = {}
    subscription_data_dict = {}
    curdatetime = datetime.datetime.now()
    for pln in plans:
        planname = pln.planname
        createdate = pln.createdate
        startdate, starttime = str(createdate).split(" ")
        planstatus = pln.status
        discountpercent = pln.discountpercent
        """
        totalcost = pln.totalcost
        amtpaid = pln.amountpaid
        amtdue = pln.amountdue
        lastpaydate = pln.lastpaydate
        subscribedon = pln.subscribedon
        discountamountapplied = pln.discountamountapplied
        if curdatetime > datetime.datetime(int(startyyyy), int(startmon), int(startdd), int(starthh), int(startmm), int(startss)) and curdatetime < datetime.datetime(int(endyyyy), int(endmon), int(enddd), int(endhh), int(endmm), int(endss)) and planstatus:
            current_plans_dict[planname] = ( planname, planstartdate, planenddate, discountpercent, \
                                             discountamountapplied, totalcost, amtpaid, amtdue, \
                                             lastpaydate, subscribedon )
        else: # plans subscribed to in the past...
            past_plans_dict[planname] = ( planname, planstartdate, planenddate, discountpercent, \
                                             discountamountapplied, totalcost, amtpaid, amtdue, \
                                             lastpaydate, subscribedon )
        """
    subscription_data_dict['current'] = current_plans_dict
    subscription_data_dict['past'] = past_plans_dict
    subscription_data_dict['displayname'] = userobj.displayname
    subscription_data_dict['profile_image_tag'] = skillutils.getprofileimgtag(request)
    inc_context = skillutils.includedtemplatevars("Subscription", request) # Since this is the 'Profile' page for the user.
    for inc_key in inc_context.keys():
        subscription_data_dict[inc_key] = inc_context[inc_key]
    tmpl = get_template("subscription/subscription.html")
    subscription_data_dict.update(csrf(request))
    cxt = Context(subscription_data_dict)
    subscriptionhtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        subscriptionhtml = subscriptionhtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(subscriptionhtml)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def showplans(request):
    message = ''
    if request.method != "GET" and request.method != 'POST': # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.SUBSCRIPTION_URL + "?msg=%s"%message)
        return response




