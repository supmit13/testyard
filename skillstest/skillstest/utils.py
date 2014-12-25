import os, sys, re, time
import tempfile, shutil

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.backends.db import SessionStore
from django.template import Template, Context

# Application specific libraries...
from skillstest.Auth.models import User, Session
from skillstest import settings as mysettings
from skillstest.errors import error_msg

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
    timestring = sesscode[-10:]
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
        return HttpResponseRedirect(gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)
    else: # Return the request
        return request



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
    

