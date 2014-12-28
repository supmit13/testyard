import os, sys, re, time
import tempfile, shutil
from functools import wraps

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.backends.db import SessionStore
from django.template import Template, Context

# Application specific libraries...
from skillstest.Auth.models import User, Session
from skillstest import settings as mysettings
from skillstest.errors import error_msg
from skillstest.Tests.models import Test, Challenge, Topic, Subtopic, Evaluator, UserTest, UserResponse

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
def is_session_valid(func, request):
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
def session_location_match(func, request):
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




