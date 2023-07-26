import os, sys, re, time
import tempfile, shutil
from functools import wraps
import datetime
import pytz
import uuid, glob
import urllib, urllib2, requests
import string, random
import StringIO, gzip
import mimetypes, mimetools
from Crypto.Cipher import DES3
import hashlib,hmac
import base64
import socket
import simplejson as json
import razorpay
import MySQLdb
from lxml import etree
from zipfile import ZipFile

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Template, Context
from django.core.mail import send_mail

# Application specific libraries...
from skillstest.Auth.models import User, Session
from skillstest import settings as mysettings
from skillstest.errors import error_msg
from skillstest.Tests.models import Test, Challenge, Topic, Subtopic, Evaluator, UserTest, UserResponse, PostLinkedin
from skillstest.Subscription.models import Plan, UserPlan, Transaction, Coupon, UserCoupon
from skillstest.Network.models import ExchangeRates, OwnerBankAccount

multiplecommapattern = re.compile("\,+")
endcommapattern = re.compile("\,$")
multiplewhitespacepattern = re.compile("\s+", re.DOTALL)
numericpattern = re.compile("\d+")

hextoascii = { '%3C' : '<', '%3E' : '>', '%20' : ' ', '%22' : '"', '%5B' : '[', '%5D' : ']', '%5C' : '\\', '%3A' : ':', '%3B' : ';', '%28' : '(', '%29' : ')', '%2D' : '-', '%2B' : '+'}

gHttpHeaders = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language' : 'en-US,en;q=0.8', 'Accept-Encoding' : 'gzip,deflate,sdch', 'Connection' : 'keep-alive', 'Host' : 'codepad.org' }
requestUrl = ""


# Class to implement NoRedirectHandler
class NoRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        infourl = urllib.addinfourl(fp, headers, req.get_full_url())
        infourl.status = code
        infourl.code = code
        return infourl
    http_error_300 = http_error_302
    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302



def isloggedin(request):
    """
    Creates and returns a session object if the request is a
    valid and authenticated session. Returns None otherwise.
    """
    if not request.COOKIES.has_key('sessioncode'):
        if mysettings.DEBUG:
            print "Invalid session code.\n"
        return False
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
        request = destroysession(request, sessobj)
        return False
    else: # Good session...
        if sessobj.status == 1:
            return True
        return False


def getPageContent(pageResponse):
    if pageResponse:
        content = pageResponse.read()
        currentPageContent = content
        # Remove the line with 'DOCTYPE html PUBLIC' string. It sometimes causes BeautifulSoup to fail in parsing the html
        currentPageContent = re.sub(r"<.*DOCTYPE\s+html\s+PUBLIC[^>]+>", "", content)
        return currentPageContent
    else:
        return None


def _getCookieFromResponse(lastResponse):
    """
    Function to extract cookies from HttpResponse object passed in as the only parameter.
    """
    cookies = ""
    lastResponseHeaders = lastResponse.info()
    responseCookies = lastResponseHeaders.getheaders("Set-Cookie")
    pathCommaPattern = re.compile(r"path=/\s*;?", re.IGNORECASE)
    domainPattern = re.compile(r"Domain=[^;]+;?", re.IGNORECASE)
    expiresPattern = re.compile(r"Expires=[^;]+;?", re.IGNORECASE)
    deletedPattern = re.compile(r"=deleted;", re.IGNORECASE)
    if responseCookies.__len__() >= 1:
        for cookie in responseCookies:
            cookieParts = cookie.split("Path=/")
            cookieParts[0] = re.sub(domainPattern, "", cookieParts[0])
            cookieParts[0] = re.sub(expiresPattern, "", cookieParts[0])
            deletedSearch = deletedPattern.search(cookieParts[0])
            if deletedSearch:
                continue
            cookies += "; " + cookieParts[0]
        multipleWhiteSpacesPattern = re.compile(r"\s+")
        cookies = re.sub(multipleWhiteSpacesPattern, " ", cookies)
        multipleSemicolonsPattern = re.compile(";\s*;")
        cookies = re.sub(multipleSemicolonsPattern, "; ", cookies)
        if re.compile("^\s*;").search(cookies):
            cookies = re.sub(re.compile("^\s*;"), "", cookies)
        return(cookies)
    else:
        return(None)


def getCodePadEditorPage():
    opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), NoRedirectHandler())
    homeDir = os.getcwd()
    requestUrl = "http://codepad.org/"
    pageRequest = urllib2.Request(requestUrl, None, gHttpHeaders)
    pageResponse = None
    try:
        pageResponse = opener.open(pageRequest)
        sessionCookies = _getCookieFromResponse(pageResponse)
        gHttpHeaders["Cookie"] = sessionCookies
    except:
        print __file__.__str__() + ": Couldn't fetch page due to limited connectivity. Please check your internet connection and try again - %s\n"%(sys.exc_info()[1].__str__())
        return(None)
    gHttpHeaders['Referer'] = requestUrl
    gHttpHeaders["Cache-Control"] = 'max-age=0'
    gHttpHeaders["Origin"] = 'http://codepad.org/'
    gHttpHeaders["Content-Type"] = 'application/x-www-form-urlencoded'
    #print "REQUEST URL = " + requestUrl
    currentPageContent = _decodeGzippedContent(getPageContent(pageResponse))
    return currentPageContent


def runCodeOnLocalResources(targetenv, enccode, client_ip, client_port):
    datadict = {'enc_code' : enccode, 'code_env' : targetenv, 'client_ip' : client_ip, 'client_port' : client_port }
    servicehost = mysettings.CODE_EXECUTE_SERVICE_HOST
    serviceport = mysettings.CODE_EXECUTE_SERVICE_PORT
    # Create a socket connection to the above mentioned host and port
    sockfd = None
    try:
        sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except:
        msg = "Failed to create a socket: %s"%sys.exc_info()[1].__str__()
        print msg
        return msg
    sockaddress = (servicehost, serviceport)
    try:
        sockfd.connect(sockaddress)
        #sockfd.create_connection(sockaddress, mysettings.SOCK_CONN_CREATE_TIMEOUT)
    except:
        msg = "Failed to create connection to the code execution service: %s"%sys.exc_info()[1].__str__()
        print msg
        return msg
    jsondata = json.dumps(datadict)
    try:
        sockfd.send(jsondata)
        #sockfd.sendall(jsondata)
    except:
        msg = "Trying to send data over the socket failed. Reason: %s"%sys.exc_info()[1].__str__()
        print msg
        return msg
    sockfd.close()
    msg = "sent data to execute... <img src='static/images/loading_small.gif'>"
    print jsondata + "\n"
    print msg
    return msg


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_client_port(request):
    client_port = request.META.get('REMOTE_PORT')
    return client_port


def destroysession(request, sessobj):
    """
    Function to destroy a session object and return a request object.
    """
    try:
        del request.COOKIES['sessioncode']
    except:
        pass
    sessobj.status = False
    sessobj.save()
    return request


