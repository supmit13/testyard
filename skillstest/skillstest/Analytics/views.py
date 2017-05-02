from django.conf import settings
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.core.context_processors import csrf
from django.views.generic import View
from django.http import HttpResponseBadRequest, HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
#from django.utils import simplejson
import simplejson
from django.db.models import Q
from django.template.response import TemplateResponse
from django.utils.http import base36_to_int, is_safe_url
from django.template import Template, Context
from django.template.loader import get_template
from django.contrib.sites.models import get_current_site
from django.contrib.sessions.backends.db import SessionStore
from django.core.mail import send_mail
from passlib.hash import pbkdf2_sha256 # To create hash of passwords
from django.utils.encoding import smart_text
from django.utils import timezone

# Standard libraries...
import os, sys, re, time, datetime
import pytz
import cPickle
import decimal, math
from Crypto.Cipher import AES, DES3
from Crypto import Random
import base64,urllib, urllib2
import simplejson as json
from openpyxl import load_workbook
from xlrd import open_workbook
import csv, string
import xml.etree.ElementTree as et
from itertools import chain
import rpy2
import rpy2.robjects as robjects
import rpy2.rinterface as ri

# Application specific libraries...
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
from skillstest.Subscription.models import Plan, UserPlan, Transaction
from skillstest.Tests.models import Topic, Subtopic, Evaluator, Test, UserTest, Challenge, UserResponse, WouldbeUsers, EmailFailure, Schedule
from skillstest.Tests.views import get_user_tests, iseditable                                                           
from skillstest import settings as mysettings
from skillstest.errors import error_msg
import skillstest.utils as skillutils
from skillstest.utils import Logger


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def analytics(request):
    message = ''
    if request.method != "GET": # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.PROFILE_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    analytics_dict = {}
    analytics_dict['displayname'] = userobj.displayname
    analytics_dict['test_topics'] = mysettings.TEST_TOPICS
    analytics_dict['gettestsbytopicurl'] = mysettings.GET_TESTS_BY_TOPIC_URL
    analytics_dict['comparewithtoppersurl'] = mysettings.COMPARE_WITH_TOPPERS_URL
    analytics_dict['comparewithallurl'] = mysettings.COMPARE_WITH_ALL_URL
    analytics_dict['comparetopicscoresurl'] = mysettings.COMPARE_TOPIC_SCORES_URL
    analytics_dict['comparechallengescoresurl'] = mysettings.COMPARE_CHALLENGE_SCORES_URL
    inc_context = skillutils.includedtemplatevars("Test Analytics", request)
    for inc_key in inc_context.keys():
        analytics_dict[inc_key] = inc_context[inc_key]
    tmpl = get_template("analytics/analytics.html")
    analytics_dict.update(csrf(request))
    cxt = Context(analytics_dict)
    analyticshtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        analyticshtml = analyticshtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(analyticshtml)
    

