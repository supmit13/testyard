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
import base64

# Application specific libraries...
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
from skillstest.Subscription.models import Plan, UserPlan, Transaction
from skillstest.Tests.models import Topic, Subtopic, Evaluator, Test, UserTest, Challenge, UserResponse, WouldbeUsers
from skillstest.Network.models import Connection, ConnectionInvitation, GroupMember, Group, Post, OwnerBankAccount, GroupJoinRequest, GentleReminder, ExchangeRates
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
    templatevars['payuconfirmurl'] = mysettings.PAYU_CONFIRM_URL
    templatevars['searchuserurl'] = mysettings.SEARCH_USER_URL
    templatevars['sendconnectionurl'] = mysettings.SEND_CONNECTION_URL
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
            grpdict['groupimagefile'] = "media/" + groupobj.owner.displayname + "/groups/" + groupobj.groupname + "/" + groupobj.groupimagefile
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
        grpdict['removedblocked'] = 0
        # Check if the logged in user has already requested to be allowed in the group
        grpjoinreqqset = GroupJoinRequest.objects.filter(group=groupobj, user=userobj, outcome='open', active=True)
        if grpjoinreqqset.__len__() > 0:
            grpdict['alreadyrequested'] = 1
        grprefuseqset = GroupJoinRequest.objects.filter(group=groupobj, user=userobj, outcome='refuse')
        if grprefuseqset.__len__() > 0:
            grpdict['alreadyrefused'] = 1
        grpallowedqset = GroupJoinRequest.objects.filter(group=groupobj, user=userobj, outcome='accept')
        if grpallowedqset.__len__() > 0:
            # Check if the user is present in the GroupMember records for this group with status set to True and removed and blocked set to False.
            gmqset = GroupMember.objects.filter(group=groupobj, member=userobj, status=True)
            if gmqset.__len__() == 0:
                grpdict['alreadyallowed'] = 0
            else:
                if gmqset[0].removed or gmqset[0].blocked:
                    grpdict['removedblocked'] = 1
                else:
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
    else: # Vanilla flavoured group - no payment to make, but require owner perms.
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
            joinrequest.outcome = 'accept'
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
        message = ""
        #message = error_msg('1102')
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
        joinrequestsinfo = {}
        joinreqsopenqset = GroupJoinRequest.objects.filter(group=grpobj, outcome='open')
        joinreqsclosedqset = GroupJoinRequest.objects.filter(group=grpobj, outcome='closed')
        joinreqsrefuseqset = GroupJoinRequest.objects.filter(group=grpobj, outcome='refuse')
        joinreqsacceptqset = GroupJoinRequest.objects.filter(group=grpobj, outcome='accept')
        joinrequestsinfo['open'] = []
        for joinreq in joinreqsopenqset:
            d = {}
            d['displayname'] = joinreq.user.displayname
            d['fullname'] = joinreq.user.firstname + " " + joinreq.user.middlename + " " + joinreq.user.lastname
            requestdtobj = joinreq.requestdate
            d['requestdate'] = skillutils.yetanotherpythontomysqldatetime(requestdtobj)
            d['userimageurl'] = "media/%s/images/%s"%(joinreq.user.displayname, joinreq.user.userpic)
            joinrequestsinfo['open'].append(d)
        joinrequestsinfo['close'] = []
        for joinreq in joinreqsclosedqset:
            d = {}
            d['displayname'] = joinreq.user.displayname
            d['fullname'] = joinreq.user.firstname + " " + joinreq.user.middlename + " " + joinreq.user.lastname
            requestdtobj = joinreq.requestdate
            d['requestdate'] = skillutils.yetanotherpythontomysqldatetime(requestdtobj)
            d['userimageurl'] = "media/%s/images/%s"%(joinreq.user.displayname, joinreq.user.userpic)
            joinrequestsinfo['close'].append(d)
        joinrequestsinfo['refuse'] = []
        for joinreq in joinreqsrefuseqset:
            d = {}
            d['displayname'] = joinreq.user.displayname
            d['fullname'] = joinreq.user.firstname + " " + joinreq.user.middlename + " " + joinreq.user.lastname
            requestdtobj = joinreq.requestdate
            d['requestdate'] = skillutils.yetanotherpythontomysqldatetime(requestdtobj)
            d['userimageurl'] = "media/%s/images/%s"%(joinreq.user.displayname, joinreq.user.userpic)
            joinrequestsinfo['refuse'].append(d)
        joinrequestsinfo['accept'] = []
        for joinreq in joinreqsacceptqset:
            d = {}
            d['displayname'] = joinreq.user.displayname
            d['fullname'] = joinreq.user.firstname + " " + joinreq.user.middlename + " " + joinreq.user.lastname
            requestdtobj = joinreq.requestdate
            d['requestdate'] = skillutils.yetanotherpythontomysqldatetime(requestdtobj)
            d['userimageurl'] = "media/%s/images/%s"%(joinreq.user.displayname, joinreq.user.userpic)
            joinrequestsinfo['accept'].append(d)
        contextdict['joinrequestsinfo'] = joinrequestsinfo
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
    contextdict['hosturl'] = skillutils.gethosturl(request)
    contextdict['customer_ip'] = mysettings.CUSTOMER_IP_ADDRESS
    # if we receive the 'REMOTE_ADDR' header, we use it here. This is what the customerIp value should be.
    if request.META.has_key('REMOTE_ADDR'): 
        contextdict['customer_ip'] = request.META['REMOTE_ADDR']
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
    contextdict['groupid'] = groupid
    contextdict['subscription_amt'] = entryfee
    contextdict['total_amt'] = entryfee
    contextdict['signature'] = mysettings.PAYU_SECOND_ID
    contextdict['extOrderId'] = skillutils.generate_random_string()
    contextdict['discountamt'] = 0
    contextdict['payuconfirmurl'] = skillutils.gethosturl(request) + "/" + mysettings.PAYU_CONFIRM_URL
    contextdict['buyeremail'] = userobj.emailid
    contextdict['buyerphone'] = userobj.mobileno
    contextdict['firstname'] = userobj.firstname
    contextdict['lastname'] = userobj.lastname
    tmpl = get_template("network/payu_payment.html")
    contextdict.update(csrf(request))
    cxt = Context(contextdict)
    payuhtml = tmpl.render(cxt)
    response = HttpResponse(payuhtml)
    return response


