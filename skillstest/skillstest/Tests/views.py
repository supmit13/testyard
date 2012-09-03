from django.conf import settings
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.core.context_processors import csrf
from django.views.generic import View
from django.http import HttpResponseBadRequest, HttpResponse, HttpResponseRedirect
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
from passlib.hash import pbkdf2_sha256 # To create hash of passwords

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


def get_user_tests(request):
    # If request method is 'GET', then retrieve Session and User info from the DB
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    testlist_ascreator = Test.objects.filter(creator=userobj)
    # Determine if the user should be shown the "Create Test" link
    createlink, testtypes, testrules, testtopics, skilltarget, testscope, answeringlanguage, progenv, existingtestnames, assocevalgrps, evalgroupslitags, createtesturl, addeditchallengeurl = "", "", "", "", "", "", "", "", "", "var evalgrpsdict = {};", "", mysettings.CREATE_TEST_URL, mysettings.EDIT_TEST_URL
    if testlist_ascreator.__len__() <= mysettings.NEW_USER_FREE_TESTS_COUNT: # Also add condition to check user's 'plan' (to be done later)
        createlink = "<a href='#' onClick='javascript:showcreatetestform(&quot;%s&quot;);loaddatepicker();'>Create New Test</a>"%userobj.id
        for ttcode in mysettings.TEST_TYPES.keys():
            ttcodeval = ttcode.replace(" ", "__")
            if ttcode == 'MULT':
                testtypes += "<option value=&quot;%s&quot; selected>%s</option>"%(ttcodeval, mysettings.TEST_TYPES[ttcode])
            else:
                testtypes += "<option value=&quot;%s&quot;>%s</option>"%(ttcodeval, mysettings.TEST_TYPES[ttcode])
        for trule in mysettings.RULES_DICT.keys():
            testrules += "<option value=&quot;%s&quot;>%s</option>"%(trule, mysettings.RULES_DICT[trule])
        for ttopics in mysettings.TEST_TOPICS:
            ttopicsval = ttopics.replace(" ", "__")
            testtopics += "<option value=&quot;%s&quot;>%s</option>"%(ttopicsval, ttopics)
        # Get topics created in the past by this user
        usertopics = Topic.objects.filter(user=userobj, isactive=True)
        for topic in usertopics:
            topicname = topic.topicname.replace(" ", "__")
            testtopics += "<option value=&quot;%s&quot;>%s</option>"%(topicname, topic.topicname)
        for skillcode in mysettings.SKILL_QUALITY.keys():
            skilltarget += "<option value=&quot;%s&quot;>%s</option>"%(skillcode, mysettings.SKILL_QUALITY[skillcode])
        for tscope in mysettings.TEST_SCOPES:
            if tscope == 'private':
                testscope += "<option value=&quot;%s&quot; selected>%s</option>"%(tscope, tscope)
            else:
                testscope += "<option value=&quot;%s&quot;>%s</option>"%(tscope, tscope)
        for alang in mysettings.ANSWER_LANG_DICT.keys():
            if alang == 'enus':
                answeringlanguage += "<option value=&quot;%s&quot; selected>%s</option>"%(alang, mysettings.ANSWER_LANG_DICT[alang])
            else:
                answeringlanguage += "<option value=&quot;%s&quot;>%s</option>"%(alang, mysettings.ANSWER_LANG_DICT[alang])
        progenv += "<option value=&quot;0&quot; selected>None</option>"
        for proglang in mysettings.COMPILER_LOCATIONS.keys():
            progenv += "<option value=&quot;%s&quot;>Yes - %s</option>"%(proglang, proglang)
    
    evaluator_groups = Evaluator.objects.filter(Q(groupmember1=userobj)|Q(groupmember2=userobj)|Q(groupmember3=userobj)| \
                                                Q(groupmember4=userobj)|Q(groupmember5=userobj)|Q(groupmember6=userobj)| \
                                                Q(groupmember7=userobj)|Q(groupmember8=userobj)|Q(groupmember9=userobj)| \
                                                Q(groupmember10=userobj))
    testlist_asevaluator = Test.objects.filter(evaluator__in=evaluator_groups)
    user_creator_other_evaluators_dict = {}
    for test in testlist_ascreator:
        user_creator_other_evaluators_dict[test.testname] = ( test.evaluator.groupmember1, test.evaluator.groupmember2, \
                                                              test.evaluator.groupmember3, test.evaluator.groupmember4, test.evaluator.groupmember5, \
                                                              test.evaluator.groupmember6, test.evaluator.groupmember7, test.evaluator.groupmember8, \
                                                              test.evaluator.groupmember9, test.evaluator.groupmember10 )
        evalgrpemaillist = []
        if test.evaluator.groupmember1 is not None:
            evalgrpemaillist.append(test.evaluator.groupmember1.emailid)
        if test.evaluator.groupmember2 is not None:
            evalgrpemaillist.append(test.evaluator.groupmember2.emailid)
        if test.evaluator.groupmember3 is not None:
            evalgrpemaillist.append(test.evaluator.groupmember3.emailid)
        if test.evaluator.groupmember4 is not None:
            evalgrpemaillist.append(test.evaluator.groupmember4.emailid)
        if test.evaluator.groupmember5 is not None:
            evalgrpemaillist.append(test.evaluator.groupmember5.emailid)
        if test.evaluator.groupmember6 is not None:
            evalgrpemaillist.append(test.evaluator.groupmember6.emailid)
        if test.evaluator.groupmember7 is not None:
            evalgrpemaillist.append(test.evaluator.groupmember7.emailid)
        if test.evaluator.groupmember8 is not None:
            evalgrpemaillist.append(test.evaluator.groupmember8.emailid)
        if test.evaluator.groupmember9 is not None:
            evalgrpemaillist.append(test.evaluator.groupmember9.emailid)
        if test.evaluator.groupmember10 is not None:
            evalgrpemaillist.append(test.evaluator.groupmember10.emailid)
        evalgrpemails = ",".join(evalgrpemaillist)
        assocevalgrps += "evalgrpsdict.%s = '%s';"%(test.evaluator.evalgroupname, evalgrpemails)
        evalgroupslitags += "<li id=&quot;%s&quot; title=&quot;%s&quot;>%s</li>"%(test.evaluator.evalgroupname, evalgrpemails, test.evaluator.evalgroupname)
        evalgroupslitags = evalgroupslitags.replace('&quot;', '\\"')

    user_evaluator_creator_other_evaluators_dict = {}
    test = None
    for test in testlist_asevaluator:
        testcreator = test.creator
        testname = test.testname
        creator_evaluators = ( testcreator, test.evaluator.groupmember1, test.evaluator.groupmember2, test.evaluator.groupmember3, test.evaluator.groupmember4, \
                          test.evaluator.groupmember5, test.evaluator.groupmember6, test.evaluator.groupmember7, test.evaluator.groupmember8, \
                          test.evaluator.groupmember9, test.evaluator.groupmember10 ) # Basically we keep the creator as the first element. Rest are evaluators.
        user_evaluator_creator_other_evaluators_dict[testname] = creator_evaluators

    try:
        testlist_ascandidate = UserTest.objects.filter(user=userobj)[0].test
    except: # Can't say if we will find any records...
        testlist_ascandidate = []
    user_candidate_other_creator_evaluator_dict = {}
    for test in testlist_ascandidate:
        testcreator = test.creator
        creator_evaluators = ( testcreator, test.evaluator.groupmember1, test.evaluator.groupmember2, test.evaluator.groupmember3, test.evaluator.groupmember4, \
                          test.evaluator.groupmember5, test.evaluator.groupmember6, test.evaluator.groupmember7, test.evaluator.groupmember8, \
                          test.evaluator.groupmember9, test.evaluator.groupmember10 )
        user_candidate_other_creator_evaluator_dict[test.testname] = creator_evaluators
    tests_user_dict = {}
    tests_user_dict['user_creator_other_evaluators_dict'] = user_creator_other_evaluators_dict
    tests_user_dict['user_evaluator_creator_other_evaluators_dict'] = user_evaluator_creator_other_evaluators_dict
    tests_user_dict['user_candidate_other_creator_evaluator_dict'] = user_candidate_other_creator_evaluator_dict
    tests_user_dict['profile_image_tag'] = skillutils.getprofileimgtag(request)
    tests_user_dict['displayname'] = userobj.displayname
    tests_user_dict['createlink'] = createlink
    tests_user_dict['testtypes'] = testtypes
    tests_user_dict['testrules'] = testrules
    tests_user_dict['testtopics'] = testtopics
    tests_user_dict['skilltarget'] = skilltarget
    tests_user_dict['answeringlanguage'] = answeringlanguage
    tests_user_dict['testscope'] = testscope
    tests_user_dict['progenv'] = progenv
    tests_user_dict['creatoremail'] = userobj.emailid
    tests_user_dict['existingtestnames'] = "','".join(user_creator_other_evaluators_dict.keys())
    tests_user_dict['existingtestnames'] = "'" + tests_user_dict['existingtestnames'] + "'"
    tests_user_dict['assocevalgrps'] = assocevalgrps
    tests_user_dict['evalgroupslitags'] = evalgroupslitags
    tests_user_dict['createtesturl'] = createtesturl
    tests_user_dict['addeditchallengeurl'] = skillutils.gethosturl(request) + "/" + mysettings.EDIT_TEST_URL
    tests_user_dict['testsummaryurl'] = mysettings.TEST_SUMMARY_URL
    tests_user_dict['deletechallengesurl'] = skillutils.gethosturl(request) + "/" + mysettings.DELETE_CHALLENGE_URL
    tests_user_dict['hosturl'] = skillutils.gethosturl(request) 
    tests_user_dict['testlinkid'] = skillutils.generate_random_string()
    return  tests_user_dict


