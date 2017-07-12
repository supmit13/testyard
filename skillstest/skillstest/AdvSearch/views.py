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

# Application specific libraries...
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
from skillstest.Subscription.models import Plan, UserPlan, Transaction
from skillstest.Tests.models import Topic, Subtopic, Evaluator, Test, UserTest, Challenge, UserResponse, WouldbeUsers, EmailFailure, Schedule, Interview, InterviewQuestions, InterviewCandidates
from skillstest.Tests.views import get_user_tests, iseditable                                                                                                                                                                                                      
from skillstest import settings as mysettings
from skillstest.errors import error_msg
import skillstest.utils as skillutils
from skillstest.utils import Logger


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def advsearch(request):
    tests_user_dict = get_user_tests(request)
    tests_user_dict['testschallengesearchurl'] = mysettings.TESTS_CHALLENGE_SEARCH_URL
    tests_user_dict['copytesturl'] = mysettings.COPY_TEST_URL
    tests_user_dict['usersearchurl'] = mysettings.USER_SEARCH_URL
    tests_user_dict['searchtestinfourl'] = mysettings.SEARCH_TEST_INFO_URL
    tests_user_dict['displaytestchallenges'] = mysettings.DISPLAY_SEARCHED_CHALLENGES_URL
    inc_context = skillutils.includedtemplatevars("Search", request)
    for inc_key in inc_context.keys():
        tests_user_dict[inc_key] = inc_context[inc_key]
    # Now create and render the template here
    tmpl = get_template("advsearch/searchscreen.html")
    tests_user_dict.update(csrf(request))
    cxt = Context(tests_user_dict)
    searchtestshtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        searchtestshtml = searchtestshtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(searchtestshtml)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def testschallengesearch(request):
    message = ''
    if request.method != "POST": 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.TESTS_CHALLENGE_SEARCH_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    testname, searchphrase, creatorname = "", "", ""
    if request.POST.has_key('testname'):
        testname = request.POST['testname']
    if request.POST.has_key('searchphrase'):
        searchphrase = request.POST['searchphrase']
    if request.POST.has_key('testcreator'):
        testcreator = request.POST['testcreator']
    testrecs = []
    testqset, challengesqset, testsqsetcreator = [], [], []
    if testname:
        testqset = Test.objects.filter(testname__icontains=testname)
    if searchphrase:
        challengesqset = Challenge.objects.filter(statement__icontains=searchphrase)
        if not testname: # Search test names for the search phrase
            testqset = Test.objects.filter(testname__icontains=searchphrase)
    if testcreator:
        testsqsetcreator = Test.objects.filter(Q(creator__displayname__icontains=testcreator) | Q(creator__firstname__icontains=testcreator) | Q(creator__lastname__icontains=testcreator))
    # Point to remember: challenges of tests that have not yet been activated or published will not figure in the list.
    # We need to implement this functionality in this method. If iseditable is True, then the test hasn't been published yet
    # and hence we cannot use its challenges/questions in our search results.
    for testobj in testqset:
        if iseditable(testobj): # Test hasn't been published yet. So it is unusable in search result
            continue
        testrecs.append(testobj)
    try:
        for challengeobj in challengesqset:
            assoctestobj = challengeobj.test
            if iseditable(assoctestobj): # Test hasn't been published yet. So it is unusable in search result
                continue
            testrecs.append(assoctestobj)
    except:
        pass
    for testobj in testsqsetcreator:
        if iseditable(testobj): # Test hasn't been published yet. So it is unusable in search result
            continue
        testrecs.append(testobj)
    resultrecs = {}
    datadict = {}
    for trec in testrecs:
        if trec.testtype == 'COMP':
            trec.testtype = "Composite"
        elif trec.testtype == 'MULT':
            trec.testtype = "Multiple Choices"
        elif trec.testtype == 'FILB':
            trec.testtype = "Fill in the Blanks"
        elif trec.testtype == 'SUBJ':
            trec.testtype = "Subjective"
        elif trec.testtype == 'CODN':
            trec.testtype = "Coding/Programming"
        elif trec.testtype == 'ALGO':
            trec.testtype = "Algorithm"
        else:
            trec.testtype = "Unrecognized Type"
        trec.allowedlanguages = trec.allowedlanguages.replace("#||#", ", ")
        if trec.quality == 'PRO':
            trec.quality = "Proficient"
        elif trec.quality == 'INT':
            trec.quality = "Intermediate"
        elif trec.quality == 'BEG':
            trec.quality = "Beginner"
        else:
            trec.quality = "Unrecognized Quality State"
        try:
            rulesetcodes = str(trec.ruleset).split("#||#")
            rulesetlist = []
            for rulesetcode in rulesetcodes:
                rulesetdesc = mysettings.RULES_DICT[rulesetcode]
                rulesetlist.append(rulesetdesc)
            rulesetstr = ", ".join(rulesetlist)
        except:
            rulesetstr = ""
        copyable = "True"
        utqset = UserTest.objects.filter(test=trec)
        wbuqset = WouldbeUsers.objects.filter(test=trec)
        testschedlist = list(chain(utqset, wbuqset))
        curdatetime = datetime.datetime.now()
        for testsched in testschedlist:
            validtill = testsched.validtill
            try:
                if not validtill or validtill == "":
                    continue
                validtillstr = str(validtill)
                validtillstrlist = validtillstr.split("+")
                validtilldd = datetime.datetime.strptime(validtillstrlist[0], "%Y-%m-%d %H:%M:%S") #This will make this offset-naive
                if validtilldd > curdatetime:
                    copyable = "False"
                    break
            except:
                message = sys.exc_info()[1].__str__()
                return HttpResponse(message)
        if copyable == True:
            schedqset = Schedule.objects.filter(test=trec)
            for schedrec in schedqset:
                slot = schedrec.slot
                validfrom, validtill = slot.split("#||#")
                if not validtill or validtill == "":
                    continue
                validtilldd = datetime.datetime.strptime(validtill, "%Y-%m-%d %H:%M:%S")
                if validtilldd > curdatetime:
                    copyable = "False"
                    break
        resultrecs[trec.testname] = {'id' : trec.id, 'topic' : trec.topic.topicname, 'creator' : trec.creator.displayname, 'testtype' : trec.testtype, 'createdate' : trec.createdate, 'maxscore' : trec.maxscore, 'passscore' : trec.passscore, 'ruleset' : rulesetstr, 'duration' : str(trec.duration/60) + " 	minutes" , 'allowedlanguages' : trec.allowedlanguages, 'challengecount' : trec.challengecount, 'publishdate' : trec.publishdate, 'multimediareqd' : trec.multimediareqd, 'progenv' : trec.progenv, 'scope' : trec.scope, 'quality' : trec.quality, 'negativescoreallowed' : trec.negativescoreallowed, 'copyable' : copyable}
    datadict['resultrecs'] = resultrecs
    tmpl = get_template("advsearch/testrecords.html")
    cxt = Context(datadict)
    testrecordshtml = tmpl.render(cxt)
    return HttpResponse(testrecordshtml)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def usersearch(request):
    message = ''
    if request.method != "POST": 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.TESTS_CHALLENGE_SEARCH_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    username, searchphrase = "", ""
    if request.POST.has_key('user'):
        username = request.POST['user']
    if request.POST.has_key('searchphrase'):
        searchphrase = request.POST['searchphrase']
    usersqset_byname = []
    usersqset_byphrase = []
    if username != "":
        usersqset_byname = User.objects.filter(displayname__icontains=username)
    if searchphrase != "":
        usersqset_byphrase = User.objects.filter(displayname__icontains=searchphrase)
        if not username:
            usersqset_byphrase_firstname = User.objects.filter(firstname__icontains=searchphrase)
            usersqset_byphrase_lastname = User.objects.filter(lastname__icontains=searchphrase)
            usersqset_byphrase_emailid = User.objects.filter(emailid__icontains=searchphrase)
            usersqset_byphrase = list(usersqset_byphrase)
            try:
                for elem in  usersqset_byphrase_firstname:
                    usersqset_byphrase.append(elem)
                for elem in  usersqset_byphrase_lastname:
                    usersqset_byphrase.append(elem)
                for elem in  usersqset_byphrase_emailid:
                    usersqset_byphrase.append(elem)
            except:
                print sys.exc_info()[1].__str__()
    userobjlist = []
    for userobject in usersqset_byname:
        userobjlist.append(userobject)
    for userobject in usersqset_byphrase:
        userobjlist.append(userobject)
    resultrecs = {}
    datadict = {}
    for userobject in userobjlist:
        firstname = userobject.firstname
        lastname = userobject.lastname
        middlename = userobject.middlename
        displayname = userobject.displayname
        active = userobject.active
        userpic = "media/" + userobject.displayname + "/images/profilepic.jpg"
        sex = userobject.sex
        if sex == 'm':
            sex = "Male"
        elif sex == 'f':
            sex = "Female"
        else:
            sex = "Unknown"
        membersince = userobject.joindate
        usertype = userobject.usertype
        if usertype == 'CONS':
            usertype = "Consultant"
        elif usertype == 'CORP':
            usertype = "Corporate"
        elif usertype == 'ACAD':
            usertype = "Academic"
        elif usertype == 'CERT':
            usertype = "Certification"
        else:
            usertype = ""
        resultrecs[displayname] = {'firstname' : firstname, 'middlename' : middlename, 'lastname' : lastname, 'active' : active, 'sex' : sex, 'userpic' : userpic, 'membersince' : membersince, 'usertype' : usertype}
    datadict['resultrecs'] = resultrecs
    tmpl = get_template("advsearch/userrecords.html")
    cxt = Context(datadict)
    userrecordshtml = tmpl.render(cxt)
    return HttpResponse(userrecordshtml)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def testinfosearch(request):
    message = ''
    if request.method != "POST": 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.TESTS_CHALLENGE_SEARCH_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    if not userobj:
        response = HttpResponse("User not found!")
        return response
    displayname = ""
    if not request.POST.has_key('displayname'):
        message = "Required parameter displayname not found!"
        response = HttpResponse(message)
        return response
    displayname = request.POST['displayname']
    datadict = {}
    uobj = None
    try:
        uobj = User.objects.get(displayname=displayname)
    except:
        message = "Could not find the user object identified by the displayname '%'"%displayname
        response = HttpResponse(message)
        return response
    testscreated = {}
    testscreatedqset = Test.objects.filter(creator=uobj, scope='public')
    for testobj in  testscreatedqset:
        testname = testobj.testname
        testtopic = testobj.topicname
        if not testtopic:
            testtopic = testobj.topic.topicname
        testtype = testobj.testtype
        testquality = testobj.quality
        negativescoring = testobj.negativescoreallowed
        testtotalscore = testobj.maxscore
        testpassscore = testobj.passscore
        testrules = testobj.ruleset
        testid = testobj.id
        if not testscreated.has_key(str(testid)):
            testscreated[str(testid)] = [testname, testtopic, testtype, testquality, negativescoring, testtotalscore, testpassscore, testrules]
        else:
            pass
    datadict['testscreated'] = testscreated
    testsevaluated = {}
    testsevaluatorqset = Test.objects.filter(scope='public')
    for testobj in testsevaluatorqset:
        evalobj = testobj.evaluator
        if (evalobj.groupmember1 and evalobj.groupmember1 == uobj) or (evalobj.groupmember2 and evalobj.groupmember2 == uobj) or (evalobj.groupmember3 and evalobj.groupmember3 == uobj) or (evalobj.groupmember4 and evalobj.groupmember4 == uobj) or (evalobj.groupmember5 and evalobj.groupmember5 == uobj) or (evalobj.groupmember6 and evalobj.groupmember6 == uobj) or (evalobj.groupmember7 and evalobj.groupmember7 == uobj) or (evalobj.groupmember8 and evalobj.groupmember8 == uobj) or (evalobj.groupmember9 and evalobj.groupmember9 == uobj) or (evalobj.groupmember10 and evalobj.groupmember10 == uobj):
            testname = testobj.testname
            testtopic = testobj.topicname
            if not testtopic:
                testtopic = testobj.topic.topicname
            testtype = testobj.testtype
            testquality = testobj.quality
            negativescoring = testobj.negativescoreallowed
            testtotalscore = testobj.maxscore
            testpassscore = testobj.passscore
            testrules = testobj.ruleset
            testid = testobj.id
            testsevaluated[str(testid)] = [testname, testtopic, testtype, testquality, negativescoring, testtotalscore, testpassscore, testrules]
        else:
            pass
    datadict['testsevaluated'] = testsevaluated
    teststaken = {}
    usertestsqset = UserTest.objects.filter(user=uobj, visibility=2)
    useremail = uobj.emailid
    wouldbeusersqset = WouldbeUsers.objects.filter(emailaddr=useremail, visibility=2)
    teststakenqset = list(chain(usertestsqset, wouldbeusersqset))
    for usertestobj in teststakenqset:
        testname = usertestobj.test.testname
        testtopic = usertestobj.test.topicname
        if not testtopic:
            testtopic = usertestobj.test.topic.topicname
        testtype = usertestobj.test.testtype
        testquality = usertestobj.test.quality
        negativescoring = usertestobj.test.negativescoreallowed
        testtotalscore = usertestobj.test.maxscore
        testpassscore = usertestobj.test.passscore
        testrules = usertestobj.test.ruleset
        testid = usertestobj.test.id
        score = usertestobj.score
        evalcommitstate = usertestobj.evalcommitstate
        if teststaken.has_key(str(testid)):
            if teststaken[str(testid)][8] > score and teststaken[str(testid)][8] != "Not evaluated yet":
                pass
            elif teststaken[str(testid)][8] == "Not evaluated yet" and not evalcommitstate:
                score = "Not evaluated yet"
            else:
                teststaken[str(testid)] = [testname, testtopic, testtype, testquality, negativescoring, testtotalscore, testpassscore, testrules, score]
        else:
            if not evalcommitstate:
                score = "Not evaluated yet"
            teststaken[str(testid)] = [testname, testtopic, testtype, testquality, negativescoring, testtotalscore, testpassscore, testrules, score]
    datadict['teststaken'] = teststaken
    interviewsconducted = {}
    interviewsconductedqset = Interview.objects.filter(interviewer=uobj, scope='public')
    for interviewobj in interviewsconductedqset:
        interviewtitle = interviewobj.title
        interviewtopic = interviewobj.topicname
        if not interviewtopic:
            interviewtopic = interviewobj.topic.topicname
        maxscore = interviewobj.maxscore
        maxduration = interviewobj.maxduration
        quality = interviewobj.quality
        interviewid = interviewobj.id
        interviewcandidateobj = None
        candidateemail = ""
        try:
            interviewcandidateobj = InterviewCandidates.objects.get(interview=interviewobj)
            candidateemail = interviewcandidateobj.emailaddr
        except:
            pass
        if not interviewsconducted.has_key(str(interviewid)):
            interviewsconducted[str(interviewid)] = [interviewtitle, interviewtopic, maxscore, maxduration, quality, candidateemail]
        else:
            pass
    datadict['interviewsconducted'] = interviewsconducted
    interviewsattended = {}
    interviewsattendedqset = InterviewCandidates.objects.filter(emailaddr=useremail)
    for interviewcandidateobj in interviewsattendedqset:
        interviewtitle = interviewcandidateobj.interview.title
        interviewer = interviewcandidateobj.interview.interviewer.displayname
        interviewtopic = interviewcandidateobj.interview.topicname
        if not interviewtopic:
            interviewtopic = interviewcandidateobj.interview.topic.topicname
        interviewdate = interviewcandidateobj.actualstarttime
        interviewcandidateid = interviewcandidateobj.id
        if not interviewsattended.has_key(str(interviewcandidateid)):
            interviewsattended[str(interviewcandidateid)] = [interviewtitle, interviewer, interviewtopic]
            #interviewsattended[str(interviewcandidateid)] = [interviewtitle, interviewer, interviewtopic, interviewdate]
        else:
            pass
    datadict['interviewsattended'] = interviewsattended
    tmpl = get_template("advsearch/usertestinfo.html")
    cxt = Context(datadict)
    usertestinfohtml = tmpl.render(cxt)
    return HttpResponse(usertestinfohtml)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def displaychallenges(request):
    message = ''
    if request.method != "POST": 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.TESTS_CHALLENGE_SEARCH_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    if not userobj:
        response = HttpResponse("User not found!")
        return response
    testid, testobj = "", None
    if not request.POST.has_key('testid'):
        message = "Error: Required parameter test Id missing in request. Cannot process request any further. Quiting."
        response = HttpResponse(message)
        return response
    testid = request.POST['testid']
    try:
        testobj = Test.objects.get(id=testid)
    except:
        message = "Could not retrieve the test object identified by the given test Id. Cannot process request any further. Quiting."
        response = HttpResponse(message)
        return response
    # First, check to see if the challenges may be shown - the test should be in public scope and it should not have any existing schedule.
    if testobj.scope != "public":
        message = "<span style='color:#AA0000;'>The test identified by name '%s' is not in public domain. Hence, the challenges are not accessible to the logged in user.</span>"%testobj.testname
        response = HttpResponse(message)
        return response
    # Check if it has a future schedule
    curdatetime = datetime.datetime.now()
    utqset = UserTest.objects.filter(test=testobj)
    wbuqset = WouldbeUsers.objects.filter(test=testobj)
    testschedlist = list(chain(utqset, wbuqset))
    showable = True
    for testsched in testschedlist:
        validtill = testsched.validtill
        try:
            if not validtill or validtill == "":
                continue
            validtillstr = str(validtill)
            validtillstrlist = validtillstr.split("+")
            validtilldd = datetime.datetime.strptime(validtillstrlist[0], "%Y-%m-%d %H:%M:%S") #This will make this offset-naive
            if validtilldd > curdatetime:
                showable = False
                break
        except:
            message = sys.exc_info()[1].__str__()
            return HttpResponse(message)
    if showable:
        schedqset = Schedule.objects.filter(test=testobj)
        for schedrec in schedqset:
            slot = schedrec.slot
            validfrom, validtill = slot.split("#||#")
            if not validtill or validtill == "":
                continue
            validtilldd = datetime.datetime.strptime(validtill, "%Y-%m-%d %H:%M:%S")
            if validtilldd > curdatetime:
                showable = False
                break
    if not showable:
        message = "The test identified by name '%s' has an existing schedule in the future. Hence, the challenges are not accessible to the logged in user."%testobj.testname
        response = HttpResponse(message)
        return response
    # Display the challenges...
    challengesqset = Challenge.objects.filter(test=testobj)
    challengesdict = {}
    for challengeobj in challengesqset:
        challengestatement = challengeobj.statement
        challengetype = challengeobj.challengetype
        challengescore = challengeobj.challengescore
        negativescore = challengeobj.negativescore
        responsekey = challengeobj.responsekey
        if not responsekey:
            responsekey = "NA"
        mediafile = challengeobj.mediafile
        additionalurl = challengeobj.additionalurl
        timeframe = challengeobj.timeframe
        challengequality = challengeobj.challengequality
        oneormore = challengeobj.oneormore
        options = [challengeobj.option1, challengeobj.option2, challengeobj.option3, challengeobj.option4, challengeobj.option5, challengeobj.option6, challengeobj.option7, challengeobj.option8 ]
        challengesdict[str(challengeobj.id)] = [challengestatement, challengetype, challengescore, negativescore, responsekey, mediafile, additionalurl, timeframe, challengequality, oneormore, options]
    tmpl = get_template("advsearch/challengeslist.html")
    datadict = {'challengesdict' : challengesdict }
    cxt = Context(datadict)
    challengesinfohtml = tmpl.render(cxt)
    return HttpResponse(challengesinfohtml)







