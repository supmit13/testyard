from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.core.context_processors import csrf
from django.views.generic import View
from django.http import HttpResponseBadRequest, HttpResponse , HttpResponseRedirect, HttpRequest
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

# Standard libraries...
import os, sys, re, time, datetime
import cPickle
import decimal, math
import urllib, urllib2
import simplejson as json
import socket

# Application specific libraries...
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
from skillstest.Subscription.models import Plan, UserPlan, Transaction
from skillstest.Tests.models import Topic, Subtopic, Evaluator, Test, UserTest, Challenge, UserResponse, WouldbeUsers
from skillstest.Network.models import Connection, ConnectionInvitation, GroupMember, Group, Post, OwnerBankAccount, GroupJoinRequest, GentleReminder
from skillstest import settings as mysettings
from skillstest.errors import error_msg
import skillstest.utils as skillutils
from skillstest.Tests.views import sendtestinvitations


def get_network_template_vars(userobj):
    templatevars = {}
    templatevars['creategroupurl'] = mysettings.CREATE_NETWORK_GROUP_URL
    templatevars['checkgrpnameavailabilityurl'] = mysettings.CHECK_GRPNAME_AVAIL_URL
    templatevars['searchgroupurl'] = mysettings.SEARCH_GROUP_URL
    templatevars['getgroupinfouri'] = mysettings.GET_GROUP_INFO_URI
    templatevars['showtestinfourl'] = mysettings.SHOW_TEST_INFO_URL
    templatevars['joinrequesturl'] = mysettings.SEND_JOIN_REQUEST_URL
    templatevars['gentlereminderurl'] = mysettings.SEND_GENTLE_REMINDER_URL
    templatevars['getgroupdataurl'] = mysettings.GET_GROUP_DATA_URL
    templatevars['grpimguploadurl'] = mysettings.GROUP_IMG_UPLOAD_URL + '?groupname='
    templatevars['savegrpdataurl'] = mysettings.SAVE_GROUP_DATA_URL
    templatevars['getpaymentgwurl'] = mysettings.PAYMENT_GW_URL
    validfrom = datetime.datetime.now()
    validfromstr = skillutils.pythontomysqldatetime2(str(validfrom))
    datepart, timepart = validfromstr.split(" ")
    datepartslist = datepart.split("-")
    templatevars['validfrom'] = datepartslist[2] + "-" + datepartslist[1] + "-" + datepartslist[0] + " " + timepart
    alltopics = list(mysettings.TEST_TOPICS)
    extratopicsqset = Topic.objects.filter(user=userobj)
    for topic in extratopicsqset:
        alltopics.append(topic.topicname)
    templatevars['alltopics'] = alltopics
    grouptypes = {}
    for grptype in mysettings.GROUP_TYPES_DICT.keys():
        grouptypes[grptype] = mysettings.GROUP_TYPES_DICT[grptype]
    templatevars['grouptypes'] = grouptypes
    availablebanks = {}
    for bankcode in mysettings.BANKS_DICT.keys():
        availablebanks[bankcode] = mysettings.BANKS_DICT[bankcode]
    templatevars['availablebanks'] = availablebanks
    alltestsqset = Test.objects.filter(creator=userobj)
    alltests = {}
    for test in alltestsqset:
        alltests[test.id] = test.testname
    templatevars['alltests'] = alltests
    allcurrencies = []
    for currency in mysettings.SUPPORTED_CURRENCIES:
        allcurrencies.append(currency)
    templatevars['allcurrencies'] = allcurrencies
    templatevars['defaultcurrency'] = mysettings.DEFAULT_CURRENCY
    return templatevars


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def network(request):
    message = ''
    if request.method != "GET": # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.DASHBOARD_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    # Display contacts and groups associated with the user.
    contactsqset = Connection.objects.filter(focususer=userobj, deleted=False, blocked=False)
    groupmembersqset = GroupMember.objects.filter(member=userobj, status=True, removed=False, blocked=False)
    contacts = []
    groups = []
    for contact in contactsqset:
        contactlink = "<a href='#/' onClick='javascript:showconnectionsprofile(&quot;%s&quot;);'>%s</a>"%(contact.id, contact.displayname)
        contacts.append(contactlink)
    for groupmember in groupmembersqset:
        grouplink = "<a href='#/' onClick='javascript:managegroup(&quot;%s&quot;, &quot;%s&quot;, &quot;%s&quot;);'>%s</a>"%(groupmember.member.displayname, groupmember.group.groupname, groupmember.group.currency, groupmember.group.groupname)
        groups.append(grouplink)
    alltopicsdict = {}
    for topic in mysettings.TEST_TOPICS:
        topicunderscored = topic.replace(" ", "_")
        alltopicsdict[topicunderscored] = topic
    dyntopicsqset = Topic.objects.filter(user=userobj)
    for topicobj in dyntopicsqset:
        topicunderscored = topicobj.topicname.replace(" ", "_")
        alltopicsdict[topicunderscored] = topicobj.topicname
    contextdict = { 'displayname' : userobj.displayname, 'msg' : '<b><i>it is social networking time!</i></b>', 'connections' : contacts, 'groups' : groups, 'topics' : alltopicsdict }
    contextdict['image_height'] = mysettings.PROFILE_PHOTO_HEIGHT
    contextdict['image_width'] = mysettings.PROFILE_PHOTO_WIDTH
    inc_context = skillutils.includedtemplatevars("Network", request) # Since this is the 'Network' page for the user.
    for inc_key in inc_context.keys():
        contextdict[inc_key] = inc_context[inc_key]
    templatevars = get_network_template_vars(userobj)
    for tkey in templatevars.keys():
        contextdict[tkey] = templatevars[tkey]
    contextdict['profile_image_tag'] = skillutils.getprofileimgtag(request)
    contextdict['baseurl'] = skillutils.gethosturl(request)
    contextdict['selfemailid'] = userobj.emailid
    # Now create and render the template here
    tmpl = get_template("network/network.html")
    contextdict.update(csrf(request))
    cxt = Context(contextdict)
    managenetworkhtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        managenetworkhtml = managenetworkhtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(managenetworkhtml)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def creategroup(request):
    message = ''
    if request.method != "POST": # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.DASHBOARD_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    groupname, groupdescription, grouptopic, ispaid, isactive, allowentry, cleartest, grouptype, maxmemberscount, bankname, branchname, ifsccode, acctownername, acctnumber, entryfee, tagline, currency, require_owner_perms =  ("" for i in range(0,18))
    if request.POST.has_key('groupname'):
        groupname = urllib.unquote(request.POST['groupname']).decode('utf8')
    if request.POST.has_key('groupdescription'):
        groupdescription = urllib.unquote(request.POST['groupdescription']).decode('utf8')
    if request.POST.has_key('tagline'):
        tagline = urllib.unquote(request.POST['tagline']).decode('utf8')
    if request.POST.has_key('grouptopic'):
        grouptopic = request.POST['grouptopic']
    if request.POST.has_key('maxmemberscount'):
        maxmemberscount = request.POST['maxmemberscount']
    if request.POST.has_key('grouptype'):
        grouptype = request.POST['grouptype']
    if request.POST.has_key('ispaid'):
        ispaid = int(request.POST['ispaid'])
    if request.POST.has_key('require_owner_perms'):
        require_owner_perms = request.POST['require_owner_perms']
    testobj = None
    try:
    	if ispaid == 1:
	    bankname = request.POST['bankname']
	    branchname = request.POST['branchname']
	    ifsccode = request.POST['ifsccode']
	    acctownername = request.POST['acctownername']
	    acctnumber = request.POST['acctnumber']
            entryfee = request.POST['entryfee']
            currency = request.POST['currency']
        else:
            ispaid = False
        if request.POST.has_key('isactive') and request.POST['isactive'] == '1':
            isactive = True
        else:
            isactive = False
        if request.POST.has_key('allowentry') and request.POST['allowentry'] == '1':
            allowentry = True
        else:
            allowentry = False
    except:
        message = "Could not create group: %s"%sys.exc_info()[1].__str__()
        response = HttpResponse(message)
        return response
    # If we survived till here, we can safely create a group and its owner groupmember object.
    if not isgroupnameunique(groupname):
        message = "Group name added is not unique. Please rectify and try to create the group again. Group names are case insensitive."
        response = HttpResponse(message)
        return response
    grpobj = Group()
    grpmember = GroupMember()
    grpobj.owner = userobj
    grpobj.groupname = groupname
    grpobj.description = groupdescription
    grpobj.tagline = tagline
    grpobj.memberscount = 1
    grpobj.maxmemberslimit = int(maxmemberscount)
    grpobj.status = isactive
    grpobj.grouptype = grouptype
    grpobj.basedontopic = grouptopic
    grpobj.allowentry = allowentry
    grpobj.ispaid = ispaid
    grpobj.adminremarks = "admin"
    grpobj.stars = 0
    if not entryfee or entryfee == "":
        entryfee = 0.0
    grpobj.entryfee = float(entryfee)
    grpobj.currency = currency
    grpmember.member = userobj
    grpmember.status = True
    grpmember.removed = False
    grpmember.blocked = False
    if require_owner_perms == '1':
        grpmember.require_owner_permission = True
    else:
        grpmember.require_owner_permission = False
    try:
        grpobj.save()
        grpmember.group = grpobj
        grpmember.save()
    except:
        print "Error: %s"%sys.exc_info()[1].__str__()
        message = "Error occurred: %s"%sys.exc_info()[1].__str__()
        response = HttpResponse(message)
        return response
    if ispaid:
        ownerbankacctobj = OwnerBankAccount()
        ownerbankacctobj.groupowner = userobj
        ownerbankacctobj.group = grpobj
        ownerbankacctobj.bankname = bankname
        ownerbankacctobj.bankbranch = branchname
        ownerbankacctobj.accountnumber = acctnumber
        ownerbankacctobj.ifsccode = ifsccode
        ownerbankacctobj.accountownername = acctownername
        ownerbankacctobj.require_owner_permission = require_owner_perms
        try:
            ownerbankacctobj.save()
        except:
            message = "Error occurred: %s"%sys.exc_info()[1].__str__()
            response = HttpResponse(message)
            return response
    # If we have reached here then we may have been able to handle all
    message = "Group created successfully."
    response = HttpResponse(message)
    return response


