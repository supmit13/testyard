# Django specific imports...
from django.conf import settings

from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.core.context_processors import csrf
from django.views.generic import View
from django.http import HttpResponseBadRequest, HttpResponse , HttpResponseRedirect, QueryDict
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.template.response import TemplateResponse
from django.utils.http import base36_to_int, is_safe_url
from django.utils.translation import ugettext as _
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.template import Template, Context
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import get_current_site
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth.hashers import make_password # We will use this to generate a hash from csrftoken and user Id.
# We will use that as our sessionid.

# Standard libraries...
import os, sys, re, time, datetime
import cPickle, urlparse
import decimal, math

# Application specific libraries...
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
from skillstest import settings as mysettings
from skillstest.errors import error_msg
import skillstest.utils as skillutils



def authenticate(uname, passwd):
    try:
        user = User.objects.get(displayname=uname)
        if user.password == make_password(passwd):  # Compare the hashes of the password
            return user
        else:
            return None
    except:
        return None


def generatesessionid(username, csrftoken, userip, ts):
    hashstr = make_password(username + csrftoken + userip + ts)
    return hashstr


@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request):
    if request.method == "GET":
        msg = None
        if request.META.has_key('QUERY_STRING'):
            msg = request.META.get('QUERY_STRING', '')
        if msg is not None and msg != '':
            var, msg = msg.split("=")
            for hexkey in mysettings.HEXCODE_CHAR_MAP.keys():
                msg = msg.replace(hexkey, mysettings.HEXCODE_CHAR_MAP[hexkey])
            msg = "<p style=\"color:#FF0000;font-size:14;font-face:'helvetica neue';font-style:bold;\">%s</p>"%msg
        else:
            msg = ""
        # Display login form
        curdate = datetime.datetime.now()
        tmpl = get_template("authentication/login.html")
        c = {'curdate' : curdate, 'msg' : msg, 'register_url' : skillutils.gethosturl(request) + "/" + mysettings.REGISTER_URL }
        c.update(csrf(request))
        cxt = Context(c)
        loginhtml = tmpl.render(cxt)
        for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
            loginhtml = loginhtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
        return HttpResponse(loginhtml)
    elif request.method == "POST":
        username = request.POST.get('username') or ""
        password = request.POST.get('password') or ""
        keeploggedin = request.POST.get('keepmeloggedin') or 0
        csrfmiddlewaretoken = request.POST.get('csrfmiddlewaretoken', "")
        userobj = authenticate(username, password)
        if not userobj: # Incorrect password - return user to login screen with an appropriate message.
            message = error_msg('1002')
            return HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)
        else: # user will be logged in after checking the 'active' field
            if userobj.active:
                sessobj = Session()
                clientip = request.META['REMOTE_ADDR']
                timestamp = int(time.time())
                # timestamp will be a 10 digit string.
                sesscode = generatesessionid(username, csrfmiddlewaretoken, clientip, timestamp.__str__())
                request.COOKIES['sessioncode'] = sesscode
                request.COOKIES['usertype'] = userobj.usertype
                sessobj.sessioncode = sesscode
                sessobj.user = userobj
                # sessobj.starttime should get populated on its own when we save this session object.
                sessobj.endtime = None
                sessobj.sourceip = clientip
                if userobj.istest: # This session is being performed by a test user, so this must be a test session.
                    sessobj.istest = True
                elif mysettings.TEST_RUN: # This is a test run as mysettings.TEST_RUN is set to True
                    sessobj.istest = True
                else:
                    sessobj.istest = False
                sessobj.useragent = request.META['HTTP_USER_AGENT']
                # Now save the session...
                sessobj.save()
                # ... and redirect to landing page.
                return HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.LOGIN_REDIRECT_URL)
            else:
                message = error_msg('1003')
                return HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)
    else:
        message = error_msg('1001')
        return HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)