"""
This view will provide the following functionalities:
Display a table of tests with latest first... These are all tests the user has created. This page will give the user
# all access to all those tests in which she/he is a creator, evaluator or candidate. For tests in which  user is
# creator or evaluator, she/he will be able to access the answer scripts of candidates who took those tests. We get
all this data in dashboard too, but from here the user will be able to go into deeper details like exact questions
attempted by a certain candidate, the exact choices/answers the candidate made and how much points/grades the user
conceded to the candidate for that answer. NOTE: This page will also provide the user with the capability to add and
modify tests that are scheduled in future and in which she/he is creator. This page will display a link that will
enable the user to create tests (if he is a premium user or has conducted less than skills_settings.NEW_USER_FREE_TESTS_COUNT since registering), add/modify/delete candidates to those tests, make assessm-
ents for tests in which she/he is the evaluator, etc.
The page consists of following:
    1) A list of all tests (of past) in which she/he is creator, ordered latest first. The fields are "Test name", "Test URL"
    (This is the url at which the creator or evaluators can access just the questions of the test in one place (as if written
    down on a physical paper), the "Test rules" associated with the entire test (or rather a popup/popunder that lists out
    the actual rules), "Full Marks", "How many candidates were invited", "How many candidates took the test", "How many suc-
    ceeded", "Percentage of successful candidates", "Percent failure", "Candidates disqualified, if any, and a popunder dis-
    playing a note of the reason of disqualification", "total marks", "negative marking, if set", "Date of test creation",
    "Date of test", "Date of test assessment (if it took more than one day to assess, then the day assessment  was completed",
    "List of the evaluators of the test (the evaluator group name, and the evaluator names too, each evaluator name will be
    a link which will lead to a page that displays the details of that evaluator pertaining to that test)", "topic and sub-
    topic of the test" and  any comments on the test made by an evaluator (or creator herself/himself) about the test.
    2) List of all tests in which the user is evaluator. Fields will be similar to above and with the addition of "Creator name of the test" and number of candidates the user assessed. This will be a link to the page which lists all candidates of the test that the user had evaluated and the names of the candidates will be links to the score (for each
question) made by the candidate and any comment added by the user against it. (The same will be available to creator if the creator is given permission to view evaluator info)
    3) List of all tests in which user had been a candidate and this will display such fields as appropriate.
    4)There will be a create test link on the top (accessible only to paid users and new users whose quota of complimentary tests is not finished)
    5) Next it will list out all upcoming tests in which the user  can register as a candidate (there would link to a page that registers a user for a test). However candidates can take that test only if the creator allows it. That mechanism will be detailed later. Whenever a user registers for a specific test, the creator of that test is sent  an email mentioning that. 
"""
@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def manage(request):
    message = ''
    if request.method != "GET": # Illegal bad request... 
        message = error_msg('1004')
        # A logging mechanism may be used to track how many and from where
        # such requests come and that may, sometimes, tell a curious story.
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.DASHBOARD_URL + "?msg=%s"%message)
        return response
    tests_user_dict = get_user_tests(request)
    inc_context = skillutils.includedtemplatevars("Tests", request) # Since this is the 'Dashboard' page for the user.
    for inc_key in inc_context.keys():
        tests_user_dict[inc_key] = inc_context[inc_key]
    # Now create and render the template here
    tmpl = get_template("tests/tests.html")
    tests_user_dict.update(csrf(request))
    cxt = Context(tests_user_dict)
    managetestshtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        managetestshtml = managetestshtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(managetestshtml)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def create(request):
    message = ''
    if request.method == "GET": # Illegal bad request... 
        message = error_msg('1004')
        # A logging mechanism may be used to track how many and from where
        # such requests come and that may, sometimes, tell a curious story.
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.MANAGE_TEST_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    testlinkid, testname, testtype, testrules, testtopic, othertopicname, \
    totalscore, numchallenges, evendistribution, negativescoring, testduration,\
    testdurationunit, challengeduration, challengedurationunit, evaluators, \
    grpname, publishdate, activedate, skilltarget, testscope,answerlanguage, \
    progenv, multimediareqd, randomsequencing, multipleattemptsallowed, \
    maxattemptscount, attemptsinterval, attemptsintervalunit, testlinkid, \
    csrfmiddlewaretoken  = "", "", "", "", "", "", "", "", "", "", "", "", "", \
     "", "", "", "", "", "", "", "", "", False, False, False, "", "", "", "", ""
    lastchallengectr, challengenumbersstr, passscore = "", "", "" # \
    # 'lastchallengectr' is the counter of the last challenge entered. \
    # 'challengenumbersstr' is a string consisting of all the created \
    # challenge counters separated by '#||#'.
    challengectr, challengestatement, challengetype, responsekey, imageurl, \
    additionalurl, timeframe, challengequality, mustrespond, challengescore, \
    challengeoptions = "", "", "", "", "", "", "", "", "", "", []
    message, activedatemysql, publishdatemysql = "", "", ""
    # First get the testlinkid. If its value doesn't exist in DB, then create 
    # a new test. Otherwise, simply display the challenges of the existing test
    # and allow the user to edit them.
    if request.POST.has_key('testlinkid'):
        testlinkid = request.POST['testlinkid']
    if request.POST.has_key('testname'):
        testname = request.POST['testname']
    if request.POST.has_key('testtype'):
        testtype = request.POST['testtype']
    if request.POST.has_key('testrules'):
        testrules = request.POST['testrules']
    if request.POST.has_key('testtopic'):
        testtopic = request.POST['testtopic']
    if request.POST.has_key('othertopicname'):
        othertopicname = request.POST['othertopicname']
    if request.POST.has_key('totalscore'):
        totalscore = request.POST['totalscore']
    if request.POST.has_key('passscore'):
        passscore = request.POST['passscore']
    if request.POST.has_key('numchallenges'):
        numchallenges = request.POST['numchallenges']
    if request.POST.has_key('evendistribution'):
        evendistribution = request.POST['evendistribution']
    if request.POST.has_key('negativescoring'):
        negativescoring = request.POST['negativescoring']
    if request.POST.has_key('testduration'):
        testduration = request.POST['testduration']
    if request.POST.has_key('testdurationunit'):
        testdurationunit = request.POST['testdurationunit']
    if request.POST.has_key('challengeduration'):
        challengeduration = request.POST['challengeduration']
    if request.POST.has_key('challengedurationunit'):
        challengedurationunit = request.POST['challengedurationunit']
    if request.POST.has_key('evaluators'):
        evaluators = request.POST['evaluators']
    if request.POST.has_key('grpname'):
        grpname = request.POST['grpname']
    if request.POST.has_key('publishdate'):
        publishdate = request.POST['publishdate']
    if request.POST.has_key('activedate'):
        activedate = request.POST['activedate']
    if request.POST.has_key('skilltarget'):
        skilltarget = request.POST['skilltarget']
    if request.POST.has_key('testscope'):
        testscope = request.POST['testscope']
    if request.POST.has_key('answerlanguage'):
        answerlanguage = request.POST['answerlanguage']
    if request.POST.has_key('progenv'):
        progenv = request.POST['progenv']
    if request.POST.has_key('multimediareqd'):
        multimediareqd = True
    if request.POST.has_key('randomsequencing'):
        randomsequencing = True
    if request.POST.has_key('multipleattemptsallowed'):
        multipleattemptsallowed = True
    if request.POST.has_key('maxattemptscount'):
        maxattemptscount = request.POST['maxattemptscount']
    if request.POST.has_key('attemptsinterval'):
        attemptsinterval = request.POST['attemptsinterval']
    if request.POST.has_key('attemptsintervalunit'):
        attemptsintervalunit = request.POST['attemptsintervalunit']
    if request.POST.has_key('testlinkid'):
        testlinkid = request.POST['testlinkid']
    if request.POST.has_key('csrfmiddlewaretoken'):
        csrfmiddlewaretoken = request.POST['csrfmiddlewaretoken']
    testqueryset = Test.objects.filter(testlinkid=testlinkid, creator=userobj) # Returns a Queryset object
    testobj = None
    if testqueryset.__len__() == 0: # This is a new test being created.
        testobj = Test()
        testobj.createdate = datetime.datetime.now()
    else:
        testobj = testqueryset[0]
    testobj.testname = testname
    if testtopic == "Other": # Topic is custom, so testobj.topicname will be "".
        topic = Topic()
        topic.topicname = othertopicname
        topic.user = userobj
        topic.isactive = True
        topic.save()
        testobj.topic = topic
        testobj.topicname = ""
    else: # Topic is built-in, so testobj.testtopic will be None.
        testobj.topic = Topic.objects.filter(id=-1)[0]
        testobj.topicname = testtopic.replace("__", " ")
    testobj.testtype = testtype
    testobj.creator = userobj
    creatoremailid = userobj.emailid
    evaluatorslist = evaluators.split(",")
    testobj.creatorisevaluator = False
    evalemailsdict = {} # This will help in removing duplicates, if any.
    for evalem in evaluatorslist:
        evalem = re.sub(skillutils.multiplewhitespacepattern, '', evalem)
        if not evalemailsdict.has_key(evalem):
            evalemailsdict[evalem] = 1
        if evalem == creatoremailid:
            testobj.creatorisevaluator = True
    if  not re.search(skillutils.numericpattern, totalscore) or (numchallenges != "" and not re.search(skillutils.numericpattern, numchallenges)):
        message = error_msg('1047')
        return HttpResponse(message)
    if numchallenges == "":
        numchallenges = -1 # -1 means the user didn't enter a value
    testobj.maxscore = totalscore
    testobj.challengecount = numchallenges
    if passscore == '' or not passscore:
        passscore = None
    testobj.passscore = passscore
    # Note: Both test duration and challenge duration will converted to seconds\
    # and then saved in DB.
    if testdurationunit == 'h':
        testobj.duration = int(testduration) * 3600 # Conversion to seconds from hr.
    elif testdurationunit == 'm':
        testobj.duration = int(testduration) * 60 # Seconds from minutes.
    else:
        testobj.duration = int(testduration)
    if challengedurationunit == 'h':
        challengeduration = int(challengeduration) * 3600
    elif challengedurationunit == 'm':
        challengeduration = int(challengeduration) * 60
    else:
        challengeduration = int(challengeduration)
    activedateparts = activedate.split('-')
    publishdateparts = publishdate.split('-')
    # Verify whether the date formats received are in 'dd-MON-yyyy' format.
    if activedateparts.__len__() < 3 or activedateparts[1].upper() not in mysettings.MONTHS_DICT.keys() or activedateparts[2].__len__() != 4 or not re.search(skillutils.numericpattern, activedateparts[2]) or activedateparts[0].__len__() != 2 or not re.search(skillutils.numericpattern, activedateparts[0]):
        message = error_msg('1042')
        return HttpResponse(message)
    else:
        activemm = mysettings.MONTHS_DICT[activedateparts[1].upper()]
        if activemm in ('01', '03', '05', '07', '08', '10', '12') and int(activedateparts[0]) > 31:
            message = error_msg('1043')
            return HttpResponse(message)
        elif activemm in ('04', '06', '09', '11') and int(activedateparts[0]) > 30:
            message = error_msg('1043')		
            return HttpResponse(message)
        elif activemm == '02' and int(activedateparts[2]) % 4 == 0 and int(activedateparts[2]) % 100 != 0 and int(activedateparts[0]) > 29: # Leap year
            message = error_msg('1043')
            return HttpResponse(message)
        elif activemm == '02' and int(activedateparts[2]) % 100 == 0 and int(activedateparts[2]) % 400 == 0 and int(activedateparts[0]) > 29: # Leap year
            message = error_msg('1043')
            return HttpResponse(message)
        elif activemm == '02' and int(activedateparts[0]) > 28:
            message = error_msg('1043')
            return HttpResponse(message)
        else:
            activedatemysql = activedateparts[2] + "-" + activemm + "-" + activedateparts[0] + " 00:00:00"
    #######################
    if publishdateparts.__len__() < 3 or publishdateparts[1].upper() not in mysettings.MONTHS_DICT.keys() or publishdateparts[2].__len__() != 4 or not re.search(skillutils.numericpattern, publishdateparts[2]) or publishdateparts[0].__len__() != 2 or not re.search(skillutils.numericpattern, publishdateparts[0]):
        message = error_msg('1044')
        return HttpResponse(message)
    else:
        publishmm = mysettings.MONTHS_DICT[publishdateparts[1].upper()]
        if publishmm in ('01', '03', '05', '07', '08', '10', '12') and int(publishdateparts[0]) > 31:
            message = error_msg('1045')
            return HttpResponse(message)
        elif publishmm in ('04', '06', '09', '11') and int(publishdateparts[0]) > 30:
            message = error_msg('1045')
            return HttpResponse(message)
        elif publishmm == '02' and int(publishdateparts[2]) % 4 == 0 and int(publishdateparts[2]) % 100 != 0 and int(publishdateparts[0]) > 29: # Leap year
            message = error_msg('1045')
            return HttpResponse(message)
        elif publishmm == '02' and int(publishdateparts[2]) % 100 == 0 and int(publishdateparts[2]) % 400 == 0 and int(publishdateparts[0]) > 29: # Leap year
            message = error_msg('1045')
            return HttpResponse(message)
        elif publishmm == '02' and int(publishdateparts[0]) > 28:
            message = error_msg('1045')
            return HttpResponse(message)
        else:
            publishdatemysql = publishdateparts[2] + "-" + publishmm + "-" + publishdateparts[0] + " 00:00:00"
    if datetime.datetime(int(activedateparts[2]), int(activemm), int(activedateparts[0]), int('00'), int('00'), int('00')) < datetime.datetime(int(publishdateparts[2]), int(publishmm), int(publishdateparts[0]), int('00'), int('00'), int('00')):
        message = error_msg('1046')
        return HttpResponse(message)
    testobj.activationdate = activedatemysql
    testobj.publishdate = publishdatemysql
    testobj.status = False # Remember to set this to True when we finally save the test along with its constituent challenges.
    testobj.allowedlanguages = answerlanguage
    # 'answerlanguage' may contain '#||#' at the end. If so, remove it.
    if re.search(re.compile(r"#||#$"), answerlanguage):
        testobj.allowedlanguages = answerlanguage[:-4]
    testobj.ruleset = testrules
    # 'testrules' may contain '#||#' at the end too. Remove it.
    if re.search(re.compile(r"#||#$"), testrules):
        testobj.ruleset = testrules[:-4]
    testobj.testlinkid = testlinkid
    testobj.quality = skilltarget
    # Handle evaluator grouping and 'Evaluator' object creation.
    evalobj = Evaluator()
    testsbycreator = Test.objects.filter(creator = userobj)
    evalnamesbycreator = []
    evalidsbycreator = []
    for tobj in testsbycreator:
        existevalobj = tobj.evaluator
        if existevalobj.evalgroupname not in evalnamesbycreator: # This is to ensure that a single evaluator name doesn't get listed more than once.
            evalnamesbycreator.append(existevalobj.evalgroupname)
            evalidsbycreator.append(existevalobj.id)
    if grpname not in evalnamesbycreator:
        evalobj.evalgroupname = grpname
        memberctr = 1
        for evalemailid in evalemailsdict.keys():
            uobjqset = User.objects.filter(emailid=evalemailid)
            if uobjqset.__len__() > 0: # Valid user exists
                uobj = uobjqset[0]
                if memberctr == 1:
                    evalobj.groupmember1 = uobj
                elif memberctr == 2:
                    evalobj.groupmember2 = uobj
                elif memberctr == 3:
                    evalobj.groupmember3 = uobj
                elif memberctr == 4:
                    evalobj.groupmember4 = uobj
                elif memberctr == 5:
                    evalobj.groupmember5 = uobj
                elif memberctr == 6:
                    evalobj.groupmember6 = uobj
                elif memberctr == 7:
                    evalobj.groupmember7 = uobj
                elif memberctr == 8:
                    evalobj.groupmember8 = uobj
                elif memberctr == 9:
                    evalobj.groupmember9 = uobj
                elif memberctr == 10:
                    evalobj.groupmember10 = uobj
                memberctr += 1
            else: # User with the email id in 'evalemailid' doesn't exist.
                pass
        evalobj.save()
        testobj.evaluator = evalobj
    else: # So a group with this name already exists. We need to see if the existing group has the same set of evaluator email Ids. If so, we simply get the existing evaluator object and assign it to this test.
        ctr = 0
        matchedgrpemails = {}
        evalid = -1
        while ctr < evalnamesbycreator.__len__():
            evalid = evalidsbycreator[ctr]
            if grpname == evalnamesbycreator[ctr]:
                matchedevalobj = Evaluator.objects.filter(id=evalid)[0]
                if matchedevalobj.groupmember1 is not None and matchedevalobj.groupmember1.emailid and matchedevalobj.groupmember1.emailid != "":
                    matchedgrpemails[matchedevalobj.groupmember1.emailid] = 1
                if matchedevalobj.groupmember2 is not None and matchedevalobj.groupmember2.emailid and matchedevalobj.groupmember2.emailid != "":
                    matchedgrpemails[matchedevalobj.groupmember2.emailid] = 1
                if matchedevalobj.groupmember3 is not None and matchedevalobj.groupmember3.emailid and matchedevalobj.groupmember3.emailid != "":
                    matchedgrpemails[matchedevalobj.groupmember3.emailid] = 1
                if matchedevalobj.groupmember4 is not None and matchedevalobj.groupmember4.emailid and matchedevalobj.groupmember4.emailid != "":
                    matchedgrpemails[matchedevalobj.groupmember4.emailid] = 1
                if matchedevalobj.groupmember5 is not None and matchedevalobj.groupmember5.emailid and matchedevalobj.groupmember5.emailid != "":
                    matchedgrpemails[matchedevalobj.groupmember5.emailid] = 1
                if matchedevalobj.groupmember6 is not None and matchedevalobj.groupmember6.emailid and matchedevalobj.groupmember6.emailid != "":
                    matchedgrpemails[matchedevalobj.groupmember6.emailid] = 1
                if matchedevalobj.groupmember7 is not None and matchedevalobj.groupmember7.emailid and matchedevalobj.groupmember7.emailid != "":
                    matchedgrpemails[matchedevalobj.groupmember7.emailid] = 1
                if matchedevalobj.groupmember8 is not None and matchedevalobj.groupmember8.emailid and matchedevalobj.groupmember8.emailid != "":
                    matchedgrpemails[matchedevalobj.groupmember8.emailid] = 1
                if matchedevalobj.groupmember9 is not None and  matchedevalobj.groupmember9.emailid and matchedevalobj.groupmember9.emailid != "":
                    matchedgrpemails[matchedevalobj.groupmember9.emailid] = 1
                if matchedevalobj.groupmember10 is not None and  matchedevalobj.groupmember10.emailid and matchedevalobj.groupmember10.emailid != "":
                    matchedgrpemails[matchedevalobj.groupmember10.emailid] = 1
                break
            ctr += 1
        if matchedgrpemails.keys().__len__() == evalemailsdict.keys().__len__():
            for matchemail in matchedgrpemails.keys():
                if not evalemailsdict.has_key(matchemail):
                    message = error_msg('1048')
                    return HttpResponse(message)
            testobj.evaluator = matchedevalobj
        else:
            message = error_msg('1048')
            return HttpResponse(message)
    testobj.allowmultiattempts = multipleattemptsallowed
    if multipleattemptsallowed:
        testobj.maxattemptscount = maxattemptscount
        testobj.attemptsinterval = attemptsinterval
        if attemptsintervalunit == 'h':
            testobj.attemptsinterval = int(attemptsinterval) * 3600
        elif attemptsintervalunit == 'm':
            testobj.attemptsinterval = int(attemptsinterval) * 60
    else:
        testobj.maxattemptscount = 1
        testobj.attemptsinterval = None
    testobj.randomsequencing = randomsequencing
    testobj.multimediareqd = multimediareqd
    testobj.progenv = None
    if progenv != '0':
        testobj.progenv = progenv
    if not testscope:
        testobj.scope = 'private' # The default value
    else:
        testobj.scope = testscope
    testobj.save()
    if request.POST.has_key('lastchallengectr'):
        lastchallengectr = request.POST['lastchallengectr']
    if request.POST.has_key('challengenumbersstr'):
        challengenumbersstr = request.POST['challengenumbersstr']
    message = error_msg('1050') # Posted test meta data successfully.
    # So we create the challenge insertion form and send it as message.
    message += _challenge_edit_form(request, testobj, lastchallengectr,  evendistribution, challengeduration, int(negativescoring))
    return HttpResponse(message)


