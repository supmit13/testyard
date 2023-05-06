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
#import rpy2
#import rpy2.robjects as robjects
#import rpy2.rinterface as ri

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
    analytics_dict['comparescoresmmmurl'] = mysettings.COMPARE_SCORES_MMM_URL
    analytics_dict['comparecohorturl'] = mysettings.COMPARE_COHORT_URL
    analytics_dict['comparesbturl'] = mysettings.COMPARE_SBT_URL
    analytics_dict['compareppturl'] = mysettings.COMPARE_PPT_URL
    analytics_dict['comparettperfurl'] = mysettings.COMPARE_TTPERF_URL
    analytics_dict['compareperfturl'] = mysettings.COMPARE_PERFT_URL
    analytics_dict['comparepassfailurl'] = mysettings.COMPARE_PASSFAIL_URL
    analytics_dict['creatorcompscoreurl'] = mysettings.CREATOR_COMPSCORE_URL
    analytics_dict['creatortestpopurl'] = mysettings.CREATOR_TESTPOP_URL
    analytics_dict['creatortesttimesurl'] = mysettings.CREATOR_TESTTIMES_URL
    analytics_dict['creatortestmmmurl'] = mysettings.CREATOR_TESTMMM_URL
    analytics_dict['creatortestusageurl'] = mysettings.CREATOR_TESTUSAGE_URL
    analytics_dict['creatortestcohorturl'] = mysettings.CREATOR_TESTCOHORT_URL
    analytics_dict['evaluatordisplayurl'] = mysettings.EVALUATOR_DISPLAY_URL
    analytics_dict['evaluatorratiopassurl'] = mysettings.EVALUATOR_PASS_RATIO_URL
    analytics_dict['evaluatorcounttestsurl'] = mysettings.EVALUATOR_COUNT_TESTS_URL
    analytics_dict['evaluatoransbytimeurl'] = mysettings.EVALUATOR_ANSTIME_URL
    analytics_dict['profile_image_tag'] = skillutils.getprofileimgtag(request)

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
    role = ""
    if request.POST.has_key('test_topic'):
        test_topic = request.POST['test_topic']
    else:
        message = "Required parameter missing in post data."
        response = HttpResponse(message)
        return response
    if request.POST.has_key('role'):
        role = request.POST['role']
    else:
        role = ""
    utqset, wuqset = None, None
    if role == "": # Default is candidate role
        utqset = UserTest.objects.filter(user=userobj)
        wuqset = WouldbeUsers.objects.filter(emailaddr=useremail)
    elif role == "creator":
        utqset = UserTest.objects.filter(test__creator=userobj)
        wuqset = WouldbeUsers.objects.filter(test__creator__emailid=useremail)
    elif role == "evaluator":
        utqset1 = UserTest.objects.filter(test__evaluator__groupmember1=userobj)
        utqset2 = UserTest.objects.filter(test__evaluator__groupmember2=userobj)
        utqset3 = UserTest.objects.filter(test__evaluator__groupmember3=userobj)
        utqset4 = UserTest.objects.filter(test__evaluator__groupmember4=userobj)
        utqset5 = UserTest.objects.filter(test__evaluator__groupmember5=userobj)
        utqset6 = UserTest.objects.filter(test__evaluator__groupmember6=userobj)
        utqset7 = UserTest.objects.filter(test__evaluator__groupmember7=userobj)
        utqset8 = UserTest.objects.filter(test__evaluator__groupmember8=userobj)
        utqset9 = UserTest.objects.filter(test__evaluator__groupmember9=userobj)
        utqset10 = UserTest.objects.filter(test__evaluator__groupmember10=userobj)
        utqset = list(chain(utqset1, utqset2, utqset3, utqset4, utqset5, utqset6, utqset7, utqset8, utqset9, utqset10))
        wuqset1 = WouldbeUsers.objects.filter(test__evaluator__groupmember1__emailid=useremail)
        wuqset2 = WouldbeUsers.objects.filter(test__evaluator__groupmember2__emailid=useremail)
        wuqset3 = WouldbeUsers.objects.filter(test__evaluator__groupmember3__emailid=useremail)
        wuqset4 = WouldbeUsers.objects.filter(test__evaluator__groupmember4__emailid=useremail)
        wuqset5 = WouldbeUsers.objects.filter(test__evaluator__groupmember5__emailid=useremail)
        wuqset6 = WouldbeUsers.objects.filter(test__evaluator__groupmember6__emailid=useremail)
        wuqset7 = WouldbeUsers.objects.filter(test__evaluator__groupmember7__emailid=useremail)
        wuqset8 = WouldbeUsers.objects.filter(test__evaluator__groupmember8__emailid=useremail)
        wuqset9 = WouldbeUsers.objects.filter(test__evaluator__groupmember9__emailid=useremail)
        wuqset10 = WouldbeUsers.objects.filter(test__evaluator__groupmember10__emailid=useremail)
        wuqset = list(chain(wuqset1, wuqset2, wuqset3, wuqset4, wuqset5, wuqset6, wuqset7, wuqset8, wuqset9, wuqset10))
    alltestshtml = "<Label style='width:300px;padding-left:5px;display:inline-block;color:#0000AA;font-weight:bold;'>Select a Test:</label>"
    alltestshtml += "<select name='usertests' class='form-control input-lg' style='width:300px;margin-bottom:5px;padding-left:5px;display:inline-block;justify:right;align:right;'><option value='all' selected>Select Test</option>"
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


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def comparescoresmmm(request):
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
    utqset = UserTest.objects.filter(test=testobj)
    wuqset = WouldbeUsers.objects.filter(test=testobj)
    userfound = ""
    testscoresdict = {}
    testscoreslist = []
    for utobj in utqset:
        username = utobj.user.displayname
        score = utobj.score
        if testscoresdict.has_key(username):
            if testscoresdict[username] < score:
                testscoresdict[username] = score
        else:
            testscoresdict[username] = score
        if utobj.user == userobj:
            userfound = score
    for wuobj in wuqset:
        emailaddr = wuobj.emailaddr
        score = wuobj.score
        if testscoresdict.has_key(emailaddr):
            if testscoresdict[emailaddr] < score:
                testscoresdict[emailaddr] = score
        else:
            testscoresdict[emailaddr] = score
        if emailaddr == useremail:
            userfound = score
    testscoreslist = testscoresdict.values()
    scoresum = 0.0
    for s in testscoreslist:
        scoresum += s
    smean = scoresum/testscoreslist.__len__()
    mindx = 0
    if testscoreslist.__len__() % 2 == 1:
        mindx = int(testscoreslist.__len__()/2) + 1
    else:
        mindx = testscoreslist.__len__()/2
    testscoreslist.sort()
    smedian = testscoreslist[mindx]
    scoresdict = {}
    for score in testscoreslist:
        if scoresdict.has_key(score):
            scoresdict[score] += 1
        else:
            scoresdict[score] = 1
    maxrepeat = [ 0, 0]
    for score in scoresdict.keys():
        if scoresdict[score] > maxrepeat[0]:
            maxrepeat[0] = scoresdict[score]
            maxrepeat[1] = score
        else:
            pass
    smode = maxrepeat[1]
    if maxrepeat[0] == 1:
        smode = 0 # No mode is available
    testinfodict['mean'] = [userfound, smean]
    testinfodict['median'] = [userfound, smedian]
    testinfodict['mode'] = [userfound, smode]
    jsonstr = json.dumps(testinfodict)
    response = HttpResponse(jsonstr)
    return response
    

