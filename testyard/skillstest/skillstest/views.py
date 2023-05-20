from django.conf import settings
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.core.context_processors import csrf
from django.views.decorators.cache import never_cache
from django.views.generic import View
from django.http import HttpResponseBadRequest, HttpResponse , HttpResponseRedirect, HttpResponsePermanentRedirect, HttpRequest
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
import simplejson
from django.db.models import Q
from django.template.response import TemplateResponse
from django.utils.http import base36_to_int, is_safe_url
from django.template import Template, Context
from django.template.loader import get_template
from django.contrib.sites.models import get_current_site
from django.contrib.sessions.backends.db import SessionStore
from passlib.hash import pbkdf2_sha256 # To create hash of passwords
import logging

# Standard libraries...
import os, sys, re, time, datetime
import cPickle
import decimal, math

# Application specific libraries...
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege, OptionalUserInfo
from skillstest.Subscription.models import Plan, UserPlan, Transaction
from skillstest.Tests.models import Topic, Subtopic, Evaluator, Test, UserTest, Challenge, UserResponse
from skillstest.models import Careers
from skillstest import settings as mysettings
from skillstest.errors import error_msg
import skillstest.utils as skillutils


def returnRedirect(request):
    requestline = request.build_absolute_uri()
    logger = logging.getLogger(__name__)
    logger.debug("REQUEST LINE: %s"%requestline)
    httpPattern = re.compile(r"^http:")
    if httpPattern.search(requestline):
        redirectUrl = "%s/%s"%("", mysettings.LOGIN_URL)
        redirectUrlParts = redirectUrl.split("//")
        urlPathPart = redirectUrlParts[redirectUrlParts.__len__() - 1]
        urlPathPart = mysettings.URL_PROTOCOL + skillutils.gethosturl(request) + urlPathPart
        urlPathPart = urlPathPart.replace("https://", "", 1)
        return HttpResponseRedirect(urlPathPart)
    #redirectUrl = "%s/%s"%("", mysettings.MANAGE_TEST_URL)
    redirectUrl = "%s/%s"%("", mysettings.INDEX_URL)
    if not skillutils.isloggedin(request):
        loginredirect = True
        for pathpattern in mysettings.UNAUTHENTICATED_ACCESS_PATH_PATTERNS:
            if re.search(pathpattern, request.path):
                loginredirect = False
                break
        if loginredirect is True:
            redirectUrl = "%s/%s"%("", mysettings.LOGIN_URL)
    redirectUrlParts = redirectUrl.split("//")
    urlPathPart = redirectUrlParts[redirectUrlParts.__len__() - 1]
    urlPathPart = mysettings.URL_PROTOCOL + skillutils.gethosturl(request) + urlPathPart
    urlPathPart = urlPathPart.replace("https://", "", 1)
    return HttpResponseRedirect(urlPathPart)