# Note: The 'challengedurationseconds' value being passed into this function is in seconds.
def _challenge_edit_form(request, testobj, lastchallengectr, evendistribution, challengedurationseconds, negativescoring=0):
    totalchallenges = testobj.challengecount
    testobj.status = False # Set this to false since we are editing a challenge
    testlinkid = testobj.testlinkid
    testtype = testobj.testtype
    multimediareqd = testobj.multimediareqd
    totalscore = testobj.maxscore
    edit_challenge_dict = { 'lastchallengectr' : lastchallengectr, 'testlinkid' : testlinkid, 'multimediareqd' : multimediareqd, 'totalscore' : totalscore, 'challengedurationseconds' : challengedurationseconds, 'testtype' : testtype }
    edit_challenge_dict['answeringoptions'] = ""
    if testtype == 'COMP':
        challengetypeslist = "<b>Select Challenge Type</b><select name='challengetype' onchange='javascript:displayoptions();'>"
        for ttcode in mysettings.TEST_TYPES.keys():
            ttcodeval = ttcode.replace(" ", "__")
            if ttcode == 'SUBJ':
                challengetypeslist += "<option value=%s selected>%s</option>"%(ttcodeval, mysettings.TEST_TYPES[ttcode])
            elif ttcode == 'COMP':
                continue # A challenge cannot be composite
            else:
                challengetypeslist += "<option value=%s>%s</option>"%(ttcodeval, mysettings.TEST_TYPES[ttcode])
        challengetypeslist += "</select><br /><div id='ansopts' style=''><b>Answer should not exceed <input type='text' name='maxsizewords' value='' size='6' maxlength='6'> words</b>(leave empty for no limit)</p></div>"
        edit_challenge_dict['challengetypeslist'] = challengetypeslist
    elif testtype == 'MULT' or testtype == 'FILB': # For 'CODN', 'ALGO' and 'SUBJ' type challenges, we need not provide any answering options.
        edit_challenge_dict['answeringoptions'] = "<p>"
        if testtype == 'MULT':
            edit_challenge_dict['answeringoptions'] += "<b>Can there be more than one correct option:</b>&nbsp;<input type='radio' name='oneormore' value='yes' checked=true onchange='javascript:displayresponsekeycontrols();'>Yes&nbsp;&nbsp;&nbsp;&nbsp;<input type='radio' name='oneormore' value='no' onchange='javascript:displayresponsekeycontrols();'>No<br />"
            edit_challenge_dict['answeringoptions'] += "<b>Please enter the options you want to be made available for this challenge/question.(max 8 options) </b><br />"
            edit_challenge_dict['answeringoptions'] += "<i>Option #a:</i> <input type='text' name='choice1' value='' onblur='javascript:displayresponsekeycontrols();'><br /><i>Option #b</i>: <input type='text' name='choice2' value='' onblur='javascript:displayresponsekeycontrols();'><br /><i>Option #c:</i> <input type='text' name='choice3' value='' onblur='javascript:displayresponsekeycontrols();'><br /><i>Option #d:</i> <input type='text' name='choice4' value='' onblur='javascript:displayresponsekeycontrols();'><br /><i>Option #e:</i> <input type='text' name='choice5' value='' onblur='javascript:displayresponsekeycontrols();'><br /><i>Option #f:</i> <input type='text' name='choice6' value='' onblur='javascript:displayresponsekeycontrols();'><br /><i>Option #g:</i> <input type='text' name='choice7' value='' onblur='javascript:displayresponsekeycontrols();'><br /><i>Option #h:</i> <input type='text' name='choice8' value='' onblur='javascript:displayresponsekeycontrols();'></p>"
            edit_challenge_dict['responsekeyscontrolslist'] = "<b>Select the correct response(s)<font size='-2'><a href='#' onmouseover='javascript:showwhyresponsekey(this);'>[why should I do this?]</a></font>:</b><br />"
            # Since the default value for 'oneormore' is yes, we will initialize the 'responsekeyscontrolslist' with checkbox controls.
            edit_challenge_dict['responsekeyscontrolslist'] += "<i>Option #a: <input type='checkbox' name='responsekey[]' value=''></i><br /><i>Option #b: <input type='checkbox' name='responsekey[]' value=''></i><br /><i>Option #c: <input type='checkbox' name='responsekey[]' value=''></i><br /><i>Option #d: <input type='checkbox' name='responsekey[]' value=''></i><br /><i>Option #e: <input type='checkbox' name='responsekey[]' value=''></i><br /><i>Option #f: <input type='checkbox' name='responsekey[]' value=''></i><br /><i>Option #g: <input type='checkbox' name='responsekey[]' value=''></i><br /><i>Option #h: <input type='checkbox' name='responsekey[]' value=''></i><br />"
        else:
            edit_challenge_dict['answeringoptions'] += "<input type='hidden' name='oneormore' value='no'>"
            edit_challenge_dict['responsekeyscontrolslist'] = "<b>Enter the correct response<font size='-2'><a href='#' onmouseover='javascript:showwhyresponsekey(this);'>[why should I do this?]</a></font>:</b><input type='text' name='responsekey' value='' size='10' maxlength='250'><br />"
    elif testtype == 'CODN' or testtype == 'ALGO': # For these testtypes user may want some constraints on the size of the response.
        edit_challenge_dict['answeringoptions'] += "<b>Answer should not exceed <input type='text' name='maxsizelines' value='' size='6' maxlength='6'> lines. </b>(leave empty for no limit.)</p>"
    elif testtype == 'SUBJ':
        edit_challenge_dict['answeringoptions'] += "<b>Answer should not exceed <input type='text' name='maxsizewords' value='' size='6' maxlength='6'> words</b>(leave empty for no limit)</p>"
    lastchallengectr = int(lastchallengectr) + 1
    edit_challenge_dict['testlinkid'] = testlinkid
    edit_challenge_dict['test_id'] = testobj.id
    edit_challenge_dict['lastchallengectr'] = lastchallengectr.__str__()
    edit_challenge_dict['challengenumbersstr'] = lastchallengectr.__str__()
    edit_challenge_dict['evendistribution'] = evendistribution # This will be '1' or '0'.
    edit_challenge_dict['challengescore'] = -1
    if evendistribution and totalchallenges > 0:
        edit_challenge_dict['challengescore'] = str(float(totalscore)/float(totalchallenges))
    elif totalchallenges == -1:
        edit_challenge_dict['challengescore'] = ""
    edit_challenge_dict['negativescoring'] = negativescoring
    edit_challenge_dict['skillqualitylist'] = ""
    for skillqual in mysettings.SKILL_QUALITY.keys():
        if testobj.quality == skillqual:
            edit_challenge_dict['skillqualitylist'] += "<option value=%s selected>%s</option>"%(skillqual, mysettings.SKILL_QUALITY[skillqual])
        else:
            edit_challenge_dict['skillqualitylist'] += "<option value=%s>%s</option>"%(skillqual, mysettings.SKILL_QUALITY[skillqual])
    # Populate the existing challenges list
    challengesqset = Challenge.objects.filter(test=testobj).order_by('id')
    edit_challenge_dict['testname'] = testobj.testname
    edit_challenge_dict['challenge_links_list'] = []
    edit_challenge_dict.update(csrf(request))
    for challenge in challengesqset:
        challengestmt = challenge.statement[:20] + " ..."
        edit_challenge_dict['challenge_links_list'].append((challenge.id, challengestmt, testobj.id, testlinkid)) # So 'challenge_links_list' is a list of tuples whose elements (in order) are challenge Id (0), abbreviated challenge statement (1) (first 20 characters), test Id (2) and the testlinkid (3).
    # Create and render the template
    edit_challenge_dict['usrid'] = testobj.creator.id
    #edit_challenge_dict['treeview'] = _showtreeview(request, testobj)
    tmpl = get_template("tests/edit_challenge.html")
    cxt = Context(edit_challenge_dict)
    editchallengehtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        editchallengehtml = editchallengehtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return editchallengehtml


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def search(request):
    tests_user_dict = get_user_tests(request)
    inc_context = skillutils.includedtemplatevars("Search", request) # Since this is the 'Dashboard' page for the user.
    for inc_key in inc_context.keys():
        tests_user_dict[inc_key] = inc_context[inc_key]
    # Now create and render the template here
    tmpl = get_template("tests/search.html")
    tests_user_dict.update(csrf(request))
    cxt = Context(tests_user_dict)
    searchtestshtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        searchtestshtml = searchtestshtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(searchtestshtml)


