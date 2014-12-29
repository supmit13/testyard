from django.conf import settings
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.generic import View
from django.http import HttpResponseBadRequest, HttpResponse , HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.db.models import Q

# Standard libraries...
import os, sys, re, time, datetime
import cPickle
import decimal, math

# Application specific libraries...
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
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
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj.user
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
    testlist_ascandidate = UserTest.objects.filter(user=userobj).test
    user_candidate_other_creator_evaluator_dict = {}
    for test in testlist_ascandidate:
        testcreator = test.creator
        creator_evaluators = ( testcreator, test.evaluator.groupmember1, test.evaluator.groupmember2, test.evaluator.groupmember3, test.evaluator.groupmember4, \
                          test.evaluator.groupmember5, test.evaluator.groupmember6, test.evaluator.groupmember7, test.evaluator.groupmember8, \
                          test.evaluator.groupmember9, test.evaluator.groupmember10 )
        user_candidate_other_creator_evaluator_dict[test.testname] = creator_evaluators
    """
    Reason Behind Extracting Financial Data at this Point:
    ------------------------------------------------------
    So, now we have all the information pertaining to 'Test's for this User object.
    Next we need the subscription data. We won't show this on dashboard openly, but
    we will put a tab on the dashboard which will display this info when the user
    clicks on it. We don't want the user to spend any more time after this click e-
    vent, since extracting the test creator/evaluator/candidate data was time cons-
    uming. Once we build up this info, we can display sufficient details of the
    figures on the dashboard in real time. However, this subscription data will be
    behind a layer 3rd party authentication (LinkedIn OAuth2). 
    Note: We will call another function to get the subscription data in order to keep
    the financial and non-financial logic separate.
    """
    subscription_data = getsubscriptiondata(userobj)
    # Now create and render the template here
    return HttpResponse()


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
    userobj = sessionobj.user
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
    if not userobj.active:
        profile_data_dict['status'] = "<a href='#' style='color:#FF0000;font-size:14;font-face:'cursive, Parkavenue';font-style:oblique;'>Active: No</a>"
    profile_data_dict['lastseen'] = Session.objects.filter(user=userobj).order_by('-endtime')[0]
    userplans = UserPlan.objects.filter(user=userobj) # Getting all UserPlans for the User.
    current_plans_dict = {}
    past_plans_dict = {}
    for upln in userplans:
        planname = upln.plan.planname
        planstartdate = upln.planstartdate
        planenddate = upln.planenddate
        planstatus = upln.planstatus
        discount = upln.discountpercentapplied
    profile_data_dict['network'] = None
    return HttpResponse()


def getuserplandata(userobj):
    pass



