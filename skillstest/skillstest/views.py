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


"""
Dashboard will consist of 2 parts - 1) Details of tests conducted by the user
and 2) details of the tests taken by the user. Also, views will be based on
the privileges of the user. 'Admin' users will be able  to view and access every
bit of information pertaining to the user, users with lesser rights will be able
to view lesser info.
"""
@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def dashboard(request):
    message = ''
    if request.method != "GET": # Illegal bad request... 
        message = error_msg('1004')
        # A logging mechanism may be used to track how many and from where
        # such requests come and that may, sometimes, tell a curious story.
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.DASHBOARD_URL + "?msg=%s"%message)
        return response
    # If request method is 'GET', then retrieve Session and User info from the DB
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    # Retrieve information pertaining to all Tests this user has access to.
    # *Starting with the ones in which the user is a creator...
    testlist_ascreator = Test.objects.filter(creator=userobj)
    # *... then the ones where the user is one of the evaluators...
    evaluator_groups = Evaluator.objects.filter(Q(groupmember1=userobj)|Q(groupmember2=userobj)|Q(groupmember3=userobj)| \
                                                Q(groupmember4=userobj)|Q(groupmember5=userobj)|Q(groupmember6=userobj)| \
                                                Q(groupmember7=userobj)|Q(groupmember8=userobj)|Q(groupmember9=userobj)| \
                                                Q(groupmember10=userobj))
    testlist_asevaluator = Test.objects.filter(evaluator__in=evaluator_groups)
    # Note: Both 'testlist_ascreator' and 'testlist_asevaluator' are QuerySet objects.
    # Get other evaluators in all tests where the user is creator
    user_creator_other_evaluators_dict = {}
    for test in testlist_ascreator:
        user_creator_other_evaluators_dict[test.testname] = ( test.evaluator.groupmember1, test.evaluator.groupmember2, \
                                                              test.evaluator.groupmember3, test.evaluator.groupmember4, test.evaluator.groupmember5, \
                                                              test.evaluator.groupmember6, test.evaluator.groupmember7, test.evaluator.groupmember8, \
                                                              test.evaluator.groupmember9, test.evaluator.groupmember10 )
    # Get the creator and other evaluator members in the 'Test' objects where the user is one of the evaluators.
    user_evaluator_creator_other_evaluators_dict = {}
    test = None
    for test in testlist_asevaluator:
        testcreator = test.creator
        testname = test.testname
        creator_evaluators = ( testcreator, test.evaluator.groupmember1, test.evaluator.groupmember2, test.evaluator.groupmember3, test.evaluator.groupmember4, \
                          test.evaluator.groupmember5, test.evaluator.groupmember6, test.evaluator.groupmember7, test.evaluator.groupmember8, \
                          test.evaluator.groupmember9, test.evaluator.groupmember10 ) # Basically we keep the creator as the first element. Rest are evaluators.
        user_evaluator_creator_other_evaluators_dict[testname] = creator_evaluators
    # *... and finally, those tests which the user has taken (i.e, user has been a candidate).
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
    dashboard_user_dict = {}
    dashboard_user_dict['displayname'] = "%s"%userobj.displayname
    dashboard_user_dict['profile_image_tag'] = skillutils.getprofileimgtag(userobj)
    dashboard_user_dict['user_creator_other_evaluators_dict'] = user_creator_other_evaluators_dict
    dashboard_user_dict['user_evaluator_creator_other_evaluators_dict'] = user_evaluator_creator_other_evaluators_dict
    dashboard_user_dict['user_candidate_other_creator_evaluator_dict'] = user_candidate_other_creator_evaluator_dict
    inc_context = skillutils.includedtemplatevars("Dashboard", request) # Since this is the 'Dashboard' page for the user.
    for inc_key in inc_context.keys():
        dashboard_user_dict[inc_key] = inc_context[inc_key]
    # Now create and render the template here
    tmpl = get_template("user/dashboard.html")
    dashboard_user_dict.update(csrf(request))
    cxt = Context(dashboard_user_dict)
    dashboardhtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        dashboardhtml = dashboardhtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(dashboardhtml)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def profile(request):
    message = ''
    if request.method != "GET": # Illegal bad request... 
        message = error_msg('1004')
        # A logging mechanism may be used to track how many and from where
        # such requests come and that may, sometimes, tell a curious story.
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.DASHBOARD_URL + "?msg=%s"%message)
        return response
    # If request method is 'GET', then retrieve Session and User info from the DB
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    # Find the following info: User's full name, user's  display name, sex, email Id, phone number (if any),
    # subscription plan chosen by the user, user since when (registration date), profile photo, whether user's
    # status is active or not, user's network information, and the date/time when the user was last seen. 
    profile_data_dict = {}
    profile_data_dict['fullname'] = "%s %s. %s"%(userobj.firstname, userobj.middlename, userobj.lastname)
    profile_data_dict['displayname'] = "%s"%userobj.displayname
    profile_data_dict['sex'] = "Undisclosed"
    if userobj.sex == 'M':
        profile_data_dict['sex'] = 'Male'
    elif profile_data_dict['sex'] == 'F':
        profile_data_dict['sex'] = 'Female'
    else:
        pass
    profile_data_dict['email'] = userobj.emailid
    profile_data_dict['mobilenumber'] = userobj.mobileno
    profile_data_dict['usersince'] = userobj.joindate
    profile_data_dict['status'] = "<a href='#' style='color:#0000FF;font-size:14;font-face:'cursive, Parkavenue';font-style:oblique;'>Active: Yes</a>"
    if not userobj.active: # This might be due to the user not yet confirming the account creation (by clicking on the link sent thru email)
        profile_data_dict['status'] = "<a href='#' style='color:#FF0000;font-size:14;font-face:'cursive, Parkavenue';font-style:oblique;'>Active: No</a>"
    profile_data_dict['newuser'] = ""
    if userobj.newuser:
        profile_data_dict['newuser'] = "<br /><a href='#' style='color:#FF0000;font-size:14;font-face:'cursive, Parkavenue';font-style:oblique;'>Have\
        you validated the email address you provided us?<br />If not, please find our message in your mailbox and click on the\
        link we have sent you through it. You need to do that in order to access our tests and other resources.</a>"
    profile_data_dict['lastseen'] = ""
    profile_data_dict['profile_image_tag'] = skillutils.getprofileimgtag(userobj)
    try:
        profile_data_dict['lastseen'] = Session.objects.filter(user=userobj).order_by('-endtime')[0]
    except:
        pass
    subscription_data = skillutils.getcurrentplans(userobj) # We just want the current plan, not all the subscription info.
    profile_data_dict['subscriptions'] = subscription_data
    # fix up the variables from included templates
    inc_context = skillutils.includedtemplatevars("Profile", request) # Since this is the 'Profile' page for the user.
    for inc_key in inc_context.keys():
        profile_data_dict[inc_key] = inc_context[inc_key]
    tmpl = get_template("user/profile.html")
    profile_data_dict.update(csrf(request))
    cxt = Context(profile_data_dict)
    profilehtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        profilehtml = profilehtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(profilehtml)
            