"""
Function to add or edit a challenge
"""
@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def edit(request):
    message = ''
    if request.method == "GET": # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.MANAGE_TEST_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    (lastchallengectr, evendistribution, multimediareqd, totalscore, challengenumbersstr, csrfmiddlewaretoken, negativescoring, mediafile, oneormore) = ("", False, False, 0, "", "", False, "", False)
    # Retrieve challenge data and create challenge object...
    challengeobj = Challenge()
    testobj = None
    if request.POST.has_key('testlinkid'):
        challengeobj.testlinkid = request.POST['testlinkid']
    if request.POST.has_key('statement'):
        challengeobj.statement = request.POST['statement']
    if request.POST.has_key('challengetype'):
        challengeobj.challengetype = request.POST['challengetype']
    else:
        if not request.POST.has_key('testtype'):
            errmsg = error_msg('1053')
            return HttpResponse(errmsg)
        challengeobj.challengetype = request.POST['testtype']
    # Sanity check for challenge type:
    if challengeobj.challengetype not in mysettings.TEST_TYPES.keys():
        message = "Challenge type '%s':"%(challengeobj.challengetype) + error_msg('1054')
        return HttpResponse(message)
    if request.POST.has_key('test_id'):
        testobj = Test.objects.filter(id=request.POST['test_id'])[0]
        challengeobj.test = testobj
        challengeobj.testlinkid = testobj.testlinkid
    elif request.POST.has_key('testlinkid'):
        testobj = Test.objects.filter(testlinkid=request.POST['testlinkid'])[0]
        challengeobj.test = testobj
        challengeobj.testlinkid = request.POST['testlinkid']
    if not request.POST.has_key('test_id') and not request.POST.has_key('testlinkid'): # This should never happen if the user is logged in.
        challengeobj.test = None
        challengeobj.testlinkid = None
        errmsg = error_msg('1051') + error_msg('1111')
        return HttpResponse(errmsg)
    if request.POST.has_key('challengedurationseconds'):
        challengeobj.timeframe = request.POST['challengedurationseconds']
    if request.POST.has_key('mustrespond'):
        challengeobj.mustrespond = request.POST['mustrespond']
    if request.POST.has_key('lastchallengectr'):
        lastchallengectr = request.POST['lastchallengectr']
    if request.POST.has_key('evendistribution'):
        evendistribution = request.POST['evendistribution']
    if request.POST.has_key('multimediareqd'):
        multimediareqd = request.POST['multimediareqd']
    if request.POST.has_key('totalscore'):
        totalscore = request.POST['totalscore']
    if request.POST.has_key('challengenumbersstr'):
        challengenumbersstr = request.POST['challengenumbersstr']
    if request.POST.has_key('csrfmiddlewaretoken'):
        csrfmiddlewaretoken = request.POST['csrfmiddlewaretoken']
    if request.POST.has_key('negativescoring'):
        negativescoring = request.POST['negativescoring']
    if request.POST.has_key('challengescore'):
        challengeobj.challengescore = request.POST['challengescore']
    if request.POST.has_key('negativescore'):
        challengeobj.negativescore = request.POST['negativescore']
    if request.FILES.has_key('mediafile'):
        mediafilename = request.FILES['mediafile'].name.split(".")[0]
        username = userobj.displayname
        fpath, message, challengemedia = skillutils.handleuploadedfile(request.FILES['mediafile'], mysettings.MEDIA_ROOT + os.path.sep + username + os.path.sep + "tests" + os.path.sep + testobj.id.__str__(), mediafilename)
        challengeobj.mediafile = request.FILES['mediafile'].name
    challengeobj.maxresponsesizeallowable = -1
    if request.POST.has_key('maxsizewords'):
        challengeobj.maxresponsesizeallowable = request.POST['maxsizewords']
        challengeobj.maxresponsesizeallowable = re.sub(re.compile(r"&#39;"), '', challengeobj.maxresponsesizeallowable)
        if challengeobj.maxresponsesizeallowable == "":
            challengeobj.maxresponsesizeallowable = -1
    elif request.POST.has_key('maxsizelines'):
        challengeobj.maxresponsesizeallowable = request.POST['maxsizelines']
        challengeobj.maxresponsesizeallowable = re.sub(re.compile(r"&#39;"), '', challengeobj.maxresponsesizeallowable)
        if challengeobj.maxresponsesizeallowable == "":
            challengeobj.maxresponsesizeallowable = -1
    if request.POST.has_key('oneormore'):
        oneormore = request.POST['oneormore']
    if request.POST.has_key('skillquality'):
        challengeobj.challengequality = request.POST['skillquality']
    if request.POST.has_key('extresourceurl'):
        challengeobj.additionalurls = request.POST['extresourceurl']
    # Now let us get the available options for 'MULT' type test
    if challengeobj.challengetype == 'MULT':
        fchoices = lambda(x):re.search(re.compile("^choice(\d+)$", re.IGNORECASE), x)
        allmatches = map(fchoices, request.POST)
        for fld in allmatches:
            if fld is None: # This is a different control, not one of the 'choice' controls
                continue
            controlname = fld.string
            ctrlcounter = fld.groups()[0]
            if not request.POST[controlname] or request.POST[controlname].strip() == "":
                continue
            challengeobj.__dict__['option%s'%ctrlcounter] = request.POST[controlname].strip()
    # Store the responsekey if challengetype value is 'FILB' or 'MULT'
    # A note on the format used to store responsekey(s): For challengetype
    # value of 'FILB', the responsekey will be a single entry and will be
    # stored as is. For challengetype value of 'MULT' and 'oneormore' value of
    # 'no', we can store the value similarly. However, for challengetype 
    # value of 'MULT' and 'oneormore' value of 'yes', there may be multiple
    # entries, so we will store the entries as a single string joined together
    # using the string '#||#'.
    challengeobj.responsekey = None
    if challengeobj.challengetype == 'FILB' and request.POST.has_key('responsekey'):
        challengeobj.responsekey = request.POST['responsekey']
    elif challengeobj.challengetype == 'MULT' and request.POST.has_key('responsekey') or request.POST.has_key('responsekey[]'):
        if oneormore == "no": # Only a single option will be correct
            challengeobj.responsekey = request.POST['responsekey']
        elif oneormore == "yes": # Multiple options may be checked
            responses = request.POST.getlist('responsekey[]')
            challengeobj.responsekey = '#||#'.join(responses)
    # ... and finally save the challenge object.
    challengeobj.save()
    savedchallengesqset = Challenge.objects.filter(test=testobj)
    savedchallengescount = savedchallengesqset.__len__()
    totalchallengescount = testobj.challengecount
    if savedchallengescount > totalchallengescount: # reconcile the difference
        testobj.challengecount = savedchallengescount
        testobj.save()
        totalchallengescount = testobj.challengecount
    savedchallengesscore = 0
    for chlng in savedchallengesqset:
        savedchallengesscore += chlng.challengescore
    statusmessage = "<font color='#0000AA'>Number of Challenges framed:<b>%s</b><br>Total Number of Challenges in the test: <b>%s</b><br>Score accounted for: <b>%s</b><br>Total Score: <b>%s</b></font><br>"%(savedchallengescount.__str__(), totalchallengescount.__str__(), savedchallengesscore.__str__(), testobj.maxscore.__str__())
    editchallengehtml = _challenge_edit_form(request, testobj, lastchallengectr,  evendistribution, challengeobj.timeframe, int(negativescoring))
    return HttpResponse(statusmessage + editchallengehtml)
    


