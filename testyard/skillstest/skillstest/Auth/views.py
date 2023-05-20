# Django specific imports...
from django.conf import settings

from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.core.context_processors import csrf
from django.views.generic import View
from django.http import HttpResponseBadRequest, HttpResponse , HttpResponseRedirect, QueryDict
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
#from django.utils import simplejson # Since django no longer ships simplejson as a part of it.
import simplejson
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
from passlib.hash import pbkdf2_sha256 # To create hash of passwords
# We will use that as our sessionid.

# Standard libraries...
import os, sys, re, time, datetime
import cPickle, urlparse
import decimal, math, base64
import requests, shutil

# Application specific libraries...
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege, EmailValidationKey
from skillstest.Tests.models import Topic, Subtopic, Evaluator, Test, UserTest, Challenge, UserResponse
from skillstest import settings as mysettings
from skillstest.errors import error_msg
import skillstest.utils as skillutils


def make_password(password):
    hash = pbkdf2_sha256.encrypt(password, rounds=200, salt_size=16)
    return hash


def authenticate(uname, passwd):
    try:
        user = User.objects.filter(displayname=uname)
        if pbkdf2_sha256.verify(passwd, user[0].password):  # Compare the hashes of the password
            return user[0]
        else:
            return None
    except:
        return None
    


def generatesessionid(username, csrftoken, userip, ts):
    hashstr = make_password(username + csrftoken + userip) + ts
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
            msg_color = 'FF0000'
            msg = skillutils.formatmessage(msg, msg_color)
        else:
            msg = ""
        # Display login form
        curdate = datetime.datetime.now()
        tmpl = get_template("authentication/login.html")
        c = {'curdate' : curdate, 'msg' : msg, 'register_url' : skillutils.gethosturl(request) + "/" + mysettings.REGISTER_URL, 'googleinfourl' : skillutils.gethosturl(request) + "/" + mysettings.GOOGLE_INFO_URL }
        inc_context = skillutils.includedtemplatevars("", request)
        for inc_key in inc_context.keys():
            c[inc_key] = inc_context[inc_key]
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
                # ... and redirect to landing page (which happens to be the profile page).
                response = HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.LOGIN_REDIRECT_URL)
                response.set_cookie('sessioncode', sesscode)
                response.set_cookie('usertype', userobj.usertype)
                return response
            else:
                message = error_msg('1003')
                return HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)
    else:
        message = error_msg('1001')
        return HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)