def _create_payu_signature(paramsdict, second_id=mysettings.PAYU_SECOND_ID, posId=mysettings.PAYU_POS_ID):
    paramnames = paramsdict.keys()
    paramnames.sort()
    concatvalue = ""
    for param in paramnames:
        concatvalue += str(paramsdict[param])
    concatvalue += second_id
    import md5
    md5obj = md5.new(concatvalue)
    hashval = md5obj.hexdigest()
    payusignature = "sender=" + str(posId) + ";algorithm=MD5;signature=" + str(hashval)
    return payusignature


"""
On receiving confirmation from the user about payment (using the page titled "Payment Process - Step #1")
this method makes an API call to the PayU payment gateway and the process of payment starts from there.
The amount of money received from users while registering for paid groups is marked to the owner of the 
group and the owner reserves the right to withdraw the amount (after being deducted by x% which goes to the
account of the website) anytime later.
"""
@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def confirmpayment_payu(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    customerIP, orderdesc, currencycode, posId, notifyurl, continueurl, productname, productquantity, productunitprice, totalamount, orderId, groupid, buyeremail = ('' for i in range(0, 13))
    paramnamesdict = {}
    if request.POST.has_key('customerIp'):
        customerIP = request.POST['customerIp']
    if request.POST.has_key('description'):
        orderdesc = request.POST['description']
    if request.POST.has_key('merchantPosId'):
        posId = request.POST['merchantPosId']
    if request.POST.has_key('notifyUrl'):
        notifyurl = request.POST['notifyUrl']
    if request.POST.has_key('continueUrl'):
        continueurl = request.POST['continueUrl']
    if request.POST.has_key('currencyCode'):
        currencycode = request.POST['currencyCode']
    if request.POST.has_key('productname'):
        productname = request.POST['productname']
    if request.POST.has_key('productquantity'):
        productquantity = request.POST['productquantity']
    if request.POST.has_key('productunitprice'):
        productunitprice = request.POST['productunitprice']
    if request.POST.has_key('totalamount'):
        totalamount = request.POST['totalamount']
    if request.POST.has_key('extOrderId'):
        orderId = request.POST['extOrderId']
    if request.POST.has_key('groupid'):
        groupid = request.POST['groupid']
    if request.POST.has_key('buyeremail'):
        buyeremail = request.POST['buyeremail']
    if request.POST.has_key('buyerphone'):
        buyerphone = request.POST['buyerphone']
    if request.POST.has_key('buyerfirstname'):
        buyerfirstname = request.POST['buyerfirstname']
    if request.POST.has_key('buyerlastname'):
        buyerlastname = request.POST['buyerlastname']
    # Add a record in the Network_groupjoinrequest table.
    joinreq = GroupJoinRequest()
    groupobj = Group.objects.get(id=groupid)
    if not groupobj:
        message = error_msg('1086')
        response = HttpResponse(message)
        return response
    joinreq.group = groupobj
    joinreq.user = userobj
    joinreq.orderId = orderId
    joinreq.requestdate = skillutils.pythontomysqldatetime2(str(datetime.datetime.now()))
    joinreq.outcome = 'open'
    joinreq.active = True
    joinreq.reason = 'payment in progress'
    
    # Create a transaction object and post the data to payU ordering API
    txnobj = Transaction()
    txnobj.orderId = orderId
    txnobj.username = userobj.displayname
    txnobj.user = userobj
    txnobj.group = groupobj
    txnobj.usersession = sesscode
    joinreq.requestdate = skillutils.pythontomysqldatetime2(str(datetime.datetime.now()))
    xchngusd = skillutils.fetch_currency_rate('USD', 'INR')
    xchngeur = skillutils.fetch_currency_rate('EUR', 'INR')
    xchngepln = skillutils.fetch_currency_rate('PLN', 'INR')
    txnobj.payamount = groupobj.entryfee
    if totalamount < txnobj.payamount: # TODO: check if any discount is to be processed
        pass
    if groupobj.currency == 'USD':
        txnobj.payamount = groupobj.entryfee * xchngusd
    elif groupobj.currency == 'EUR':
        txnobj.payamount = groupobj.entryfee * xchngeur
    else:
        pass
    txnobj.paymode = 'PAYU'
    txnobj.comments = "Join paid group named '%s' by user '%s'"%(groupobj.groupname, userobj.displayname)
    txnobj.invoice_email = buyeremail
    txnobj.trans_status = False # Initialized to False. Once payment is made, it will be updated to True.
    
    payuparamsdict = {}
    #payuparamsdict['customerIp'] = customerIP
    payuparamsdict['customerIp'] = "127.0.0.1"
    payuparamsdict['merchantPosId'] = posId
    payuparamsdict['description'] = orderdesc
    payuparamsdict['currencyCode'] = mysettings.DEFAULT_CURRENCY
    payuparamsdict['totalAmount'] = str(txnobj.payamount)
    payuparamsdict['products[0].name'] = groupobj.groupname
    payuparamsdict['products[0].unitPrice'] = str(txnobj.payamount)
    payuparamsdict['products[0].quantity'] = "1"
    payuparamsdict['continueUrl'] = continueurl
    payuparamsdict['buyer.email'] = buyeremail
    payuparamsdict['buyer.phone'] = buyerphone
    payuparamsdict['buyer.firstName'] = buyerfirstname
    payuparamsdict['buyer.lastName'] = buyerlastname
    signature = _create_payu_signature(payuparamsdict, mysettings.PAYU_SECOND_ID, mysettings.PAYU_POS_ID)
    payuparamsdict['OpenPayu-Signature'] = signature
    payudata = urllib.urlencode(payuparamsdict)
    print payudata
    #payuparamsdict = { 
    #	"customerIp": customerIP, \
    #	"merchantPosId": str(posId), \
    #	"description": str(orderdesc),\
    #	"currencyCode": mysettings.DEFAULT_CURRENCY, \
    #	"totalAmount": str(txnobj.payamount), \
    #	"extOrderId":orderId, \
    #	"buyer": { \
    # 		"email": buyeremail, \
    # 		"phone": str(buyerphone), \
    # 		"firstName": userobj.firstname, \
    # 		"lastName": userobj.lastname \
    #	        },\
    #	"products": [ \
    #   		{ \
    #       	"name": groupobj.groupname,\
    #       	"unitPrice": str(txnobj.payamount), \
    #       	"quantity": "1" \
    #   	        },\
    #	],\
    #    "continueUrl" : urllib.quote_plus(continueurl), \
    #}
    #payuparamsdict["OpenPayu-Signature"] = _create_payu_signature(payuparamsdict, mysettings.PAYU_SECOND_ID, mysettings.PAYU_POS_ID)
    #payuparamsdict_str = json.dumps(payuparamsdict)
    # Create a POST request with the above data and send it to /api/v2_1/orders
    headers = { 'Host' : 'developers.payu.com', 'Cache-Control' : 'max-age=0', 'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 'Accept-Encoding' : 'gzip,deflate,sdch', 'Accept-Language' : 'en-US,en;q=0.8', 'Connection' : 'keep-alive', 'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.120 Chrome/37.0.2062.120 Safari/537.36', 'Cookie' : '_vis_opt_s=1%7C; _vis_opt_test_cookie=1;', 'If-Modified-Since' : '' }
    #headers['Authorization'] = 'Basic ' + str(base64.b64encode(str(mysettings.PAYU_POS_ID) + ":" + mysettings.PAYU_SECOND_ID))
    # Throw a GET request at the Start page of payu payment gateway to get the cookies
    (status, httpresp) = _sendrequest(mysettings.PAYU_START_URL, 'GET', None, headers)
    if type(httpresp) == str:
        print "Error sending request: " + httpresp
        response = HttpResponse(httpresp)
        return response
    respheaders = httpresp.info()
    cookiestr = ""
    if respheaders.has_key('Set-Cookie'):
        httponlypattern = re.compile("HttpOnly", re.IGNORECASE)
        cookies = respheaders['Set-Cookie']
        cookieparts = cookies.split(";")
        for cookie in cookieparts:
            print cookie
            cookiekeyvals = cookie.split("=")
            if cookiekeyvals.__len__() == 2:
                cookiekey, cookieval = cookiekeyvals[0], cookiekeyvals[1]
            else:
                continue
            if cookiekey == 'Path' or cookiekey == 'path' or cookiekey == 'secure' or cookiekey == 'Expires' or cookiekey=='HttpOnly' or cookiekey == 'expires':
                continue
            if httponlypattern.search(cookiekey):
                cookiekey = cookiekey.replace(" HttpOnly, ", "")
            cookiestr += cookiekey + "=" + cookieval + ";"
    cookiestr = cookiestr[:-1]
    print cookiestr, "EEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
    headers = { 'Content-Type' : "application/x-www-form-urlencoded", 'Host' : 'secure.payu.com', 'Origin' : '', 'Cache-Control' : 'max-age=0', 'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', 'Accept-Encoding' : 'gzip,deflate', 'Accept-Language' : 'en-US,en;q=0.8', 'Connection' : 'keep-alive', 'User-Agent' : 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.120 Chrome/37.0.2062.120 Safari/537.36', 'Cookie' : cookiestr }
    (status, httpresp) = _sendrequest(mysettings.PAYU_ORDER_CREATION_URL, 'POST', payudata, headers)
    encpayucontent = httpresp.read()
    responseHeaders = httpresp.info()
    for hdr in responseHeaders.keys():
        print hdr + " ===== >> " + responseHeaders[hdr] + "\n"
    payucontent = skillutils.decodeGzippedContent(encpayucontent)
    if not status:
        message += "<font color='#AA0000' style='font-weight:bold'>" + payucontent + "</font>"
    else:
        print payucontent
        """
        try:
            txnobj.save()
        except:
            message += "Could not save transaction object - Error: %s"%sys.exc_info()[1].__str__()
            response = HttpResponse(message)
            return response
        try:
            joinreq.save()
        except:
            message = "Could not save join request - Error: %s"%sys.exc_info()[1].__str__()
            response = HttpResponse(message)
            return response
        message += "<br>Saved joinrequest and transaction objects.<br>"
        """
    #print "\n##############################\n", data, "\n#################################\n"
    response = HttpResponse(payucontent)
    return response


def _sendrequest(target, method, data, headers={}):
    request = None
    if method == 'POST':
        request = urllib2.Request(target, data, headers)
    elif method == 'GET':
        request = urllib2.Request(target, None, headers)
    else:
        message = error_msg('1100')
        return (0, message) + " - " + sys.exc_info()[1].__str__()
    opener = urllib2.build_opener()
    resp = None
    try:
        resp = opener.open(request)
    except:
        print "DDDDDDDDDDDDDDDDDDDDDD",sys.exc_info()[1].__str__()
        respcode = resp.getcode()
        print respcode, "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW"
        if respcode == '304':
            respheaders = resp.info()
            if respheaders.has_key('Location'):
                target = respheaders['Location']
                print target, "SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS"
                (status, resp) = _sendrequest(target, method, data, headers)
                return (1, resp)
            else:
                message = error_msg('1103')
        else:
            message = "Error code is not 304!"
        message = error_msg('1101') + " - " + sys.exc_info()[1].__str__()
        return (0,message)
    return (1, resp)


"""
Search other users and allow the logged in user to send connect requests.
"""
@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def searchuser(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    usersdict = {}
    emailid, targetusername, teststaken = ('' for i in range(0, 3))
    if request.POST.has_key('emailid'):
        emailid = request.POST['emailid']
    if request.POST.has_key('targetusername'):
        targetusername = request.POST['targetusername']
    if request.POST.has_key('teststaken'):
        teststaken = request.POST['teststaken']
    userqset = User.objects.all()
    if emailid and emailid != "":
        emailid = emailid.strip()
        userqset = userqset.filter(emailid__contains=emailid)
    if targetusername and targetusername != "":
        targetusername = targetusername.strip()
        userqset = userqset.filter(displayname__contains=targetusername)
    if teststaken and teststaken != "":
        teststaken = teststaken.strip()
        testslist = teststaken.split(",")
        for test in testslist:
            testobjectsqset = Test.objects.filter(testname__icontains=test)
            for testobj in testobjectsqset:
                usertestqueryset = UserTest.objects.filter(test=testobj)
                for utobj in usertestqueryset:
                    userdispname = utobj.user.displayname
                    if userdispname == userobj.displayname: # if the user is the same as the logged in user, we skip it.
                        continue
                    if not usersdict.has_key(userdispname):
                        profileimglink = "media/%s/images/%s"%(displayname,str(utobj.user.userpic))
                        usersdict[userdispname] = {'profileimage' : profileimglink, 'name' : utobj.user.firstname + " " + utobj.user.middlename + " " + utobj.user.lastname, 'uid' : utobj.user.id }
    for uobj in userqset:
        displayname = uobj.displayname
        if displayname == userobj.displayname: # if the user is the same as the logged in user, we skip it.
            continue
        if not usersdict.has_key(displayname):
            profileimglink = "media/%s/images/%s"%(displayname,str(uobj.userpic))
            usersdict[displayname] = {'profileimage' : profileimglink, 'name' : uobj.firstname + " " + uobj.middlename + " " + uobj.lastname, 'uid' : uobj.id }
    message = json.dumps(usersdict)
    response = HttpResponse(message)
    return response


"""
Function to send connection requests to users on testyard.
"""
@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def sendconnectionrequest(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    userid = 0
    if request.POST.has_key('userid'):
        userid = request.POST['userid']
    if not userid:
        message = error_msg('1104')
        response = HttpResponse(message)
        return response
    targetuser = User.objects.get(id=userid)
    if not targetuser:
        message = error_msg('1105')
        message = message%userid
        response = HttpResponse(message)
        return response
    # Check if the user has already sent a connection invitation or if the user is already in the contact list.
    # For already existing connections, check both ways, i.e. where focususer is userobj (case #1) , as well as where focususer is targetuser (case #2).
    connqueryset = Connection.objects.filter(focususer=userobj, connectedto=targetuser, deleted=False) # Case #1
    if connqueryset.__len__() > 0:
        message = error_msg('1108')
        message = message%targetuser.displayname
        response = HttpResponse(message)
        return response
    connqueryset = Connection.objects.filter(focususer=targetuser, connectedto=userobj, deleted=False) # Case #2
    if connqueryset.__len__() > 0:
        message = error_msg('1108')
        message = message%focususer.displayname
        response = HttpResponse(message)
        return response
    conninviteqset = ConnectionInvitation.objects.filter(fromuser=userobj, touser=targetuser, invitationstatus='open')
    if conninviteqset.__len__() > 0:
        message = error_msg('1109')
        message = message%targetuser.displayname
        response = HttpResponse(message)
        return response
    # Check if a ConnectionInvitation object with invitationstatus = refuse exists. If so, we do not send any further requests.
    conninviterefusedqset = ConnectionInvitation.objects.filter(fromuser=userobj, touser=targetuser, invitationstatus='refuse')
    if conninviterefusedqset.__len__() > 0:
        message = error_msg('1110')
        response = HttpResponse(message)
        return response
    # Check if a ConnectionInvitation object with invitationstatus = closed exists. If so, we merely change the invitationstatus to open.
    conninviteclosedqset = ConnectionInvitation.objects.filter(fromuser=userobj, touser=targetuser, invitationstatus='closed')
    if conninviteclosedqset.__len__() > 0:
        conninviteclosedqset[0].invitationstatus = 'open'
        conninviteclosedqset[0].save()
        message = error_msg('1107')
        message = message%targetuser.displayname
        response = HttpResponse(message)
        return response
    # Create a 'ConnectionInvitation' object
    conninvite = ConnectionInvitation()
    conninvite.fromuser = userobj
    conninvite.touser = targetuser
    conninvite.invitationcontent = mysettings.CONNECT_INVITATION_CONTENT
    try:
        conninvite.save()
    except:
        message = error_msg('1106')
        message = message%targetuser.displayname
        response = HttpResponse(message)
        return response
    message = error_msg('1107')
    message = message%targetuser.displayname
    response = HttpResponse(message)
    return response