def _showtreeview(request, testobj):
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    treeview = "<center><SCRIPT language='JavaScript' src='%s/javascript/treeview/ua.js'></SCRIPT><SCRIPT language='JavaScript' src='%s/javascript/treeview/ftiens4.js'></SCRIPT><SCRIPT language='JavaScript'> USETEXTLINKS = 1;STARTALLOPEN = 0;ICONPATH = '%s/images/treeview/';"%(mysettings.STATIC_ROOT, mysettings.STATIC_ROOT, mysettings.STATIC_ROOT)
    treeview += "foldersTree = gFld(\"<i><font size='-1' color='#0000AA'>%s</font></i>\", \"diffFolder.gif\", \"<img src=''>\");"%testobj.testname
    challengesqset = Challenge.objects.filter(test=testobj)
    varcounter = 1
    for chlng in challengesqset:
        treeview += "foldersTree.treeID = 'Frameset';"
        statementshort = chlng.statement[:10]
        treeview += "var varservice_%s = \"<a href='#' id='chkservice_%s' onClick='javascript:editchallange(%s);'>%s</a>\";"%(varcounter.__str__(),varcounter.__str__(), chlng.id, statementshort)
        varcounter += 1
    treeview += "</SCRIPT></center><DIV style='position:absolute; top:0; left:0;'><TABLE border=0><TR><TD><FONT size=-2><A style='font-size:7pt;text-decoration:none;color:silver' href='http://www.treemenu.net/'></A></FONT></TD></TR></TABLE></DIV><SCRIPT language='JavaScript'>initializeDocument();</SCRIPT>"
    return treeview