"""
Note: Even though we are accepting values for UserPrivilege, very limited privilege related info is being used right now.
This is because we have 3 different class of Users and these 3 classes of Users replace the logic that privileges implement.
The 3 classes of Users are:  creators, assessors (Evaluator) and assessees.
"""
@csrf_protect
@never_cache
def register(request):
    #privs = Privilege.objects.all()
    privileges = {}
    #for p in privs:
    #    privileges[p.privname] = p.privdesc
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
        (username, password, password2, email, firstname, middlename, lastname, mobilenum) = ("", "", "", "", "", "", "", "")
        tmpl = get_template("authentication/newuser.html")
        #c = {'curdate' : curdate, 'msg' : msg, 'login_url' : skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL, 'register_url' : skillutils.gethosturl(request) + "/" + mysettings.REGISTER_URL, 'privileges' : privileges, 'min_passwd_strength' : mysettings.MIN_ALLOWABLE_PASSWD_STRENGTH, }
        c = {'curdate' : curdate, 'msg' : msg, 'login_url' : skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL, 'hosturl' : skillutils.gethosturl(request),\
             'register_url' : skillutils.gethosturl(request) + "/" + mysettings.REGISTER_URL,\
             'min_passwd_strength' : mysettings.MIN_ALLOWABLE_PASSWD_STRENGTH, 'username' : username, 'password' : password, 'password2' : password2,\
                 'email' : email, 'firstname' : firstname, 'middlename' : middlename, 'lastname' : lastname, 'mobilenum' : mobilenum, \
             'availabilityURL' :  mysettings.availabilityURL, 'hosturl' : skillutils.gethosturl(request), 'profpicheight' : mysettings.PROFILE_PHOTO_HEIGHT, 'profpicwidth' : mysettings.PROFILE_PHOTO_WIDTH }
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
        profpic = ""
        #userprivilege = request.POST['userprivilege']
        csrftoken = request.POST['csrfmiddlewaretoken']
        message = ""
        # Validate the collected data...
        if password != password2:
            message = error_msg('1011')
        elif mysettings.MULTIPLE_WS_PATTERN.search(username):
            message =  error_msg('1012')
        elif not mysettings.EMAIL_PATTERN.search(email):
            message =  error_msg('1013')
        elif mobilenum != "" and not mysettings.PHONENUM_PATTERN.search(mobilenum):
            message = error_msg('1014')
        elif sex not in ('m', 'f', 'u'):
            message = error_msg('1015')
        elif usertype not in ('CORP', 'CONS', 'ACAD', 'CERT'):
            message = error_msg('1016')
        elif not mysettings.REALNAME_PATTERN.search(firstname) or not mysettings.REALNAME_PATTERN.search(lastname) or not mysettings.REALNAME_PATTERN.search(middlename):
            message = error_msg('1017')
        #elif userprivilege not in privileges:
        #    message = error_msg('1018')
        elif skillutils.check_password_strength(password) < mysettings.MIN_ALLOWABLE_PASSWD_STRENGTH:
            message = error_msg('1019')
        if request.FILES.has_key('profpic'):
            fpath, message, profpic = skillutils.handleuploadedfile(request.FILES['profpic'], mysettings.MEDIA_ROOT + os.path.sep + username + os.path.sep + "images")
            # User's images will be stored in "MEDIA_ROOT/<Username>/images/".
        if message != "" and mysettings.DEBUG:
            print message + "\n"
        if message != "":
            curdate = datetime.datetime.now()
            tmpl = get_template("authentication/newuser.html")
            c = {'curdate' : curdate, 'msg' : "<font color='#FF0000'>%s</font>"%message, 'login_url' : skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL,\
                 'register_url' : skillutils.gethosturl(request) + "/" + mysettings.REGISTER_URL, \
                 'min_passwd_strength' : mysettings.MIN_ALLOWABLE_PASSWD_STRENGTH, 'username' : username, 'password' : password, 'password2' : password2,\
                 'email' : email, 'firstname' : firstname, 'middlename' : middlename, 'lastname' : lastname, 'mobilenum' : mobilenum, \
                 'availabilityURL' :  mysettings.availabilityURL, 'hosturl' : skillutils.gethosturl(request), 'profpicheight' : mysettings.PROFILE_PHOTO_HEIGHT, 'profpicwidth' : mysettings.PROFILE_PHOTO_WIDTH }
            c.update(csrf(request))
            cxt = Context(c)
            registerhtml = tmpl.render(cxt)
            for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
                registerhtml = registerhtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
            return HttpResponse(registerhtml)
        else: # Create the user and redirect to the dashboard page with a status message.
            user = User()
            #usrpriv = UserPrivilege()
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
            user.userpic = profpic
            emailvalidkey = EmailValidationKey()
            emailvalidkey.email = email
            emailvalidkey.vkey = skillutils.generate_random_string()
            try:
                user.save() # New user record inserted now. 'joindate' added automatically.
                emailvalidkey.save()
            except:
                message = sys.exc_info()[1].__str__()
                tmpl = get_template("authentication/newuser.html")
                curdate = datetime.datetime.now()
                c = {'curdate' : curdate, 'msg' : "<font color='#FF0000'>%s</font>"%message, 'login_url' : skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL,\
                 'register_url' : skillutils.gethosturl(request) + "/" + mysettings.REGISTER_URL, \
                 'min_passwd_strength' : mysettings.MIN_ALLOWABLE_PASSWD_STRENGTH, 'username' : username, 'password' : password, 'password2' : password2,\
                 'email' : email, 'firstname' : firstname, 'middlename' : middlename, 'lastname' : lastname, 'mobilenum' : mobilenum, \
                'availabilityURL' :  mysettings.availabilityURL, 'hosturl' : skillutils.gethosturl(request), 'profpicheight' : mysettings.PROFILE_PHOTO_HEIGHT, 'profpicwidth' : mysettings.PROFILE_PHOTO_WIDTH }
                c.update(csrf(request))
                cxt = Context(c)
                reghtml = tmpl.render(cxt)
                return HttpResponse(reghtml)
            #usrpriv.user = user
            #usrpriv.privilege = userprivilege
            #usrpriv.status = True
            #usrpriv.save() # Associated user privilege saved.
            subject = """ TestYard Registration - Activate your account on TestYard by verifying your email. """
            message = """
                Dear %s,

                Thanks for creating your account on TestYard. In order to be able to login and use it, you need
                to verify this email address (which you have entered as an input during registration). You can
                do this by clicking on the hyperlink here: <a href='%s/%s?vkey=%s'>Verify My Account</a>. Once you have ver-
                ified your account, you would be able to use it.

                If you feel this email has been sent to you in error, please get back to us at the email address
                mentioned here: support@testyard.com

                Thanks and Regards,
                %s, CEO, TestYard.
                
            """%(user.displayname, skillutils.gethosturl(request), mysettings.ACCTACTIVATION_URL, emailvalidkey.vkey, mysettings.MAILSENDER)
            fromaddr = "register@testyard.com"
            skillutils.sendemail(user, subject, message, fromaddr)
            # Print a success message and ask user to validate email. The current screen is
            # only a providential state where the user appears to be logged in but has no right
            # to perform any action.
            message = "<font color='#0000FF'>Hello %s, welcome on board TestYard(&#8482;). We hope you will have a hassle-free association with us.<br /> \
            In case of any issues, please feel free to drop us (support@testyard.com) an email regarding the matter. Our 24x7 <br />\
            support center staff would only be too glad to help you out. Happy testing... </font>"%username
            tmpl = get_template("user/profile.html")
            curdate = datetime.datetime.now()
            c = {'curdate' : curdate, 'msg' : message, 'login_url' : skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL, 'csrftoken' : csrftoken}
            c.update(csrf(request))
            cxt = Context(c)
            profile = tmpl.render(cxt)
            for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
                profile = profile.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
            return HttpResponse(profile)
    else: # Process this as erroneous request
        message = error_msg('1004')
        if mysettings.DEBUG:
            print "Unhandled method call during registration.\n"
        return HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.REGISTER_URL + "?msg=%s"%message)