def checksession(request):
    """
    Wrapper over isloggedin to redirect the user to login page if the
    session is found to have expired or invalid for some reason.
    Use this as it is a standard way to check the session and redirect
    to the login page if session is invalid.
    """
    if not isloggedin(request):
        loginredirect = True
        for pathpattern in mysettings.UNAUTHENTICATED_ACCESS_PATH_PATTERNS:
            if re.search(pathpattern, request.path) is not None:
                loginredirect = False
                break
        if loginredirect is True:
            message = error_msg('1006')
            return HttpResponseRedirect(gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)
        else:
            return request
    else: # Return the request
        return request


def is_session_valid(func):
    """
    Decorator version of checksession to check the validity of  a session. Uses the same isloggedin function above internally.
    """
    def sessioncheck(request):
        if not isloggedin(request):
            loginredirect = True
            for pathpattern in mysettings.UNAUTHENTICATED_ACCESS_PATH_PATTERNS:
                if re.search(pathpattern, str(request.path)) is not None:
                    loginredirect = False
                    break
            if loginredirect is True:
                message = error_msg('1006')
                response = HttpResponseRedirect(gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)
            else:
                return func(request)
        else: # Return the request
            response = func(request)
        return response
    return sessioncheck


def session_location_match(func):
    """
    Decorator to match the session and location info stored in DB and the ones retrieved from the request
    """
    def checkconsistency(request):
        sesscode, usertype, clientIP_fromheader = None, "", ""
        try:
            sesscode = request.COOKIES['sessioncode']
            usertype = request.COOKIES['usertype']
            clientIP_fromheader = request.META['REMOTE_ADDR']
        except:
            pass
        # Check to see if the values for this session stored in DB are identical to those we extracted from the headers just now.
        try:
            session_obj = Session.objects.get(sessioncode=sesscode)
        except:
            loginredirect = True
            for pathpattern in mysettings.UNAUTHENTICATED_ACCESS_PATH_PATTERNS:
                if re.search(pathpattern, request.path) is not None:
                    loginredirect = False
                    break
            if loginredirect is True:
                message = error_msg('1006')
                # Create response with redirect to login page and this message as GET arg. Return that response
                response = HttpResponseRedirect(gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)
            else:
                response = func(request)
                return response
        if session_obj.user.usertype != usertype or session_obj.sourceip != clientIP_fromheader:
            message = error_msg('1007')
            # Create response with redirect to login page and this message as GET arg. Return that response
            response = HttpResponseRedirect(gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)
        else:
            response = func(request)
        return response
    return checkconsistency



def gethosturl(request):
    url = mysettings.URL_PROTOCOL
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


def sendemail(userobj, subject, message, fromaddr):
    """
    Method to send an email to the email id of the user passed in as the argument.
    Should be done asynchronously - put the email in a queue from where the email
    handler will pick in batches of (say) 10 emails at a time and send them before
    running to pick up the next batch.
    """
    retval = 0
    try:
        retval = send_mail(subject, message, fromaddr, [userobj.emailid,], False)
        return retval
    except:
        if mysettings.DEBUG:
            print "sendemail failed for %s - %s\n"%(userobj.emailid, sys.exc_info()[1].__str__())
        return None



def generate_random_string():
    """
    Generate a random string
    """
    random = str(uuid.uuid4())
    random = random.replace("-","")
    tstr = str(int(time.time() * 1000))
    random = random + tstr
    return random


def mkdir_p(path):
    if not os.access(path, os.F_OK):
        os.makedirs(path)
        os.chmod(path, 0666)


def get_extension(tmpfilepath):
    """
    Get the extension of a temporary file created using tempfile.mkstemp
    """
    fileparts = tmpfilepath.split(".")
    if fileparts.__len__() < 2:
        return ""
    ext = fileparts[1][0:3]
    return ext


def get_extension2(filename):
    """
    Replica of 'get_extension' defined in earlier. In previous version,
    the file extension is assumed to be 3 chars long only. Hence, in this present
    scenario, it doesn't work. This version handles that scenario.
    """
    extPattern = re.compile("\.(\w{3,4})$")
    extMatch = extPattern.search(filename)
    ext = ""
    if extMatch:
        ext = extMatch.groups()[0]
    return ext