"""
View to display the test summary screen.  This screen allows the creator
to view challenges and various attributes of the challenges on one screen,
enabling the creator to modify/edit/delete them.
"""
@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def testsummary(request):
    message = ''
    if request.method != "GET": # Illegal bad request... 
        message = error_msg('1004')
        # A logging mechanism may be used to track how many and from where
        # such requests come and that may, sometimes, tell a curious story.
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.MANAGE_TEST_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    test_id = None
    if not request.GET.has_key('test_id'):
        message = error_msg('1055')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.MANAGE_TEST_URL + "?msg=%s"%message)
        return response
    test_id = request.GET['test_id']
    testobj = None
    tests_summary_dict = {}
    testqset = Test.objects.filter(id=test_id)
    if testqset.__len__() == 0:
        message = error_msg('1056')
        response = HttpResponse(skillutils.gethosturl(request) + "/" + mysettings.MANAGE_TEST_URL + "?msg=%s"%message)
        return response
    else:
        testobj = testqset[0]
    challengesqset = Challenge.objects.filter(test=testobj) # This should yield one or more challenges
    tests_summary_dict['challenge_links_list'] = []
    tests_summary_dict['challenges'] = []
    testlinkid = testobj.testlinkid
    for chlng in challengesqset:
        challenge = {}
        challenge['shortform'] = chlng.statement[:12] + " ..."
        challenge['id'] = chlng.id
        challenge['challengescore'] = chlng.challengescore
        challenge['challengetype'] = mysettings.TEST_TYPES[chlng.challengetype]
        challenge['timeframe'] = chlng.timeframe
        challenge['mediafile'] = chlng.mediafile
        challenge['mediafileshortname'] = challenge['mediafile']
        if not challenge['mediafile']:
            challenge['mediafileshortname'] = ""
        else:
            challenge['mediafileshortname'] = chlng.mediafile[:8] + " ..."
        challenge['statement'] = chlng.statement
        tests_summary_dict['challenge_links_list'].append((chlng.id, chlng.statement[:20] + " ...", testobj.id, testlinkid))
        tests_summary_dict['challenges'].append(challenge)
    tests_summary_dict['testname'] = testobj.testname
    tests_summary_dict['test_id'] = testobj.id
    tmpl = get_template("tests/test_summary.html")
    tests_summary_dict.update(csrf(request))
    cxt = Context(tests_summary_dict)
    testsummaryhtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        testsummaryhtml = testsummaryhtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(testsummaryhtml)