@csrf_protect
@never_cache
def register(request):
    privs = Privilege.objects.all()
    privileges = {}
    for p in privs:
        privileges[p.privname] = p.privdesc
    if request.method == "GET": # display the registration form
        msg = ''
        if request.META.has_key('QUERY_STRING'):
            msg = request.META.get('QUERY_STRING', '')
        if msg is not None and msg != '':
            var, msg = msg.split("=")
            for hexkey in mysettings.HEXCODE_CHAR_MAP.keys():
                msg = msg.replace(hexkey, mysettings.HEXCODE_CHAR_MAP[hexkey])
            msg = "<p style=\"color:#FF0000;font-size:14;font-face:'helvetica neue';font-style:bold;\">%s</p>"%msg
        else:
            msg = ""
        curdate = datetime.datetime.now()
        tmpl = get_template("authentication/newuser.html")
        c = {'curdate' : curdate, 'msg' : msg, 'login_url' : skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL, 'register_url' : skillutils.gethosturl(request) + "/" + mysettings.REGISTER_URL, 'privileges' : privileges, 'min_passwd_strength' : mysettings.MIN_ALLOWABLE_PASSWD_STRENGTH, }
        c.update(csrf(request))
        cxt = Context(c)
        registerhtml = tmpl.render(cxt)
        for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
            registerhtml = registerhtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
        return HttpResponse(registerhtml)
    elif request.method == "POST": # Process registration form data
        username = request.POST['username']
        password = request.POST['password']
        password2 = request.POST['password2']
        email = request.POST['email']
        firstname = request.POST['firstname']
        middlename = request.POST['middlename']
        lastname = request.POST['lastname']
        sex = request.POST['sex']
        usertype = request.POST['usertype']
        mobilenum = request.POST['mobilenum']
        userprivilege = request.POST['userprivilege']
        csrftoken = request.POST['csrfmiddlewaretoken']
        message = ""
        # Validate the collected data...
        if password != password2:
            message = error_msg('1011')
        elif mysettings.MULTIPLE_WS_PATTERN.search(username):
            message =  error_msg('1012')
        elif mysettings.EMAIL_PATTERN.search(email):
            message =  error_msg('1013')
        elif mobilenum != "" and mysettings.PHONENUM_PATTERN.search(mobilenum):
            message = error_msg('1014')
        elif sex not in ('m', 'f', 'u'):
            message = error_msg('1015')
        elif usertype not in ('CORP', 'CONS', 'ACAD', 'CERT'):
            message = error_msg('1016')
        elif mysettings.REALNAME_PATTERN.search(firstname) or mysettings.REALNAME_PATTERN.search(lastname) or mysettings.REALNAME_PATTERN.search(middlename):
            message = error_msg('1017')
        elif userprivilege not in privileges:
            message = error_msg('1018')
        elif skillutils.check_password_strength(password) < mysettings.MIN_ALLOWABLE_PASSWD_STRENGTH:
            message = error_msg('1019')
        fpath, message = skillutils.handleuploadedfile(request.FILES['profpic'], mysettings.MEDIA_ROOT + os.path.sep + username + os.path.sep + "images")
        # User's images will be stored in "MEDIA_ROOT/<Username>/images/".
        if message != "" and mysettings.DEBUG:
            print message + "\n"
        if message != "":
            return HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.REGISTER_URL + "?msg=%s"%message)
        if message != "" and mysettings.DEBUG:
            print message + "\n"
        if message != "":
            return HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.REGISTER_URL + "?msg=%s"%message)
        else: # Create the user and redirect to the dashboard page with a status message.
            user = User()
            usrpriv = UserPrivilege()
            user.firstname = firstname
            user.middlename = middlename
            user.lastname = lastname
            user.displayname = username
            user.emailid = email
            user.password = make_password(password) # Store password as a hash.
            user.mobileno = mobilenum
            user.sex = sex
            user.usertype = usertype
            user.istest = False
            user.active = False # Will become active when user verifies email Id.
            user.userpic = ""
            user.save() # New user record inserted now. 'joindate' added automatically.
            usrpriv.user = user
            usrpriv.privilege = userprivilege
            usrpriv.status = True
            usrpriv.save() # Associated user privilege saved.
            skillutils.sendemail(user)
            # Print a success message and ask user to validate email. The current screen is
            # only a providential state where the user seems to be logged in but has no right
            # to perform any action.
            message = "Hello %s, welcome on board TestYard(&#8482;). We hope you will have a smooth association with us.<br /> \
            In case of any issues, please feel free to drop us (support@testyard.com) an email regarding the matter. Our 24x7 <br />\
            support center staff would only be too glad to help you out. Happy testing... "%username
            tmpl = get_template("user/dashboard.html")
            c = {'curdate' : curdate, 'msg' : message, 'login_url' : skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL, 'csrftoken' : csrftoken}
            c.update(csrf(request))
            cxt = Context(c)
            dashboard = tmpl.render(cxt)
            return HttpResponse(dashboard)
    else: # Process this as erroneous request
        message = error_msg('1004')
        if mysettings.DEBUG:
            print "Unhandled method call during registration.\n"
        return HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.REGISTER_URL + "?msg=%s"%message)


