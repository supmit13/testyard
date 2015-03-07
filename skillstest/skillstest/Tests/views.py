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
    createlink, testtypes, testrules, testtopics, skilltarget, testscope, answeringlanguage, progenv, existingtestnames, assocevalgrps, evalgroupslitags, createtesturl, addeditchallengeurl, savechangesurl, addmoreurl, clearnegativescoreurl, deletetesturl, showuserviewurl, editchallengeurl = "", "", "", "", "", "", "", "", "", "var evalgrpsdict = {};", "", mysettings.CREATE_TEST_URL, mysettings.EDIT_TEST_URL, mysettings.SAVE_CHANGES_URL, mysettings.ADD_MORE_URL, mysettings.CLEAR_NEGATIVE_SCORE_URL, mysettings.DELETE_TEST_URL, mysettings.SHOW_USER_VIEW_URL, mysettings.EDIT_CHALLENGE_URL
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
    tests_user_dict['testlist_asevaluator'] = testlist_asevaluator
    tests_user_dict['testlist_ascandidate'] = testlist_ascandidate
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
    tests_user_dict['edittesturl'] = skillutils.gethosturl(request) + "/" + mysettings.EDIT_EXISTING_TEST_URL
    tests_user_dict['testsummaryurl'] = mysettings.TEST_SUMMARY_URL
    tests_user_dict['deletechallengesurl'] = skillutils.gethosturl(request) + "/" + mysettings.DELETE_CHALLENGE_URL
    tests_user_dict['savechangesurl'] = skillutils.gethosturl(request) + "/" + mysettings.SAVE_CHANGES_URL
    tests_user_dict['addmoreurl'] = skillutils.gethosturl(request) + "/" + addmoreurl
    tests_user_dict['clearnegativescoreurl'] = skillutils.gethosturl(request) + "/" + clearnegativescoreurl
    tests_user_dict['deletetesturl'] = skillutils.gethosturl(request) + "/" + deletetesturl
    tests_user_dict['showuserviewurl'] = skillutils.gethosturl(request) + "/" + showuserviewurl
    tests_user_dict['editchallengeurl'] = skillutils.gethosturl(request) + "/" + editchallengeurl
    tests_user_dict['hosturl'] = skillutils.gethosturl(request) 
    tests_user_dict['testlinkid'] = skillutils.generate_random_string()
    return  tests_user_dict


