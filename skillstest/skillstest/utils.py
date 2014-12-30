import os, sys, re, time
import tempfile, shutil
from functools import wraps
import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.backends.db import SessionStore
from django.template import Template, Context

# Application specific libraries...
from skillstest.Auth.models import User, Session
from skillstest import settings as mysettings
from skillstest.errors import error_msg
from skillstest.Tests.models import Test, Challenge, Topic, Subtopic, Evaluator, UserTest, UserResponse
from skillstest.Subscription.models import Plan, UserPlan, Transaction

"""
Creates and returns a session object if the request is a
valid and authenticated session. Returns None otherwise.
"""
def isloggedin(request):
    sesscode = request.COOKIES['sessioncode']
    try:
        sessobj = Session.objects.get(sessioncode=sesscode)
    except:
        if mysettings.DEBUG:
            print "Invalid session code.\n"
        return False
    timestring = sesscode[-10:] # Last 10 digits is the timestamp value.
    current_ts = int(time.time())
    usertype = sessobj.user.usertype
    delta = current_ts - int(timestring)
    if delta > mysettings.SESSION_EXPIRY_LIMIT[usertype.upper()]: # Stale session
        if mysettings.DEBUG:
            print "Session has passed its maximum length of time.\n"
        request = destroysession(request)
        return False
    else: # Good session...
        return True
        

"""
Function to destroy a session object and return a request object.
"""
def destroysession(request):
    if request.has_key('COOKIES'):
        del request['COOKIES']
    return request


"""
Wrapper over isloggedin to redirect the user to login page if the
session is found to have expired or invalid for some reason.
Use this as it is a standard way to check the session and redirect
to the login page if session is invalid.
"""
def checksession(request):
    if not isloggedin(request):
        message = error_msg('1006')
        return HttpResponseRedirect(gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)
    else: # Return the request
        return request


"""
Decorator version of checksession to check the validity of  a session. Uses the same isloggedin function above internally.
"""
def is_session_valid(func):
    def sessioncheck(request):
        if not isloggedin(request):
            message = error_msg('1006')
            response = HttpResponseRedirect(gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)
        else: # Return the request
            response = func(request)
        return response
    return sessioncheck


"""
Decorator to match the session and location info stored in DB and the ones retrieved from the request
"""
def session_location_match(func):
    def checkconsistency(request):
        sesscode = request.COOKIES['sessioncode']
        usertype = request.COOKIES['usertype']
        clientIP_fromheader = request.META['REMOTE_ADDR']
        # Check to see if the values for this session stored in DB are identical to those we extracted from the headers just now.
        try:
            session_obj = Session.objects.get(sessioncode=sesscode)
        except:
            message = error_msg('1006')
            # Create response with redirect to login page and this message as GET arg. Return that response
            response = HttpResponseRedirect(gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)
        if session_obj.user.usertype != usertype or session_obj.sourceip != clientIP_fromheader:
            message = error_msg('1007')
            # Create response with redirect to login page and this message as GET arg. Return that response
            response = HttpResponseRedirect(gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)
        else:
            response = func(request)
        return response
    return checkconsistency



def gethosturl(request):
    url = 'http://'
    host = request.get_host()
    if not host:
        if request.META.has_key('HTTP_SERVER_NAME'):
            url = url + request.META['HTTP_SERVER_NAME']
        else:
            url = url + "localhost"
        if request.META.has_key('HTTP_SERVER_PORT') and request.META['HTTP_SERVER_PORT'] != '80':
            url = url + ":" + request.META['HTTP_SERVER_PORT'].__str__()
    else:
        url = url + host
    return url


"""
Method to send an email to the email id of the user passed in as the argument.
Should be done asynchronously - put the email in a queue from where the email
handler will pick in batches of (say) 10 emails at a time and send them before
running to pick up the next batch.
"""
def sendemail(userobj):
    pass


"""
Handle uploaded file. Create the destination path if required.
Returns a list containing the path to the uploaded file and a message
(which would be '' in case of success).
"""
def handleuploadedfile(uploaded_file, targetdir):
    fd, filepath = tempfile.mkstemp(prefix=uploaded_file.name, dir=targetdir)
    if uploaded_file.size() > mysettings.MAX_FILE_SIZE_ALLOWED:
        message = error_msg['1005']
        return [ None, message ]
    with open(filepath, 'wb') as destination:
        destinationfile = destination + os.path.sep + mysettings.PROFILE_PHOTO_NAME
        shutil.copyfileobj(uploaded_file, destinationfile)
    return [ filepath, '' ]


"""
Format message (with color and font) and return it as a displayable string
(after removing all hexcoded characters and HTML entities, if present).
"""
def formatmessage(msg, msg_color):
    var, msg = msg.split("=")
    for hexkey in mysettings.HEXCODE_CHAR_MAP.keys():
        msg = msg.replace(hexkey, mysettings.HEXCODE_CHAR_MAP[hexkey])
    msg = "<p style=\"color:#%s;font-size:14;font-face:'helvetica neue';font-style:bold;\">%s</p>"%(msg_color, msg)
    return msg
            
    