@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def gettestsbytopic(request):
    message = ''
    if request.method != "POST": # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.PROFILE_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    useremail = userobj.emailid
    test_topic = ""
    if request.POST.has_key('test_topic'):
        test_topic = request.POST['test_topic']
    else:
        message = "Required parameter missing in post data."
        response = HttpResponse(message)
        return response
    utqset = UserTest.objects.filter(user=userobj)
    wuqset = WouldbeUsers.objects.filter(emailaddr=useremail)
    alltestshtml = "<font color='#00BB00'><b>Select a Test:</b></font>"
    alltestshtml += "<select name='usertests'><option value='all' selected>Select Test</option>"
    uniqtestnames = {}
    try:
        for ut in utqset:
            if ut.test.topic.topicname == test_topic or ut.test.topicname == test_topic:
                if not uniqtestnames.has_key(ut.test.testname):
                    alltestshtml += "<option value='" + str(ut.test.id) + "'>" + ut.test.testname + "</option>\n"
                    uniqtestnames[ut.test.testname] = 1
        for wu in wuqset:
            if wu.test.topic.topicname == test_topic or wu.test.topicname == test_topic:
                if not uniqtestnames.has_key(wu.test.testname):
                    alltestshtml += "<option value='" + str(wu.test.id) + "'>" + wu.test.testname + "</option>\n"
                    uniqtestnames[wu.test.testname] = 1
    except:
        message = sys.exc_info()[1].__str__()
        return HttpResponse(message)
    alltestshtml += "</select>\n"
    response = HttpResponse(alltestshtml)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def comparewithtoppers(request):
    message = ''
    if request.method != "POST": # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.PROFILE_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    useremail = userobj.emailid
    analytic_technique = ""
    test_topic = ""
    testid = ""
    if request.POST.has_key('analytic_technique'):
        analytic_technique = request.POST['analytic_technique']
    else:
        message = "Required parameter (analytic_technique) missing."
        response = HttpResponse(message)
        return response
    if request.POST.has_key('test_topic'):
        test_topic = request.POST['test_topic']
    else:
        message = "Required parameter (test_topic) missing."
        response = HttpResponse(message)
        return response
    if request.POST.has_key('testid'):
        testid = request.POST['testid']
    else:
        testid = "all"
    # Find every test score in the given test topic for this user as well as the max score in all those tests.
    testinfodict = {}
    testobjlist = []
    if testid == "all":# First, get all tests for the selected test topic
        testobjqset = Test.objects.filter(topic__topicname=test_topic)
        for testobj in testobjqset:
            testobjlist.append(testobj)
        testobjqset = Test.objects.filter(topicname=test_topic)
        for testobj in testobjqset:
            testobjlist.append(testobj)
    else:
        testobjqset = Test.objects.filter(id=testid)
        testobjlist = list(testobjqset)
    testobjdict = {}
    for testobj in testobjlist:
        testname = testobj.testname
        if testobjdict.has_key(testname):
            continue
        else:
            testobjdict[testname] = 1
        utqset = UserTest.objects.filter(user=userobj, test=testobj)
        wuqset = WouldbeUsers.objects.filter(emailaddr=useremail, test=testobj)
        for utobj in utqset:
            if testinfodict.has_key(testname):
                if testinfodict[testname][0] < utobj.score:
                    testinfodict[testname] = [ utobj.score, 0 ]
                else:
                    pass # We only take the highest score for the user in the particular test.
            else:
                testinfodict[testname] = [ utobj.score, 0 ]
        for wuobj in wuqset:
            if testinfodict.has_key(testname):
                if testinfodict[testname][0] < wuobj.score:
                    testinfodict[testname] = [ wuobj.score, 0 ]
                else:
                    pass # We only take the highest score for the user in the particular test.
            else:
                testinfodict[testname] = [ wuobj.score, 0 ]
        
        # Now get the max score for this test
        utmaxqset = UserTest.objects.filter(test=testobj)
        wumaxqset = WouldbeUsers.objects.filter(test=testobj)
        for utmaxobj in utmaxqset:
            if testinfodict.has_key(testobj.testname) and utmaxobj.score > testinfodict[testobj.testname][1]:
                testinfodict[testobj.testname][1] = utmaxobj.score
        for wumaxobj in wumaxqset:
            if testinfodict.has_key(testobj.testname) and wumaxobj.score > testinfodict[testobj.testname][1]:
                testinfodict[testobj.testname][1] = wumaxobj.score
    # There, now we have all the data we need in testinfodict for plotting bar charts.
    jsonstr = json.dumps(testinfodict)
    response = HttpResponse(jsonstr)
    return response
    

@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def comparewithall(request):
    message = ''
    if request.method != "POST": # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.PROFILE_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    useremail = userobj.emailid
    analytic_technique = ""
    test_topic = ""
    testid = ""
    if request.POST.has_key('analytic_technique'):
        analytic_technique = request.POST['analytic_technique']
    else:
        message = "Required parameter (analytic_technique) missing."
        response = HttpResponse(message)
        return response
    if request.POST.has_key('test_topic'):
        test_topic = request.POST['test_topic']
    else:
        message = "Required parameter (test_topic) missing."
        response = HttpResponse(message)
        return response
    if request.POST.has_key('testid'):
        testid = request.POST['testid']
    else:
        message = "Required parameter (testid) missing."
        response = HttpResponse(message)
        return response
    testinfodict = {}
    uniqdict = {}
    testobj = Test.objects.get(id=testid)
    utqset = UserTest.objects.filter(test=testobj)
    wuqset = WouldbeUsers.objects.filter(test=testobj)
    j = 1
    for utobj in utqset:
        username = utobj.user.displayname
        userscore = utobj.score
        if not uniqdict.has_key(username):
            hiddenname = "hidden_" + str(j)
            testinfodict[hiddenname] = userscore
            j += 1
            uniqdict[username] = 1
        else:
            pass
    for wuobj in wuqset:
        emailaddr = wuobj.emailaddr
        score = wuobj.score
        if not uniqdict.has_key(emailaddr):
            hiddenname = "hidden_" + str(j)
            testinfodict[hiddenname] = score
            j += 1
            uniqdict[emailaddr] = 1
        else:
            pass
    jsonstr = json.dumps(testinfodict)
    response = HttpResponse(jsonstr)
    return response
    

