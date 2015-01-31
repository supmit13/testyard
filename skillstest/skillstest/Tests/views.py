from django.conf import settings
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
    createlink, testtypes, testrules, testtopics, skilltarget, testscope, answeringlanguage, progenv, existingtestnames, assocevalgrps, evalgroupslitags = "", "", "", "", "", "", "", "", "", "var evalgrpsdict = {};", "<li id=&quot;drag_eval_groups&quot; title=&quot;drag,eval,groups&quot;>drag eval groups</li>"
    if testlist_ascreator.__len__() <= mysettings.NEW_USER_FREE_TESTS_COUNT: # Also add condition to check user's 'plan' (to be done later)
        createlink = "<a href='#' onClick='javascript:showcreatetestform(&quot;%s&quot;);loaddatepicker();'>Create New Test</a>"%userobj.id
        for ttcode in mysettings.TEST_TYPES.keys():
            if ttcode == 'MULT':
                testtypes += "<option value=&quot;%s&quot; selected>%s</option>"%(ttcode, mysettings.TEST_TYPES[ttcode])
            else:
                testtypes += "<option value=&quot;%s&quot;>%s</option>"%(ttcode, mysettings.TEST_TYPES[ttcode])
        for trule in mysettings.RULES_DICT.keys():
            testrules += "<option value=&quot;%s&quot;>%s</option>"%(trule, mysettings.RULES_DICT[trule])
        for ttopics in mysettings.TEST_TOPICS:
            testtopics += "<option value=&quot;%s&quot;>%s</option>"%(ttopics, ttopics)
        # Get topics created in the past by this user
        usertopics = Topic.objects.filter(user=userobj, isactive=True)
        for topic in usertopics:
            testtopics += "<option value='%s'>%s</option>"%(topic.topicname, topic.topicname)
        for skillcode in mysettings.SKILL_QUALITY.keys():
            skilltarget += "<option value=&quot;%s&quot;>%s</option>"%(skillcode, mysettings.SKILL_QUALITY[skillcode])
        for tscope in mysettings.TEST_SCOPES:
            if tscope == 'public':
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
        evalgrpemails = ",".join(test.evaluator.groupmember1.emailid, test.evaluator.groupmember2.emailid, test.evaluator.groupmember3.emailid, test.evaluator.groupmember4.emailid, test.evaluator.groupmember5.emailid, test.evaluator.groupmember6.emailid, test.evaluator.groupmember7.emailid, test.evaluator.groupmember8.emailid, test.evaluator.groupmember9.emailid, test.evaluator.groupmember10.emailid)
        evalgrpemails = re.sub(skillutils.multiplecommapattern, ",", evalgrpemails)
        evalgrpemails = re.sub(skillutils.endcommapattern, "",evalgrpemails)
        assocevalgrps += "evalgrpsdict.%s = %s;"%(test.evaluator.evalgroupname, evalgrpemails)
        evalgroupslitags += "<li id=&quot;%s&quot; title=&quot;%s&quot;>%s</li>"%(test.evaluator.evalgroupname, evalgrpemails, test.evaluator.evalgroupname)

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
    tests_user_dict['existingtestnames'] = ",".join(user_creator_other_evaluators_dict.keys())
    tests_user_dict['assocevalgrps'] = assocevalgrps
    tests_user_dict['evalgroupslitags'] = evalgroupslitags
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




def create(request):
    return HttpResponse(createtestshtml)


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


def edit(request):
    get_user_dict = get_user_tests(request)
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