def isgroupnameunique(grpname):
    grpqsets = Group.objects.filter(groupname=grpname) 
    # Django is frustrating at times like this. I want a case-sensitive search and fucking django doesn't work that way. 
    # No way to say "select * from sometable where BINARY somefield=somevalue".
    if grpqsets.__len__() > 0:
        return False
    return True


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def checkgrpnameavailability(request):
    message = ''
    if request.method != "POST": # Illegal bad request...
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.DASHBOARD_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    grpname = ""
    if request.POST.has_key('groupname'):
        grpname = request.POST['groupname']
    else:
        message = "<font color='#AA0000' size=-2>No groupname received.</font>"
        response = HttpResponse(message)
        return response
    if not isgroupnameunique(grpname):
        message = "<font color='#AA0000' size=-2>Name is not available</font>"
    else:
        message = "<font color='#0000AA' size=-2>Available</font>"
    response = HttpResponse(message)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def searchgroups(request):
    message = ''
    if request.method != "POST": # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.DASHBOARD_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    grpkeyword = ""
    selectedtopics = []
    if request.POST.has_key('grpkeyword'):
        grpkeyword = request.POST['grpkeyword'];
    querystring = request.body
    querystringparts = querystring.split("&")
    for querypart in querystringparts:
        k,v = querypart.split("=")
        if k == 'grpkeyword' or k == 'csrfmiddlewaretoken':
            continue
        elif k == 'topic':
            v = v.replace("_", " ")
            selectedtopics.append(v)
    # Note: the keyword may be a part of group's name, description or tagline.
    results = []
    groupsqset = list(Group.objects.filter(groupname__contains=grpkeyword, description__contains=grpkeyword))
    #groupsqset.append(Group.objects.filter(tagline__contains=grpkeyword))
    #groupsqset2 = list(Group.objects.filter())
    #for grp in groupsqset2:
    #    groupsqset.append(grp)
    for grpobj in groupsqset:
        for topicname in selectedtopics:
            topicname = topicname.replace("%20", " ")
            if grpobj.basedontopic == topicname:
                d = { 'groupname' : grpobj.groupname, 'tagline' : grpobj.tagline, 'description' : grpobj.description, 'memberscount' : grpobj.memberscount, 'membername' : userobj.displayname }
                results.append(d)
                break
    message = json.dumps(results)
    response = HttpResponse(message)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def getgroupinfo(request):
    message = ''
    if request.method != "POST": # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.DASHBOARD_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    grpname, membername, csrftoken = "", "", ""
    if request.POST.has_key('groupname'):
        grpname = request.POST['groupname']
    if request.POST.has_key('membername'):
        membername = request.POST['membername'] # this should be userobj.displayname value.
    if request.POST.has_key('csrfmiddlewaretoken'):
        csrftoken = request.POST['csrfmiddlewaretoken']
    groupqueryset = Group.objects.filter(groupname=grpname)
    if not groupqueryset or groupqueryset.__len__() == 0:
        message = error_msg('1084')%(grpname)
        response = HttpResponse(message)
        return response
    groupobj = groupqueryset[0]
    grpdict = {}
    if groupobj.status:
        grpdict['groupid'] = groupobj.id
        grpdict['name'] = groupobj.groupname
        grpdict['tagline'] = groupobj.tagline
        grpdict['description'] = groupobj.description
        grpdict['memberscount'] = groupobj.memberscount
        grpdict['grouptype'] = groupobj.grouptype
        createdate = groupobj.creationdate
        createdate_serializable = ""
        if createdate:
            yyyy, mm, dd = str(createdate.year), str(createdate.month), str(createdate.day)
            hh, minute, ss = str(createdate.hour), str(createdate.minute), str(createdate.second)
            if mm.__len__() < 2:
                mm = '0' + mm
            if dd.__len__() < 2:
                dd = '0' + dd
            if hh.__len__() < 2:
                hh = '0' + hh
            if minute.__len__() < 2:
                minute = '0' + minute
            if ss.__len__() < 2:
                ss = '0' + ss
            createdate_serializable = yyyy + "-" + mm + "-" + dd + " " + hh + ":" + minute + ":" + ss
        grpdict['creationdate'] = createdate_serializable
        grpdict['allowentry'] = groupobj.allowentry
        grpdict['topic'] = groupobj.basedontopic
        #grpdict['groupimagefile'] = groupobj.groupimagefile
        grpdict['stars'] = groupobj.stars
        grpdict['ispaid'] = groupobj.ispaid
        grpdict['entryfee'] = groupobj.entryfee
        grpdict['currency'] = groupobj.currency
        grpdict['adminremarks'] = groupobj.adminremarks
        grpdict['require_owner_perms'] = groupobj.require_owner_permission
        if groupobj.groupimagefile:
            grpdict['groupimagefile'] = "media/" + userobj.displayname + "/groups/" + groupobj.groupname + "/" + groupobj.groupimagefile
        else:
            grpdict['groupimagefile'] = ""
        grpdict['owner'] = groupobj.owner.displayname
        grpdict['posts'] = []
        grouppostslist = grpdict['posts']
        postqueryset = Post.objects.filter(posttargettype='group', posttargetgroup=groupobj, scope='public', deleted=False, hidden=False)
        postctr=0
        for postobj in postqueryset:
            postdict = {}
            postdict['content'] = postobj.postcontent
            postdict['poster_name'] = postobj.poster.displayname
            postdict['imagefile'] = postobj.imagefile
            postdict['videofile'] = postobj.videofile
            postdict['stars'] = postobj.stars
            grouppostslist.append(postdict)
        grpdict['posts'] = grouppostslist
        # At max only one of the following 4 variables will have a value of '1'.
        grpdict['alreadyrequested'] = 0
        grpdict['alreadyrefused'] = 0
        grpdict['alreadyallowed'] = 0
        grpdict['alreadyignored'] = 0
        # Check if the logged in user has already requested to be allowed in the group
        grpjoinreqqset = GroupJoinRequest.objects.filter(group=groupobj, user=userobj, outcome='open', active=True)
        if grpjoinreqqset.__len__() > 0:
            grpdict['alreadyrequested'] = 1
        grprefuseqset = GroupJoinRequest.objects.filter(group=groupobj, user=userobj, outcome='refuse')
        if grprefuseqset.__len__() > 0:
            grpdict['alreadyrefused'] = 1
        grpallowedqset = GroupJoinRequest.objects.filter(group=groupobj, user=userobj, outcome='accept')
        if grpallowedqset.__len__() > 0:
            grpdict['alreadyallowed'] = 1
        grpignoredqset = GroupJoinRequest.objects.filter(group=groupobj, user=userobj, outcome='close')
        if grpignoredqset.__len__() > 0:
            grpdict['alreadyignored'] = 1
    try:
        groupcontent = json.dumps(grpdict) # serialize json
    except:
        print "Error: %s"%sys.exc_info()[1].__str__()
    response = HttpResponse(groupcontent)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def handlejoinrequest(request):
    message = ''
    if request.method != "POST": # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.DASHBOARD_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    groupid = None
    allowentryflag = False
    allowinvitationflag = False
    allowownerintimation = False
    blockflag = False
    if request.POST.has_key('groupid'):
        groupid = request.POST['groupid']
    else:
        message = error_msg('1085')
        response = HttpResponse(message)
        return response
    require_owner_perms = False
    #if request.POST.has_key('require_owner_perms') and request.POST['require_owner_perms'] == '1':
    #    require_owner_perms = True
    groupqset = Group.objects.filter(id=groupid)
    if groupqset.__len__() == 0:
        message = error_msg('1086')
        response = HttpResponse(message)
        return response
    groupobj = groupqset[0]
    joinrequest = GroupJoinRequest()
    joinrequest.user = userobj
    joinrequest.group = groupobj
    require_owner_perms = groupobj.require_owner_permission
    if groupobj.ispaid:
        joinrequest.outcome = 'open'
        joinrequest.active = True
        joinrequest.reason += "Paid user."
        allowinvitationflag = True
        grpmember = GroupMember()
        grpmember.member = userobj
        grpmember.group = groupobj
        grpmember.status = False # Make status True once payment is processed
        grpmember.removed = False
        grpmember.blocked = False
        # Handle payment through payment gateway 
    else: # Vanilla flavoured group - no payment to make.
        if require_owner_perms:
            joinrequest.outcome = 'hold'
            joinrequest.active = True
            joinrequest.reason += "require owner perms" 
            # The group owner will be presented with a page listing all join requests whose  
            # 'outcome' is 'hold' and 'reason' is 'require owner perms'.
            allowinvitationflag = True
            try:
                joinrequest.save()
                message = "A message bearing your request to join the group has been sent to the owner of the group. You will be added as soon as the owner approves your request."
            except:
                message = "Could not save the join request: %s"%sys.exc_info()[1].__str__()
        else:
            joinrequest.outcome = 'close'
            joinrequest.active = False
            joinrequest.reason += ""
            
            grpmember = GroupMember()
            grpmember.member = userobj
            grpmember.group = groupobj
            grpmember.status = True
            grpmember.removed = False
            grpmember.blocked = False
            allowinvitationflag = False
            try:
                joinrequest.save()
            except:
                message = "Could not save the join request: %s"%sys.exc_info()[1].__str__()
                response = HttpResponse(message)
                return response
            try:
                grpmember.save()
                message = "Join request handled successfully."
            except:
                message = error_msg('1097')%(sys.exc_info()[1].__str__())
    response = HttpResponse(message)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def sendgentlereminder(request):
    message = ''
    if request.method != "POST": # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.DASHBOARD_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    groupid = None
    if request.POST.has_key('groupid'):
        groupid = request.POST['groupid']
    else:
        message = error_msg('1085')
        response = HttpResponse(message)
        return response
    groupqset = Group.objects.filter(id=groupid)
    if groupqset.__len__() == 0:
        message = error_msg('1086')
        response = HttpResponse(message)
        return response
    groupobj = groupqset[0]
    grpjoinqset = GroupJoinRequest.objects.filter(group=groupobj, user=userobj)
    grpjoinobj = None
    if grpjoinqset.__len__() > 0:
        grpjoinobj = grpjoinqset[0]
    reminderflag = True
    if grpjoinobj is not None:
        gm = GentleReminder()
        gm.grpjoinrequest = grpjoinobj
        try:
            gm.save()
            message = "Success: Added gentle reminder in GentleReminder"
            emailsubject = "Gentle Reminder - Please add %s in group '%s'"%(userobj.displayname, groupobj.groupname)
            emailmessage = """
		Hi,
		
		This is a gentle reminder to add me in the group named '%s'."""%groupobj.groupname
	    emailmessage += """I have sent a request to you to join the group '%s'. Could you please allow me into the group so that I
                may access its resources and participate in all conversations.
                """%(groupobj.groupname)
	    emailmessage += """Thanks,
		%s
            """%(userobj.displayname)

	    skillutils.sendemail(groupobj.owner, emailsubject, emailmessage, userobj.emailid)
            response = HttpResponse(message)
            return response
        except:
            message = "Could not save record in GentleReminder. Error: %s"%sys.exc_info()[1].__str__()
            response = HttpResponse(message)
            return response
    else:
        message = "Error: Could not find matching record in GroupJoinRequest"
        response = HttpResponse(message)
        return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def getgroupdata(request):
    message = ''
    if request.method != "POST": # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.DASHBOARD_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode) # 'sessionobj' is a QuerySet object...
    userobj = sessionobj[0].user
    groupmembername, groupname = None, None
    if request.POST.has_key('membername'):
        groupmembername = request.POST['membername']
    if request.POST.has_key('groupname'):
        groupname = request.POST['groupname']
    if not groupmembername or not groupname: # if either of the variables is None, we will set a message and return
        message = error_msg('1087')
        response = HttpResponse(message)
        return response
    # All is well if we are here... extract data from Network_group
    grpobj = None
    grpqset = None
    try:
        grpqset = Group.objects.filter(groupname=groupname).filter(owner=userobj)
    except:
        print "Error finding the requested group: %s"%(sys.exc_info()[1].__str__())
        message = error_msg('1089')
        response = HttpResponse(message)
    if not grpqset or grpqset.__len__() == 0:
        message = error_msg('1088')
        response = HttpResponse(message)
        return response
    grpobj = grpqset[0]
    contextdict = {}
    contextdict['groupname'] = grpobj.groupname
    contextdict['tagline'] = grpobj.tagline
    contextdict['description'] = grpobj.description
    contextdict['ownedby'] = grpobj.owner.firstname + " " + grpobj.owner.middlename + " " + grpobj.owner.lastname + " (" + grpobj.owner.displayname + ") "
    if grpobj.groupimagefile is not None:
        contextdict['groupimagefile'] = grpobj.groupimagefile
    else:
        contextdict['groupimagefile'] = "static/images/nopic.png"
    contextdict['basedontopic'] = grpobj.basedontopic
    topicsdict = {}
    for topicname in mysettings.TEST_TOPICS:
        topickey = topicname.replace(" ", "_")
        topicsdict[topickey] = topicname
    topicsqset = Topic.objects.filter(user=userobj)
    for topicobj in topicsqset:
        topicname = topicobj.topicname
        topickey = topicname.replace(" ", "_")
        topicsdict[topickey] = topicname
    contextdict['alltopics'] = topicsdict
    contextdict['memberscount'] = grpobj.memberscount
    contextdict['maxmemberslimit'] = grpobj.maxmemberslimit
    contextdict['grouptype'] = grpobj.grouptype
    allgrptypesdict = {}
    for grptypecode in mysettings.GROUP_TYPES_DICT.keys():
        allgrptypesdict[grptypecode] = mysettings.GROUP_TYPES_DICT[grptypecode]
    contextdict['allgrouptypes'] = allgrptypesdict
    contextdict['allowentry'] = grpobj.allowentry
    contextdict['status'] = grpobj.status
    contextdict['adminremarks'] = grpobj.adminremarks
    contextdict['stars'] = grpobj.stars
    contextdict['ispaid'] = grpobj.ispaid
    contextdict['require_owner_perms'] = grpobj.require_owner_permission
    if grpobj.ispaid:
        ownerbankacctqset = OwnerBankAccount.objects.filter(groupowner=userobj, group=grpobj)
        if ownerbankacctqset.__len__() > 0:
            ownerbankacctobj = ownerbankacctqset[0] # Expect to have only one account registered for the user.
            contextdict['bankname'] = ownerbankacctobj.bankname
            contextdict['bankbranch'] = ownerbankacctobj.bankbranch
            contextdict['accountnumber'] = ownerbankacctobj.accountnumber
            contextdict['ifsccode'] = ownerbankacctobj.ifsccode
            contextdict['accountownername'] = ownerbankacctobj.accountownername
        else:
            contextdict['bankname'] = ""
            contextdict['bankbranch'] = ""
            contextdict['accountnumber'] = ""
            contextdict['ifsccode'] = ""
            contextdict['accountownername'] = ""
    if grpobj.ispaid:
        contextdict['entryfee'] = grpobj.entryfee
        contextdict['currency'] = grpobj.currency
    # Is the user the owner of this group? If so, we will need to display all the join requests to the group.
    # The owner (user) should be able to review the join requests and selectively allow some of them into the group.
    isowner = False
    if groupmembername == grpobj.owner.displayname:
        isowner = True
    contextdict['userisowner'] = isowner
    if isowner is True:
        allmembersqset = GroupMember.objects.filter(group=grpobj)
        contextdict['groupmembers'] = tuple(allmembersqset) # should be immutable
    grppostsqset = Post.objects.filter(posttargetgroup=grpobj)
    contextdict['groupposts'] = tuple(grppostsqset) # should be immutable
    if isowner is True:
        joinreqqset = GroupJoinRequest.objects.filter(group=grpobj)
        contextdict['joinrequests'] = tuple(joinreqqset) # should be immutable
    if grpobj.ispaid:
        bankacctqset = OwnerBankAccount.objects.filter(groupowner=grpobj.owner)
        contextdict['ownerbankaccts'] = tuple(bankacctqset) # should be immutable
        contextdict['bankaccountid'] = ""
        if bankacctqset.__len__() > 0:
            contextdict['bankaccountid'] = bankacctqset[0].id
    # Render content using 'contextdict'
    tmpl = get_template("network/managegroups.html")
    contextdict.update(csrf(request))
    cxt = Context(contextdict)
    managegroupshtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        managegroupshtml = managegroupshtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(managegroupshtml)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def groupimgupload(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    query_string = request.META['QUERY_STRING']
    paramkeyval = query_string.split("=")
    groupname = ""
    groupobj = None
    if paramkeyval[0] == 'groupname':
        groupname = paramkeyval[1]
        groupqset = Group.objects.filter(groupname=groupname)
        if groupqset.__len__() == 0:
            message = error_msg('1088')
            response = HttpResponse(message)
            return response
        groupobj = groupqset[0]
    if request.FILES.has_key('profpic'):
        grpimgpath = mysettings.MEDIA_ROOT + os.path.sep + userobj.displayname + os.path.sep + "groups" + os.path.sep + groupname
        imagefilename = request.FILES['profpic'].name.split(".")[0]
        fpath, message, profpic = skillutils.handleuploadedfile2(request.FILES['profpic'], grpimgpath, imagefilename)
        groupobj.groupimagefile = profpic
        try:
            groupobj.save()
            message = "success"
        except:
            message = error_msg('1041')
    else:
        message = "failed"
    return HttpResponse(message)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def savegroupdata(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    topics, maxmemberslimit, grouptypes, allowentry, ispaid, entryfee, bankname, bankbranch, acctname, acctnum, ifsccode, alltestsowned, adminremarks, groupname, currency = ("" for i in range(0,15))
    if request.POST.has_key('topics'):
        topics = request.POST['topics']
        topics = topics.replace("_", " ")
    if request.POST.has_key('maxmemberslimit'):
        maxmemberslimit = request.POST['maxmemberslimit']
    if request.POST.has_key('grouptypes'):
        grouptypes = request.POST['grouptypes']
    if request.POST.has_key('allowentry') and request.POST['allowentry'] == '1':
        allowentry = True
    else:
        allowentry = False
    if request.POST.has_key('ispaid') and request.POST['ispaid'] == '1':
        ispaid = True
    else:
        ispaid = False
    if request.POST.has_key('entryfee'):
        entryfee = request.POST['entryfee']
    if request.POST.has_key('currency'):
        currency = request.POST['currency']
    if request.POST.has_key('bankname'):
        bankname = request.POST['bankname']
    if request.POST.has_key('bankbranch'):
        bankbranch = request.POST['bankbranch']
    if request.POST.has_key('acctname'):
        acctname = request.POST['acctname']
    if request.POST.has_key('acctnum'):
        acctnum = request.POST['acctnum']
    if request.POST.has_key('ifsccode'):
        ifsccode = request.POST['ifsccode']
    if request.POST.has_key('adminremarks'):
        adminremarks = request.POST['adminremarks']
    if request.POST.has_key('groupname'):
        grpname = request.POST['groupname']
    groupqset = Group.objects.filter(groupname=grpname).filter(owner=userobj)
    if groupqset.__len__() == 0:
        message = error_msg('1088')
        response = HttpResponse(message)
        return response
    groupobj = groupqset[0]
    groupobj.maxmemberslimit = maxmemberslimit
    groupobj.grouptype = grouptypes
    groupobj.basedontopic = topics
    groupobj.adminremarks = adminremarks
    groupobj.allowentry = allowentry
    groupobj.ispaid = ispaid
    if entryfee == "":
        groupobj.entryfee = 0
    else:
        groupobj.entryfee = float(entryfee)
        groupobj.currency = currency
    bankacctqset = OwnerBankAccount.objects.filter(groupowner=userobj, group=groupobj)
    bankacctobj = None
    if bankacctqset.__len__() == 0:
        bankacctobj = OwnerBankAccount()
        bankacctobj.groupowner = userobj
        bankacctobj.group = groupobj
    else:
        bankacctobj = bankacctqset[0]
    bankacctobj.bankname = bankname
    bankacctobj.bankbranch = bankbranch
    bankacctobj.accountnumber = acctnum
    bankacctobj.ifsccode = ifsccode
    bankacctobj.accountownername = acctname
    try:
        groupobj.save()
        bankacctobj.save()
    except:
        message = error_msg('1090') + "Error: %s"%sys.exc_info()[1].__str__()
        response = HttpResponse(message)
        return response
    return HttpResponse(error_msg('1091'))


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def showpaymentscreen(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    groupid = -1
    entryfee = ""
    if request.POST.has_key('groupid'):
        groupid = request.POST['groupid']
    if request.POST.has_key('entryfee'):
        entryfee = request.POST['entryfee']
    if groupid == -1 or groupid == '':
        message = error_msg('1085')
        response = HttpResponse(message)
        return response
    groupobj = Group.objects.get(id=groupid)
    contextdict = {}
    if not groupobj:
        message = error_msg('1086')
        response = HttpResponse(message)
        return response
    contextdict['hosturl'] = socket.gethostname()
    contextdict['customer_ip'] = mysettings.CUSTOMER_IP_ADDRESS
    entryfee = groupobj.entryfee
    curr = groupobj.currency
    if curr == 'USD':
        equiv_rs = entryfee * skillutils.fetch_currency_rate('USD', 'INR')
    elif curr == 'EUR':
        equiv_rs = entryfee * skillutils.fetch_currency_rate('EUR', 'INR')
    else:
        equiv_rs = entryfee
    contextdict['order_desc'] = entryfee
    contextdict['posId'] = mysettings.PAYU_POS_ID
    contextdict['groupname'] = groupobj.groupname
    contextdict['subscription_amt'] = entryfee
    contextdict['total_amt'] = entryfee
    contextdict['signature'] = mysettings.PAYU_SECOND_ID
    tmpl = get_template("network/payu_payment.html")
    contextdict.update(csrf(request))
    cxt = Context(contextdict)
    payuhtml = tmpl.render(cxt)
    response = HttpResponse(payuhtml)
    return response