"""
Function to check the strength of the password. Returns
an integer between 1 and 5 with 5 being the strongest and
1 being the weakest. 0 denotes the absence of any character 
(empty string '').
"""
def check_password_strength(passwd):
    if passwd.__len__() == 0:
        return 0
    strength = 0
    if passwd.__len__() > 6:
        strength += 1
    contains_digits, contains_special_char, contains_lowercase, contains_uppercase = 0, 0, 0, 0
    special_characters = "~`!#$%^&*+=-[]\\\';,/{}|\":<>?"
    for i in passwd.__len__() - 1:
        if passwd[i] >= '0' and passwd[i] <= '9':
            strength += 1
            continue
        if passwd[i] == passwd[i].upper():
            strength += 1
            continue
        if passwd[i] == passwd[i].lower():
            strength += 1
            continue
        if passwd[i] in special_characters:
            strength += 1
            continue
    return strength


"""
Method to copy a given Test object and create a new (duplicate) Test
object which is owned by the User who requested the copy. Returns the copied Test
object, None on failure. The primary owner/creator of the test has to
transfer the rights to the new copied  test to the new user in order for
the new user to access it. However, the 'evaluator' field will not
be copied in the duplicate test.
"""
def copy_test(testobj, creatorid, userobj):
    newtest = Test()
    # Check if creatorobj is the creator of testobj or not. If not, return None.
    if testobj.creator.id != creatorid:
        return None
    newtest.testname = testobj.testname
    newtest.subtopic = testobj.subtopic
    newtest.creator = userobj
    newtest.creatorisevaluator = testobj.creatorisevaluator
    newtest.evaluator = None
    newtest.testtype = testobj.testtype
    newtest.createdate = datetime.datetime.now()
    newtest.maxscore = testobj.maxscore
    newtest.passscore = testobj.passscore
    newtest.ruleset = testobj.ruleset
    newtest.duration = testobj.duration
    newtest.allowedlanguages = testobj.allowedlanguages
    newtest.challengecount = testobj.challengecount
    newtest.activationdate = datetime.datetime.now()
    newtest.status = testobj.status
    newtest.quality = testobj.quality
    return newtest


"""
pagetitle is expected to be the title string of the page with first letter in uppercase.
"""
def includedtemplatevars(pagetitle):
    curdate = datetime.datetime.now()
    select_profile = ""
    select_dashboard = ""
    select_subscription = ""
    select_tests = ""
    select_search = ""
    select_pronet = ""
    select_analytics = ""
    select_aboutus = ""
    select_helpndoc = ""
    select_careers = ""
    if pagetitle == 'Profile':
        select_profile = " class=\"highlight\""
    elif pagetitle == 'Dashboard':
        select_dashboard = " class=\"highlight\""
    elif pagetitle == 'Subscription':
        select_subscription = " class=\"highlight\""
    elif pagetitle == 'Tests':
        select_tests = " class=\"highlight\""
    elif pagetitle == 'Search':
        select_search = " class=\"highlight\""
    elif pagetitle == 'Networking':
        select_pronet = " class=\"highlight\""
    elif pagetitle == 'Test Analytics':
        select_analytics = " class=\"highlight\""
    elif pagetitle == 'About Us':
        select_aboutus = " class=\"highlight\""
    elif pagetitle == 'Help/Documentation':
        select_helpndoc = " class=\"highlight\""
    elif pagetitle == 'Careers/Jobs':
        select_careers = " class=\"highlight\""
    else: # Invalid tab, control should not have come here. Skip quietly.
        pass
    cntxt = { 'pagetitle' : pagetitle, 'select_profile' : select_profile, 'select_dashboard' : select_dashboard, 'select_subscription' : select_subscription, \
              'select_tests' : select_tests, 'select_search' : select_search, 'select_pronet' : select_pronet, 'select_analytics' : select_analytics, \
              'select_aboutus' : select_aboutus, 'select_helpndoc' : select_helpndoc, 'select_careers' : select_careers, }
    return cntxt



"""
Function to get the current plans a given user has subscribed to.
"""
def getcurrentplans(userobj):
    currentplans = {}
    userplans = UserPlan.objects.filter(user=userobj).order_by('-subscribedon') # Getting all UserPlans for the User.
    for usrpln in userplans: # userplans is a queryset object...
        planstart = usrpln.planstartdate
        startdate, starttime = planstart.split(" ")
        startyyyy, startmon, startdd = startdate.split("-")
        starthh, startmm, startss = starttime.split(":")
        planend = usrpln.planenddate
        enddate, endtime = planend.split(" ")
        endyyyy, endmon, enddd = enddate.split("-")
        endhh, endmm, endss = endtime.split(":")
        planstatus = usrpln.planstatus
        subscribed = usrpln.subscribedon
        planname = usrpln.plan.planname
        # For this plan to be the current plan, the current datetime value should be between planstart and planend.
        curdatetime = datetime.datetime.now()
        if curdatetime > datetime.datetime(int(startyyyy), int(startmon), int(startdd), int(starthh), int(startmm), int(startss)) and curdatetime < datetime.datetime(int(endyyyy), int(endmon), int(enddd), int(endhh), int(endmm), int(endss)) and planstatus:
            tests = usrpln.plan.tests
            price = usrpln.plan.price
            currentplans[planname] = ( planstart, planend, price, usrpln.totalcost, usrpln.amountpaid, usrpln.amountdue, usrpln.discountpercentapplied )
            """
            Plan data (7 element tuple) listed as follows:
            index 0: start date and time of the user's subscription of the plan.
            index 1: end date and time of the user's subscription of the plan.
            index 2: officially listed price of the plan (different from the price at which user subscribed since waivers, discounts, freebies etc, may be given)
            index 3: total cost that the user has to pay for the package. This includes all waivers, discounts, etc.
            index 4: amount already paid by the user (may be through EMIs or part payment).
            index 5: amount that the user still needs to pay
            index 6: discount applied on the plan.
            """
    return currentplans