def logout(request):
    message = ''
    if request.method != "GET": # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.DASHBOARD_URL + "?msg=%s"%message)
        return response
    request = skillutils.checksession(request)
    sesscode = request.COOKIES['sessioncode']
    sessionobj = None
    try:
        sessionobj = Session.objects.filter(sessioncode=sesscode)
    except:
        response = HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=%s"%message)
        return response
    if type(request) == 'HttpRequest':
        request = skillutils.destroysession(request, sessionobj[0])
    message = error_msg('1031')
    response = HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=%s"%message)
    return response



def aboutus(request):
    aboutus_data_dict = {}
    # Need check to see if user is logged in.
    #aboutus_data_dict['displayname'] = "%s"%userobj.displayname
    #aboutus_data_dict['profile_image_tag'] = skillutils.getprofileimgtag(userobj)
    # fix up the variables from included templates
    inc_context = skillutils.includedtemplatevars("About Us", request) # Since this is the 'Profile' page for the user.
    for inc_key in inc_context.keys():
        aboutus_data_dict[inc_key] = inc_context[inc_key]
    tmpl = get_template("aboutus.html")
    aboutus_data_dict.update(csrf(request))
    cxt = Context(aboutus_data_dict)
    aboutushtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        aboutushtml = aboutushtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(aboutushtml)



def helpndocs(request):
    helpndocs_data_dict = {}
    # fix up the variables from included templates. Need check to see if user is logged in.
    #helpndocs_data_dict['displayname'] = "%s"%userobj.displayname
    #helpndocs_data_dict['profile_image_tag'] = skillutils.getprofileimgtag(userobj)
    inc_context = skillutils.includedtemplatevars("Help/Documentation", request) # Since this is the 'Profile' page for the user.
    for inc_key in inc_context.keys():
        helpndocs_data_dict[inc_key] = inc_context[inc_key]
    tmpl = get_template("help.html")
    helpndocs_data_dict.update(csrf(request))
    cxt = Context(helpndocs_data_dict)
    helphtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        helphtml = helphtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(helphtml)



def careers(request):
    careers_data_dict = {}
    # fix up the variables from included templates. Need check to see if user is logged in.
    #careers_data_dict['displayname'] = "%s"%userobj.displayname
    #careers_data_dict['profile_image_tag'] = skillutils.getprofileimgtag(userobj)
    inc_context = skillutils.includedtemplatevars("Careers/Jobs", request) # Since this is the 'Profile' page for the user.
    for inc_key in inc_context.keys():
        careers_data_dict[inc_key] = inc_context[inc_key]
    tmpl = get_template("careers.html")
    careers_data_dict.update(csrf(request))
    cxt = Context(careers_data_dict)
    careershtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        careershtml = careershtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(careershtml)


"""
View to handle profile image change
"""
@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def profileimagechange(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    if request.FILES.has_key('profpic'):
        fpath, message, profpic = skillutils.handleuploadedfile(request.FILES['profpic'], mysettings.MEDIA_ROOT + os.path.sep + userobj.displayname + os.path.sep + "images")
        userobj.userpic = profpic
        try:
            userobj.save()
            return HttpResponse("success")
        except:
            message = error_msg('1041')
            response = HttpResponse(message)
            return response
    return HttpResponse("failed")