def handler404(request):	
    return HttpResponseRedirect("%s/%s"%("", mysettings.LOGIN_URL))


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
    usertestqset = []
    try:
        usertestqset = UserTest.objects.filter(user=userobj)
    except: # Can't say if we will find any records...
        usertestqset = []
    testlist_ascandidate = []
    for usertest in usertestqset:
        testlist_ascandidate.append(usertest.test)
    user_candidate_other_creator_evaluator_dict = {}
    for test in testlist_ascandidate:
        testcreator = test.creator
        creator_evaluators = ( testcreator, test.evaluator.groupmember1, test.evaluator.groupmember2, test.evaluator.groupmember3, test.evaluator.groupmember4, \
                          test.evaluator.groupmember5, test.evaluator.groupmember6, test.evaluator.groupmember7, test.evaluator.groupmember8, \
                          test.evaluator.groupmember9, test.evaluator.groupmember10 )
        user_candidate_other_creator_evaluator_dict[test.testname] = creator_evaluators
    dashboard_user_dict = {}
    dashboard_user_dict['displayname'] = "%s"%userobj.displayname
    dashboard_user_dict['profile_image_tag'] = skillutils.getprofileimgtag(request)
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
def getcountrieslist(request):
    message = ''
    if request.method != "GET": # Illegal bad request... 
        message = error_msg('1004')
        # A logging mechanism may be used to track how many and from where
        # such requests come and that may, sometimes, tell a curious story.
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.PROFILE_URL + "?msg=%s"%message)
        return response
    countrieslist = ["Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Austrian Empire", "Azerbaijan", "Baden", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Bavaria", "Belarus", "Belgium", "Belize", "Benin", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Brunswick and Luneburg", "Bulgaria", "Burkina Faso", "Burma", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Cayman Islands", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo", "Costa Rica", "Cote d'Ivoire (Ivory Coast)", "Croatia", "Cuba", "Cyprus", "Czech Republic", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominican Republic", "Duchy of Parma", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "The Gambia", "Georgia", "Germany", "Ghana", "The Grand Duchy of Tuscany", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Hanover", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "North Korea", "South Korea", "Kosovo", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Lew Chew", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mecklenburg-Schwerin", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nassau", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Macedonia", "Norway", "Oldenburg", "Oman", "Orange Free State", "Pakistan", "Palau", "Panama", "Papal States", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Piedmont-Sardinia", "Poland", "Portugal", "Qatar", "Republic of Genoa", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Schaumburg-Lippe", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "The Solomon Islands", "Somalia", "South Africa", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Two Sicilies", "Uganda", "Ukraine", "The United Arab Emirates", "The United Kingdom", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Wurttemberg", "Yemen", "Zambia", "Zimbabwe" ]
    return HttpResponse(simplejson.dumps(countrieslist))



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
    profile_data_dict['profile_image_tag'] = skillutils.getprofileimgtag(request)
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
    userinfoqset = OptionalUserInfo.objects.filter(user=userobj)
    if userinfoqset.__len__() == 0:
        profile_data_dict['houseno_and_street_address'] = ""
        profile_data_dict['city'] = ""
        profile_data_dict['pin_or_zip_code'] = ""
        profile_data_dict['country'] = ""
        profile_data_dict['profession'] = ""
        profile_data_dict['age'] = ""
        profile_data_dict['reasonforuse'] = ""
        profile_data_dict['selfdescription'] = ""
        profile_data_dict['highestqualification'] = ""
        profile_data_dict['fieldofstudy'] = ""
        profile_data_dict['presentemployer_or_institution'] = ""
    else:
        profile_data_dict['houseno_and_street_address'] = userinfoqset[0].houseno_and_street_address
        profile_data_dict['city'] = userinfoqset[0].city
        profile_data_dict['pin_or_zip_code'] = userinfoqset[0].pin_or_zip_code
        profile_data_dict['country'] = userinfoqset[0].country
        profile_data_dict['profession'] = userinfoqset[0].profession
        profile_data_dict['age'] = userinfoqset[0].age
        profile_data_dict['reasonforuse'] = userinfoqset[0].reasonforuse
        profile_data_dict['selfdescription'] = userinfoqset[0].selfdescription
        profile_data_dict['highestqualification'] = userinfoqset[0].highestqualification
        profile_data_dict['fieldofstudy'] = userinfoqset[0].fieldofstudy
        profile_data_dict['presentemployer_or_institution'] = userinfoqset[0].presentemployer_or_institution
    profile_data_dict['user_id'] = userobj.id
    profile_data_dict['saveoptionalinfourl'] = mysettings.SAVE_OPTIONAL_INFO_URL
    tmpl = get_template("user/profile.html")
    profile_data_dict.update(csrf(request))
    profile_data_dict['getautocompletecountriesurl'] = mysettings.AUTOCOMPLETE_COUNTRIES_URL
    cxt = Context(profile_data_dict)
    profilehtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        profilehtml = profilehtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(profilehtml)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def saveoptionalinfo(request):
    message = ''
    if request.method != "POST": # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.DASHBOARD_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    countrieslist = ["Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Austrian Empire", "Azerbaijan", "Baden", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Bavaria", "Belarus", "Belgium", "Belize", "Benin", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Brunswick and Luneburg", "Bulgaria", "Burkina Faso", "Burma", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Cayman Islands", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo", "Costa Rica", "Cote d'Ivoire (Ivory Coast)", "Croatia", "Cuba", "Cyprus", "Czech Republic", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominican Republic", "Duchy of Parma", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "The Gambia", "Georgia", "Germany", "Ghana", "The Grand Duchy of Tuscany", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Hanover", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "North Korea", "South Korea", "Kosovo", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Lew Chew", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mecklenburg-Schwerin", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nassau", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Macedonia", "Norway", "Oldenburg", "Oman", "Orange Free State", "Pakistan", "Palau", "Panama", "Papal States", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Piedmont-Sardinia", "Poland", "Portugal", "Qatar", "Republic of Genoa", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Schaumburg-Lippe", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "The Solomon Islands", "Somalia", "South Africa", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Two Sicilies", "Uganda", "Ukraine", "The United Arab Emirates", "The United Kingdom", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Wurttemberg", "Yemen", "Zambia", "Zimbabwe" ]
    houseno_and_street_address, city, pin_or_zip_code, country, profession, age, reasonforuse, selfdescription, highestqualification, fieldofstudy, presentemployer_or_institution = "", "", "", "", "", 0, "", "", "", "", "" 
    if request.POST.has_key('houseno_and_street_address'):
        houseno_and_street_address = request.POST['houseno_and_street_address']
        if houseno_and_street_address.__len__() > 500:
            message = "Error: Too many characters in 'House No. and Street Address' field. Please limit it to 500 characters only. Could not save information."
            return HttpResponse(message)
    if request.POST.has_key('city'):
        city = request.POST['city']
    if request.POST.has_key('pin_or_zip_code'):
        pin_or_zip_code = request.POST['pin_or_zip_code']
    if request.POST.has_key('country'):
        country = request.POST['country']
        if country.title() not in countrieslist:
            response = HttpResponse("Error: Invalid country name. Could not save information.")
            return response
    if request.POST.has_key('profession'):
        profession = request.POST['profession']
    if request.POST.has_key('age'):
        age = request.POST['age']
        try:
            age = int(age)
            if age < 0 or age > 100:
                message = "Error: Invalid age. Could not save information"
                response = HttpResponse(message)
                return response
        except:
            message = "Error: Invalid non-integer age. Could not save information"
            response = HttpResponse(message)
            return response
    if request.POST.has_key('reasonforuse'):
        reasonforuse = request.POST['reasonforuse']
        if reasonforuse.__len__() > 500:
            message = "Error: Too many characters in 'Reason for Use' field. Please limit it to 500 characters only. Could not save information."
            return HttpResponse(message)
    if request.POST.has_key('selfdescription'):
        selfdescription = request.POST['selfdescription']
        if selfdescription.__len__() > 500:
            message = "Error: Too many characters in 'Self Description' field. Please limit it to 500 characters only. Could not save information."
            return HttpResponse(message)
    if request.POST.has_key('highestqualification'):
        highestqualification = request.POST['highestqualification']
    if request.POST.has_key('fieldofstudy'):
        fieldofstudy = request.POST['fieldofstudy']
    if request.POST.has_key('presentemployer_or_institution'):
        presentemployer_or_institution = request.POST['presentemployer_or_institution']
    optionaluserinfoqset = OptionalUserInfo.objects.filter(user=userobj)
    userinfo = None
    if optionaluserinfoqset.__len__() == 0: # New data
        userinfo = OptionalUserInfo()
    else:
        userinfo = optionaluserinfoqset[0]
    if not userinfo:
        message = error_msg('1161')
        return HttpResponse(message)
    userinfo.user = userobj
    userinfo.houseno_and_street_address = houseno_and_street_address
    userinfo.city = city
    userinfo.pin_or_zip_code = pin_or_zip_code
    userinfo.country = country
    userinfo.profession = profession
    userinfo.age = age
    userinfo.reasonforuse = reasonforuse
    userinfo.selfdescription = selfdescription
    userinfo.highestqualification = highestqualification
    userinfo.fieldofstudy = fieldofstudy
    userinfo.presentemployer_or_institution = presentemployer_or_institution
    userinfo.save()
    message = "Successfully saved user information."
    return HttpResponse(message)