def handleuploadedfile(uploaded_file, targetdir, filename=mysettings.PROFILE_PHOTO_NAME):
    """
    Handle uploaded file. Create the destination path if required.
    Returns a list containing the path to the uploaded file and a message
    (which would be '' in case of success).
    """
    mkdir_p(targetdir)
    if uploaded_file.size > mysettings.MAX_FILE_SIZE_ALLOWED:
        message = "Error: " + error_msg('1005')
        return [ None, message, '' ]
    ext = get_extension(uploaded_file.name)
    destinationfile = os.path.sep.join([ targetdir, filename + "." + ext, ])
    with open(destinationfile, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
        destination.close()
        os.chmod(targetdir, 0777)
        os.chmod(destinationfile, 0777) # Is there a way to club these 'chmod' statements?
    return [ destinationfile, '', filename + "." + ext ]


def handleuploadedfile2(uploaded_file, targetdir, filename=mysettings.PROFILE_PHOTO_NAME):
    """
    Replica of 'handleuploadedfile' defined in earlier. In previous version,
    the file extension is assumed to be 3 chars long only. Hence, in this present
    scenario, it doesn't work. This version handles that scenario.
    """
    mkdir_p(targetdir)
    if uploaded_file.size > mysettings.MAX_FILE_SIZE_ALLOWED:
        message = "Error: " + error_msg('1005')
        return [ None, message, '' ]
    ext = get_extension2(uploaded_file.name)
    destinationfile = os.path.sep.join([ targetdir, filename + "." + ext, ])
    with open(destinationfile, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
        destination.close()
        os.chmod(targetdir, 0777)
        os.chmod(destinationfile, 0777) # Is there a way to club these 'chmod' statements?
    return [ destinationfile, '', filename + "." + ext ]


def getprofileimgtag(request):
    """
    Function to form the img tag for profile image based on whether
    the user has a profile image or not.
    """
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    csrftoken = ''
    if request.COOKIES.has_key('csrftoken'):
        csrftoken = request.COOKIES['csrftoken']
    profimgfile = userobj.userpic.__str__()
    profimagepath = os.path.sep.join([ mysettings.MEDIA_ROOT, userobj.displayname, "images", profimgfile ])
    profileimgtag = "<img src='/static/images/profile.png' height='102' width='102' alt='Profile Image' id='profileimage'><br /><div id='uploadbox' style='display: none;'></div><a href='#' onClick='return uploader(&quot;%s&quot;,&quot;%s&quot;);'><font size='-1'>upload profile image</font></a>"%(mysettings.PROFIMG_CHANGE_URL, csrftoken)
    if os.path.exists(profimagepath) and profimgfile != "":
        profileimgtag = "<img src='media/%s/images/%s' height='102' width='102' alt='Profile Image'><br /><div id='uploadbox' style='display: none;'></div><a href='#' onClick='return uploader(&quot;%s&quot;, &quot;%s&quot;);'><font size='-1'>change profile image</font></a>"%(userobj.displayname, profimgfile, mysettings.PROFIMG_CHANGE_URL, csrftoken)
    return profileimgtag


def formatmessage(msg, msg_color):
    """
    Format message (with color and font) and return it as a displayable string
    (after removing all hexcoded characters and HTML entities, if present).
    """
    var, msg = msg.split("=")
    for hexkey in mysettings.HEXCODE_CHAR_MAP.keys():
        msg = msg.replace(hexkey, mysettings.HEXCODE_CHAR_MAP[hexkey])
    msg = "<p style=\"color:#%s;font-size:14;font-face:'helvetica neue';font-style:bold;\">%s</p>"%(msg_color, msg)
    return msg
    


def check_password_strength(passwd):
    if passwd.__len__() == 0:
        return 0
    strength = 0
    if passwd.__len__() > 6:
        strength += 1
    contains_digits, contains_special_char, contains_lowercase, contains_uppercase = 0, 0, 0, 0
    special_characters = "~`!#$%^&*+=-[]\\\';,/{}|\":<>?"
    i = 0
    while i < passwd.__len__() - 1:
        if passwd[i] >= '0' and passwd[i] <= '9':
            strength += 1
            i += 1
            continue
        if passwd[i] == passwd[i].upper():
            strength += 1
            i += 1
            continue
        if passwd[i] == passwd[i].lower():
            strength += 1
            i += 1
            continue
        if passwd[i] in special_characters:
            strength += 1
            i += 1
            continue
        i += 1
    return strength



def copy_test(testobj, userobj):
    """
    Method to copy a given Test object and create a new (duplicate) Test
    object which is owned by the User who requested the copy. Returns the copied Test
    object, None on failure. The primary owner/creator of the test has to
    transfer the rights to the new copied  test to the new user in order for
    the new user to access it. However, the 'evaluator' field will not
    be copied in the duplicate test.
    """
    newtest = Test()
    newtest.testname = "Copy of " + testobj.testname
    newtest.subtopic = testobj.subtopic
    newtest.topic = testobj.topic
    newtest.creator = userobj
    newtest.creatorisevaluator = testobj.creatorisevaluator
    evaluator = Evaluator()
    evaluator.evalgroupname = "eval_" + generate_random_string() # This will be a randomly generated string
    evaluator.groupmember1 = userobj
    evaluator.save()
    newtest.evaluator = evaluator
    newtest.testtype = testobj.testtype
    newtest.createdate = datetime.datetime.now()
    newtest.maxscore = testobj.maxscore
    newtest.passscore = testobj.passscore
    newtest.ruleset = testobj.ruleset
    newtest.duration = testobj.duration
    newtest.allowedlanguages = testobj.allowedlanguages
    newtest.challengecount = testobj.challengecount
    newtest.activationdate = datetime.datetime.now() + datetime.timedelta(seconds=864000) # 10 days ahead
    newtest.publishdate = datetime.datetime.now() + datetime.timedelta(seconds=864000)
    newtest.status = 0
    newtest.quality = testobj.quality
    newtest.testlinkid = generate_random_string()
    newtest.allowmultiattempts = testobj.allowmultiattempts
    newtest.maxattemptscount = testobj.maxattemptscount
    newtest.attemptsinterval = testobj.attemptsinterval
    newtest.attemptsintervalunit = testobj.attemptsintervalunit
    newtest.randomsequencing = testobj.randomsequencing
    newtest.multimediareqd = testobj.multimediareqd
    newtest.progenv = testobj.progenv
    newtest.negativescoreallowed = testobj.negativescoreallowed
    newtest.scope = testobj.scope
    newtest.save()
    newtestid = newtest.id
    challengesqset = Challenge.objects.filter(test=testobj)
    for challenge in challengesqset:
        newchallenge = Challenge()
        newchallenge.test = newtest
        newchallenge.statement = challenge.statement
        newchallenge.challengetype = challenge.challengetype
        newchallenge.maxresponsesizeallowable = challenge.maxresponsesizeallowable
        newchallenge.option1 = challenge.option1
        newchallenge.option2 = challenge.option2
        newchallenge.option3 = challenge.option3
        newchallenge.option4 = challenge.option4
        newchallenge.option5 = challenge.option5
        newchallenge.option6 = challenge.option6
        newchallenge.option7 = challenge.option7
        newchallenge.option8 = challenge.option8
        newchallenge.challengescore = challenge.challengescore
        newchallenge.negativescore = challenge.negativescore
        newchallenge.mustrespond = challenge.mustrespond
        newchallenge.responsekey = challenge.responsekey
        newchallenge.mediafile = challenge.mediafile
        newchallenge.additionalurl = challenge.additionalurl
        newchallenge.timeframe = challenge.timeframe
        newchallenge.subtopic = challenge.subtopic
        newchallenge.challengequality = challenge.challengequality
        newchallenge.testlinkid = newtest.testlinkid
        newchallenge.oneormore = challenge.oneormore
        newchallenge.save()
    return newtest



def includedtemplatevars(pagetitle, request):
    """
    pagetitle is expected to be the title string of the page with first letter in uppercase.
    """
    curdate = datetime.datetime.now()
    select_profile = ""
    select_dashboard = ""
    select_subscription = ""
    select_tests = ""
    select_search = ""
    select_socnet = ""
    select_analytics = ""
    select_aboutus = ""
    select_helpndoc = ""
    select_careers = ""
    select_plans = ""
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
    elif pagetitle == 'Network':
        select_socnet = " class=\"highlight\""
    elif pagetitle == 'Test Analytics':
        select_analytics = " class=\"highlight\""
    elif pagetitle == 'About Us':
        select_aboutus = " class=\"highlight\""
    elif pagetitle == 'Help/Documentation':
        select_helpndoc = " class=\"highlight\""
    elif pagetitle == 'Careers/Jobs':
        select_careers = " class=\"highlight\""
    elif pagetitle == 'Plans & Pricing':
        select_plans = " class=\"highlight\""
    else: # Invalid tab, control should not have come here. Skip quietly.
        pass
    cntxt = { 'pagetitle' : pagetitle, 'select_profile' : select_profile, 'select_dashboard' : select_dashboard, 'select_subscription' : select_subscription, \
              'select_tests' : select_tests, 'select_search' : select_search, 'select_socnet' : select_socnet, 'select_analytics' : select_analytics, \
              'select_aboutus' : select_aboutus, 'select_helpndoc' : select_helpndoc, 'select_careers' : select_careers, 'select_plans' : select_plans,}
    # Add the page URLs from mysettings in context
    cntxt['profile_url'] = gethosturl(request) + "/" + mysettings.PROFILE_URL
    cntxt['dashboard_url'] = gethosturl(request) + "/" + mysettings.DASHBOARD_URL
    cntxt['subscription_url'] = gethosturl(request) + "/" + mysettings.SUBSCRIPTION_URL
    cntxt['tests_url'] = gethosturl(request) + "/" + mysettings.MANAGE_TEST_URL
    cntxt['search_url'] = gethosturl(request) + "/" + mysettings.SEARCH_URL
    cntxt['network_url'] = gethosturl(request) + "/" + mysettings.NETWORK_URL
    cntxt['analytics_url'] = gethosturl(request) + "/" + mysettings.ANALYTICS_URL
    cntxt['aboutus_url'] = gethosturl(request) + "/" + mysettings.ABOUTUS_URL
    cntxt['helpndoc_url'] = gethosturl(request) + "/" + mysettings.HELP_URL
    cntxt['careers_url'] = gethosturl(request) + "/" + mysettings.CAREER_URL
    cntxt['plans_url'] = gethosturl(request) + "/" + mysettings.PLANS_URL
    cntxt['logout_url'] = gethosturl(request) + "/" + mysettings.LOGOUT_URL
    cntxt['privacypolicy_url'] = gethosturl(request) + "/" + mysettings.PRIVPOLICY_URL
    cntxt['tou_url'] = gethosturl(request) + "/" + mysettings.TERMSOFUSE_URL
    return cntxt


def getcurrentplans(userobj):
    """
    Function to get the current plans a given user has subscribed to.
    """
    currentplans = {}
    userplans = UserPlan.objects.filter(user=userobj).order_by('-subscribedon') # Getting all UserPlans for the User.
    for usrpln in userplans: # userplans is a queryset object...
        planstart = usrpln.planstartdate.strftime("%Y-%m-%d %H:%M:%S")
        startdate, starttime = planstart.split(" ")
        startyyyy, startmon, startdd = startdate.split("-")
        starthh, startmm, startss = starttime.split(":")
        planend = usrpln.planenddate.strftime("%Y-%m-%d %H:%M:%S")
        enddate, endtime = planend.split(" ")
        endyyyy, endmon, enddd = enddate.split("-")
        endhh, endmm, endss = endtime.split(":")
        planstatus = usrpln.planstatus
        subscribed = usrpln.subscribedon
        planname = usrpln.plan.planname
        # For this plan to be the current plan, the current datetime value should be between planstart and planend.
        curdatetime = datetime.datetime.now()
        if curdatetime > datetime.datetime(int(startyyyy), int(startmon), int(startdd), int(starthh), int(startmm), int(startss)) and curdatetime < datetime.datetime(int(endyyyy), int(endmon), int(enddd), int(endhh), int(endmm), int(endss)) and planstatus:
            tests = usrpln.plan.testsninterviews
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


def mysqltopythondatetime(mysqldatetime):
    mysqldate, mysqltime = mysqldatetime.split(" ")
    mysqlyyyy, mysqlmon, mysqldd = mysqldate.split("-")
    hms = mysqltime.split(":")
    if hms.__len__() < 3:
        mysqlhh, mysqlmm, mysqlss = '00', '00', '00'
    else:
        mysqlhh, mysqlmm, mysqlss = hms[0], hms[1], '00'
    pythondatetime = datetime.datetime(int(mysqlyyyy), int(mysqlmon), int(mysqldd), int(mysqlhh), int(mysqlmm), int(mysqlss))
    return pythondatetime


def pythontomysqldatetime(dt_date):
    """
    The parameter should be a string representation of datetime.datetime object. e.g. datetime.datetime.now()
    """
    dt_date_parts = dt_date.split(' ')
    timepattern = re.compile(r"(\d{1,2}:\d{1,2}:\d{1,2})\.?\d*$")
    timematch = timepattern.search(dt_date_parts[1])
    timepart = '00:00:00'
    if timematch:
        timepart = timematch.groups()[0]
    mysqlcompatibledate = dt_date_parts[0] + " " + timepart
    return mysqlcompatibledate


def pythontomysqldatetime2(dt_date):
    """
    The parameter should be a string representation of datetime.datetime object. e.g. datetime.datetime.now()
    """
    dt_date_parts = dt_date.split(' ')
    timepattern = re.compile(r"(\d{1,2}:\d{1,2}:\d{1,2})\.?\d*$")
    timematch = None
    if dt_date_parts.__len__() > 1:
        timematch = timepattern.search(dt_date_parts[1])
    if not timematch:
        mysqlcompatibledate = "Not Applicable"
        return mysqlcompatibledate
    timepart = '00:00:00'
    if timematch:
        timepart = timematch.groups()[0]
    mysqlcompatibledate = ""
    if dt_date_parts.__len__() > 0:
        mysqlcompatibledate = dt_date_parts[0] + " " + timepart
    return mysqlcompatibledate


def yetanotherpythontomysqldatetime(dt_date):
    """
    The name suggests the purpose and attempt. (uugh!!!)
    """
    year = str(dt_date.year)
    mon = str(dt_date.month)
    day = str(dt_date.day)
    minute = str(dt_date.minute)
    hour = str(dt_date.hour)
    second = str(dt_date.second)
    if mon.__len__() == 1:
        mon = "0" + mon
    if day.__len__() == 1:
        day = "0" + day
    if hour.__len__() == 1:
        hour = "0" + hour
    if minute.__len__() == 1:
        minute = "0" + minute
    if second.__len__() == 1:
        second = "0" + second
    mysqldt = year + "-" + mon + "-" + day + " " + hour + ":" + minute + ":" + second
    return mysqldt


def readabledatetime(mysqldatefmt):
    """
    This will receive a date formatted like: 2015-03-24 16:59:34+00:00
    The return value would be '24 Mar 2015, 16:59:34'. If the date comes
    in any other format, the returned value would in the format 
    YYYY-MM-DD hh:mm:ss.
    """
    if not mysqldatefmt:
        return ""
    datepart, timepart = "", ""
    mysqldatefmt_parts = mysqldatefmt.__str__().split(" ")
    if mysqldatefmt_parts.__len__() >= 2:
        datepart, timepart = mysqldatefmt_parts[0], mysqldatefmt_parts[1]
    else:
        return ""
    dateelements = datepart.split("-")
    cleantimeparts,junktimeparts = timepart.split("+")
    if dateelements.__len__() != 3:
        print "Received date is not in expected format: YYYY-MM-DD hh:mm:ss: %s\n"%mysqldatefmt
        return datepart + " " + cleantimeparts[0]
    YYYY = dateelements[0]
    MM = dateelements[1]
    DD = dateelements[2]
    mon = mysettings.REV_MONTHS_DICT[str(MM)]
    readabledatetimestr = '%s %s %s, %s'%(DD, mon, YYYY, cleantimeparts)
    return readabledatetimestr



def urlencodestring(s):
    tmphash = {'str' : s }
    encodedStr = urllib.urlencode(tmphash)
    encodedPattern = re.compile(r"^str=(.*)$")
    encodedSearch = encodedPattern.search(encodedStr)
    encodedStr = encodedSearch.groups()[0]
    encodedStr = encodedStr.replace('.', '%2E')
    encodedStr = encodedStr.replace('-', '%2D')
    encodedStr = encodedStr.replace(',', '%2C')
    return (encodedStr)


def converttimeunit(secs):
    yearsecs = (365 * 24 * 60 * 60)
    monthsecs = (30 * 24 * 60 * 60)
    daysecs = 86400
    hoursecs = 3600
    minutesecs = 60
    years, months, days, hour, minutes, seconds = 0, 0, 0, 0, 0, 0
    if secs > yearsecs:
        years = int(secs / yearsecs)
        secs = secs % yearsecs 
    if secs > monthsecs:
        months = int(secs/monthsecs)
        secs = secs % monthsecs
    if secs > daysecs:
        days = int(secs/daysecs)
        secs = secs % daysecs
    if secs > hoursecs:
        hours = int(secs/hoursecs)
        secs = secs % hoursecs
    if secs > minutesecs:
        minutes = int(secs/minutesecs)
        seconds = secs % minutesecs
    seconds = int(seconds)
    intervalstring = ""
    if years > 0:
        intervalstring += str(years) + " years "
    if months > 0:
        intervalstring += str(months) + " months "
    if days > 0:
        intervalstring += str(days) + " days "
    if hours > 0:
        intervalstring += str(hours) + " hours "
    if minutes > 0:
        intervalstring += str(minutes) + " minutes "
    if seconds > 0:
        intervalstring += str(seconds) + " seconds"
    return intervalstring


def randomstringgen(size=26, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def fetch_currency_rate(fromcurr, tocurr):
    currentdate = str(datetime.datetime.now())
    currentdateparts = currentdate.split(" ")
    y,m,d = currentdateparts[0].split("-")
    minhour,minminute,minsecond = 0,0,1
    maxhour, maxminute,maxsecond = 23,59,59
    dateofrate_min = datetime.datetime(int(y), int(m),int(d), minhour,minminute,minsecond,0, pytz.UTC)
    dateofrate_max = datetime.datetime(int(y), int(m),int(d), maxhour,maxminute,maxsecond,0, pytz.UTC)
    try:
        xchangeqset = ExchangeRates.objects.filter(curr_from=fromcurr, curr_to=tocurr)
        for xchangeobj in xchangeqset:
            if xchangeobj.dateofrate is not None and xchangeobj.dateofrate > dateofrate_min and xchangeobj.dateofrate < dateofrate_max:
                return float(xchangeobj.conv_rate)
        # If we ever come to this point, then we clearly don't have the necessary conversion rate in DB. Let's try the reverse.
        xchangeqset = ExchangeRates.objects.filter(curr_from=tocurr, curr_to=fromcurr)
        for xchangeobj in xchangeqset:
            if xchangeobj.dateofrate is not None and xchangeobj.dateofrate > dateofrate_min and xchangeobj.dateofrate < dateofrate_max:
                return float(1/float(xchangeobj.conv_rate))
        # If we come here, then we possibly don't have a record for today's date yet. Let's try yesterday.
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        yesterdaystr = str(yesterday)
        yesterdayparts = yesterdaystr.split(" ")
        y,m,d = yesterdayparts[0].split("-")
        dateofrate_min = datetime.datetime(int(y), int(m),int(d), minhour,minminute,minsecond,0, pytz.UTC)
        dateofrate_max = datetime.datetime(int(y), int(m),int(d), maxhour,maxminute,maxsecond,0, pytz.UTC)
        xchangeqset = ExchangeRates.objects.filter(curr_from=fromcurr, curr_to=tocurr)
        for xchangeobj in xchangeqset:
            if xchangeobj.dateofrate is not None and xchangeobj.dateofrate > dateofrate_min and xchangeobj.dateofrate < dateofrate_max:
                return float(xchangeobj.conv_rate)
        # If we ever come to this point, then we clearly don't have the necessary conversion rate in DB. Let's try the reverse.
        xchangeqset = ExchangeRates.objects.filter(curr_from=tocurr, curr_to=fromcurr)
        for xchangeobj in xchangeqset:
            if xchangeobj.dateofrate is not None and xchangeobj.dateofrate > dateofrate_min and xchangeobj.dateofrate < dateofrate_max:
                return float(1/float(xchangeobj.conv_rate))
    except:
        print "Error: %s"%sys.exc_info()[1].__str__()
    return 1



def decodeGzippedContent(encoded_content):
    response_stream = StringIO.StringIO(encoded_content)
    decoded_content = ""
    try:
        gzipper = gzip.GzipFile(fileobj=response_stream)
        decoded_content = gzipper.read()
    except: # Maybe this isn't gzipped content after all....
        decoded_content = encoded_content
    return(decoded_content)

_decodeGzippedContent = decodeGzippedContent

class Logger(object):

    def __init__(self, logfilewithpath):
        if not os.path.exists(logfilewithpath):
            parentdir = os.path.dirname(logfilewithpath)
            if not os.path.exists(parentdir):
                os.makedirs(parentdir)
        else:
            parentdir = os.path.dirname(logfilewithpath)
        self.logfile = os.pathsep.join([parentdir, os.path.basename(logfilewithpath)])
        self.logfilehandle = open(self.logfile, 'w')

    def logmessage(self, msg):
        self.logfilehandle.write(msg)


    def close(self):
        self.logfilehandle.close()



def remove_control_chars(s):
    control_chars = ''.join(map(unichr, range(0,32) + range(127,160)))
    control_char_re = re.compile('[%s]' % re.escape(control_chars))
    return control_char_re.sub('', s)


# Taken from an answer on stackoverflow
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def des3Decrypt(encString, key, iv):
    # Method to decrypt DES3 encrypted strings.
    # For now, this is just a placeholder. But
    # please do not start making edits here as
    # it gets called from Tests.views code.
    """
    des3 = DES3.new(key, DES3.MODE_CFB, iv)
    des3.decrypt(encString)
    """
    return encString


def repl_token_generator():
    """
    This is the token generator function, but it is not complete as yet.
    Also, it is erroneous and takes up ATM card after dispensing the amount
    """
    h = hashlib.sha256()
    h.update(mysettings.REPL_SECRET)
    hdig = h.hexdigest()

    t = int(time.time() * 1000).__str__()
    digest_maker = hmac.new(hdig)
    digest_maker.update(t)
    digest = digest_maker.hexdigest()
    return digest


def applycoupon(couponobj, xobj, objtype='plan'):
    """
    Function to apply a coupon on either the subscription of a plan or
    the joining in a paid group.
    """
    couponamt = couponobj.discount_value
    actualamt = 0.00
    if not xobj:
        return None
    if objtype == 'plan':
        actualamt = xobj.price
    elif objtype == 'group':
        actualamt = xobj.entryfee
    else: # objtype is neither 'plan' nor 'group'. Not recognized by this function.
        return None
    discountedamt = float(actualamt) - float(couponamt)
    # if discountedamt is negative, make it 0
    if discountedamt < float(0):
        discountedamt = 0.00
    return discountedamt

"""
Automation for onboarding a client on razorpay.
It should add razorpayid in OwnerBankAccount object.
"""
def onboardclientonrazor_old(bankacctid):
    opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler())
    httpHeaders = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'}
    bankacctobj = OwnerBankAccount.objects.get(id=bankacctid)
    linked_acct_name = bankacctobj.groupowner.firstname + " " + bankacctobj.groupowner.lastname
    clienttype = 2
    phone_no = bankacctobj.groupowner.mobileno
    if not phone_no:
        phone_no = mysettings.DEFAULT_PHONENO_PLACEHOLDER
    emailid = bankacctobj.groupowner.emailid
    acctno = bankacctobj.accountnumber
    accttype = 2
    ifsccode = bankacctobj.ifsccode
    beneficiary_name = bankacctobj.accountownername
    targeturi = mysettings.RAZORPAY_BASEURI + "/transfers"
    data = {'name' : beneficiary_name, 'email' : emailid, 'contact' : phone_no, 'data-key' : mysettings.RAZORPAY_KEY}
    postdata = urllib.urlencode(data)
    onboardrequest = urllib2.Request(targeturi, postdata,httpHeaders)
    try:
        onboardresponse = opener.open(onboardrequest)
    except:
        message = "The Onboarding API request failed with the following reason: %s\n"%sys.exc_info()[1].__str__()
        return message
    responsecontent = decodeGzippedContent(onboardresponse.read())
    return responsecontent
    


def onboardclientonrazor(bankacctid):
    """
    try:
        bankacctobj = OwnerBankAccount.objects.get(id=bankacctid)
    except:
        message = "Could not find the OwnerBankAccount object with the ID %s. Error: %s\n"%(bankacctid, sys.exc_info()[1].__str__())
        return message
    #ff = open("/home/supmit/work/testyard/tmpfiles/message0004.txt", "w")
    #ff.write("HERE")
    #ff.close()
    start_url = "https://dashboard.razorpay.com/submerchants"
    linked_accts_url = "https://dashboard.razorpay.com/merchant/api/test/linked_accounts?count=25"
    opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler())
    httpHeaders = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/png,*/*;q=0.8'}
    data = { 'account': True, 'name': bankacctobj.accountownername, 'email': bankacctobj.groupowner.emailid, 'mode': "test"}
    postdata = urllib.urlencode(data)
    ff = open("/home/supmit/work/testyard/tmpfiles/postdump0002.txt", "w")
    ff.write(str(postdata))
    ff.close()
    pageRequest = urllib2.Request(start_url, postdata, httpHeaders)
    pageResponse= None
    cookies = {'XSRF-TOKEN' : '', 'rzp_usr_session' : ''}
    try:
        pageResponse = opener.open(pageRequest)
        pageResponseContent = _decodeGzippedContent(pageResponse.read())
        ff = open("/home/supmit/work/testyard/tmpfiles/responsedump.txt", "w")
        ff.write(str(pageResponseContent))
        ff.close()
    except:
        msg = "Could not fetch start url. Error: %s"%sys.exc_info()[1].__str__()
        ff = open("/home/supmit/work/testyard/tmpfiles/responsedump.txt", "w")
        ff.write(msg)
        ff.close()
        return msg
    pageResponseHeaders = pageResponse.info()
    cookieheaders = pageResponseHeaders['Set-Cookie']
    ff = open("/home/supmit/work/testyard/tmpfiles/customerdump.txt", "w")
    ff.write(str(cookieheaders))
    ff.close()
    """
    try:
        bankacctobj = OwnerBankAccount.objects.get(id=bankacctid)
    except:
        message = "Could not find the OwnerBankAccount object with the ID %s\n"%bankacctid
        return message
    client = razorpay.Client(auth=(mysettings.RAZORPAY_KEY, mysettings.RAZORPAY_SECRET))
    try:
        data = client.customer.create(data={'name' : bankacctobj.accountownername, 'email' : bankacctobj.groupowner.emailid, 'contact' : bankacctobj.groupowner.mobileno, 'notes' : {'bank_name' : bankacctobj.bankname, 'bank_branch' : bankacctobj.bankbranch}})
        razor_id = data['id']
        bankacctobj.razor_account_id = razor_id
        bankacctobj.save()
        return razor_id
    except:
        return 0 # Customer already exists.
    

def initrazorpay():
    client = razorpay.Client(auth=(mysettings.RAZORPAY_KEY, mysettings.RAZORPAY_SECRET))
    return client

def connectdb(user='root', passwd='Spmprx13@', dbname='testyard', host='localhost', port=3306):
    dbconn = MySQLdb.connect(host=host, user=user, passwd=passwd, db=dbname, port=port)
    cursor = dbconn.cursor()
    return (dbconn, cursor)


def connectdb_p(user='root', passwd='Spmprx13@', dbname='testyard', host='localhost', port=3306):
    """
    Returns the dbconnection and 'MySQLCursorPrepared' cursor object
    """
    dbconn = MySQLdb.connect(host=host, user=user, passwd=passwd, db=dbname, port=port)
    cursor = dbconn.cursor(prepared=True)
    return (dbconn, cursor)
    
    
def disconnectdb(dbconn, cursor):
    cursor.close()
    dbconn.close()


def createopener():
    opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler())
    return opener

def getshorturl(url):
    httpheaders = { 'User-Agent' : r'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.10) Gecko/20111103 Firefox/3.6.24',  'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language' : 'en-us,en;q=0.5', 'Accept-Encoding' : 'gzip,deflate', 'Accept-Charset' : 'ISO-8859-1,utf-8;q=0.7,*;q=0.7', 'Keep-Alive' : '115', 'Connection' : 'keep-alive', 'content-type' : 'application/json'}
    requesturl = mysettings.URL_SHORTENER_HOST + "/url"
    requestdict = { 'target_url' : url}
    requestdata = json.dumps(requestdict).encode("utf-8")
    httpheaders['content-length'] = requestdata.__len__()
    requestobj = urllib2.Request(requesturl, data=requestdata, headers=httpheaders)
    opener = createopener()
    responseobj = None
    try:
        responseobj = opener.open(requestobj)
    except:
        print("Error: %s"%sys.exc_info()[1].__str__())
        return None
    responsedata = responseobj.read()
    return responsedata


def gettargeturl(key):
    httpheaders = { 'User-Agent' : r'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.10) Gecko/20111103 Firefox/3.6.24',  'Accept' : 'application/json', 'Accept-Language' : 'en-us,en;q=0.5', 'Accept-Encoding' : 'gzip,deflate', 'Accept-Charset' : 'ISO-8859-1,utf-8;q=0.7,*;q=0.7', 'Keep-Alive' : '115', 'Connection' : 'keep-alive', }
    #print(key)
    requesturl = "http://192.168.1.6:8080/%s"%key
    requestobj = urllib2.Request(requesturl, headers=httpheaders)
    opener = createopener()
    responseobj = None
    try:
        responseobj = opener.open(requestobj)
    except:
        print("Error: %s"%sys.exc_info()[1].__str__())
        return None
    return responseobj



def paypal_get_accesstoken():
    oauth2url = "%s/v1/oauth2/token"%mysettings.PAYPAL_SANDBOX_URL
    oauth2user = mysettings.PAYPAL_CLIENT_ID + ":" + mysettings.PAYPAL_SECRET_01
    httpheaders = {'Content-Type' : 'application/x-www-form-urlencoded', 'Accept' : '*/*', 'User-Agent' : 'TestYard 1.1', 'Authorization' : 'Bearer %s'%base64.b64encode(oauth2user)}
    postdata = "grant_type=client_credentials"
    httpheaders['Content-Length'] = postdata.__len__()
    try:
        resp = requests.post(oauth2url, headers=httpheaders, data=postdata)
        access_token = resp.json()['access_token']
        return access_token
    except:
        return None


# API Docs: https://developer.paypal.com/docs/multiparty/seller-onboarding/before-payment/
# Form for using multiparty sellers: https://developer.paypal.com/docs/multiparty/#tell-us-about-your-platform
def paypal_seller_onboarding(request):
    """
        Implement PayPal seller's onboarding:
        1. Get an Access Token by authenticating using OAuth2.
        2. Generate a sign-up link for the seller on your platform.
        3. Use the "action_url" from the response to redirect seller to the paypal signup page.
        4. Once  signup flow is completed, the seller is returned to -
        partner_config_override/return_url field of the Partner Referrals API.
    """
    accesstoken = paypal_get_accesstoken()
    if accesstoken is None:
        message = "Couldn't retrieve access token from paypal: %s"%sys.exc_info()[1].__str__()
        return message
    signuplinkurl = "https://api-m.sandbox.paypal.com/v2/customer/partner-referrals"
    httpheaders = {'Content-Type' : 'application/json', 'Authorization' : 'Bearer %s'%accesstoken, 'Content-Length' : ''}
    trackingid = randomstringgen() # Need to save this in the DB
    jsondata = {'tracking_id' : trackingid, 'operations' : [{'operation' : 'API_INTEGRATION', 'api_integration_preference' : {'rest_api_integration' : {'integration_method' : 'PAYPAL', 'integration_type' : 'THIRD_PARTY', 'third_party_details' : {'features' : ["PAYMENT", "REFUND"]}}}}], 'products' : ["EXPRESS_CHECKOUT",], 'legal_consents' : [{"type": "SHARE_DATA_CONSENT", "granted": True}]}
    postdata = json.dumps(jsondata)
    httpheaders['Content-Length'] = postdata.__len__()
    try:
        signuplinkresponse = requests.post(signuplinkurl, headers=httpheaders, data=postdata)
        responsejson = signuplinkresponse.json()
        referraldataurl = responsejson['links'][0]['href']
        redirecturl = responsejson['links'][1]['href']
        return str(redirecturl) # Send the signup link back to the caller and from there to the javascript caller
    except:
        message = "Could not retrieve sign up link response: %s"%sys.exc_info()[1].__str__()
        return message


def dumpasxml(username, testrecords_ascreator, testrecords_ascandidate, interviewrecords_ascreator, interviewrecords_ascandidate):
    """
    We will create 4 files here - one each for each of the record types.
    Finally, we will zip them up and return the path to the zipped archive.
    """
    curdatetime = datetime.datetime.now()
    curdatetimestr = curdatetime.strftime("%Y%m%d%H%M%S")
    tmpdir = mysettings.PROJECT_ROOT + os.path.sep + "userdata" + os.path.sep + "tmpdir" + os.path.sep + username + "_xml_" + curdatetimestr
    if not os.path.exists(tmpdir):
        mkdir_p(tmpdir)
    targetzipfile = mysettings.PROJECT_ROOT + os.path.sep + "userdata" + os.path.sep + "tmpdir" + os.path.sep + username + "_xml_" + curdatetimestr + ".zip"
    dumpfile1 = tmpdir + os.path.sep + username + "_testsascreator_" + curdatetimestr + ".xml"
    dumpfile2 = tmpdir + os.path.sep + username + "_testsascandidate_" + curdatetimestr + ".xml"
    dumpfile3 = tmpdir + os.path.sep + username + "_interviewsascreator_" + curdatetimestr + ".xml"
    dumpfile4 = tmpdir + os.path.sep + username + "_interviewsascandidate_" + curdatetimestr + ".xml"
    filecontent1 = """<?xml version="1.0" encoding="UTF-8" ?>\n"""
    filecontent2 = """<?xml version="1.0" encoding="UTF-8" ?>\n"""
    filecontent3 = """<?xml version="1.0" encoding="UTF-8" ?>\n"""
    filecontent4 = """<?xml version="1.0" encoding="UTF-8" ?>\n"""
    filepaths = []
    alltestscreated = etree.Element("tests")
    for testname in testrecords_ascreator.keys():
        testtag = etree.SubElement(alltestscreated, "test")
        metadata = etree.SubElement(testtag, "metadata")
        testrecord = testrecords_ascreator[testname]
        for tagname in testrecord.keys():
            if tagname != "challenges":
                tag = etree.SubElement(metadata, tagname.lower())
                tag.text = str(testrecord[tagname])
            else:
                pass
                
        challenges = testrecord['challenges']
        for challenge in challenges:
            chtag = etree.SubElement(testtag, "challenge")
            for chkey in challenge.keys():
                chkeytag = etree.SubElement(chtag, chkey.lower())
                chkeytag.text = str(challenge[chkey])
    alltestscreatedxml = etree.tostring(alltestscreated)
    filecontent1 += alltestscreatedxml
    tcrfp = open(dumpfile1, "wb")
    tcrfp.write(filecontent1)
    tcrfp.close()
    filepaths.append(dumpfile1)
    # Done writing all tests created by user.
    alltestscandidate = etree.Element("tests")
    for testname in testrecords_ascandidate.keys():
        testtag = etree.SubElement(alltestscandidate, "test")
        testrecord = testrecords_ascandidate[testname]
        for testkey in testrecord:
            attributetag = etree.SubElement(testtag, testkey.lower())
            attributetag.text = str(testrecord[testkey])
    alltestscandidatexml = etree.tostring(alltestscandidate)
    filecontent2 += alltestscandidatexml
    tcdfp = open(dumpfile2, "wb")
    tcdfp.write(filecontent2)
    tcdfp.close()
    filepaths.append(dumpfile2)
    # Done writing all tests where user was a candidate (test taker)
    allinterviewscreated = etree.Element("interviews")
    for interviewtitle in interviewrecords_ascreator.keys():
        interviewtag = etree.SubElement(allinterviewscreated, "interview")
        interviewrecord = interviewrecords_ascreator[interviewtitle]
        for intkey in interviewrecord.keys():
            intkeytag = etree.SubElement(interviewtag, intkey.lower())
            intkeytag.text = str(interviewrecord[intkey])
    allinterviewscreatedxml = etree.tostring(allinterviewscreated)
    filecontent3 += allinterviewscreatedxml
    icrfp = open(dumpfile3, "wb")
    icrfp.write(filecontent3)
    icrfp.close()
    filepaths.append(dumpfile3)
    # Done writing all interviews created by the user.
    allinterviewscandidate = etree.Element("interviews")
    for interviewtitle in interviewrecords_ascandidate.keys():
        interviewtag = etree.SubElement(allinterviewscandidate, "interview")
        interviewrecord = interviewrecords_ascandidate[interviewtitle]
        for intkey in interviewrecord.keys():
            intkeytag = etree.SubElement(interviewtag, intkey.lower())
            intkeytag.text = str(interviewrecord[intkey])
    allinterviewscandidatexml = etree.tostring(allinterviewscandidate)
    filecontent4 += allinterviewscandidatexml
    icdfp = open(dumpfile4, "wb")
    icdfp.write(filecontent4)
    icdfp.close()
    filepaths.append(dumpfile4)
    # TODO: Validate all 4 files against their respective xsd files.
    # Done writing all interviews that the user attended as an interviewee... Now we have all 4 files.
    # So zip the flippin' thing up and shove it up the user's a***.
    with ZipFile(targetzipfile, 'w') as zip:
        for filep in filepaths:
            zip.write(filep)
    return targetzipfile # Done and dusted!
    
    
    """
    from lxml import etree
    # https://stackoverflow.com/questions/58002988/how-to-validate-xml-with-xsd-in-python
    root = etree.Element('a')
    child1 = etree.SubElement(root, 'b')
    print(etree.tostring(root))
    xmlschema_doc = etree.parse('test_xsd.xsd')
    xmlschema = etree.XMLSchema(xmlschema_doc)
    doc = etree.XML(etree.tostring(root))
    validation_result = xmlschema.validate(doc)
    print(validation_result)
    
    # https://www.geeksforgeeks.org/reading-and-writing-xml-files-in-python/
    
    # https://stackoverflow.com/questions/3330366/how-to-validate-an-xml-file-against-an-xsd-schema-using-amara-library-in-python
    from lxml import etree
    source_file = 'test.xml'
    schema_file = 'test.xsd'
    with open(schema_file) as f_schema:
        schema_doc = etree.parse(f_schema)
        schema = etree.XMLSchema(schema_doc)
        parser = etree.XMLParser(schema = schema)
        with open(source_file) as f_source:
            try:
                doc = etree.parse(f_source, parser)
            except etree.XMLSyntaxError as e:
                # this exception is thrown on schema validation error
                print e
    """


def dumpascsv(username, testrecords_ascreator, testrecords_ascandidate, interviewrecords_ascreator, interviewrecords_ascandidate):
    """
    We will create 4 files here - one each for each of the record types.
    Finally, we will zip them up and return the path to the zipped archive.
    """
    curdatetime = datetime.datetime.now()
    curdatetimestr = curdatetime.strftime("%Y%m%d%H%M%S")
    tmpdir = mysettings.PROJECT_ROOT + os.path.sep + "userdata" + os.path.sep + "tmpdir" + os.path.sep + username + "_csv_" + curdatetimestr
    if not os.path.exists(tmpdir):
        mkdir_p(tmpdir)
    targetzipfile = mysettings.PROJECT_ROOT + os.path.sep + "userdata" + os.path.sep + "tmpdir" + os.path.sep + username + "_csv_" + curdatetimestr + ".zip"
    dumpfile1 = tmpdir + os.path.sep + username + "_testsascreator_" + curdatetimestr + ".csv"
    dumpfile2 = tmpdir + os.path.sep + username + "_testsascandidate_" + curdatetimestr + ".csv"
    dumpfile3 = tmpdir + os.path.sep + username + "_interviewsascreator_" + curdatetimestr + ".csv"
    dumpfile4 = tmpdir + os.path.sep + username + "_interviewsascandidate_" + curdatetimestr + ".csv"
    filecontent1, filecontent2, filecontent3, filecontent4 = "", "", "", ""
    headerflag = True
    headers = []
    messages = []
    filepaths = []
    for testname in testrecords_ascreator.keys():
        testrecord = testrecords_ascreator[testname]
        if headerflag is True:
            for testkey in testrecord.keys():
                if testkey != "challenges":
                    headers.append(testkey)
                else:
                    challengeslist = testrecord['challenges']
                    try:
                        challengeheaders = challengeslist[0].keys()
                    except:
                        challengeheaders = ['challengeid', 'challengestatement', 'challengetype', 'maxresponsesizeallowable', 'challengescore', 'negativescore', 'compulsoryforuser', 'challengeimagepath', 'externalresourcepath', 'challengeallocatedtime', 'challenge_subtopic_id', 'challengequality', 'challenge_testlinkid', 'morethanoneoptioncorrect', 'proglang', 'mathenv', 'option1', 'option2', 'option3', 'option4', 'option5', 'option6', 'option7', 'option8', 'correctresponse']
                    for chhdr in challengeheaders:
                        headers.append(chhdr)
            filecontent1 += ",".join(headers) + "\n"
            headerflag = False
        for hdr in headers:
            try:
                value = testrecord[hdr]
            except: # The header could be a field in the dict in challenges list.
                try:
                    value = testrecord['challenges'][hdr]
                except: # May be a mistake somewhere...
                    value = ""
                    messages.append("Value for header '%' could not be found for test with name '%s'"%(hdr, testname))
            filecontent1 += '"' + str(value) + '",'
        filecontent1 = filecontent1[:-1] + "\n" # Remove last comma from the string and add a newline.
    tcrfp = open(dumpfile1, "wb")
    tcrfp.write(filecontent1)
    tcrfp.close() # Data for tests as creator dumped in file.
    filepaths.append(dumpfile1)
    headerflag = True
    headers = []
    for testname in testrecords_ascandidate.keys():
        testrecord = testrecords_ascandidate[testname]
        if headerflag is True:
            for testkey in testrecord.keys():
                headers.append(testkey)
            filecontent2 = ",".join(headers) + "\n"
            headerflag = False
        for hdr in headers:
            try:
                value = str(testrecord[hdr])
            except:
                messages.append("Could not find value for key '%s' of test '%s'"%(hdr, testname))
                value = ""
            filecontent2 += '"' + value + '",'
        filecontent2 = filecontent2[:-1] + "\n"
    tcdfp = open(dumpfile2, "wb")
    tcdfp.write(filecontent2)
    tcdfp.close() # Data for tests as candidate dumped in file
    filepaths.append(dumpfile2)
    headerflag = True
    headers = []
    for interviewtitle in interviewrecords_ascreator.keys():
        interviewrecord = interviewrecords_ascreator[interviewtitle]
        if headerflag is True:
            for intkey in interviewrecord.keys():
                headers.append(intkey)
            filecontent3 = ",".join(headers) + "\n"
            headerflag = False
        for hdr in headers:
            try:
                value = str(interviewrecord[hdr])
            except:
                message.append("Could not find value for key '%s' of interview titled '%s'"%(hdr, interviewtitle))
                value = ""
            filecontent3 += '"' + value + '",'
        filecontent3 = filecontent3[:-1] + "\n"
    icrfp = open(dumpfile3, "wb")
    icrfp.write(filecontent3)
    icrfp.close() # Data for interviews as creator dumped in file
    filepaths.append(dumpfile3)
    headerflag = True
    headers = []
    for interviewtitle in interviewrecords_ascandidate.keys():
        interviewrecord = interviewrecords_ascandidate[interviewtitle]
        if headerflag is True:
            for intkey in interviewrecord.keys():
                headers.append(intkey)
            filecontent4 = ",".join(headers) + "\n"
            headerflag = False
        for hdr in headers:
            try:
                value = str(interviewrecord[hdr])
            except:
                message.append("Could not find value for key '%s' of interview titled '%s'"%(hdr, interviewtitle))
                value = ""
            filecontent4 += '"' + value + '",'
        filecontent4 = filecontent4[:-1] + "\n"
    icrfp = open(dumpfile4, "wb")
    icrfp.write(filecontent4)
    icrfp.close() # Data for interviews as candidate dumped in file.
    filepaths.append(dumpfile4)
    # Now zip up all files in the directory 
    with ZipFile(targetzipfile, 'w') as zip:
        for filep in filepaths:
            zip.write(filep)
    return targetzipfile # Zipped archive path