"""
Check if a username is available or not.
"""
def checkavailability(request):
    username = ""
    if request.GET.has_key('username'):
        username = request.GET['username']
    user = User.objects.filter(displayname=username)
    if user.__len__() > 0: # Not available
        return HttpResponse('0')
    else: # Available
        return HttpResponse('1')



"""
view to handle account activation. We would be getting a
GET query string of the form "vkey=<some-uuid-string>".
"""
def acctactivation(request):
    vkey = ""
    if request.GET.has_key('vkey'):
        vkey = request.GET['vkey']
    else:
        return HttpResponse("Invalid request")
    if vkey == "":
        return HttpResponse("Invalid request")
    allrecs = EmailValidationKey.objects.filter(vkey=vkey)
    if allrecs.__len__() == 0: # No entry found that matches the vkey.
        return HttpResponse("Invalid Request")
    # There should not be cases where we get multiple emails for same vkey.
    # If we get that, then that is a bug in the system.
    email = allrecs[0].email # We take the first value
    user = User.objects.filter(emailid=email)
    userobj = user[0]
    userobj.newuser = False # Should no longer be considered to be a new user.
    userobj.active = True # Activate account
    try:
        userobj.save() # Email is validated now.
        curdate = datetime.datetime.now()
        tmpl = get_template("authentication/activation.html")
        msg = """
        Your email address has been validated. Now you may use your TestYard.com account by logging into it.
        """
        c = {'curdate' : curdate, 'displayname' : userobj.displayname, 'msg' : msg, 'profile_image_tag' : skillutils.getprofileimgtag(request) }
        c.update(csrf(request))
        cxt = Context(c)
        activehtml = tmpl.render(cxt)
        return HttpResponse(activehtml)
    except:
        return HttpResponse("Email could not be validated - %s.\n"%sys.exc_info()[1].__str__())


# Methods for handling requests from mobile handsets and other devices that may be considered in future.
@csrf_exempt
@never_cache
def mobile_verifypassword(request):
    if request.method != "POST":
        message = "Error: %s"%error_msg('1004')
        return HttpResponse(message)
    if not request.POST.has_key('data'):
        return HttpResponse("")
    postdata = request.POST['data']
    print postdata
    keystring = "test"
    ivstring = "test"
    #decryptedPostdata = skillutils.des3Decrypt(postdata, keystring, ivstring)
    decodedPostdata = base64.b64decode(postdata)
    namevaluepairslist = decodedPostdata.split("&")
    argdict = {}
    for namevalue in namevaluepairslist:
        name, value = namevalue.split("=")
        argdict[name] = value
    username = ""
    if argdict.has_key('username'):
        username = argdict['username']
    else:
        return HttpResponse("")
    if argdict.has_key('password'):
        password = argdict['password']
    else:
        return HttpResponse("")
    if argdict.has_key('csrfmiddlewaretoken'):
        csrftoken = argdict['csrfmiddlewaretoken']
    else:
        return HttpResponse("")
    if mysettings.DEBUG:
        print "USERNAME = " + username
        print "PASSWORD = " + password
    userobj = authenticate(username, password)
    if not userobj:
        return HttpResponse("Error: %s"%error_msg('1002'))
    if userobj.active:
        sessobj = Session()
        clientip = request.META['REMOTE_ADDR']
        timestamp = int(time.time())
        sesscode = generatesessionid(username, csrftoken, clientip, timestamp.__str__())
        sessobj.sessioncode = sesscode
        sessobj.user = userobj
        sessobj.endtime = None
        sessobj.sourceip = clientip
        sessobj.useragent = request.META['HTTP_USER_AGENT']
        sessobj.save()
        response = HttpResponse("sesscode=" + sesscode)
        response.set_cookie('sessioncode', sesscode)
        response.set_cookie('usertype', userobj.usertype)
        if mysettings.DEBUG:
            print "SESSION CODE = " + sesscode
        return response
    else:
        message = "Error: %s"%error_msg('1003')
        return HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)