def logout(request):
    message = ''
    if request.method != "GET": # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.MANAGE_TEST_URL + "?msg=%s"%message)
        return response
    request = skillutils.checksession(request)
    if type(request) == HttpResponseRedirect:
        return request
    sesscode = request.COOKIES['sessioncode']
    sessionobj = None
    try:
        sessionobj = Session.objects.filter(sessioncode=sesscode)
    except:
        response = HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=%s"%message)
        return response
    for i in range(0, sessionobj.__len__()):
        request = skillutils.destroysession(request, sessionobj[i])
    message += error_msg('1031')
    response = HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=%s"%message)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def aboutus(request):
    if request.method != "GET":
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.ABOUTUS_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    displayname = userobj.displayname
    aboutus_data_dict = {}
    # Need check to see if user is logged in.
    # aboutus_data_dict['displayname'] = "%s"%userobj.displayname
    # aboutus_data_dict['profile_image_tag'] = skillutils.getprofileimgtag(request)
    # fix up the variables from included templates
    inc_context = skillutils.includedtemplatevars("About Us", request) # Since this is the 'Profile' page for the user.
    for inc_key in inc_context.keys():
        aboutus_data_dict[inc_key] = inc_context[inc_key]
    aboutus_data_dict['displayname'] = displayname
    aboutus_data_dict['freetestscount'] = mysettings.NEW_USER_FREE_TESTS_COUNT
    aboutus_data_dict['profile_image_tag'] = skillutils.getprofileimgtag(request)
    tmpl = get_template("aboutus.html")
    aboutus_data_dict.update(csrf(request))
    cxt = Context(aboutus_data_dict)
    aboutushtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        aboutushtml = aboutushtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(aboutushtml)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def helpndocs(request):
    if request.method != "GET":
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.ABOUTUS_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    displayname = userobj.displayname
    helpndocs_data_dict = {}
    # fix up the variables from included templates. Need check to see if user is logged in.
    #helpndocs_data_dict['displayname'] = "%s"%userobj.displayname
    #helpndocs_data_dict['profile_image_tag'] = skillutils.getprofileimgtag(request)
    inc_context = skillutils.includedtemplatevars("Help/Documentation", request) # Since this is the 'Profile' page for the user.
    for inc_key in inc_context.keys():
        helpndocs_data_dict[inc_key] = inc_context[inc_key]
    helpndocs_data_dict['displayname'] = displayname
    helpndocs_data_dict['detailhelpurl'] = mysettings.DETAIL_HELP_URL
    helpndocs_data_dict['profile_image_tag'] = skillutils.getprofileimgtag(request)
    tmpl = get_template("help.html")
    helpndocs_data_dict.update(csrf(request))
    cxt = Context(helpndocs_data_dict)
    helphtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        helphtml = helphtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(helphtml)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def detailedhelp(request):
    if request.method != "POST":
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.ABOUTUS_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    displayname = userobj.displayname
    helppage = ""
    if request.POST.has_key('help'):
        helppage = request.POST['help']
    tmpl = get_template("helpndocs/profilehelp.html") # Default help screen
    pagetitle = "Help - Profile"
    if helppage == 'dashboard':
        tmpl = get_template("helpndocs/dashboardhelp.html")
        pagetitle = "Help - Dashboard"
    elif helppage == 'subscription':
        tmpl = get_template("helpndocs/subscriptionhelp.html")
        pagetitle = "Help - Subscription"
    elif helppage == 'test':
        tmpl = get_template("helpndocs/testhelp.html")
        pagetitle = "Help - Tests"
    elif helppage == 'network':
        tmpl = get_template("helpndocs/networkhelp.html")
        pagetitle = "Help - Network"
    elif helppage == 'search':
        tmpl = get_template("helpndocs/searchhelp.html")
        pagetitle = "Help - Search"
    elif helppage == 'analytics':
        tmpl = get_template("helpndocs/analyticshelp.html")
        pagetitle = "Help - Analytics"
    help_dict = { 'displayname' : displayname, 'pagetitle' : pagetitle }
    help_dict.update(csrf(request))
    cxt = Context(help_dict)
    helphtml = tmpl.render(cxt)
    response = HttpResponse(helphtml)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def careers(request):
    if request.method != "GET":
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.ABOUTUS_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    careers_data_dict = {}
    # fix up the variables from included templates. Need check to see if user is logged in.
    #careers_data_dict['displayname'] = "%s"%userobj.displayname
    #careers_data_dict['profile_image_tag'] = skillutils.getprofileimgtag(request)
    inc_context = skillutils.includedtemplatevars("Careers/Jobs", request) # Since this is the 'Profile' page for the user.
    for inc_key in inc_context.keys():
        careers_data_dict[inc_key] = inc_context[inc_key]
    careers_data_dict['displayname'] = userobj.displayname
    careers_data_dict['profile_image_tag'] = skillutils.getprofileimgtag(request)
    careersqset = Careers.objects.filter(status=True)
    positionslist = []
    for careerobj in careersqset:
        position = {}
        position['shortname'] = careerobj.position_shortname
        position['longname'] = careerobj.position_longname
        position['code'] = careerobj.position_code
        position['description'] = careerobj.position_description
        position['closingdate'] = careerobj.closingdate
        position['maxsalaryoffered'] = careerobj.maxsalaryoffered
        position['maxsalarytimeunit'] = careerobj.maxsalarytimeunit
        position['urgencyindays'] = careerobj.urgencyindays
        position['position_type'] = careerobj.position_type
        position['experiencedesired'] = careerobj.experiencedesired
        position['skillset'] = careerobj.skillset
        position['position_location'] = careerobj.position_location
        position['department'] = careerobj.department
        position['contactperson'] = careerobj.contactperson
        position['contactemail'] = careerobj.contactemail
        position['conditions'] = careerobj.conditions
        positionslist.append(position)
    careers_data_dict['positionslist'] = positionslist
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
    errorpattern = re.compile("^error\:", re.IGNORECASE)
    if request.FILES.has_key('profpic') and request.FILES['profpic'] is not None:
        fext = request.FILES['profpic'].name.split(".")[-1]
        if fext not in mysettings.ALLOWED_IMAGE_EXTENSIONS:
            message = "Error: File should be one of the following types: %s"%", ".join(mysettings.ALLOWED_IMAGE_EXTENSIONS)
            return HttpResponse(message)
        fpath, message, profpic = skillutils.handleuploadedfile(request.FILES['profpic'], mysettings.MEDIA_ROOT + os.path.sep + userobj.displayname + os.path.sep + "images")
        if re.search(errorpattern, message):
            message = errorpattern.sub("", message)
            return HttpResponse(message)
        userobj.userpic = profpic
        try:
            userobj.save()
            message = "success"
        except:
            message = error_msg('1041')
    else:
        message = "failed"
    return HttpResponse(message)