@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def comparecohort(request):
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
    # Find out all users who have taken this test
    testusersemaillist = []
    utqset = UserTest.objects.filter(test=testobj)
    wuqset = WouldbeUsers.objects.filter(test=testobj)
    testinfodict = {}
    uniqemailiddict = {}
    for utobj in utqset:
        useremailid = utobj.emailaddr
        if uniqemailiddict.has_key(useremailid):
            continue
        else:
            uniqemailiddict[useremailid] = 1
        testusersemaillist.append(useremailid)
    for wuobj in wuqset:
        useremailid = wuobj.emailaddr
        if uniqemailiddict.has_key(useremailid):
            continue
        else:
            uniqemailiddict[useremailid] = 1
        testusersemaillist.append(useremailid)
    # So we now have all users (their email Ids in fact), who have taken this test
    # Now lets find out what tests each of the users have taken.
    for emailid in testusersemaillist:
        utqset2 = UserTest.objects.filter(emailaddr=emailid)
        for utobj2 in utqset2:
            try:
                tname = utobj2.test.testname
            except:
                continue
                #return HttpResponse(sys.exc_info()[1].__str__() + tname) # Test matching query does not exist
            if testinfodict.has_key(tname):
                testinfodict[tname] += 1
            else:
                testinfodict[tname] = 1
        wuqset2 = WouldbeUsers.objects.filter(emailaddr=emailid)
        for wuobj2 in wuqset2:
            testname = wuobj2.test.testname
            if testinfodict.has_key(testname):
                testinfodict[testname] += 1
            else:
                testinfodict[testname] = 1
    jsonstr = json.dumps(testinfodict)
    response = HttpResponse(jsonstr)
    return response
    


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def comparesbt(request):
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
    testinfodict = {}
    # Get all tests taken by this user
    allurqset = UserResponse.objects.filter(emailaddr=useremail)
    uniqtestsdict = {}
    for urobj in allurqset:
        if urobj.test.topicname != test_topic and urobj.test.topic.topicname != test_topic:
            continue
	if uniqtestsdict.has_key(urobj.test.testname):
	    continue
        testobj = urobj.test
	uniqtestsdict[testobj.testname] = 1
	utqset = UserTest.objects.filter(test=testobj, user=userobj)
	utobj = None
	if utqset.__len__() > 0:
	    utobj = utqset[0]
	else:
	    continue
        testtime = utobj.starttime
        if not testtime: # Test has not been started yet. We do not consider these tests
            continue
        mon = str(testtime.month)
        day = str(testtime.day)
        hour = str(testtime.hour)
        minute = str(testtime.minute)
        second = str(testtime.second)
        if mon.__len__() < 2:
            mon = '0' + mon
        if day.__len__() < 2:
            day = '0' + day
        if hour.__len__() < 2:
            hour = '0' + hour
        if minute.__len__() < 2:
            minute = '0' + minute
        if second.__len__() < 2:
            second = '0' + second
        testtime_str = str(testtime.year) + "-" + mon + "-" + day + " " + hour + ":" + minute + ":" + second
	testscore = utobj.score
	testinfodict[testobj.testname] = [testtime_str, testscore ]
	wuqset = WouldbeUsers.objects.filter(test=testobj, emailaddr=useremail)
        wuobj = None
	if wuqset.__len__() > 0:
	    wuobj = wuqset[0]
	else:
	    continue
        testtime = wuobj.starttime
        if not testtime: # Test has not been started yet. We do not consider these tests.
            continue
        mon = str(testtime.month)
        day = str(testtime.day)
        hour = str(testtime.hour)
        minute = str(testtime.minute)
        second = str(testtime.second)
        if mon.__len__() < 2:
            mon = '0' + mon
        if day.__len__() < 2:
            day = '0' + day
        if hour.__len__() < 2:
            hour = '0' + hour
        if minute.__len__() < 2:
            minute = '0' + minute
        if second.__len__() < 2:
            second = '0' + second
        testtime_str = str(testtime.year) + "-" + mon + "-" + day + " " + hour + ":" + minute + ":" + second
	testscore = wuobj.score
	testinfodict[testobj.testname] = [testtime_str, testscore ]
    jsonstr = json.dumps(testinfodict)
    response = HttpResponse(jsonstr)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def comparescoreperc(request):
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
    testinfodict = {}
    # First, get all tests taken by the user in ascending order of the 'starttime' field in UserTest and WouldbeUsers models.
    try:
        utqset = UserTest.objects.filter(user=userobj, test__topicname=test_topic, starttime__isnull = False).order_by('starttime')
        wbuqset = WouldbeUsers.objects.filter(emailaddr=useremail, test__topicname=test_topic, starttime__isnull = False).order_by('starttime')
    except:
        return HttpResponse(sys.exc_info()[1].__str__())
    # Sanitize the data
    utlist = list(utqset)
    wbulist = list(wbuqset)
    ctr = 0
    while ctr < utlist.__len__():
        if utlist[ctr].starttime == "":
            utlist.pop(ctr)
        ctr += 1
    ctr = 0
    while ctr < wbulist.__len__():
        if wbulist[ctr].starttime == "":
            wbulist.pop(ctr)
        ctr += 1
    # Now, we take the earliest date/time and the current date/time and divide the time range in periods of 1 month duration.
    if utlist.__len__() == 0 and wbulist.__len__() == 0:
        message = "There is no data available to plot this statistic."
        response = HttpResponse(message)
        return response
    elif utlist.__len__() == 0 and wbulist.__len__() > 0:
        utlist = wbulist
    elif utlist.__len__() > 0 and wbulist.__len__() == 0:
        wbulist = utlist
    t01, t02 = "", ""
    if utlist.__len__() > 0:
        t01 = utlist[0].starttime
    if wbulist.__len__() > 0:
        t02 = wbulist[0].starttime
    curdatetime = datetime.datetime.now()
    t01 = str(t01).split("+")[0]
    t02 = str(t02).split("+")[0]
    try:
        t01_d = datetime.datetime.strptime(t01, '%Y-%m-%d %H:%M:%S')
        t02_d = datetime.datetime.strptime(t02, '%Y-%m-%d %H:%M:%S')
        timeperiods = []
        t0 = t02_d
        if t01_d < t02_d:
            t0 = t01_d
        t = t0
    except:
        return HttpResponse(sys.exc_info()[1].__str__())
    while t < curdatetime:
        try:
            mon = t.month
            year = t.year
            if(str(mon).__len__() < 2):
                mon = '0' + str(mon)
            timetuple = (str(mon), str(year))
            timeperiods.append(timetuple)
            mon = int(mon) + 1
            if mon == 13:
                mon = '01'
                year = year + 1
            if str(mon).__len__() < 2:
                mon = "0" + str(mon)
            tstr = str(year) + "-" + str(mon) + "-01 00:00:00"
            t = datetime.datetime.strptime(tstr, '%Y-%m-%d %H:%M:%S')
        except:
            return HttpResponse(sys.exc_info()[1].__str__())
    for period in timeperiods:
        monbyyear = str(period[0]) + "/" + str(period[1])
        testinfodict[monbyyear] = 0
    percentagedict = {}
    for utobj in utlist:
        score = utobj.score
        maxscore = utobj.test.maxscore
        uttime = str(utobj.starttime)
        uttimeparts = uttime.split(" ")
        if uttimeparts.__len__() < 1:
            continue
        uttimedateparts = uttimeparts[0].split("-")
        mon = str(uttimedateparts[1])
        year = str(uttimedateparts[0])
        if mon.__len__() < 2:
            mon = '0' + mon
        percentage = (float(score)/float(maxscore)) * 100
        monbyyear = mon + "/" + year
        if percentagedict.has_key(monbyyear):
            percentagedict[monbyyear].append(percentage)
        else:
            percentagedict[monbyyear] = [percentage ]
    for wbuobj in wbulist:
        score = wbuobj.score
        maxscore = wbuobj.test.maxscore
        wbutime = str(wbuobj.starttime)
        wbutimeparts = wbutime.split(" ")
        if wbutimeparts.__len__() < 1:
            continue
        wbutimedateparts = wbutimeparts[0].split("-")
        mon = str(wbutimedateparts[1])
        year = str(wbutimedateparts[0])
        if mon.__len__() < 2:
            mon = '0' + mon
        percentage = (float(score)/float(maxscore)) * 100
        monbyyear = mon + "/" + year
        if percentagedict.has_key(monbyyear):
            percentagedict[monbyyear].append(percentage)
        else:
            percentagedict[monbyyear] = [percentage ]
    for period in testinfodict.keys():
        if percentagedict.has_key(period):
            perclist = percentagedict[period]
            count = perclist.__len__()
            percsum = 0
            for perc in perclist:
                percsum += perc
            percentageval = float(percsum)/count
            testinfodict[period] = percentageval
    jsonstr = json.dumps(testinfodict)
    response = HttpResponse(jsonstr)
    return response
    


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def comparettperf(request):
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
    testinfodict = {}
    testtypes = {}
    try:
        for k,v in mysettings.TEST_TYPES.iteritems():
            testtypes[k] = v
        for chtype in testtypes.keys():
            urespqset = UserResponse.objects.filter(emailaddr=useremail, test__topicname=test_topic, challenge__challengetype=chtype)
            for urespobj in urespqset:
                maxscore = urespobj.challenge.challengescore
                obtainedscore = urespobj.evaluation
                if testinfodict.has_key(chtype):
                    scorelist= testinfodict[chtype]
                    scorelist[0] += obtainedscore
                    scorelist[1] += maxscore
                    testinfodict[chtype] = scorelist
                else:
                    testinfodict[chtype] = [obtainedscore, maxscore]
    except:
        return HttpResponse(sys.exc_info()[1].__str__())
    jsonstr = json.dumps(testinfodict)
    response = HttpResponse(jsonstr)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def comparepassfail(request):
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
    testinfodict = {}
    try:
        utqset = UserTest.objects.filter(user=userobj, test__topicname=test_topic, starttime__isnull = False, outcome__isnull=False).order_by('starttime')
        wbuqset = WouldbeUsers.objects.filter(emailaddr=useremail, test__topicname=test_topic, starttime__isnull = False, outcome__isnull=False).order_by('starttime')
    except:
        return HttpResponse(sys.exc_info()[1].__str__())
    # Sanitize the data
    utlist = list(utqset)
    wbulist = list(wbuqset)
    ctr = 0
    while ctr < utlist.__len__():
        if utlist[ctr].starttime == "":
            utlist.pop(ctr)
        ctr += 1
    ctr = 0
    while ctr < wbulist.__len__():
        if wbulist[ctr].starttime == "":
            wbulist.pop(ctr)
        ctr += 1
    # Now, we take the earliest date/time and the current date/time and divide the time range in periods of 1 month duration.
    if utlist.__len__() == 0 and wbulist.__len__() == 0:
        message = "There is no data available to plot this statistic."
        response = HttpResponse(message)
        return response
    elif utlist.__len__() == 0 and wbulist.__len__() > 0:
        utlist = wbulist
    elif utlist.__len__() > 0 and wbulist.__len__() == 0:
        wbulist = utlist
    t01, t02 = "", ""
    if utlist.__len__() > 0:
        t01 = utlist[0].starttime
    if wbulist.__len__() > 0:
        t02 = wbulist[0].starttime
    curdatetime = datetime.datetime.now()
    t01 = str(t01).split("+")[0]
    t02 = str(t02).split("+")[0]
    try:
        t01_d = datetime.datetime.strptime(t01, '%Y-%m-%d %H:%M:%S')
        t02_d = datetime.datetime.strptime(t02, '%Y-%m-%d %H:%M:%S')
        timeperiods = []
        t0 = t02_d
        if t01_d < t02_d:
            t0 = t01_d
        t = t0
    except:
        return HttpResponse(sys.exc_info()[1].__str__())
    while t < curdatetime:
        try:
            mon = t.month
            year = t.year
            if(str(mon).__len__() < 2):
                mon = '0' + str(mon)
            timetuple = (str(mon), str(year))
            timeperiods.append(timetuple)
            mon = int(mon) + 1
            if mon == 13:
                mon = '01'
                year = year + 1
            if str(mon).__len__() < 2:
                mon = "0" + str(mon)
            tstr = str(year) + "-" + str(mon) + "-01 00:00:00"
            t = datetime.datetime.strptime(tstr, '%Y-%m-%d %H:%M:%S')
        except:
            return HttpResponse(sys.exc_info()[1].__str__())
    for period in timeperiods:
        monbyyear = str(period[0]) + "/" + str(period[1])
        testinfodict[monbyyear] = 0
    outcomedict = {}
    for utobj in utlist:
        outcome = utobj.outcome
        uttime = str(utobj.starttime)
        uttimeparts = uttime.split(" ")
        if uttimeparts.__len__() < 1:
            continue
        uttimedateparts = uttimeparts[0].split("-")
        mon = str(uttimedateparts[1])
        year = str(uttimedateparts[0])
        if mon.__len__() < 2:
            mon = '0' + mon
        monbyyear = mon + "/" + year
        if outcomedict.has_key(monbyyear):
            outcomelist = outcomedict[monbyyear]
            if outcome:
                outcomelist[0] += 1 # Passes
            else:
                outcomelist[1] += 1 # Fails
            outcomedict[monbyyear] = outcomelist
        else:
            outcomelist = [0, 0]
            if outcome:
                outcomelist = [1, 0]
            else:
                outcomelist = [0, 1]
            outcomedict[monbyyear] = outcomelist
    for wbuobj in wbulist:
        outcome = utobj.outcome
        wbutime = str(wbuobj.starttime)
        wbutimeparts = wbutime.split(" ")
        if wbutimeparts.__len__() < 1:
            continue
        wbutimedateparts = wbutimeparts[0].split("-")
        mon = str(wbutimedateparts[1])
        year = str(wbutimedateparts[0])
        if mon.__len__() < 2:
            mon = '0' + mon
        monbyyear = mon + "/" + year
        if outcomedict.has_key(monbyyear):
            outcomelist = outcomedict[monbyyear]
            if outcome:
                outcomelist[0] += 1 # Passes
            else:
                outcomelist[1] += 1 # Fails
            outcomedict[monbyyear] = outcomelist
        else:
            outcomelist = [0, 0]
            if outcome:
                outcomelist = [1, 0]
            else:
                outcomelist = [0, 1]
            outcomedict[monbyyear] = outcomelist
    for period in testinfodict.keys():
        if outcomedict.has_key(period):
            outcomelist = outcomedict[period]
            testinfodict[period] = outcomelist
        else:
            testinfodict[period] = [0, 0]
    jsonstr = json.dumps(testinfodict)
    response = HttpResponse(jsonstr)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def creatorcompscores(request):
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
    if testid == 'all':
        message = "Required parameter (testid) missing."
        response = HttpResponse(message)
        return response
    testobj = Test.objects.get(id=testid)
    #Check if the user is the creator of this test. If not, send a message back informing the user about it.
    if testobj.creator != userobj:
        message = "You are not the creator of this test. Hence it would not be possible for you to view the scores of the takers of this test."
        response = HttpResponse(message)
        return response
    # Find out all users who have taken this test
    testusersemaillist = []
    utqset = UserTest.objects.filter(test=testobj, evalcommitstate=True, disqualified=False, starttime__isnull = False, cancelled=False)
    wuqset = WouldbeUsers.objects.filter(test=testobj, evalcommitstate=True, disqualified=False, starttime__isnull = False, cancelled=False)
    testinfodict = {}
    for utobj in utqset:
        username = utobj.user.displayname
        score = utobj.score
        if testinfodict.has_key(username) and testinfodict[username] < score: # Display highest score if user has taken multiple attempts.
            testinfodict[username] = score
        elif not testinfodict.has_key(username):
            testinfodict[username] = score
        else:
            pass
    for wbuobj in wuqset:
        emailid = wbuobj.emailaddr
        score = wbuobj.score
        if testinfodict.has_key(emailid) and testinfodict[emailid] < score: # Display highest score if user has taken multiple attempts.
            testinfodict[emailid] = score
        elif not testinfodict.has_key(emailid):
            testinfodict[emailid] = score
        else:
            pass
    jsonstr = json.dumps(testinfodict)
    response = HttpResponse(jsonstr)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def creatortestpopularity(request):
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
        if request.POST['testid'] == 'all':
            testid = ""
        else:
            testid = request.POST['testid']
    else:
        pass
    testobj = None
    testslist = []
    if testid != "":
        testobj = Test.objects.get(id=testid)
    if testobj is not None:
        if testobj.creator != userobj:
            message = "You are not the creator of this test. Hence you may not view the popularity of this test. Please select a topic to view the popularity of all tests under that topic of which you are the creator."
            response = HttpResponse(message)
            return response
        else:
            testslist.append(testobj)
    else:
        # Create a list of tests under the given topic
        try:
            testsqset = Test.objects.filter(topicname=test_topic, creator=userobj)
            moretests = Test.objects.filter(topic__topicname=test_topic, creator=userobj)
            testslist = list(chain(testsqset, moretests))
        except:
            return HttpResponse(sys.exc_info()[1].__str__())
    testinfodict = {}
    for tobj in testslist:
        testname = tobj.testname
        utqset = UserTest.objects.filter(test=tobj)
        wbuqset = WouldbeUsers.objects.filter(test=tobj)
        takerscount = list(utqset).__len__() + list(wbuqset).__len__()
        testinfodict[testname] = takerscount
    jsonstr = json.dumps(testinfodict)
    response = HttpResponse(jsonstr)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def creatortesttimes(request):
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
    if testid == 'all':
        message = "Required parameter (testid) missing."
        response = HttpResponse(message)
        return response
    testobj = Test.objects.get(id=testid)
    if testobj.creator != userobj:
        message = "You are not the creator of this test. Hence you may not view details of this test. Please select a test you created to view its details."
        response = HttpResponse(message)
        return response
    testinfodict = {}
    utqset = UserTest.objects.filter(test=testobj, starttime__isnull=False)
    wbuqset = WouldbeUsers.objects.filter(test=testobj, starttime__isnull=False)
    for utobj in utqset:
        starttime = utobj.starttime
        if starttime is not None:
            starttime = starttime.strftime("%Y-%m-%dT%H:%M:%S")
        username = utobj.user.displayname
        if testinfodict.has_key(username):
            timeslist = testinfodict[username]
            timeslist.append(starttime)
            testinfodict[username] = timeslist
        else:
            timeslist = []
            timeslist.append(starttime)
            testinfodict[username] = timeslist
    for wbuobj in wbuqset:
        emailid = wbuobj.emailaddr
        starttime = wbuobj.starttime
        if starttime is not None:
            starttime = starttime.strftime("%Y-%m-%dT%H:%M:%S")
        if testinfodict.has_key(emailid):
            timeslist = testinfodict[emailid]
            timeslist.append(starttime)
            testinfodict[emailid] = timeslist
        else:
            timeslist = []
            timeslist.append(starttime)
            testinfodict[emailid] = timeslist
    jsonstr = json.dumps(testinfodict)
    response = HttpResponse(jsonstr)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def creatortestmmm(request):
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
    if testid == 'all':
        message = "Required parameter (testid) missing."
        response = HttpResponse(message)
        return response
    try:
        testobj = Test.objects.get(id=testid)
        if testobj.creator != userobj:
            message = "You are not the creator of this test. Hence you may not view details of this test. Please select a test you created to view its details."
            response = HttpResponse(message)
            return response
        testinfodict = {}
        utqset = UserTest.objects.filter(test=testobj)
        wbuqset = WouldbeUsers.objects.filter(test=testobj)
    except:
        return HttpResponse(sys.exc_info()[1].__str__())
    testscoresdict = {}
    testscoreslist = []
    for utobj in utqset:
        username = utobj.user.displayname
        score = utobj.score
        if testscoresdict.has_key(username):
            if testscoresdict[username] < score:
                testscoresdict[username] = score
        else:
            testscoresdict[username] = score
    for wbuobj in wbuqset:
        emailaddr = wbuobj.emailaddr
        score = wbuobj.score
        if testscoresdict.has_key(emailaddr):
            if testscoresdict[emailaddr] < score:
                testscoresdict[emailaddr] = score
        else:
            testscoresdict[emailaddr] = score
    testscoreslist = testscoresdict.values()
    scoresum = 0.0
    for s in testscoreslist:
        scoresum += s
    smean = scoresum/testscoreslist.__len__()
    mindx = 0
    if testscoreslist.__len__() % 2 == 1:
        mindx = int(testscoreslist.__len__()/2) + 1
    else:
        mindx = testscoreslist.__len__()/2
    testscoreslist.sort()
    smedian = testscoreslist[mindx]
    scoresdict = {}
    for score in testscoreslist:
        if scoresdict.has_key(score):
            scoresdict[score] += 1
        else:
            scoresdict[score] = 1
    maxrepeat = [ 0, 0]
    for score in scoresdict.keys():
        if scoresdict[score] > maxrepeat[0]:
            maxrepeat[0] = scoresdict[score]
            maxrepeat[1] = score
        else:
            pass
    smode = maxrepeat[1]
    if maxrepeat[0] == 1:
        smode = 0 # No mode is available
    testinfodict['mean'] = smean
    testinfodict['median'] = smedian
    testinfodict['mode'] = smode
    jsonstr = json.dumps(testinfodict)
    response = HttpResponse(jsonstr)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def creatortestusage(request):
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
    # Get all tests created by this user under the given topic
    testsqset = Test.objects.filter(creator=userobj, topicname=test_topic)
    moretestsqset = Test.objects.filter(creator=userobj, topic__topicname=test_topic)
    testinfodict = {}
    try:
        for testobj in testsqset:
            utqset = UserTest.objects.filter(test=testobj)
            wbuqset = WouldbeUsers.objects.filter(test=testobj)
            testname = testobj.testname
            testscount = list(utqset).__len__() + list(wbuqset).__len__()
            testinfodict[testname] = testscount
        for testobj in moretestsqset:
            utqset = UserTest.objects.filter(test=testobj)
            wbuqset = WouldbeUsers.objects.filter(test=testobj)
            testname = testobj.testname
            testscount = list(utqset).__len__() + list(wbuqset).__len__()
            if testinfodict.has_key(testname):
                testinfodict[testname] += testscount
            else:
                testinfodict[testname] = testscount
    except:
        return HttpResponse(sys.exc_info()[1].__str__())
    jsonstr = json.dumps(testinfodict)
    response = HttpResponse(jsonstr)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def creatortestcohort(request):
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
    if testid == "all":
        message = "Required parameter (testid) missing."
        response = HttpResponse(message)
        return response
    testobj = Test.objects.get(id=testid)
    if testobj.creator != userobj:
        message = "You are not the creator of this test. Hence you may not view details of this test. Please select a test you created to view its details."
        response = HttpResponse(message)
        return response
    testinfodict = {}
    utqset = UserTest.objects.filter(test=testobj)
    wbuqset = WouldbeUsers.objects.filter(test=testobj)
    testuserslist = []
    uniqusers = {}
    for utobj in utqset:
        username = utobj.user.displayname
        if uniqusers.has_key(username):
            pass
        else:
            testuserslist.append(username)
            uniqusers[username] = 1
    for wbuobj in wbuqset:
        emailid = wbuobj.emailaddr
        if uniqusers.has_key(emailid):
            pass
        else:
            testuserslist.append(emailid)
            uniqusers[emailid] = 1
    for usr in testuserslist:
        emailpat = re.compile("@")
        # Check if the usr value is an email or a username
        foundflag = re.search(emailpat, usr)
        uobj = None
        utqset2 = None
        wbuqset2 = None
        if not foundflag: # User is a registered user. So find the user object for this user.
            uobj = User.objects.get(displayname=usr)
            try:
                utqset2 = UserTest.objects.filter(user=uobj).exclude(test = testobj)
                for utobj2 in utqset2:
                    testname = utobj2.test.testname
                    if testinfodict.has_key(testname):
                        testinfodict[testname] += 1
                    else:
                        testinfodict[testname] = 1
            except:
                continue
        else:
            try:
                wbuqset2 = WouldbeUsers.objects.filter(emailaddr = usr).exclude(test=testobj)
                for wbuobj2 in wbuqset2:
                    testname = wbuobj2.test.testname
                    if testinfodict.has_key(testname):
                        testinfodict[testname] += 1
                    else:
                        testinfodict[testname] = 1
            except:
                continue
    jsonstr = json.dumps(testinfodict)
    response = HttpResponse(jsonstr)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def evaluatorpassratio(request):
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
    canview = False
    creatorobj = testobj.creator
    evaluator = testobj.evaluator
    if userobj == creatorobj:
        canview = True
    if canview == False:
        if (evaluator.groupmember1 and userobj == evaluator.groupmember1) or (evaluator.groupmember2 and userobj == evaluator.groupmember2) or (evaluator.groupmember3 and userobj == evaluator.groupmember3) or (evaluator.groupmember4 and userobj == evaluator.groupmember4) or (evaluator.groupmember5 and userobj == evaluator.groupmember5) or (evaluator.groupmember6 and userobj == evaluator.groupmember6) or (evaluator.groupmember7 and userobj == evaluator.groupmember7) or (evaluator.groupmember8 and userobj == evaluator.groupmember8) or (evaluator.groupmember9 and userobj == evaluator.groupmember9) or (evaluator.groupmember10 and userobj == evaluator.groupmember10):
            canview = True
    if canview == False: # user is not an evaluator or creator of this test. Hence, she cannot view the stats.
        message = "You are not an evaluator or creator of this test. Hence, you may not view the stats for this test. Select a test in which you have played the role of an evaluator or creator to view its stats."
        response = HttpResponse(message)
        return response
    # User may view the stats for this test.
    utqset = UserTest.objects.filter(test=testobj)
    wbuqset = WouldbeUsers.objects.filter(test=testobj)
    testinfodict = {}
    total_tests = list(utqset).__len__() + list(wbuqset).__len__()
    pass_count = 0
    fail_count = 0
    not_evaluated = 0
    for utobj in utqset:
        if utobj.outcome == True:
            pass_count += 1
        elif utobj.outcome == False:
            fail_count += 1
        elif utobj.outcome == "" or utobj.outcome == None:
            not_evaluated += 1
        else:
            pass
    for wbuobj in wbuqset:
        if wbuobj.outcome == True:
            pass_count += 1
        elif wbuobj.outcome == False:
            fail_count += 1
        elif wbuobj.outcome == "" or wbuobj.outcome == None:
            not_evaluated += 1
        else:
            pass
    testinfodict['passed'] = pass_count
    testinfodict['failed'] = fail_count
    testinfodict['not evaluated'] = not_evaluated
    testinfodict['total'] = total_tests
    jsonstr = json.dumps(testinfodict)
    response = HttpResponse(jsonstr)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def evaluatorcounttests(request):
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
    utqset = UserTest.objects.filter(test__topicname=test_topic, score__isnull = False)
    wbuqset = WouldbeUsers.objects.filter(test__topicname=test_topic, score__isnull = False)
    testinfodict = {}
    for utobj in utqset:
        tobj = utobj.test
        isevaluator = False
        if tobj.creator == userobj:
            isevaluator = True
        evalobj = utobj.test.evaluator
        if isevaluator == False and (evalobj.groupmember1 and evalobj.groupmember1 == userobj) or (evalobj.groupmember2 and evalobj.groupmember2 == userobj) or (evalobj.groupmember3 and evalobj.groupmember3 == userobj) or (evalobj.groupmember4 and evalobj.groupmember4 == userobj) or (evalobj.groupmember5 and evalobj.groupmember5 == userobj) or (evalobj.groupmember6 and evalobj.groupmember6 == userobj) or (evalobj.groupmember7 and evalobj.groupmember7 == userobj) or (evalobj.groupmember8 and evalobj.groupmember8 == userobj) or (evalobj.groupmember9 and evalobj.groupmember9 == userobj) or (evalobj.groupmember10 and evalobj.groupmember10 == userobj):
            isevaluator = True
        if isevaluator == False:
            continue # The user is not an evaluator of this test.
        testname = tobj.testname
        if testinfodict.has_key(testname):
            testinfodict[testname] += 1
        else:
            testinfodict[testname] = 1
    for wbuobj in wbuqset:
        tobj = wbuobj.test
        isevaluator = False
        if tobj.creator == userobj:
            isevaluator = True
        evalobj = wbuobj.test.evaluator
        if isevaluator == False and (evalobj.groupmember1 and evalobj.groupmember1 == userobj) or (evalobj.groupmember2 and evalobj.groupmember2 == userobj) or (evalobj.groupmember3 and evalobj.groupmember3 == userobj) or (evalobj.groupmember4 and evalobj.groupmember4 == userobj) or (evalobj.groupmember5 and evalobj.groupmember5 == userobj) or (evalobj.groupmember6 and evalobj.groupmember6 == userobj) or (evalobj.groupmember7 and evalobj.groupmember7 == userobj) or (evalobj.groupmember8 and evalobj.groupmember8 == userobj) or (evalobj.groupmember9 and evalobj.groupmember9 == userobj) or (evalobj.groupmember10 and evalobj.groupmember10 == userobj):
            isevaluator = True
        if isevaluator == False:
            continue # The user is not an evaluator of this test.
        testname = tobj.testname
        if testinfodict.has_key(testname):
            testinfodict[testname] += 1
        else:
            testinfodict[testname] = 1
    jsonstr = json.dumps(testinfodict)
    response = HttpResponse(jsonstr)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def evaluatoranswerscriptsbytime(request):
    """
    Line Plot number of answerscripts evaluated in a monthly periods starting from the user's sign up time.  
    """
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
    utqset = UserTest.objects.filter(test__topicname=test_topic, score__isnull = False).order_by('starttime')
    wbuqset = WouldbeUsers.objects.filter(test__topicname=test_topic, score__isnull = False).order_by('starttime')
    testinfodict = {}
    signuptime = userobj.joindate
    curdatetime = datetime.datetime.now()
    signuptime = signuptime.replace(tzinfo=None) # make signuptime offset naive... we don't need offset aware datetime here.
    t = signuptime
    timeperiods = []
    try:
        while t < curdatetime:
            try:
                mon = t.month
                year = t.year
                if(str(mon).__len__() < 2):
                    mon = '0' + str(mon)
                timetuple = (str(mon), str(year))
                timeperiods.append(timetuple)
                mon = int(mon) + 1
                if mon == 13:
                    mon = '01'
                    year = year + 1
                if str(mon).__len__() < 2:
                    mon = "0" + str(mon)
                tstr = str(year) + "-" + str(mon) + "-01 00:00:00"
                t = datetime.datetime.strptime(tstr, '%Y-%m-%d %H:%M:%S')
            except:
                return HttpResponse(sys.exc_info()[1].__str__())
    except:
        return HttpResponse(sys.exc_info()[1].__str__())
    for tp in timeperiods:
        tpstr = tp[0] + "/" + tp[1]
        testinfodict[tpstr] = 0
    for utobj in utqset:
        isevaluator = False
        if utobj.test.creator == userobj:
            isevaluator = True
        evalobj = utobj.test.evaluator
        if isevaluator == False and (evalobj.groupmember1 and evalobj.groupmember1 == userobj) or (evalobj.groupmember2 and evalobj.groupmember2 == userobj) or (evalobj.groupmember3 and evalobj.groupmember3 == userobj) or (evalobj.groupmember4 and evalobj.groupmember4 == userobj) or (evalobj.groupmember5 and evalobj.groupmember5 == userobj) or (evalobj.groupmember6 and evalobj.groupmember6 == userobj) or (evalobj.groupmember7 and evalobj.groupmember7 == userobj) or (evalobj.groupmember8 and evalobj.groupmember8 == userobj) or (evalobj.groupmember9 and evalobj.groupmember9 == userobj) or (evalobj.groupmember10 and evalobj.groupmember10 == userobj):
            isevaluator = True
        if isevaluator == False:
            continue # The user is not an evaluator of this test.
        evalts = utobj.first_eval_timestamp
        if not evalts or evalts == "":
            continue
        evaldt = datetime.datetime.fromtimestamp(float(evalts))
        evalmon = evaldt.month
        evalyear = evaldt.year
        if str(evalmon).__len__() < 2:
            evalmon = "0" + str(evalmon)
        evalperiod = str(evalmon) + "/" + str(evalyear)
        testinfodict[evalperiod] += 1
    for wbuobj in wbuqset:
        isevaluator = False
        if wbuobj.test.creator == userobj:
            isevaluator = True
        evalobj = wbuobj.test.evaluator
        if isevaluator == False and (evalobj.groupmember1 and evalobj.groupmember1 == userobj) or (evalobj.groupmember2 and evalobj.groupmember2 == userobj) or (evalobj.groupmember3 and evalobj.groupmember3 == userobj) or (evalobj.groupmember4 and evalobj.groupmember4 == userobj) or (evalobj.groupmember5 and evalobj.groupmember5 == userobj) or (evalobj.groupmember6 and evalobj.groupmember6 == userobj) or (evalobj.groupmember7 and evalobj.groupmember7 == userobj) or (evalobj.groupmember8 and evalobj.groupmember8 == userobj) or (evalobj.groupmember9 and evalobj.groupmember9 == userobj) or (evalobj.groupmember10 and evalobj.groupmember10 == userobj):
            isevaluator = True
        if isevaluator == False:
            continue # The user is not an evaluator of this test.
        evalts = wbuobj.first_eval_timestamp
        if not evalts or evalts == "":
            continue
        evaldt = datetime.datetime.fromtimestamp(float(evalts))
        evalmon = evaldt.month
        evalyear = evaldt.year
        if str(evalmon).__len__() < 2:
            evalmon = "0" + str(evalmon)
        evalperiod = str(evalmon) + "/" + str(evalyear)
        testinfodict[evalperiod] += 1
    jsonstr = json.dumps(testinfodict)
    response = HttpResponse(jsonstr)
    return response 