"""
This view will provide the following functionalities:
Display a table of tests with latest first... These are all tests the user has created. This page will give the user
# access to all those tests in which she/he is a creator, evaluator or candidate. For tests in which  user is
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
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    tests_user_dict = get_user_tests(request)
    inc_context = skillutils.includedtemplatevars("Tests", request) # Since this is the 'Dashboard' page for the user.
    for inc_key in inc_context.keys():
        tests_user_dict[inc_key] = inc_context[inc_key]
    testnames_created_list = tests_user_dict['user_creator_other_evaluators_dict'].keys()
    testnames_created_list = testnames_created_list.sort()
    testnames_created_dict = {}
    for test_name in testnames_created_list:
        try:
            tobj = Test.objects.filter(testname=test_name, creator=userobj)[0]
            test_topic = tobj.topicname
            fullmarks = tobj.maxscore
            passscore = tobj.passscore
            publishdate = tobj.publishdate
            tid = tobj.id
            duration = tobj.duration
            ruleset = tobj.ruleset
            testtype = tobj.testtype
            testquality = tobj.quality
            teststandard = mysettings.SKILL_QUALITY[testquality]
            status = tobj.status
            progenv = tobj.progenv
            negativescoring = tobj.negativescoreallowed
            multipleattempts = tobj.allowmultiattempts
            maxattemptscount = tobj.maxattemptscount
            attemptsinterval = tobj.attemptsinterval
            attemptsintervalunit = tobj.attemptsinterval
            scope = tobj.scope
            activationdate = tobj.activationdate
            testurl = generatetesturl(tobj, userobj)
            evalprofileurlsdict = {}
            testnames_created_dict[test_name] = [tid, testurl, test_topic, fullmarks, passscore, publishdate, activationdate, duration, ruleset, testtype, teststandard, status, progenv, negativescoring, multipleattempts, maxattemptscount, attemptsinterval, attemptsintervalunit, scope, evalprofileurlsdict]
        except:
            response = "Error Retrieving Tests Where User As Creator: %s"%sys.exc_info()[1].__str__()
            return HttpResponse(response)
    tests_user_dict['creator_tests_info'] = testnames_created_dict
    testnames_evaluated_list = tests_user_dict['user_evaluator_creator_other_evaluators_dict'].keys()
    testnames_evaluated_list = testnames_evaluated_list.sort()
    testnames_evaluated_dict = {}
    testlist_asevaluator = tests_user_dict['testlist_asevaluator']
    for tobj in testlist_asevaluator:
        try:
            test_name = tobj.testname
            test_topic = tobj.topicname
            creatorname = tobj.creator.displayname
            fullmarks = tobj.maxscore
            passscore = tobj.passscore
            publishdate = tobj.publishdate
            tid = tobj.id
            duration = tobj.duration
            ruleset = tobj.ruleset
            testtype = tobj.testtype
            testquality = tobj.quality
            teststandard = mysettings.SKILL_QUALITY[testquality]
            status = tobj.status
            progenv = tobj.progenv
            negativescoring = tobj.negativescoreallowed
            multipleattempts = tobj.allowmultiattempts
            maxattemptscount = tobj.maxattemptscount
            attemptsinterval = tobj.attemptsinterval
            attemptsintervalunit = tobj.attemptsinterval
            scope = tobj.scope
            activationdate = tobj.activationdate
            testurl = generatetesturl(tobj, userobj)
            evalprofileurlsdict = {}
            testnames_evaluated_dict[test_name] = [tid, testurl, test_topic, fullmarks, passscore, publishdate, activationdate, duration, ruleset, testtype, teststandard, status, progenv, negativescoring, multipleattempts, maxattemptscount, attemptsinterval, attemptsintervalunit, scope, evalprofileurlsdict]
        except:
            response = "Error Retrieving Tests Where User As Evaluator: %s"%sys.exc_info()[1].__str__()
            return HttpResponse(response)
    tests_user_dict['evaluator_tests_info'] = testnames_evaluated_dict
    testnames_candidature_list = tests_user_dict['user_candidate_other_creator_evaluator_dict'].keys()
    testnames_candidature_list = testnames_candidature_list.sort()
    testnames_candidature_dict = {}
    testlist_ascandidate = tests_user_dict['testlist_ascandidate']
    for tobj in testlist_ascandidate:
        try:
            test_name = tobj.testname
            test_topic = tobj.topicname
            creatorname = tobj.creator.displayname
            fullmarks = tobj.maxscore
            passscore = tobj.passscore
            publishdate = tobj.publishdate
            tid = tobj.id
            duration = tobj.duration
            ruleset = tobj.ruleset
            testtype = tobj.testtype
            testquality = tobj.quality
            teststandard = mysettings.SKILL_QUALITY[testquality]
            status = tobj.status
            progenv = tobj.progenv
            negativescoring = tobj.negativescoreallowed
            multipleattempts = tobj.allowmultiattempts
            maxattemptscount = tobj.maxattemptscount
            attemptsinterval = tobj.attemptsinterval
            attemptsintervalunit = tobj.attemptsinterval
            scope = tobj.scope
            activationdate = tobj.activationdate
            testurl = generatetesturl(tobj, userobj)
            evalprofileurlsdict = {}
            testnames_candidature_dict[test_name] = [tid, testurl, test_topic, fullmarks, passscore, publishdate, activationdate, duration, ruleset, testtype, teststandard, status, progenv, negativescoring, multipleattempts, maxattemptscount, attemptsinterval, attemptsintervalunit, scope, evalprofileurlsdict]
        except:
            response = "Error Retrieving Tests Where User As Evaluator: %s"%sys.exc_info()[1].__str__()
            return HttpResponse(response)
    tests_user_dict['candidate_tests_info'] = testnames_candidature_dict
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
    challengeoptions, exist_test_id = "", "", "", "", "", "", "", "", "", "", [], None
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
    if request.POST.has_key('exist_test_id'):
        exist_test_id = request.POST['exist_test_id']
    testqueryset = Test.objects.filter(testlinkid=testlinkid, creator=userobj) # Returns a Queryset object
    testobj = None
    if testqueryset.__len__() == 0: # This is a new test being created.
        testobj = Test()
        testobj.createdate = datetime.datetime.now()
    else:
        testobj = testqueryset[0]
        if exist_test_id and exist_test_id != "":
            testobj = Test.objects.filter(id=exist_test_id)[0]
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
        #print matchedgrpemails.keys().__len__()
        #print evalemailsdict.keys().__len__()
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
        testobj.attemptsintervalunit = attemptsintervalunit
    else:
        testobj.maxattemptscount = 1
        testobj.attemptsinterval = None
        testobj.attemptsintervalunit = None
    testobj.randomsequencing = randomsequencing
    testobj.multimediareqd = multimediareqd
    testobj.progenv = None
    if progenv != '0':
        testobj.progenv = progenv
    if not testscope:
        testobj.scope = 'private' # The default value
    else:
        testobj.scope = testscope
    if negativescoring and negativescoring != '0':
        testobj.negativescoreallowed = True
    else:
        testobj.negativescoreallowed = False
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
def _challenge_edit_form(request, testobj, lastchallengectr, evendistribution, challengedurationseconds, negativescoring=False):
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
    (lastchallengectr, evendistribution, multimediareqd, totalscore, challengenumbersstr, csrfmiddlewaretoken, negativescoring, mediafile, oneormore) = ("", False, False, 0, "", "", 0, "", False)
    # Retrieve challenge data and create challenge object...
    editoperationflag = False
    challengeobj = Challenge()
    if request.POST.has_key('challengeid'):
        challengeobj = Challenge.objects.filter(id=request.POST['challengeid'])[0]
        editoperationflag = True
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
    if request.POST.has_key('negativescore'):
        negativescoring = request.POST['negativescore']
        if negativescoring == "":
            negativescoring = 0
        challengeobj.negativescore = negativescoring
    if request.POST.has_key('challengescore'):
        challengeobj.challengescore = request.POST['challengescore']
    if not challengeobj.challengescore or challengeobj.challengescore == "":
        challengeobj.challengescore = 0
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
        challengeobj.additionalurl = request.POST['extresourceurl']
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
            challengeobj.oneormore = False
        elif oneormore == "yes": # Multiple options may be checked
            responses = request.POST.getlist('responsekey[]')
            challengeobj.oneormore = True
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
    if editoperationflag == True:
        statusmessage = "<font color='#0000BB'><b><i>The changes were saved successfully</i></b></font>"
    editchallengehtml = _challenge_edit_form(request, testobj, lastchallengectr,  evendistribution, challengeobj.timeframe, int(testobj.negativescoreallowed))
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
        for hexkey in mysettings.INV_HEXCODE_CHAR_MAP.keys():
            if hexkey == ' ':
                continue
            challenge['statement'] = challenge['statement'].replace(hexkey, mysettings.INV_HEXCODE_CHAR_MAP[hexkey])
        tests_summary_dict['challenge_links_list'].append((chlng.id, chlng.statement[:20] + " ...", testobj.id, testlinkid))
        tests_summary_dict['challenges'].append(challenge)
    tests_summary_dict['testname'] = testobj.testname
    tests_summary_dict['test_id'] = testobj.id
    tests_summary_dict['usrid'] = userobj.id
    tmpl = get_template("tests/test_summary.html")
    tests_summary_dict.update(csrf(request))
    cxt = Context(tests_summary_dict)
    testsummaryhtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        testsummaryhtml = testsummaryhtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(testsummaryhtml)


# Function to determine if a test is editable or not.
def iseditable(testobj):
    curdatetime = datetime.datetime.now()
    publishdate = testobj.publishdate.__str__()
    pubdateparts = publishdate.split(" ")
    pubdate = pubdateparts[0]
    pubtime = pubdateparts[1]
    pubyyyy, pubmon, pubdd = pubdate.split("-")
    pubhhmmss = pubtime.split(":")
    pubhh = int(pubhhmmss[0])
    pubmm = int(pubhhmmss[1])
    #pubss = int(pubhhmmss[2])
    publishdatetime = datetime.datetime(int(pubyyyy), int(pubmon), int(pubdd), pubhh, pubmm, 0)
    if publishdatetime < curdatetime:
        return None
    else:
        return 1


"""
This view is responsible for handling all delete challenge requests.
Delete challenge requests come from one of 2 javascript functions in
test.html - 'deletechallenge()' to delete a single challenge and
'deleteselected()' to delete multiple challenges at a single sweep.
NOTE: To be implemented - Challenges may be deleted only before 
publishdate of the test and only when the test is not active (activedate
is in future).
"""
@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def deletechallenges(request):
    message = ''
    if request.method != "POST": # Illegal bad request... 
        message = error_msg('1004')
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
    # Find the testobj that contains this challenge
    testobj = None
    try:
        testobj = Challenge.objects.filter(id=challengeidlist[0])[0].test
    except:
        message = error_msg('1061')
        return HttpResponse(message)
    # Find if this test (or the challenges of the test) are editable...
    # If the current  date is past the publishdate or the status of the test
    # is active, then the test should not be made editable.
    res = iseditable(testobj) and not testobj.status
    if not res:
        message = "<font color='#FF0000'>%s</font>"%error_msg('1060')
        return HttpResponse(message)
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
    testobj.challengecount = testobj.challengecount - challengesdeleted.__len__()
    testobj.save()
    if missingchidlist.__len__() > 0:
        message += "The following challenge Ids could not be found: " + ", ".join(missingchidlist) + ". "
    if challengesdeleted.__len__() == numchallenges:
        message = "The selected challenges where successfully deleted."
    response = HttpResponse(message)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def savechanges(request):
    message = ''
    if request.method != "POST": 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.MANAGE_TEST_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    challengeduration = {}
    challengescore = {}
    durationpattern = re.compile(r"^challengeduration_(\d+)$")
    scorepattern = re.compile(r"^challengescore_(\d+)$")
    challengeids = []
    for ekey in request.POST.keys():
        durationmatch = durationpattern.search(ekey)
        scorematch = scorepattern.search(ekey)
        if durationmatch:
            challengeduration[durationmatch.groups()[0]] = request.POST[ekey]
            challengeids.append(durationmatch.groups()[0])
        elif scorematch:
            challengescore[scorematch.groups()[0]] = request.POST[ekey]
        else:
            pass
    nonexistentchallenges = []
    #updatedchallenges = 0
    testobj = None
    try:
        testobj = Challenge.objects.filter(id=challengeids[0])[0].test
    except:
        message = "<font color='#FF0000'>%s</font>"%error_msg('1061')
        return HttpResponse(message)
    if not iseditable(testobj) or testobj.status:
        message = "<font color='#FF0000'>%s</font>"%error_msg('1060')
        return HttpResponse(message)
    for chid in challengeids:
        try:
            challenge = Challenge.objects.filter(id=chid)[0]
        except:
            nonexistentchallenges.append(chid)
        challenge.challengescore = challengescore[chid]
        if challenge.challengescore.strip() == "":
            challenge.challengescore = 0
        challenge.timeframe = challengeduration[chid]
        if challenge.timeframe.strip() == "":
            challenge.timeframe = testobj.duration
        challenge.save()
        #updatedchallenges += 1
    message = "challenges were successfully updated. "
    if nonexistentchallenges.__len__() > 0:
        message += "The following challenges could not be found: "
        message += ", ".join(nonexistentchallenges)
    return HttpResponse(message)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def addmorechallenges(request):
    testobj = None
    message = ''
    if request.method != "POST": 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.MANAGE_TEST_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    # Create the test object from the test Id passed.
    if not request.POST.has_key('testid'):
        message = "<font color='#FF0000'>No Test Id found in request</font>";
        return HttpResponse(message)
    testid = request.POST['testid']
    try:
        testobj = Test.objects.filter(id=testid)[0]
    except:
        message = "<font color='#FF0000'>Test with the specified Test Id (%s) was not found.</font>"%testid
        return HttpResponse(message)
    if not iseditable(testobj) or testobj.status:
        message = "<font color='#FF0000' size=-1>%s</font>"%error_msg('1060')
        return HttpResponse(message)
    # Get all challenges from the challenge table
    challengeqset = Challenge.objects.filter(test=testobj)
    lastchallengectr = 1
    evendistribution = False
    challengeduration = testobj.duration
    negativescoring = 1 # We make it True by default  as we do not store what the user specified during test creation. Not storing it doesn't make any difference to the user.
    if challengeqset.__len__() == 0:
        message += _challenge_edit_form(request, testobj, lastchallengectr,  evendistribution, challengeduration, int(negativescoring))
        return HttpResponse(message)
    else:
        lastchallengectr = challengeqset.__len__()
        evendistribution = False
        challengeduration = challengeqset[0].timeframe
        # We will set negativescoring to 1 as we can't be sure if the user wants to use it or not.
        #negativescoring = challengeqset[0].negativescore
        negativescoring = testobj.negativescoreallowed
    message = _challenge_edit_form(request, testobj, lastchallengectr,  evendistribution, challengeduration, int(testobj.negativescoreallowed))
    return HttpResponse(message)

"""
The following view handles the requests for editing existing tests.
"""
@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def editexistingtest(request):
    testobj = None
    message = ''
    if request.method != "POST": 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.MANAGE_TEST_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    # Create the test object from the test Id passed.
    if not request.POST.has_key('testid'):
        message = "<font color='#FF0000'>%s</font>"%error_msg('1059');
        return HttpResponse(message)
    testid = request.POST['testid']
    try:
        testobj = Test.objects.filter(id=testid)[0]
    except:
        message = "<font color='#FF0000'>Test with the specified Test Id (%s) was not found.</font>"%testid
        return HttpResponse(message)
    if not testobj: #  If we still have a null object (for whatever reason), inform the user that the operation has failed.
        message = "<font color='#FF0000'>%s</font>"%error_msg('1058')
        return HttpResponse(message)
    if not iseditable(testobj) or testobj.status:
        message = "<font color='#FF0000'>%s</font>"%error_msg('1060')
        return HttpResponse(message)
    create_test_dict = {}
    create_test_dict['testname'] = testobj.testname
    testtype = testobj.testtype
    """
    create_test_dict['testtypes'] = ""
    for ttcode in mysettings.TEST_TYPES.keys():
        ttcodeval = ttcode.replace(" ", "__")
        if ttcode == testtype:
            create_test_dict['testtypes'] += "<option value=&quot;%s&quot; selected>%s</option>"%(ttcodeval, mysettings.TEST_TYPES[ttcode])
        else:
            create_test_dict['testtypes'] += "<option value=&quot;%s&quot;>%s</option>"%(ttcodeval, mysettings.TEST_TYPES[ttcode])
    """
    create_test_dict['testtypesvalue'] = testtype
    ruleset = testobj.ruleset
    rules = ruleset.split("#||#")
    create_test_dict['testrules'] = ""
    for trule in mysettings.RULES_DICT.keys():
        if trule in rules:
            create_test_dict['testrules'] += "<option value=&quot;%s&quot; selected>%s</option>"%(trule, mysettings.RULES_DICT[trule])
        else:
            create_test_dict['testrules'] += "<option value=&quot;%s&quot;>%s</option>"%(trule, mysettings.RULES_DICT[trule])
    create_test_dict['topic'] = testobj.topic
    testtopicname = testobj.topicname
    create_test_dict['testtopics'] = ""
    for ttopics in mysettings.TEST_TOPICS:
        ttopicsval = ttopics.replace(" ", "__")
        if testtopicname == ttopics:
            create_test_dict['testtopics'] += "<option value=&quot;%s&quot; selected>%s</option>"%(ttopicsval, ttopics)
        else:
            create_test_dict['testtopics'] += "<option value=&quot;%s&quot;>%s</option>"%(ttopicsval, ttopics)
        # Get topics created in the past by this user
    usertopics = Topic.objects.filter(user=userobj, isactive=True)
    for topic in usertopics:
        topicname = topic.topicname.replace(" ", "__")
        if testtopicname == topic.topicname:
            create_test_dict['testtopics'] += "<option value=&quot;%s&quot; selected>%s</option>"%(topicname, topic.topicname)
        else:
            create_test_dict['testtopics'] += "<option value=&quot;%s&quot;>%s</option>"%(topicname, topic.topicname)
    create_test_dict['totalscore'] = testobj.maxscore
    create_test_dict['evendistribution'] = 1 # Need to find from the existing challenges as to what its value should be.
    challengeqset = Challenge.objects.filter(test=testobj)
    prevchalscore = -1
    for challenge in challengeqset:
        if challenge.challengescore != prevchalscore and  prevchalscore != -1:
            create_test_dict['evendistribution'] = 0
            break
        prevchalscore = challenge.challengescore
    create_test_dict['negativescoring'] = testobj.negativescoreallowed
    create_test_dict['passscore'] = testobj.passscore
    if not create_test_dict['passscore']:
        create_test_dict['passscore'] = ""
    create_test_dict['testduration'] = testobj.duration
    create_test_dict['testdurationunit'] = "s"
    testduration_minute = int(testobj.duration)/60
    if testduration_minute > 0:
        create_test_dict['testduration'] = testduration_minute
        create_test_dict['testdurationunit'] = "m"
    # Randomly pick up a Challenge object for this test
    challengeobject = None
    challengeobjectqset = Challenge.objects.filter(test=testobj)
    if challengeobjectqset.__len__() == 0: #there are no challenge objects for this test
        create_test_dict['challengeduration'] = create_test_dict['testduration']  # so set the time duration of the entire test for this challenge - a bit of arbitrary decision.
        create_test_dict['challengedurationunit'] = create_test_dict['testdurationunit']
    else:
        challengeobject = challengeobjectqset[0]
    if challengeobject:
        create_test_dict['challengeduration'] = challengeobject.timeframe
        create_test_dict['challengedurationunit'] = 's'
    # Done with duration calculations...
    create_test_dict['grpname'] = testobj.evaluator
    evalobj = Evaluator.objects.filter(evalgroupname=testobj.evaluator)[0]
    create_test_dict['evaluators'] = ""
    if evalobj.groupmember1 and evalobj.groupmember1.emailid != "":
        create_test_dict['evaluators'] += evalobj.groupmember1.emailid + ","
    if evalobj.groupmember2 and evalobj.groupmember2.emailid != "":
        create_test_dict['evaluators'] += evalobj.groupmember2.emailid + ","
    if evalobj.groupmember3 and evalobj.groupmember3.emailid != "":
        create_test_dict['evaluators'] += evalobj.groupmember3.emailid + ","
    if evalobj.groupmember4 and evalobj.groupmember4.emailid != "":
        create_test_dict['evaluators'] += evalobj.groupmember4.emailid + ","
    if evalobj.groupmember5 and evalobj.groupmember5.emailid != "":
        create_test_dict['evaluators'] += evalobj.groupmember5.emailid + ","
    if evalobj.groupmember6 and evalobj.groupmember6.emailid != "":
        create_test_dict['evaluators'] += evalobj.groupmember6.emailid + ","
    if evalobj.groupmember7 and evalobj.groupmember7.emailid != "":
        create_test_dict['evaluators'] += evalobj.groupmember7.emailid + ","
    if evalobj.groupmember8 and evalobj.groupmember8.emailid != "":
        create_test_dict['evaluators'] += evalobj.groupmember8.emailid + ","
    if evalobj.groupmember9 and evalobj.groupmember9.emailid != "":
        create_test_dict['evaluators'] += evalobj.groupmember9.emailid + ","
    if evalobj.groupmember10 and evalobj.groupmember10.emailid != "":
        create_test_dict['evaluators'] += evalobj.groupmember10.emailid + ","
    create_test_dict['creatoremail'] = User.objects.filter(id=testobj.creator_id)[0].emailid + "," + create_test_dict['evaluators'] 
    # The variable name 'creatoremail' (above) is very misleading, but since I 
    # had been using it since earlier and don't want to disturb the stable
    # code, I am continuing with its usage. Note that the 'creatoremail'
    # actually holds the comma separated email ids of all evaluators as 
    # well as the email id of the creator.
    create_test_dict['creatoremail'] = re.sub(re.compile(r",\s*$"), "", create_test_dict['creatoremail']) # Removes all trailing comma's
    publishdatetime = testobj.publishdate.__str__()
    publishdateparts = publishdatetime.split(" ")
    publishdate, publishtime = publishdateparts[0], publishdateparts[1]
    publishyyyy, publishmon, publishday = publishdate.split("-")
    publishmon = mysettings.REV_MONTHS_DICT[publishmon]
    create_test_dict['publishdate'] = publishday + "-" + publishmon + "-" + publishyyyy
    activationdate = testobj.activationdate.__str__()
    activationdatetime = activationdate.split(" ")
    activationdatepart, activationtimepart = activationdatetime[0], activationdatetime[1]
    activationdateyyyy, activationdatemon, activationdateday = activationdatepart.split("-")
    activationdatemon = mysettings.REV_MONTHS_DICT[activationdatemon]
    create_test_dict['activedate'] = activationdateday + "-" + activationdatemon + "-" + activationdateyyyy
    skilltarget = testobj.quality
    create_test_dict['skilltarget'] = ""
    for skillcode in mysettings.SKILL_QUALITY.keys():
        if skillcode == skilltarget:
            create_test_dict['skilltarget'] += "<option value=&quot;%s&quot; selected>%s</option>"%(skillcode, mysettings.SKILL_QUALITY[skillcode])
        else:
            create_test_dict['skilltarget'] += "<option value=&quot;%s&quot;>%s</option>"%(skillcode, mysettings.SKILL_QUALITY[skillcode])
    testscope = testobj.scope
    create_test_dict['testscope'] = ""
    for tscope in mysettings.TEST_SCOPES:
        if tscope == testscope:
            create_test_dict['testscope'] += "<option value=&quot;%s&quot; selected>%s</option>"%(tscope, tscope)
        else:
            create_test_dict['testscope'] += "<option value=&quot;%s&quot;>%s</option>"%(tscope, tscope)
    answeringlanguages = testobj.allowedlanguages
    chosenlanguages = answeringlanguages.split('#||#')
    create_test_dict['answeringlanguage'] = ""
    for alang in mysettings.ANSWER_LANG_DICT.keys():
        if alang in chosenlanguages:
            create_test_dict['answeringlanguage'] += "<option value=&quot;%s&quot; selected>%s</option>"%(alang, mysettings.ANSWER_LANG_DICT[alang])
        else:
            create_test_dict['answeringlanguage'] += "<option value=&quot;%s&quot;>%s</option>"%(alang, mysettings.ANSWER_LANG_DICT[alang])
    testprogenv = testobj.progenv
    create_test_dict['progenv'] = ""
    if not testprogenv:
        create_test_dict['progenv'] += "<option value=&quot;0&quot; selected>None</option>"
        for proglang in mysettings.COMPILER_LOCATIONS.keys():
            create_test_dict['progenv'] += "<option value=&quot;%s&quot;>Yes - %s</option>"%(proglang, proglang)
    else:
        create_test_dict['progenv'] += "<option value=&quot;0&quot;>None</option>"
        for proglang in mysettings.COMPILER_LOCATIONS.keys():
            if testprogenv == proglang:
                create_test_dict['progenv'] += "<option value=&quot;%s&quot; selected>Yes - %s</option>"%(proglang, proglang)
            else:
                create_test_dict['progenv'] += "<option value=&quot;%s&quot;>Yes - %s</option>"%(proglang, proglang)
    create_test_dict['multimediareqd'] = testobj.multimediareqd
    create_test_dict['randomsequencing'] = testobj.randomsequencing
    create_test_dict['multipleattemptsallowed'] = testobj.allowmultiattempts
    create_test_dict['testlinkid'] = testobj.testlinkid
    create_test_dict['maxattemptscount'] = testobj.maxattemptscount
    create_test_dict['attemptsinterval'] = testobj.attemptsinterval
    create_test_dict['attemptsintervalunit'] = testobj.attemptsintervalunit
    create_test_dict['exist_test_id'] = testid
    create_test_dict['numchallenges'] = testobj.challengecount
    create_test_dict['createtesturl'] = skillutils.gethosturl(request) + '/' + mysettings.CREATE_TEST_URL
    tmpl = get_template("tests/create_test_form.html")
    create_test_dict.update(csrf(request))
    cxt = Context(create_test_dict)
    createtesthtml = tmpl.render(cxt)
    createtesthtml = re.sub(re.compile(r'\\"'), "&quot;", createtesthtml)
    #createtesthtml = re.sub(re.compile(r'"\s+\+\s+uid\s+\+\s+"'), userobj.id.__str__(), createtesthtml)
    #createtesthtml = "var uid='" + userobj.id + "';" + createtesthtml
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        createtesthtml = createtesthtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(createtesthtml)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def clearnegativescoreurl(request):
    testobj = None
    message = ''
    if request.method != "POST": 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.MANAGE_TEST_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    # Create the test object from the test Id passed.
    if not request.POST.has_key('exist_test_id'):
        message = "<font color='#FF0000'>%s</font>"%error_msg('1059');
        return HttpResponse(message)
    testid = request.POST['exist_test_id']
    try:
        testobj = Test.objects.filter(id=testid)[0]
    except:
        message = "<font color='#FF0000'>Test with the specified Test Id (%s) was not found.</font>"%testid
        return HttpResponse(message)
    if not testobj: #  If we still have a null object (for whatever reason), inform the user that the operation has failed.
        message = "<font color='#FF0000'>%s</font>"%error_msg('1058')
        return HttpResponse(message)
    if not iseditable(testobj) or testobj.status:
        message = "<font color='#FF0000'>%s</font>"%error_msg('1060')
        return HttpResponse(message)
    # Now we are sure we have a valid Test object. Find all Challenges. But first, set 'negativescoreallowed' for the test object to False.
    testobj.negativescoreallowed = False
    allchallenges = Challenge.objects.filter(test=testobj)
    if allchallenges.__len__() == 0: # There are no challenges in this test.
        resp = "<font color='#0000BB' size=-1>Negative scoring has been disabled for this test.</font>"
        return HttpResponse(resp)
    for challenge in allchallenges:
        challenge.negativescore = 0
        challenge.save()
    testobj.save()
    resp = "<font color='#0000BB' size=-1>Negative scoring has been disabled for this test.</font>"
    return HttpResponse(resp)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def deletetest(request):
    testobj = None
    message = ''
    if request.method != "POST": 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.MANAGE_TEST_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    # Create the test object from the test Id passed.
    if not request.POST.has_key('test_id'):
        message = "<font color='#FF0000'>%s</font>"%error_msg('1059');
        return HttpResponse(message)
    testid = request.POST['test_id']
    try:
        testobj = Test.objects.filter(id=testid)[0]
    except:
        message = "<font color='#FF0000'>Test with the specified Test Id (%s) was not found.</font>"%testid
        return HttpResponse(message)
    if testobj and (not iseditable(testobj) or testobj.status):
        message = "<font color='#FF0000' size=-1>%s</font>"%error_msg('1060')
        return HttpResponse(message)
    testname = testobj.testname
    # Now we have the test_id of the test that we need to delete. So we fetch 
    # all the challenges belonging to that test and delete them first. The we 
    # delete the test and return a HttpResponse.
    allchallenges = Challenge.objects.filter(test=testobj)
    chcount = 0
    for challenge in allchallenges:
        challenge.delete() # Deleted challenge...
        chcount += 1
    # Now delete the test object
    testobj.delete()
    message = "<font color='#0000BB' size=-1>The test named '%s' containing %s challenges was successfully deleted.</font>"%(testname, chcount.__str__())
    return HttpResponse(message)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def showuserview(request):
    testobj = None
    challengeobj = None
    message = ''
    if request.method != "POST": 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.MANAGE_TEST_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    # Create the test object from the test Id passed.
    if not request.POST.has_key('testid'):
        message = "<font color='#FF0000'>%s</font>"%error_msg('1059');
        return HttpResponse(message)
    testid = request.POST['testid']
    if not request.POST.has_key('challengeid'):
        message = "<font color='#FF0000'>%s</font>"%error_msg('1061');
        return HttpResponse(message)
    challengeid = request.POST['challengeid']
    """
    if not request.POST.has_key('testlinkid'):
        message = "<font color='#FF0000'>%s</font>"%error_msg('1062');
        return HttpResponse(message)
    testlinkid = request.POST['testlinkid']
    """
    try:
        testobj = Test.objects.filter(id=testid)[0]
    except:
        message = "<font color='#FF0000'>Test with the specified Test Id (%s) was not found.</font>"%testid
        return HttpResponse(message)
    try:
        challengeobj = Challenge.objects.filter(id=challengeid)[0]
    except:
        message = "<font color='#FF0000'>Challenge with the specified Challenge Id (%s) was not found.</font>"%challengeid
        return HttpResponse(message)
    challenge_dict = {}
    # Is the test editable?
    challenge_dict['editable'] = 1
    if not iseditable(testobj) or testobj.status:
        challenge_dict['editable'] = 0;
    # We need to find whether we can have both 'previous' and 'next' buttons or
    # only one of them
    allchallenges = Challenge.objects.filter(test=testobj).order_by('id')
    # But before doing that we need to see if we got a 'trav' argument. If so
    # we need to alter the challenge Id accordingly.
    if request.POST.has_key('trav'):
        direction = request.POST['trav']
        if direction.lower() == 'prev': # Find the challenge which was added
            #just prior to the challenge identified by the current challenge Id.
            previd = -1
            for chlng in allchallenges:
                if str(chlng.id) == challengeid:
                    if previd == -1: # The challengeid we have is the first one. So do nothing.
                        break
                    else:
                        challengeid = previd
                        challengeobj = Challenge.objects.filter(id=challengeid)[0]
                        break
                previd = chlng.id
        elif direction.lower() == 'next': # Find the next challenge
            nextctr = 0
            for chlng in allchallenges:
                if str(chlng.id) == challengeid:
                    if nextctr == allchallenges.__len__() - 1: # This is the last challenge, no next one. So just break out.
                        break
                    else:
                        challengeid = allchallenges[nextctr + 1].id
                        challengeobj = Challenge.objects.filter(id=challengeid)[0]
                        break
                nextctr += 1
        else: # Unrecognized 'trav' value, so no action need be taken.
            pass
    # By default we have both of them.
    challenge_dict['previous'] = 1
    challenge_dict['next'] = 1
    chctr = 0
    for chlng in allchallenges:
        if chlng.id == challengeobj.id:
            break
        chctr += 1
    if chctr == 0: # This is the first challenge, so no 'previous' button.
        challenge_dict['previous'] = 0
    if chctr == allchallenges.__len__() - 1: # Last challenge, so no 'next' button.
        challenge_dict['next'] = 0
    challenge_dict['testid'] = testid
    challenge_dict['challengeid'] = challengeid
    challengetype = challengeobj.challengetype
    challengemedia = challengeobj.mediafile
    challenge_dict['challengestatement'] = challengeobj.statement
    challenge_dict['challengetypedesc'] = ''
    if challengetype == 'MULT':
        challenge_dict['challengetypedesc'] = 'Multiple Choice'
    elif challengetype == 'FILB':
        challenge_dict['challengetypedesc'] = 'Fill up the Blanks'
    elif challengetype == 'SUBJ':
        challenge_dict['challengetypedesc'] = 'Subjective Type'
    elif challengetype == 'CODN':
        challenge_dict['challengetypedesc'] = 'Code writing/Programming'
    elif challengetype == 'ALGO':
        challenge_dict['challengetypedesc'] = 'Algorithms'
    else:
        challenge_dict['challengetypedesc'] = 'Unsupported Type'
    challenge_dict['challengetype'] = challengetype
    challenge_dict['responsekey'] = challengeobj.responsekey
    challenge_dict['challengemedia'] = challengemedia
    challenge_dict['testlinkid'] = testobj.testlinkid
    if challengemedia:
        username = userobj.displayname
        challenge_dict['challengemedia'] = "media" + os.path.sep + username + os.path.sep + "tests" + os.path.sep + testobj.id.__str__() + os.path.sep + challengemedia
    challenge_dict['oneormore'] = challengeobj.oneormore
    challengeoptions = []	
    if challengetype == 'MULT': # multiple choice type test
        for ctr in range(8):
            option = "option" + ctr.__str__()
            if challengeobj.__dict__.has_key(option) and challengeobj.__dict__[option] is not None:
                if challengeobj.__dict__[option] != "":
                    challengeoptions.append(challengeobj.__dict__[option])
        if challengeobj.oneormore:
            responsekeyslist = challengeobj.responsekey.split('#||#')
            challenge_dict['responsekey'] = "', '".join(responsekeyslist)
            challenge_dict['responsekey'] = "'" + challenge_dict['responsekey'] + "'"
    else:
        challengeoptions = None # Except for 'MULT' type tests,
                                # challengeoptions do not have any significance.
    challenge_dict['challengeoptions'] = challengeoptions
    challengescore = challengeobj.challengescore
    challengenegativescore = None
    if testobj.negativescoreallowed:
        challengenegativescore = challengeobj.negativescore
    maxtimeallowed = challengeobj.timeframe
    usermustrespond = challengeobj.mustrespond
    challenge_dict['challengescore'] = challengescore
    challenge_dict['challengenegativescore'] = challengenegativescore
    challenge_dict['maxtimeallowed'] = maxtimeallowed
    challenge_dict['usermustrespondresp'] = 'No'
    if usermustrespond:
        challenge_dict['usermustrespondresp'] = 'Yes'
    challenge_dict['additionalurl'] = challengeobj.additionalurl
    challenge_dict['challengequality'] = challengeobj.challengequality
    challenge_dict['oneormoreresp'] = 'Yes'
    if not challengeobj.oneormore:
        challenge_dict['oneormoreresp'] = 'No'
    tmpl = get_template("tests/challenge_user_view.html")
    challenge_dict.update(csrf(request))
    cxt = Context(challenge_dict)
    challengehtml = tmpl.render(cxt)
    return HttpResponse(challengehtml)
    

@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def editchallenge(request):
    testobj = None
    challengeobj = None
    message = ''
    if request.method != "POST": 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.MANAGE_TEST_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    # Need the test id to create the test object so we that can find the number of challenges it has.
    if not request.POST.has_key('testid'):
        message = "<font color='#FF0000'>%s</font>"%error_msg('1059');
        return HttpResponse(message)
    testid = request.POST['testid']
    if not request.POST.has_key('challengeid'):
        message = "<font color='#FF0000'>%s</font>"%error_msg('1061');
        return HttpResponse(message)
    challengeid = request.POST['challengeid']
    try:
        testobj = Test.objects.filter(id=testid)[0]
    except:
        message = "<font color='#FF0000'>Test with the specified Test Id (%s) was not found.</font>"%testid
        return HttpResponse(message)
    if not iseditable(testobj) or testobj.status:
        message = "<font color='#FF0000' size=-1>%s</font>"%error_msg('1060')
        return HttpResponse(message)
    try:
        challengeobj = Challenge.objects.filter(id=challengeid)[0]
    except:
        message = "<font color='#FF0000'>Challenge with the specified Challenge Id (%s) was not found.</font>"%challengeid
        return HttpResponse(message)
    # So now we have the entire challenge object, so we create the dict for the template.
    challenge_dict = {}
    testchallenges = Challenge.objects.filter(test=testobj).order_by('id')
    challengenumbersstr = 1
    totalscore = 0
    evendistrib = True
    prevscore = 0
    for chlng in testchallenges:
        if chlng.id == challengeobj.id:
            challenge_dict['challengenumbersstr'] = challengenumbersstr
        challengenumbersstr += 1
        totalscore += chlng.challengescore
        if chlng.challengescore != prevscore and prevscore > 0:
            evendistrib = False
        prevscore = chlng.challengescore
    challenge_dict['challengeid'] = challengeid
    challenge_dict['statement'] = challengeobj.statement
    challenge_dict['multimediareqd'] = testobj.multimediareqd
    challenge_dict['negativescoring'] = testobj.negativescoreallowed
    challenge_dict['testtype'] = testobj.testtype
    challenge_dict['testname'] = testobj.testname
    challenge_dict['mediafile'] = challengeobj.mediafile
    challenge_dict['extresourceurl'] = challengeobj.additionalurl
    if challenge_dict['extresourceurl'] is None:
        challenge_dict['extresourceurl'] = ""
    challenge_dict['challengescore'] = challengeobj.challengescore
    challenge_dict['existingchallengescore'] = challengeobj.challengescore
    challenge_dict['negativescore'] = challengeobj.negativescore
    challenge_dict['mustrespond'] = challengeobj.mustrespond
    challenge_dict['challengedurationseconds'] = challengeobj.timeframe
    challenge_dict['maxsizeallowable'] = challengeobj.maxresponsesizeallowable
    if challengeobj.maxresponsesizeallowable == -1: # no limit on response size
        challenge_dict['maxsizeallowable'] = ''
    respkeys = challengeobj.responsekey
    challenge_dict['responsekey'] = []
    challenge_dict['options'] = [] # This will be populated in case of 'MULT' type
    if challengeobj.challengetype == 'MULT':
        for ctr in range(8):
            option = "option" + ctr.__str__()
            if challengeobj.__dict__.has_key(option) and challengeobj.__dict__[option] is not None:
                if challengeobj.__dict__[option] != "":
                    challenge_dict['options'].append(challengeobj.__dict__[option])
    if challengeobj.responsekey and re.search(mysettings.SEPARATOR_PATTERN, challengeobj.responsekey):
        challenge_dict['responsekey'] = challengeobj.responsekey.split('#||#')
    else:
        challenge_dict['responsekey'] = [respkeys, ]
    challenge_dict['challengequality'] = challengeobj.challengequality
    challenge_dict['oneormore'] = challengeobj.oneormore
    challenge_dict['testlinkid'] = challengeobj.testlinkid
    
    challenge_dict['skillqualitylist'] = ''
    for skillqual in mysettings.SKILL_QUALITY.keys():
        if challenge_dict['challengequality'] == skillqual:
            challenge_dict['skillqualitylist'] += "<option value='%s' selected>%s</option>"%(skillqual, mysettings.SKILL_QUALITY[skillqual])
        else:
            challenge_dict['skillqualitylist'] += "<option value='%s'>%s</option>"%(skillqual, mysettings.SKILL_QUALITY[skillqual])
    challengetypeslist = ''
    if challenge_dict['testtype'] == 'COMP':
        challengetypeslist += "<b>Select Challenge Type</b><select name='challengetype' onchange='javascript:displayoptions();'>"
        for ttcode in mysettings.TEST_TYPES.keys():
            ttcodeval = ttcode.replace(" ", "__")
            if ttcode == challengeobj.challengetype:
                challengetypeslist += "<option value=%s selected>%s</option>"%(ttcodeval, mysettings.TEST_TYPES[ttcode])
            elif ttcode == 'COMP':
                continue # A challenge cannot be composite
            else:
                challengetypeslist += "<option value=%s>%s</option>"%(ttcodeval, mysettings.TEST_TYPES[ttcode])
        challengetypeslist += "</select><br />"
        if challengeobj.challengetype == 'SUBJ':
            challengetypeslist += "<div id='ansopts' style=''><b>Answer should not exceed <input type='text' name='maxsizewords' value='%s' size='6' maxlength='6'> words</b>(leave empty for no limit)</p></div>"%(challenge_dict['maxsizeallowable'].__str__())
        elif challengeobj.challengetype == 'CODN' or challengeobj.challengetype == 'ALGO':
            challengetypeslist += "<div id='ansopts' style=''><b>Answer should not exceed <input type='text' name='maxsizelines' value='%s' size='6' maxlength='6'> lines</b>(leave empty for no limit)</p></div>"%(challenge_dict['maxsizeallowable'].__str__())
        else:
            pass
    challenge_dict['challengetypeslist'] = challengetypeslist
    challenge_dict['responsekeyscontrolslist'] = ''
    challenge_dict['answeringoptions'] = ''
    if challengeobj.challengetype == 'MULT':
        challenge_dict['responsekeyscontrolslist'] += "<b>Select the correct response(s)<font size='-2'><a href='#' onmouseover='javascript:showwhyresponsekey(this);'>[why should I do this?]</a></font>:</b><br>"
        if challenge_dict['oneormore']:
            challenge_dict['answeringoptions'] += "<p><b>Can there be more than one correct option:</b>&nbsp;<input type='radio' name='oneormore' value='yes' checked=true onchange='javascript:displayresponsekeycontrols();'>Yes&nbsp;&nbsp;&nbsp;&nbsp;<input type='radio' name='oneormore' value='no' onchange='javascript:displayresponsekeycontrols();'>No<br />"
        else:
            challenge_dict['answeringoptions'] += "<p><b>Can there be more than one correct option:</b>&nbsp;<input type='radio' name='oneormore' value='yes' onchange='javascript:displayresponsekeycontrols();'>Yes&nbsp;&nbsp;&nbsp;&nbsp;<input type='radio' name='oneormore' value='no' checked=true onchange='javascript:displayresponsekeycontrols();'>No<br />"
        challenge_dict['answeringoptions'] += "<b>Please enter the options you want to be made available for this challenge/question.(max 8 options) </b><br />"
        #print challenge_dict['options'][4]
        if challenge_dict['options'].__len__() > 0 and challenge_dict['options'][0]:
            challenge_dict['answeringoptions'] += "<i>Option #a:</i> <input type='text' name='choice1' value='%s' onblur='javascript:displayresponsekeycontrols();'><br />"%(challenge_dict['options'][0])
        else:
            challenge_dict['answeringoptions'] += "<i>Option #a:</i> <input type='text' name='choice1' value='' onblur='javascript:displayresponsekeycontrols();'><br />"
        if challenge_dict['options'].__len__() > 1 and challenge_dict['options'][1]:
            challenge_dict['answeringoptions'] += "<i>Option #b</i>: <input type='text' name='choice2' value='%s' onblur='javascript:displayresponsekeycontrols();'><br />"%(challenge_dict['options'][1])
        else:
            challenge_dict['answeringoptions'] += "<i>Option #b</i>: <input type='text' name='choice2' value='' onblur='javascript:displayresponsekeycontrols();'><br />"
        if challenge_dict['options'].__len__() > 2 and challenge_dict['options'][2]:
            challenge_dict['answeringoptions'] += "<i>Option #c:</i> <input type='text' name='choice3' value='%s' onblur='javascript:displayresponsekeycontrols();'><br />"%(challenge_dict['options'][2])
        else:
            challenge_dict['answeringoptions'] += "<i>Option #c:</i> <input type='text' name='choice3' value='' onblur='javascript:displayresponsekeycontrols();'><br />"
        if challenge_dict['options'].__len__() > 3 and challenge_dict['options'][3]:
            challenge_dict['answeringoptions'] += "<i>Option #d:</i> <input type='text' name='choice4' value='%s' onblur='javascript:displayresponsekeycontrols();'><br />"%(challenge_dict['options'][3])
        else:
            challenge_dict['answeringoptions'] += "<i>Option #d:</i> <input type='text' name='choice4' value='' onblur='javascript:displayresponsekeycontrols();'><br />"
        if challenge_dict['options'].__len__() > 4 and challenge_dict['options'][4]:
            challenge_dict['answeringoptions'] += "<i>Option #e:</i> <input type='text' name='choice5' value='%s' onblur='javascript:displayresponsekeycontrols();'><br />"%(challenge_dict['options'][4])
        else:
            challenge_dict['answeringoptions'] += "<i>Option #e:</i> <input type='text' name='choice5' value='' onblur='javascript:displayresponsekeycontrols();'><br />"
        if challenge_dict['options'].__len__() > 5 and challenge_dict['options'][5]:
            challenge_dict['answeringoptions'] += "<i>Option #f:</i> <input type='text' name='choice6' value='%s' onblur='javascript:displayresponsekeycontrols();'><br />"%(challenge_dict['options'][5])
        else:
            challenge_dict['answeringoptions'] += "<i>Option #f:</i> <input type='text' name='choice6' value='' onblur='javascript:displayresponsekeycontrols();'><br />"
        if challenge_dict['options'].__len__() > 6 and challenge_dict['options'][6]:
            challenge_dict['answeringoptions'] += "<i>Option #g:</i> <input type='text' name='choice7' value='%s' onblur='javascript:displayresponsekeycontrols();'><br />"%(challenge_dict['options'][6])
        else:
            challenge_dict['answeringoptions'] += "<i>Option #g:</i> <input type='text' name='choice7' value='' onblur='javascript:displayresponsekeycontrols();'><br />"
        if challenge_dict['options'].__len__() > 7 and challenge_dict['options'][7]:
            challenge_dict['answeringoptions'] += "<i>Option #h:</i> <input type='text' name='choice8' value='%s' onblur='javascript:displayresponsekeycontrols();'></p>"%(challenge_dict['options'][7])
        else:
            challenge_dict['answeringoptions'] += "<i>Option #h:</i><input type='text' name='choice8' value='' onblur='javascript:displayresponsekeycontrols();'></p>"
        if challenge_dict['oneormore']:
            for option in challenge_dict['options']:
                if option  in challenge_dict['responsekey']:
                    challenge_dict['responsekeyscontrolslist'] += "<i><input type='checkbox' name='responsekey[]' value='" + option  + "' checked>" + option + "</i><br>"
                else:
                    challenge_dict['responsekeyscontrolslist'] += "<i><input type='checkbox' name='responsekey[]' value='" + option + "'>" + option + "</i><br>"
        else: # Only one option is correct
            for option in challenge_dict['options']:
                if option  in challenge_dict['responsekey']:
                    challenge_dict['responsekeyscontrolslist'] += "<i><input type='radio' name='responsekey' value='" + option  + "' checked=true>" + option + "</i><br>"
                else:
                    challenge_dict['responsekeyscontrolslist'] += "<i><input type='radio' name='responsekey' value='" + option + "'>" + option + "</i><br>"
    elif challengeobj.challengetype == 'FILB':
         challenge_dict['responsekeyscontrolslist'] += "<b>Enter the correct response<font size='-2'><a href='#' onmouseover='javascript:showwhyresponsekey(this);'>[why should I do this?]</a></font>:</b><input type='text' name='responsekey' value='%s' size='10' maxlength='250'><br>"%(challenge_dict['responsekey'][0])
         challenge_dict['answeringoptions'] += "<input type='hidden' name='oneormore' value='no'>"
    elif challengeobj.challengetype == 'CODN' or challengeobj.challengetype == 'ALGO':
        pass
        #challenge_dict['answeringoptions'] += "<b>Answer should not exceed <input type='text' name='maxsizelines' value='%s' size='6' maxlength='6'> lines. </b>(leave empty for no limit.)</p>"%(challenge_dict['maxsizeallowable'].__str__())
    elif challengeobj.challengetype == 'SUBJ':
        pass
        #challenge_dict['answeringoptions'] += "<b>Answer should not exceed <input type='text' name='maxsizewords' value='%s' size='6' maxlength='6'> words</b>(leave empty for no limit)</p>"%(challenge_dict['maxsizeallowable'].__str__())
    else:
        pass
    challenge_dict['evendistribution'] = evendistrib
    challenge_dict['test_id'] = testid # or challengeobj.test.id
    challenge_dict['lastchallengectr'] = testchallenges.__len__()
    challenge_dict['totalscore'] = totalscore
    challenge_dict['usrid'] = userobj.id
    challenge_dict['challenge_links_list'] = []
    for challenge in testchallenges:
        challengestmt = challenge.statement[:20] + " ..."
        challenge_dict['challenge_links_list'].append((challenge.id, challengestmt, testobj.id, testobj.testlinkid))
    tmpl = get_template("tests/edit_challenge.html")
    challenge_dict.update(csrf(request))
    cxt = Context(challenge_dict)
    challengehtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        challengehtml = challengehtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(challengehtml)

"""
The function below generates a test URL at realtime. For a given test,
it generates the URL every time. But before generating it checks the 
privileges of the user it is servicing, and handles the generation of the
test URL accordingly. The view pointed to by this URL is the same as what
the candidate sees while taking the test. The only difference will be
the controls for entering the response would be readonly and/or disabled.
"""
def generatetesturl(testobj, userobj):
    pass