"""
This view showcases the features of TestYard and points out the 
conveniences of using it. This is to be displayed without the
need to have a valid authenticated session. The page should include
links to the Login and Register pages as well as a link to Plans
page.
"""
def index(request):
    if request.method != 'GET':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode, usertype = "", ""
    if request.COOKIES.has_key('sessioncode'):
        sesscode = request.COOKIES['sessioncode']
    if request.COOKIES.has_key('usertype'):
        usertype = request.COOKIES['usertype']
    sessionobj, userobj = None, None
    if sesscode != "":
        sessionobj = Session.objects.filter(sessioncode=sesscode)
        userobj = sessionobj[0].user
    # Initialize context...
    index_user_dict = {}
    inc_context = skillutils.includedtemplatevars("", request)
    for inc_key in inc_context.keys():
        index_user_dict[inc_key] = inc_context[inc_key]
    curdate = datetime.datetime.now()
    index_user_dict['curdate'] = curdate
    index_user_dict['login_url'] = mysettings.LOGIN_URL
    index_user_dict['register_url'] = mysettings.REGISTER_URL
    index_user_dict['logged_in_as'] = ""
    if userobj is not None:
        index_user_dict['logged_in_as'] = userobj.displayname
    tmpl = get_template("user/index.html")
    index_user_dict.update(csrf(request))
    cxt = Context(index_user_dict)
    indexhtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        indexhtml = indexhtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(indexhtml)
    