"""
This view is responsible for handling all delete challenge requests.
Delete challenge requests come from one of 2 javascript functions in
test.html - 'deletechallenge()' to delete a single challenge and
'deleteselected()' to delete multiple challenges at a single sweep.
"""
@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def deletechallenges(request):
    message = ''
    if request.method != "POST": # Illegal bad request... 
        message = error_msg('1004')
        # A logging mechanism may be used to track how many and from where
        # such requests come and that may, sometimes, tell a curious story.
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.MANAGE_TEST_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    challenge_id = None
    if not request.POST.has_key('challengeid'):
        message = error_msg('1057')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.MANAGE_TEST_URL + "?msg=%s"%message)
        return response
    else:
        challenge_id = request.POST['challengeid']
    numchallenges = 1
    if request.POST.has_key('numchallenges'):
        numchallenges = request.POST['numchallenges']
    challengeidlist = challenge_id.split("#||#")
    if numchallenges == 1:
        challengeidlist = [challengeidlist[0], ]
    #elif numchallenges > 1:
    #    challengeidlist.pop() # pop the last element as it is bound to be empty.
    challengesdeleted = []
    missingchidlist = []
    for chid in challengeidlist:
        try:
            chlng = Challenge.objects.filter(id=chid)[0]
            chlng.delete()
            challengesdeleted.append(chid)
        except:
            missingchidlist.append(chid)
    message = "The challenges/questions identified by the following Ids have been deleted: " + ", ".join(challengesdeleted) + ". "
    if missingchidlist.__len__() > 0:
        message += "The following challenge Ids could not be found: " + ", ".join(missingchidlist) + ". "
    if challengesdeleted.__len__() == numchallenges:
        message = "The selected challenges where successfully deleted."
    response = HttpResponse(message)
    return response