@csrf_protect
def storegoogleuserinfo(request):
    if request.method != "POST":
        message = "Error: %s"%error_msg('1004')
        return HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)
    # Get all the post data
    firstname, lastname, username, gender, emailid, profpicurl = "", "", "", "", "", ""
    password = mysettings.GOOGLE_SIGNIN_DEFAULT_PASSWORD # This is a special string to be used as password for google authentication users
    if request.POST.has_key('firstname'):
        firstname = request.POST['firstname']
    if request.POST.has_key('lastname'):
        lastname = request.POST['lastname']
    if request.POST.has_key('emailid'):
        emailid = request.POST['emailid']
    if request.POST.has_key('gender'):
        gender = request.POST['gender']
    if request.POST.has_key('googleid'):
        username = request.POST['googleid']
    if request.POST.has_key('profpic'):
        profpicurl = request.POST['profpic']
    sex = "U"
    if gender == "male":
        sex = "M"
    elif gender == "female":
        sex = "F"
    userobj = None
    try:
        userobj = User.objects.get(emailid=emailid)
    except:
        pass
    if userobj is None: # We need to create this user - this is the first time
        userobj = User()
        username = username.replace("+", " ")
        userobj.displayname = username
        userobj.emailid = emailid
        userobj.password = password
        userobj.sex = sex
        userobj.firstname = firstname
        userobj.middlename = ""
        userobj.lastname = lastname
        userobj.usertype = 'CORP'
        userobj.active = True
        userobj.istest = False
        userobj.mobileno = ""
        try:
            r = requests.get(profpicurl, stream=True) # Try to get the file, if possible.
            if r.status_code == 200:
                imgpath = mysettings.PROJECT_ROOT + os.path.sep + "userdata" + os.path.sep + username + os.path.sep + "images"
                imgfile = imgpath + os.path.sep + "profilepic.jpg" # If it is not a jpeg file, suck!
                skillutils.mkdir_p(imgpath)
                with open(imgfile, 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)
            userobj.userpic = "profilepic.jpg"
        except:
            userobj.userpic = ""
        userobj.newuser = False # Google users will not need to have verified accounts.
        try:
            userobj.save()
        except:
            message = "Couldn't save user information for use with TestYard. Please Register on this website to use our services."
            response = HttpResponse(message)
            return response
    # Now, log the user in.
    authuserobj = authenticate(username, password)
    if not authuserobj: # Incorrect password - return user to login screen with an appropriate message.
        message = error_msg('1002')
        return HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)
    else: # user will be logged in after checking the 'active' field
        if authuserobj.active:
            sessobj = Session()
            clientip = request.META['REMOTE_ADDR']
            timestamp = int(time.time())
            # timestamp will be a 10 digit string.
            sesscode = generatesessionid(username, csrfmiddlewaretoken, clientip, timestamp.__str__())
            sessobj.sessioncode = sesscode
            sessobj.user = authuserobj
            # sessobj.starttime should get populated on its own when we save this session object.
            sessobj.endtime = None
            sessobj.sourceip = clientip
            if authuserobj.istest: # This session is being performed by a test user, so this must be a test session.
                sessobj.istest = True
            elif mysettings.TEST_RUN: # This is a test run as mysettings.TEST_RUN is set to True
                sessobj.istest = True
            else:
                sessobj.istest = False
            sessobj.useragent = request.META['HTTP_USER_AGENT']
            # Now save the session...
            sessobj.save()
            # ... and redirect to landing page (which happens to be the profile page).
            response = HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.LOGIN_REDIRECT_URL)
            response.set_cookie('sessioncode', sesscode)
            response.set_cookie('usertype', authuserobj.usertype)
        else: # User is not active
            message = "The user is not active."
            return HttpResponseRedirect(skillutils.gethosturl(request) + "/" + mysettings.LOGIN_URL + "?msg=" + message)
    return response
    