@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def comparetopicscores(request):
    message = ''
    if request.method != "POST": # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.PROFILE_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    useremail = userobj.emailid
    analytic_technique = ""
    test_topic = ""
    testid = ""
    if request.POST.has_key('analytic_technique'):
        analytic_technique = request.POST['analytic_technique']
    else:
        message = "Required parameter (analytic_technique) missing."
        response = HttpResponse(message)
        return response
    if request.POST.has_key('test_topic'):
        test_topic = request.POST['test_topic']
    else:
        message = "Required parameter (test_topic) missing."
        response = HttpResponse(message)
        return response
    # Ignore the testid argument entirely.
    testqset = Test.objects.filter(topicname=test_topic)
    testobjslist = []
    for testobj in testqset:
        testobjslist.append(testobj)
    testqset = Test.objects.filter(topic__topicname = test_topic)
    for testobj in testqset:
        testobjslist.append(testobj)
    testinfodict = {}
    for testobj in testobjslist:
        utqset = UserTest.objects.filter(test=testobj, user=userobj)
        for utobj in utqset:
            testname = utobj.test.testname
            if testinfodict.has_key(testname):
                score = testinfodict[testname]
                if utobj.score > score:
                    testinfodict[testname] = utobj.score # We consider the highest score in tests that have been repeated by the user.
            else:
                testinfodict[testname] = utobj.score
        wuqset = WouldbeUsers.objects.filter(test=testobj, emailaddr=useremail)
        for wuobj in wuqset:
            testname = wuobj.test.testname
            if testinfodict.has_key(testname):
                score = testinfodict[testname]
                if wuobj.score > score:
                    testinfodict[testname] = wuobj.score # We consider the highest score in tests that have been repeated by the user.
            else:
                testinfodict[testname] = wuobj.score
    jsonstr = json.dumps(testinfodict)
    response = HttpResponse(jsonstr)
    return response
            

@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def comparechallengescores(request):
    message = ''
    if request.method != "POST": # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.PROFILE_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    useremail = userobj.emailid
    analytic_technique = ""
    test_topic = ""
    testid = ""
    if request.POST.has_key('analytic_technique'):
        analytic_technique = request.POST['analytic_technique']
    else:
        message = "Required parameter (analytic_technique) missing."
        response = HttpResponse(message)
        return response
    if request.POST.has_key('test_topic'):
        test_topic = request.POST['test_topic']
    else:
        message = "Required parameter (test_topic) missing."
        response = HttpResponse(message)
        return response
    if request.POST.has_key('testid'):
        testid = request.POST['testid']
    else:
        message = "Required parameter (testid) missing."
        response = HttpResponse(message)
        return response
    testobj = Test.objects.get(id=testid)
    testinfodict = {}
    userresponseqset = UserResponse.objects.filter(test=testobj)
    for respobj in userresponseqset:
        challenge = respobj.challenge.statement
        if testinfodict.has_key(challenge):
            try:
                if respobj.emailaddr == useremail:
                    testinfodict[challenge][0] = respobj.evaluation
                    if respobj.evaluation > testinfodict[challenge][1]:
                        testinfodict[challenge][1] = respobj.evaluation
                else:
                    if respobj.evaluation > testinfodict[challenge][1]:
                        testinfodict[challenge][1] = respobj.evaluation
                    else:
                        pass
            except:
                return HttpResponse(sys.exc_info()[1].__str__())
        else:
            try:
                if respobj.emailaddr == useremail:
                    testinfodict[challenge] = [ respobj.evaluation, 0]
                else:
                    testinfodict[challenge] = [0, respobj.evaluation ]
            except:
                return HttpResponse(sys.exc_info()[1].__str__())
    jsonstr = json.dumps(testinfodict)
    response = HttpResponse(jsonstr)
    return response











