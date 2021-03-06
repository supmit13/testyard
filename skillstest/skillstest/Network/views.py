from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.core.context_processors import csrf
from django.views.generic import View
from django.http import HttpResponseBadRequest, HttpResponse , HttpResponseRedirect, HttpRequest
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Q
from django.template.response import TemplateResponse
from django.utils.http import base36_to_int, is_safe_url
from django.template import Template, Context
from django.template.loader import get_template
from django.contrib.sites.models import get_current_site
from django.core.mail import send_mail
from django.contrib.sessions.backends.db import SessionStore
import stripe

# Standard libraries...
import os, sys, re, time, datetime
import cPickle
import decimal, math
import urllib, urllib2
import simplejson as json
import socket
import base64, md5
from itertools import chain
from threading import Thread

# Application specific libraries...
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
from skillstest.Subscription.models import Plan, UserPlan, Transaction
from skillstest.Tests.models import Topic, Subtopic, Evaluator, Test, UserTest, Challenge, UserResponse, WouldbeUsers
from skillstest.Network.models import Connection, ConnectionInvitation, GroupMember, Group, Post, OwnerBankAccount, GroupJoinRequest, GentleReminder, ExchangeRates, SubscriptionEarnings, GroupPaidTransactions, WithdrawalActivity, WePay, RazorPayTransaction
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
    templatevars['leavegroupurl'] = mysettings.LEAVE_GROUP_URL
    templatevars['grpimguploadurl'] = mysettings.GROUP_IMG_UPLOAD_URL + '?groupname='
    templatevars['savegrpdataurl'] = mysettings.SAVE_GROUP_DATA_URL
    templatevars['getpaymentgwurl'] = mysettings.PAYMENT_GW_URL
    templatevars['getsubscriptiongwurl'] = mysettings.SUBSCRIPTION_GW_URL
    templatevars['payuconfirmurl'] = mysettings.PAYU_CONFIRM_URL
    templatevars['stripeconfirmurl'] = mysettings.STRIPE_CONFIRM_URL
    templatevars['searchuserurl'] = mysettings.SEARCH_USER_URL
    templatevars['sendconnectionurl'] = mysettings.SEND_CONNECTION_URL
    templatevars['savegroupjoinstatusurl'] = mysettings.SAVE_GROUP_JOIN_STATUS_URL
    templatevars['handleconnectinviteurl'] = mysettings.CONNECTION_INVITE_HANDLER_URL
    templatevars['postcontenturl'] = mysettings.POST_MESSAGE_CONTENT_URL
    templatevars['postreplyurl'] = mysettings.POST_REPLY_CONTENT_URL
    templatevars['nextpostcontenturl'] = mysettings.NEXT_POST_LIST_URL
    templatevars['postsperpage'] = mysettings.MAX_POSTS_IN_PAGE
    templatevars['newmessagereadurl'] = mysettings.NEW_MESSAGE_READ_URL
    templatevars['sendmessageresponseurl'] = mysettings.SEND_MSG_RESPONSE_URL
    templatevars['messagesearchurl'] = mysettings.MESSAGE_SEARCH_URL
    templatevars['testtogroupsurl'] = mysettings.TEST_TO_GROUPS_URL
    templatevars['gettestgroupsurl'] = mysettings.GET_TEST_GROUPS_URL
    templatevars['getconnectioninfourl'] = mysettings.GET_CONNECTION_INFO_URL
    templatevars['getgroupowneddicturl'] = mysettings.GET_GROUPS_OWNED_URL
    templatevars['getgroupmemberdicturl'] = mysettings.GET_GROUPS_MEMBER_URL
    templatevars['getconnectionsdicturl'] = mysettings.GET_CONN_DICT_URL
    templatevars['blockuserurl'] = mysettings.BLOCK_USER_URL
    templatevars['unblockuserurl'] = mysettings.UNBLOCK_USER_URL
    templatevars['removeuserurl'] = mysettings.REMOVE_USER_URL
    templatevars['sendmessageurl'] = mysettings.SEND_MESSAGE_URL
    templatevars['managemembersurl'] = mysettings.MANAGE_GROUP_MEMBERS_URL
    templatevars['manageownedgrpsurl'] = mysettings.MANAGE_OWNED_GROUPS_URL
    templatevars['grpinfosaveurl'] = mysettings.GROUPINFO_SAVE_URL
    templatevars['sendamessageurl'] = mysettings.SEND_A_MESSAGE_URL
    templatevars['groupprofileurl'] = mysettings.GROUP_PROFILE_URL
    templatevars['exitgroupurl'] = mysettings.EXIT_GROUP_URL
    templatevars['cutpercent'] = mysettings.CUT_FRACTION * 100

    validfrom = datetime.datetime.now()
    validfromstr = skillutils.pythontomysqldatetime2(str(validfrom))
    datepart, timepart = validfromstr.split(" ")
    datepartslist = datepart.split("-")
    templatevars['validfrom'] = datepartslist[2] + "-" + datepartslist[1] + "-" + datepartslist[0] + " " + timepart
    alltopics = list(mysettings.TEST_TOPICS)
    extratopicsqset = Topic.objects.filter(user=userobj)
    uniqextratopicset = {}
    for topic in extratopicsqset:
        tname = topic.topicname
        tname = tname.replace("+", " ")
        if uniqextratopicset.has_key(tname):
            pass
        else:
            uniqextratopicset[tname] = '1'
            alltopics.append(tname)
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
    contactsqset = Connection.objects.filter(focususer=userobj, deleted=False)
    groupmembersqset = GroupMember.objects.filter(member=userobj, status=True, removed=False, blocked=False).order_by('-group').order_by('-membersince')
    groupsownerqset = Group.objects.filter(owner=userobj).order_by('-id')
    connectioninvitationsqset = ConnectionInvitation.objects.filter(touser=userobj, invitationstatus='open').order_by('invitationdate')
    contacts = []
    groups = []
    groupsdict = {}
    testtakersdict = {}
    contactsdict = {}
    connectinvitesdict = {}
    messagesdict = {}
    uobjlist = []
    for contact in contactsqset:
        contactlink = "<a href='#/' onClick='javascript:showconnectionsprofile(&quot;%s&quot;);'>%s</a><!-- - <a href='#/' onClick='javascript:manageconnection(%s);'>manage</a> -->"%(contact.id, contact.connectedto.displayname, contact.id)
        if contact.blocked:
            contactlink = "<a href='#/' onClick='javascript:showconnectionsprofile(&quot;%s&quot;);'><font color='#AA0000'>%s</font></a> - <a href='#/' onClick='javascript:unblock(%s);'><font color='#AA0000' size=-1>[Unblock]</font></a>"%(contact.id, contact.connectedto.displayname, contact.id)
        contacts.append(contactlink)
        if not contactsdict.has_key(str()):
            contactsdict[str(contact.id)] = contact.connectedto.displayname
            uobj = User.objects.get(displayname=contact.connectedto.displayname)
            uobjlist.append(uobj)
        else:
            pass
    uniqgroups = {}
    for groupmember in groupmembersqset:
        grouplink = "<a href='#/' onClick='javascript:managegroup(&quot;%s&quot;, &quot;%s&quot;, &quot;%s&quot;);'>%s</a>"%(groupmember.member.displayname, groupmember.group.groupname, groupmember.group.currency, groupmember.group.groupname)
        if uniqgroups.has_key(groupmember.group.groupname):
            continue
        uniqgroups[groupmember.group.groupname] = 1
        groups.append(grouplink)
        if not groupsdict.has_key(groupmember.group.id):
            groupsdict[groupmember.group.id] = groupmember.group.groupname
    usertestqset = UserTest.objects.filter(user=userobj).distinct()
    try:
        for utobj in usertestqset:
            testtakersdict[utobj.test.id] = utobj.test.testname
    except:
        pass
    alltopicsdict = {}
    for topic in mysettings.TEST_TOPICS:
        topicunderscored = topic.replace(" ", "_")
        alltopicsdict[topicunderscored] = topic
    dyntopicsqset = Topic.objects.filter(user=userobj)
    for topicobj in dyntopicsqset:
        topicunderscored = topicobj.topicname.replace(" ", "_")
        alltopicsdict[topicunderscored] = topicobj.topicname
    messageiduseddict = {};
    messagesqset = Post.objects.filter(posttargettype='user', posttargetuser=userobj, relatedpost_id=None).order_by('-createdon')
    messageobj = None
    for messageobj in messagesqset:
        if messageobj.attachmentfile:
            attachtag = str("<a href='media/" + messageobj.poster.displayname + "/posts/" + messageobj.attachmentfile + "'><img src='static/images/attachment.png' height='20px' width='20px' title='Attachment'></a>")
        else:
            attachtag = ""
        messagesdict[messageobj.id] = [ messageobj.poster.displayname + "##" + str(messageobj.createdon) + "##" + attachtag + "##" + messageobj.postmsgtag + "##" + messageobj.postcontent, ]
        if messageobj.newmsg is True:
            messagesdict[messageobj.id] = ["new##" + messagesdict[messageobj.id][0], ]
        if not messageiduseddict.has_key(messageobj.id):
            messageiduseddict[messageobj.id] = 1
        else:
            pass
        subpostsqset1 = Post.objects.filter(posttargettype='user', poster=userobj, relatedpost_id=messageobj.id).order_by('-createdon')
        subpostsqset2 = Post.objects.filter(posttargettype='user', posttargetuser=userobj, relatedpost_id=messageobj.id).order_by('-createdon')
        subpostsqset = list(chain(subpostsqset1, subpostsqset2))
        subpostslist = []
        for subpost in subpostsqset:
            if not messageiduseddict.has_key(subpost.id):
                messageiduseddict[subpost.id] = 1
            else:
                pass
            poststr = ""
            if subpost.newmsg is True:
                poststr = "new##"
            if subpost.attachmentfile:
                attachtag = str("<a href='media/" + subpost.poster.displayname + "/posts/" + subpost.attachmentfile + "'><img src='static/images/attachment.png' height='20px' width='20px' title='Attachment'></a>")
            else:
                attachtag = ""
            poststr += str(subpost.id) + "##" + subpost.poster.displayname + "##" + str(subpost.createdon) + "##" + attachtag + "##" + subpost.postmsgtag + "##" + subpost.postcontent
            subpostslist.append(poststr)
        if messageobj is not None:
            messagesdict[messageobj.id].append(subpostslist)
    messagesqset2 = []
    if messageobj is not None:
        messagesqset2 = Post.objects.filter(posttargettype='user', posttargetuser=userobj).exclude(relatedpost_id=messageobj.id).exclude(relatedpost_id=None).order_by('-createdon')
    for messageobj in messagesqset2:
        if not messageiduseddict.has_key(messageobj.id):
            messageiduseddict[messageobj.id] = 1
        else:
            pass
        if messageobj.attachmentfile:
            attachtag = str("<a href='media/" + messageobj.poster.displayname + "/posts/" + messageobj.attachmentfile + "'><img src='static/images/attachment.png' height='20px' width='20px' title='Attachment'></a>")
        else:
            attachtag = ""
        messagesdict[messageobj.id] = [ messageobj.poster.displayname + "##" + str(messageobj.createdon) + "##" + attachtag + "##" + messageobj.postmsgtag + "##" + messageobj.postcontent, ]
        if messageobj.newmsg is True:
            messagesdict[messageobj.id] = ["new##" + messagesdict[messageobj.id][0], ]
    messagesdictstr = json.dumps(messagesdict)
    messagesdictenc = base64.b64encode(messagesdictstr)
    for conninvite in connectioninvitationsqset:
        fromuser = conninvite.fromuser
        fromusername = fromuser.displayname
        fromuserid = fromuser.id
        invid = conninvite.id
        invitationdate = conninvite.invitationdate
        invitationcontent = conninvite.invitationcontent
        invitationcontent_short = invitationcontent[:15] + "..."
        if not connectinvitesdict.has_key(fromusername):
            connectinvitesdict[str(invid)] = [ fromuserid, fromusername, invitationdate, invitationcontent_short, invitationcontent ]
        else:
            connectinvitesdict[str(invid)][2] = invitationdate
            connectinvitesdict[str(invid)][3] = invitationcontent_short
    contextdict = { 'displayname' : userobj.displayname, 'connections' : contacts, 'groups' : groups, 'topics' : alltopicsdict }
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
    contextdict['groupsdict'] = groupsdict
    contextdict['testtakersdict'] = testtakersdict
    contextdict['contactsdict'] = contactsdict
    contextdict['connectinvitesdict'] = connectinvitesdict
    contextdict['messagesdict'] = messagesdict
    contextdict['messagesdictenc'] = messagesdictenc
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
    groupname, groupdescription, grouptopic, ispaid, isactive, allowentry, cleartest, grouptype, maxmemberscount, bankname, branchname, ifsccode, acctownername, acctnumber, entryfee, subscriptionfee, tagline, currency, require_owner_perms, payschemeval =  ("" for i in range(0,20))
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
            payschemeval = request.POST['payscheme']
            entryfee = request.POST['entryfee']
            subscriptionfee = request.POST['subscriptionfee']
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
    if not entryfee or entryfee == "" or payschemeval != "entryfeebased":
        entryfee = 0.0
    grpobj.entryfee = float(entryfee)
    if not subscriptionfee or subscriptionfee == "" or payschemeval != "subscriptionbased":
        subscriptionfee = 0.0
    grpobj.subscription_fee = float(subscriptionfee)
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
    groupsqset = Group.objects.filter(Q(groupname__icontains=grpkeyword) | Q(description__icontains=grpkeyword))
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
        grpdict['subscriptionfee'] = groupobj.subscription_fee
        grpdict['currency'] = groupobj.currency
        grpdict['basedontopic'] = groupobj.basedontopic
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
            postdict['attachmentfile'] = postobj.attachmentfile
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
            gmqset = GroupMember.objects.filter(group=groupobj, member=userobj, status=True).order_by('-membersince')
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
        grppaidtxnqset = GroupPaidTransactions.objects.filter(group=groupobj, payer=userobj).order_by('-transdatetime')
        grpdict['memberstatus'] = "Not a member yet"
        if list(grppaidtxnqset).__len__() > 0:
            grppaidtxnobj = grppaidtxnqset[0]
            targetdate = grppaidtxnobj.targetperiod
            grpdict['memberstatus'] = "Member till %s"%str(targetdate)
            tz_info = targetdate.tzinfo
            currdate = datetime.datetime.now(tz_info)
            if currdate > targetdate:
                grpdict['memberstatus'] = "Subscription expired on %s"%str(targetdate)
                grpdict['alreadyallowed'] = 0 # This user needs to pay again to be a member of the group. The previous membership has expired.
            else:
                pass
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
            joinrequest.outcome = 'open'
            joinrequest.active = True
            joinrequest.reason += "require owner perms" 
            # The group owner will be presented with a page listing all join requests whose  
            # 'outcome' is 'open' and 'reason' is 'require owner perms'.
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
                message = "Join request sent successfully."
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
            message = "Success: Sent a Gentle Reminder to %s"%groupobj.owner
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
            message = "Could not send a gentle reminder. Error: %s"%sys.exc_info()[1].__str__()
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
    groupmembername, groupname, owned = None, None, None
    if request.POST.has_key('membername'):
        groupmembername = request.POST['membername']
    if request.POST.has_key('groupname'):
        groupname = request.POST['groupname']
    if request.POST.has_key('owned'):
        owned = request.POST['owned']
    if not groupmembername or not groupname: # if either of the variables is None, we will set a message and return
        message = error_msg('1087')
        response = HttpResponse(message)
        return response
    # All is well if we are here... extract data from Network_group
    grpobj = None
    grpqset = None
    try:
        grpqset = Group.objects.filter(groupname=groupname)
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
    contextdict['dispname'] = userobj.displayname
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
    contextdict['basedontopic'] = grpobj.basedontopic
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
        contextdict['subscriptionfee'] = grpobj.subscription_fee
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
    # Get a list of the top level posts (relatedpost_id=None)
    grppostsqset = Post.objects.filter(posttargetgroup=grpobj).filter(relatedpost_id=None).order_by('-createdon')[:(int(mysettings.MAX_POSTS_IN_PAGE) + 1)] # We limit results to first batch of the set here.
    postcontent = []
    for grppost in grppostsqset:
        content = grppost.postcontent
        content = content.replace("\n", "<br>")
        poster = grppost.poster.displayname
        msgtag = grppost.postmsgtag
        posttargettype = grppost.posttargettype
        posttargetgroup = grppost.posttargetgroup
        posttargetuser = grppost.posttargetuser
        posttargettest = grppost.posttargettest
        attachmentfile = grppost.attachmentfile
        attachmentfile = "media/" + poster + "/posts/" + attachmentfile
        scope = 'public'
        if grppost.scope != 'public':
            continue # should be shown only to users who are in the contact list of the current user - will be implemented later.
        if grppost.deleted or grppost.hidden: # Do not show this post.
            continue
        stars = grppost.stars
        postid = grppost.id
        # Now find out which posts are related to this post using the relatedpost_id field
        subposts = Post.objects.filter(relatedpost_id=postid).order_by('-createdon')
        subpostlist = []
        for subp in subposts:
            try:
                subcontent = subp.postcontent
                subcontent = subcontent.replace("\n", "<br>")
                subposter = subp.poster.displayname
                subattachment = subp.attachmentfile
                subattachment = "media/" + subposter + "/posts/" + subattachment
                subscope = 'public'
                if subp.scope != 'public':
                    continue
                if subp.deleted or subp.hidden:
                    continue
                substars = subp.stars
                subprofpic = "media/" + subp.poster.displayname + "/images/" + str(subp.poster.userpic)
                subpostdate = subp.createdon
                subpostid = subp.id
                subpostdate = skillutils.pythontomysqldatetime(str(subpostdate))
                subpost_params = [ subcontent, subposter, subattachment, subscope, substars.__str__(), subprofpic, subpostdate, subpostid ]
                subpostlist.append(subpost_params)
            except:
                message = error_msg('1135') + "<br>" + sys.exc_info()[1].__str__()
                response = HttpResponse(message)
                continue
        profpic = "media/" + grppost.poster.displayname + "/images/" + str(grppost.poster.userpic)
        postdate = str(grppost.createdon)
        try:
            postdate = skillutils.pythontomysqldatetime(postdate)
        except:
            postdate = ""
        postid = grppost.id
        
        postattr = (content, poster, attachmentfile, scope, stars.__str__(), profpic, postdate, postid, msgtag, posttargettype, subpostlist)
        postcontent.append(postattr)
    try:
        postcontentenc = base64.b64encode(json.dumps(postcontent))
    except:
        message = error_msg('1135') + "\n" + sys.exc_info()[1].__str__()
        print message
        response = HttpResponse(message)
        return response
    contextdict['groupposts'] = postcontentenc
    if isowner is True:
        joinrequestsinfo = { 'open' : [], 'close' : [], 'refuse' : [], 'accept' : [] }
        joinreqsopenqset = GroupJoinRequest.objects.filter(group=grpobj, outcome='open')
        joinreqsclosedqset = GroupJoinRequest.objects.filter(group=grpobj, outcome='close')
        joinreqsrefuseqset = GroupJoinRequest.objects.filter(group=grpobj, outcome='refuse')
        joinreqsacceptqset = GroupJoinRequest.objects.filter(group=grpobj, outcome='accept')
        for joinreq in joinreqsopenqset:
            displayname = joinreq.user.displayname
            fullname = joinreq.user.firstname + " " + joinreq.user.middlename + " " + joinreq.user.lastname
            requestdtobj = joinreq.requestdate
            requestdate = skillutils.yetanotherpythontomysqldatetime(requestdtobj)
            userimageurl = "media/%s/images/%s"%(joinreq.user.displayname, joinreq.user.userpic)
            ll = [ displayname, fullname, requestdate, userimageurl ]
            joinrequestsinfo['open'].append(ll)
        for joinreq in joinreqsclosedqset:
            displayname = joinreq.user.displayname
            fullname = joinreq.user.firstname + " " + joinreq.user.middlename + " " + joinreq.user.lastname
            requestdtobj = joinreq.requestdate
            requestdate = skillutils.yetanotherpythontomysqldatetime(requestdtobj)
            userimageurl = "media/%s/images/%s"%(joinreq.user.displayname, joinreq.user.userpic)
            ll = [ displayname, fullname, requestdate, userimageurl ]
            joinrequestsinfo['close'].append(ll)
        for joinreq in joinreqsrefuseqset:
            displayname = joinreq.user.displayname
            fullname = joinreq.user.firstname + " " + joinreq.user.middlename + " " + joinreq.user.lastname
            requestdtobj = joinreq.requestdate
            requestdate = skillutils.yetanotherpythontomysqldatetime(requestdtobj)
            userimageurl = "media/%s/images/%s"%(joinreq.user.displayname, joinreq.user.userpic)
            ll = [ displayname, fullname, requestdate, userimageurl ]
            joinrequestsinfo['refuse'].append(ll)
        for joinreq in joinreqsacceptqset:
            displayname = joinreq.user.displayname
            fullname = joinreq.user.firstname + " " + joinreq.user.middlename + " " + joinreq.user.lastname
            requestdtobj = joinreq.requestdate
            requestdate = skillutils.yetanotherpythontomysqldatetime(requestdtobj)
            userimageurl = "media/%s/images/%s"%(joinreq.user.displayname, joinreq.user.userpic)
            grpmemberqset = GroupMember.objects.filter(group=grpobj, member=joinreq.user)
            """
            if grpmemberqset.__len__() == 0:
                if grpobj.owner != joinreq.user:
                    message = error_msg('1115')
                    response = HttpResponse(message)
                    return response
            """
            if grpmemberqset.__len__() > 0:
                grpmemberobj = grpmemberqset[0]
                if grpmemberobj.group.owner.displayname != grpmemberobj.member.displayname:
                    ll = [ displayname, fullname, requestdate, userimageurl, grpmemberobj.removed, grpmemberobj.blocked ]
                else:
                    ll = [ displayname, fullname, requestdate, userimageurl, -1, -1 ]
                joinrequestsinfo['accept'].append(ll)
        joinrequestsinfo_str = json.dumps(joinrequestsinfo)
        contextdict['joinrequestsinfo'] = base64.b64encode(joinrequestsinfo_str) # Had to encode this as otherwise the data gets garbled.
    if grpobj.ispaid:
        bankacctqset = OwnerBankAccount.objects.filter(groupowner=grpobj.owner)
        contextdict['ownerbankaccts'] = tuple(bankacctqset) # should be immutable
        contextdict['bankaccountid'] = ""
        if bankacctqset.__len__() > 0:
            contextdict['bankaccountid'] = bankacctqset[0].id
    contextdict['postsperpage'] = mysettings.MAX_POSTS_IN_PAGE
    # Render content using 'contextdict'
    tmpl = get_template("network/managegroups.html")
    if owned:
        tmpl = get_template("network/manageownedgroups.html")
    contextdict.update(csrf(request))
    cxt = Context(contextdict)
    try:
        managegroupshtml = tmpl.render(cxt)
    except:
        print sys.exc_info()[1].__str__()
        message = error_msg('1132')
        response = HttpResponse(message)
        return response
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        managegroupshtml = managegroupshtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(managegroupshtml)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def nextpostlist(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    groupname, nextfirst, nextlast = "", -1, -1
    if request.POST.has_key('groupname'):
        groupname = request.POST['groupname']
    if request.POST.has_key('nextfirst'):
        nextfirst = int(request.POST['nextfirst'])
    if request.POST.has_key('nextlast'):
        nextlast = int(request.POST['nextlast'])
    if not groupname:
        message = error_msg('1087')
        response = HttpResponse(message)
        return response
    if nextfirst == -1 or nextlast == -1:
        message = error_msg('1136')
        response = HttpResponse(message)
        return response
    grpobj = None
    try:
        grpobj = Group.objects.get(groupname=groupname)
    except:
        message = error_msg('1084')%groupname
        response = HttpResponse(message)
        return response
    postsqset = Post.objects.filter(posttargetgroup=grpobj).filter(relatedpost_id=None).order_by('-createdon')[nextfirst:(nextlast + 1)]
    postcontent = []
    for grppost in postsqset:
        content = grppost.postcontent
        content = content.replace("\n", "<br>")
        poster = grppost.poster.displayname
        msgtag = grppost.postmsgtag
        posttargettype = grppost.posttargettype
        posttargetgroup = grppost.posttargetgroup
        posttargetuser = grppost.posttargetuser
        posttargettest = grppost.posttargettest
        attachmentfile = grppost.attachmentfile
        attachmentfile = "media/" + poster + "/posts/" + attachmentfile
        scope = 'public'
        if grppost.scope != 'public':
            continue # should be shown only to users who are in the contact list of the current user - will be implemented later.
        if grppost.deleted or grppost.hidden: # Do not show this post.
            continue
        stars = grppost.stars
        postid = grppost.id
        # Now find out which posts are related to this post using the relatedpost_id field
        subposts = Post.objects.filter(relatedpost_id=postid).order_by('-createdon')
        subpostlist = []
        for subp in subposts:
            try:
                subcontent = subp.postcontent
                subcontent = subcontent.replace("\n", "<br>")
                subposter = subp.poster.displayname
                subattachment = subp.attachmentfile
                subattachment = "media/" + subposter + "/posts/" + subattachment
                subscope = 'public'
                if subp.scope != 'public':
                    continue
                if subp.deleted or subp.hidden:
                    continue
                substars = subp.stars
                subprofpic = "media/" + subp.poster.displayname + "/images/" + str(subp.poster.userpic)
                subpostdate = subp.createdon
                subpostid = subp.id
                subpostdate = skillutils.pythontomysqldatetime(str(subpostdate))
                subpost_params = [ subcontent, subposter, subattachment, subscope, substars.__str__(), subprofpic, subpostdate, subpostid ]
                subpostlist.append(subpost_params)
            except:
                message = error_msg('1135') + "<br>" + sys.exc_info()[1].__str__()
                response = HttpResponse(message)
                continue
        profpic = "media/" + grppost.poster.displayname + "/images/" + str(grppost.poster.userpic)
        postdate = str(grppost.createdon)
        try:
            postdate = skillutils.pythontomysqldatetime(postdate)
        except:
            postdate = ""
        postid = grppost.id
        
        postattr = (content, poster, attachmentfile, scope, stars.__str__(), profpic, postdate, postid, msgtag, posttargettype, subpostlist)
        postcontent.append(postattr)
    try:
        postcontentenc = base64.b64encode(json.dumps(postcontent))
    except:
        message = error_msg('1135') + "\n" + sys.exc_info()[1].__str__()
        print message
        response = HttpResponse(message)
        return response
    message = postcontentenc
    response = HttpResponse(message)
    return response


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
        groupname = groupname.replace("+", " ")
        groupname = groupname.replace("%20", " ")
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
    topics, maxmemberslimit, grouptypes, allowentry, ispaid, entryfee, subscriptionfee, bankname, bankbranch, acctname, acctnum, ifsccode, alltestsowned, adminremarks, groupname, currency = ("" for i in range(0,16))
    req_owner_perms = False
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
    if request.POST.has_key('payscheme'):
        payscheme = request.POST['payscheme']
    if(payscheme == "entryfeebased"):
        if request.POST.has_key('entryfee'):
            entryfee = request.POST['entryfee']
        else:
            entryfee = 0.00
    else:
        if request.POST.has_key('subscriptionfee'):
            subscriptionfee = request.POST['subscriptionfee']
        else:
            subscriptionfee = 0.00
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
    if request.POST.has_key('require_owner_perms'):
        req_owner_perms = True
    groupqset = Group.objects.filter(groupname=grpname).filter(owner=userobj)
    if groupqset.__len__() == 0:
        message = error_msg('1088')
        response = HttpResponse(message)
        return response
    groupobj = groupqset[0]
    groupobj.maxmemberslimit = maxmemberslimit
    groupobj.grouptype = grouptypes
    groupobj.basedontopic = topics
    adminremarks = re.sub("['\"]", "&amp;quot;", adminremarks)
    groupobj.adminremarks = adminremarks
    groupobj.allowentry = allowentry
    groupobj.ispaid = ispaid
    groupobj.require_owner_permission = req_owner_perms
    if entryfee == "":
        groupobj.entryfee = 0
    else:
        groupobj.entryfee = float(entryfee)
        groupobj.currency = currency
    if subscriptionfee == "":
        groupobj.subscription_fee = 0
    else:
        groupobj.subscription_fee = float(subscriptionfee)
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
    subscriptionfee = ""
    if request.POST.has_key('groupid'):
        groupid = request.POST['groupid']
    if request.POST.has_key('entryfee'):
        entryfee = request.POST['entryfee']
    if request.POST.has_key('subscriptionfee'):
        subscriptionfee = request.POST['subscriptionfee']
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
    contextdict['subscription_amt'] = subscriptionfee
    contextdict['total_amt'] = entryfee
    contextdict['signature'] = mysettings.PAYU_SECOND_ID
    contextdict['extOrderId'] = skillutils.generate_random_string()
    contextdict['discountamt'] = 0
    contextdict['stripeconfirmurl'] = skillutils.gethosturl(request) + "/" + mysettings.STRIPE_CONFIRM_URL
    contextdict['buyeremail'] = userobj.emailid
    contextdict['buyerphone'] = userobj.mobileno
    contextdict['firstname'] = userobj.firstname
    contextdict['lastname'] = userobj.lastname
    contextdict['payscheme'] = "entryfee"
    targetdate = datetime.datetime.now() + datetime.timedelta(days=36500)
    contextdict['targetdate'] = targetdate
    contextdict['currencyrateurl'] = skillutils.gethosturl(request) + "/" + mysettings.CURRENCY_RATE_URL
    #tmpl = get_template("network/payu_payment.html")
    tmpl = get_template("network/stripe_payment.html")
    contextdict.update(csrf(request))
    cxt = Context(contextdict)
    stripehtml = tmpl.render(cxt)
    response = HttpResponse(stripehtml)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def showsubscriptionpaymentscreen(request):
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
    subscriptionfee = ""
    if request.POST.has_key('groupid'):
        groupid = request.POST['groupid']
    if request.POST.has_key('subscriptionfee'):
        subscriptionfee = request.POST['subscriptionfee']
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
    subscriptionfee = groupobj.subscription_fee
    curr = groupobj.currency
    if curr == 'USD':
        equiv_rs = subscriptionfee * skillutils.fetch_currency_rate('USD', 'INR')
    elif curr == 'EUR':
        equiv_rs = subscriptionfee * skillutils.fetch_currency_rate('EUR', 'INR')
    else:
        equiv_rs = subscriptionfee
    contextdict['order_desc'] = subscriptionfee
    contextdict['posId'] = mysettings.PAYU_POS_ID
    contextdict['groupname'] = groupobj.groupname
    contextdict['groupid'] = groupid
    contextdict['subscription_amt'] = subscriptionfee
    contextdict['total_amt'] = subscriptionfee
    contextdict['signature'] = mysettings.PAYU_SECOND_ID
    contextdict['extOrderId'] = skillutils.generate_random_string()
    contextdict['discountamt'] = 0
    contextdict['stripeconfirmurl'] = skillutils.gethosturl(request) + "/" + mysettings.STRIPE_CONFIRM_URL
    contextdict['buyeremail'] = userobj.emailid
    contextdict['buyerphone'] = userobj.mobileno
    contextdict['firstname'] = userobj.firstname
    contextdict['lastname'] = userobj.lastname
    contextdict['payscheme'] = "subscriptionfee"
    targetdate = datetime.datetime.now() + datetime.timedelta(days=30)
    contextdict['targetdate'] = targetdate
    contextdict['currencyrateurl'] = skillutils.gethosturl(request) + "/" + mysettings.CURRENCY_RATE_URL
    #tmpl = get_template("network/payu_payment.html")
    tmpl = get_template("network/stripe_payment.html")
    contextdict.update(csrf(request))
    cxt = Context(contextdict)
    stripehtml = tmpl.render(cxt)
    response = HttpResponse(stripehtml)
    return response


def getcurrencyrate(request):
    if request.POST.has_key('currname'):
        currname = request.POST['currname']
    exchangerateqset = ExchangeRates.objects.filter(curr_from='USD', curr_to=currname).order_by('-dateofrate')
    if exchangerateqset.__len__() > 0:
        exchangerate = exchangerateqset[0].conv_rate
        return HttpResponse(exchangerate)
    return HttpResponse("1")


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
    #convert the amount (in USD) to PLN
    exchangerateqset = ExchangeRates.objects.filter(curr_from='USD', curr_to='PLN').order_by('-dateofrate')
    exchangerate = mysettings.PLN_TO_USD
    if exchangerateqset.__len__() > 0:
        exchangerate = exchangerateqset[0].conv_rate
    totalamount = float(totalamount)/float(exchangerate) # This is in USD
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
    # First, make a request to get Bearer Id
    payuposid = mysettings.PAYU_POS_ID
    payuclientsecret = mysettings.PAYU_CLIENT_SECRET
    client_ip = skillutils.get_client_ip(request)
    postdata = "grant_type=client_credentials&client_id=" + payuposid + "&client_secret=" + payuclientsecret;
    no_redirect_opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), skillutils.NoRedirectHandler())
    httpHeaders = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'application/json', 'Accept-Language' : 'en-US,en;q=0.8', 'Accept-Encoding' : 'gzip,deflate,sdch', 'Connection' : 'keep-alive', 'Host' : mysettings.PAYU_DOMAIN, 'Cache-Control' : 'no-cache', 'Pragma' : 'no-cache' }
    content_length = postdata.__len__()
    httpHeaders['Content-Length'] = content_length
    pageRequest = urllib2.Request(mysettings.PAYU_AUTH_BEARER_CODE_URL, postdata, httpHeaders)
    try:
        pageResponse = no_redirect_opener.open(pageRequest)
    except:
        pageResponse = None
    if not pageResponse:
        message = "Could not get the bearer code: %s"%sys.exc_info()[1].__str__()
        response = HttpResponse(message)
        return response
    pageContent = pageResponse.read()
    bearerinfodict = json.loads(pageContent)
    bearertoken = bearerinfodict['access_token']
    # Now, make the call to the PAYU orders API endpoint...
    ordersUrl = mysettings.PAYU_ORDERS_URL
    httpHeaders['Authorization'] = "Bearer %s"%bearertoken
    httpHeaders['Content-Type'] = "application/json"
    urlnotify = mysettings.URL_PROTOCOL + request.META['SERVER_NAME'] + "/" + mysettings.MY_PAYU_NOTIFY_URL_PATH + orderId + "/"
    groupobj = Group.objects.get(id=groupid)
    if not groupobj:
        message = error_msg('1086')
        response = HttpResponse(message)
        return response
    xchnginr = skillutils.fetch_currency_rate('INR', 'USD')
    xchngeur = skillutils.fetch_currency_rate('EUR', 'USD')
    xchngpln = skillutils.fetch_currency_rate('PLN', 'USD')
    
    productunitprice = groupobj.entryfee
    if groupobj.currency == 'INR':
        productunitprice = groupobj.entryfee * xchnginr
    elif groupobj.currency == 'EUR':
        productunitprice = groupobj.entryfee * xchngeur
    elif groupobj.currency == 'PLN':
        productunitprice = groupobj.entryfee * xchngpln
    else:
        pass
    #totalamount = productunitprice
    #data = { 'notifyUrl' : urlnotify, 'customerIp' : customerIP, 'merchantPosId' : payuposid, 'description' : orderdesc, 'currencyCode' : 'PLN', 'totalAmount' : str(int(totalamount)*100), 'buyer' : { "email": buyeremail,  "phone": buyerphone, "firstName": buyerfirstname, "lastName": buyerlastname, "language": "en"  }, 'settings' : { "invoiceDisabled":"true" }, 'products' : [{ "name": productname, "unitPrice": str(int(float(productunitprice))*100),  "quantity": "1"  }]}
    data = { 'notifyUrl' : urlnotify, 'customerIp' : customerIP, 'merchantPosId' : payuposid, 'description' : orderdesc, 'currencyCode' : 'PLN', 'totalAmount' : str(totalamount), 'buyer' : { "email": buyeremail,  "phone": buyerphone, "firstName": buyerfirstname, "lastName": buyerlastname, "language": "en"  }, 'settings' : { "invoiceDisabled":"true" }, 'products' : [{ "name": productname, "unitPrice": str(productunitprice),  "quantity": "1"  }]}
    # We are sending PLN above, but it should be USD. Need to see how to do that. 
    # PayU has this irritating behaviour of hard setting the currency value to fucking PLN.
    jsondata = json.dumps(data)
    response = HttpResponse(jsondata)
    return response
    content_length = jsondata.__len__()
    httpHeaders['Content-Length'] = content_length
    pageRequest = urllib2.Request(ordersUrl, jsondata, httpHeaders)
    try:
        pageResponse = no_redirect_opener.open(pageRequest)
    except:
        pageResponse = None
    if not pageResponse:
        message = "Could not get the orders page: %s"%sys.exc_info()[1].__str__()
        response = HttpResponse(message)
        return response
    jsonContent = pageResponse.read()
    contentDict = json.loads(jsonContent)
    orderId = contentDict['orderId']
    redirectUri = contentDict['redirectUri']
    status = contentDict['status']
    response = HttpResponse(redirectUri)
    # Add or update a record in the Network_groupjoinrequest table.
    joinreq = GroupJoinRequest()
    joinreq.group = groupobj
    joinreq.user = userobj
    joinreq.orderId = orderId
    joinreq.requestdate = skillutils.pythontomysqldatetime2(str(datetime.datetime.now()))
    joinreq.outcome = 'open'
    joinreq.active = False # IMPORTANT NOTE: Remember to set this to 'True' when the transaction completes successfully.
    joinreq.reason = 'payment in progress'
    # Create a transaction object and post the data to payU ordering API.
    txnobj = Transaction()
    txnobj.orderId = orderId
    txnobj.username = userobj.displayname
    txnobj.user = userobj
    txnobj.group = groupobj
    txnobj.plan = None
    txnobj.usersession = sesscode
    joinreq.requestdate = skillutils.pythontomysqldatetime2(str(datetime.datetime.now()))
    txnobj.payamount = groupobj.entryfee * (1 - mysettings.CUT_FRACTION)
    if groupobj.currency == 'INR':
        txnobj.payamount = groupobj.entryfee * xchnginr
    elif groupobj.currency == 'EUR':
        txnobj.payamount = groupobj.entryfee * xchngeur
    elif groupobj.currency == 'PLN':
        txnobj.payamount = groupobj.entryfee * xchngpln
    else:
        pass
    if totalamount < txnobj.payamount: # TODO: check if any discount is to be processed
        pass
    txnobj.transactiondate = datetime.datetime.now()
    txnobj.paymode = 'PAYU'
    txnobj.comments = "Join paid group named '%s' by user '%s'"%(groupobj.groupname, userobj.displayname)
    txnobj.invoice_email = buyeremail
    txnobj.trans_status = False # Initialized to False. Once payment is made, it will be updated to True.
    txnobj.clientIp = ""
    txnobj.extOrderId = ""
    try:
        txnobj.save()
        joinreq.save()
    except:
        response = HttpResponse(sys.exc_info()[1].__str__())
    orderId = contentDict['orderId']
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def confirmpayment_stripe(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    customerIP, orderdesc, currencycode, posId, notifyurl, continueurl, productname, productquantity, productunitprice, totalamount, orderId, groupid, buyeremail, customernameoncard, currency, cardnumber, cvv, expirymonth, expiryyear, city, state, country, zipcode, cardtype, address1, address2, payscheme = ('' for i in range(0, 27))
    paramnamesdict = {}
    if request.POST.has_key('customerIp'):
        customerIP = request.POST['customerIp']
    if request.POST.has_key('payscheme'):
        payscheme = request.POST['payscheme']
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
    if request.POST.has_key('currency'):
        currency = request.POST['currency']
    #convert the amount (in USD) to whatever currency selected by the user.
    exchangerateqset = ExchangeRates.objects.filter(curr_from='USD', curr_to=currency).order_by('-dateofrate')
    if exchangerateqset.__len__() > 0:
        exchangerate = exchangerateqset[0].conv_rate
    else:
        exchangerate = 1
        return HttpResponse("Exchange rate for USD to " + currency + "does not exist")
    totalamount = float(totalamount)*float(exchangerate) # This is in currency selected by user.
    if request.POST.has_key('customername'):
        customernameoncard = request.POST['customername']
    if request.POST.has_key('card_no'):
        cardnumber = request.POST['card_no']
    if request.POST.has_key('cvvNumber'):
        cvv = request.POST['cvvNumber']
    if request.POST.has_key('ccExpiryMonth'):
        expirymonth = request.POST['ccExpiryMonth']
    if request.POST.has_key('ccExpiryYear'):
        expiryyear = request.POST['ccExpiryYear']
    if request.POST.has_key('addressline1'):
        address1 = request.POST['addressline1']
    if request.POST.has_key('addressline2'):
        address2 = request.POST['addressline2']
    if request.POST.has_key('city'):
        city = request.POST['city']
    if request.POST.has_key('state'):
        state = request.POST['state']
    if request.POST.has_key('country'):
        country = request.POST['country']
    if request.POST.has_key('zipcode'):
        zipcode = request.POST['zipcode']
    if request.POST.has_key('cardtype'):
        cardtype = request.POST['cardtype']
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
    address = address1 + " " + address2

    stripesecret = mysettings.STRIPE_API_SECRET
    stripe.api_key = stripesecret
    client_ip = skillutils.get_client_ip(request)
    try:
        token = stripe.Token.create(
        card={
            "number": cardnumber,
            "exp_month": expirymonth,
            "exp_year": expiryyear,
            "cvc": cvv,
	  },
        )
    except:
        return HttpResponse("Token object could not be created: %s"%sys.exc_info()[1].__str__())
    try:
        addressdict = {"line1" : address1, "city" : city, "country" : country, "postal_code" : zipcode }
        customer = stripe.Customer.create(name=customernameoncard, address=addressdict, source=token.id, description="Customer Email: " + buyeremail)
    except:
        return HttpResponse("Customer object could not be created: %s"%sys.exc_info()[1].__str__())
    custid = customer.id
    chargeid = None
    try:
        charge = stripe.Charge.create(amount=int(totalamount*100), currency=currency.lower(), customer=custid)
    except:
        return HttpResponse("Charge object could not be created: %s"%sys.exc_info()[1].__str__())
    response = HttpResponse("<p style='color:blue;'>The amount %s was successfully paid. The Transaction (Charge) Id is %s. Please note it down for any future reference.</p>"%(str(round(totalamount, 2)), charge.id))
    chargeid = charge.id
    groupobj = Group.objects.get(id=groupid)
    if not groupobj:
        message = error_msg('1086')
        response = HttpResponse(message)
        return response
    """
    xchnginr = skillutils.fetch_currency_rate('USD', 'INR')
    xchngeur = skillutils.fetch_currency_rate('USD', 'EUR')
    xchnggbp = skillutils.fetch_currency_rate('USD', 'GBP')
    """
    xchnginr = 77.00
    xchngeur = 0.89
    xchnggbp = 0.81
    # Add or update a record in the Network_groupjoinrequest table.
    joinreq = GroupJoinRequest()
    joinreq.group = groupobj
    joinreq.user = userobj
    joinreq.orderId = orderId
    joinreq.requestdate = skillutils.pythontomysqldatetime2(str(datetime.datetime.now()))
    joinreq.outcome = 'open'
    joinreq.active = False # IMPORTANT NOTE: Remember to set this to 'True' when the transaction completes successfully.
    joinreq.reason = 'payment in progress'
    # Create a transaction object.
    txnobj = Transaction()
    txnobj.orderId = orderId
    txnobj.username = userobj.displayname
    txnobj.user = userobj
    txnobj.group = groupobj
    txnobj.plan = None
    txnobj.usersession = sesscode
    joinreq.requestdate = skillutils.pythontomysqldatetime2(str(datetime.datetime.now()))
    grppaidtxnobj = GroupPaidTransactions()
    grppaidtxnobj.group = groupobj
    grppaidtxnobj.payer = userobj
    grppaidtxnobj.currency = "USD"
    grppaidtxnobj.payeripaddress = customerIP
    grppaidtxnobj.stripechargeid = chargeid
    # Handle payscheme here... txnobj.payamount should always be stored as USD
    if payscheme == "entryfee":
        txnobj.payamount = groupobj.entryfee * (1 - mysettings.CUT_FRACTION)
        if groupobj.currency == 'INR':
            txnobj.payamount = float(groupobj.entryfee/xchnginr) * (1 - mysettings.CUT_FRACTION)
        elif groupobj.currency == 'EUR':
            txnobj.payamount = float(groupobj.entryfee/xchngeur) * (1 - mysettings.CUT_FRACTION)
        elif groupobj.currency == 'GBP':
            txnobj.payamount = float(groupobj.entryfee/xchnggbp) * (1 - mysettings.CUT_FRACTION)
        else:
            pass
        grppaidtxnobj.amount = txnobj.payamount
        grppaidtxnobj.reason = "entryfee"
        grppaidtxnobj.targetperiod = datetime.datetime.now() + datetime.timedelta(days=36500) # Set a time long enough into the future.
    elif payscheme == "subscriptionfee":
        txnobj.payamount = groupobj.subscription_fee * (1 - mysettings.CUT_FRACTION)
        if groupobj.currency == 'INR':
            txnobj.payamount = float(groupobj.subscription_fee/xchnginr) * (1 - mysettings.CUT_FRACTION)
        elif groupobj.currency == 'EUR':
            txnobj.payamount = float(groupobj.subscription_fee/xchngeur) * (1 - mysettings.CUT_FRACTION)
        elif groupobj.currency == 'GBP':
            txnobj.payamount = float(groupobj.subscription_fee/xchnggbp) * (1 - mysettings.CUT_FRACTION)
        else:
            pass
        grppaidtxnobj.amount = txnobj.payamount
        grppaidtxnobj.reason = "subscriptionfee"
        grppaidtxnobj.targetperiod = datetime.datetime.now() + datetime.timedelta(days=30)
    else:
        pass
    if totalamount < txnobj.payamount: # TODO: check if any discount is to be processed
        pass
    txnobj.transactiondate = datetime.datetime.now()
    txnobj.paymode = 'STRIPE'
    txnobj.comments = "Join paid group named '%s' by user '%s'"%(groupobj.groupname, userobj.displayname)
    txnobj.invoice_email = buyeremail
    txnobj.trans_status = True # Payment is made, hence True.
    txnobj.clientIp = ""
    txnobj.extOrderId = ""
    txnobj.txnid_stripe = chargeid
    grpmember = GroupMember()
    grpmember.member = userobj
    grpmember.group = groupobj
    grpmember.status = True
    grpmember.removed = False
    grpmember.blocked = False
    try:
        txnobj.save()
        message = "Successfully joined group."
        joinreq.reason = message
        joinreq.active = True
        joinreq.outcome = "accept" # Set the outcome of this request to 'accept' as the group owner has already received the entry fee.
        joinreq.save()
        grppaidtxnobj.save()
    except:
        response = HttpResponse(sys.exc_info()[1].__str__())
    try:
        grpmember.grppaidtxn_id = grppaidtxnobj.id
        grpmember.save()
    except:
        message = error_msg('1097')%(sys.exc_info()[1].__str__())
    return response


def notifypayupayment(request):
    pass


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
        respcode = resp.getcode()
        if respcode == '304':
            respheaders = resp.info()
            if respheaders.has_key('Location'):
                target = respheaders['Location']
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
        userqset = userqset.filter(emailid__icontains=emailid)
    if targetusername and targetusername != "":
        targetusername = targetusername.strip()
        userqset = userqset.filter(displayname__icontains=targetusername)
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


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def savegroupjoinstatus(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    ctr = 0
    displaynames, groupname, states = ("" for i in range(0,3))
    if request.POST.has_key('displaynames'):
        displaynames = request.POST['displaynames']
    if request.POST.has_key('groupname'):
        groupname = request.POST['groupname']
    if request.POST.has_key('states'):
        states = request.POST['states']
    if request.POST.has_key('hit'):
        hit = request.POST['hit']
    if hit == 'single':
        ctr = int(request.POST['counter'])
    if hit == 'multi':
        blockstates = request.POST['blockstates']
        removestates = request.POST['removestates']
    blockstates_parts = []
    removestates_parts = []
    displaynames_list = displaynames.split("##")
    states_list = states.split("##")
    state = 'open'
    if not groupname or displaynames.__len__() == 0:
        message = error_msg('1111')
        response = HttpResponse(message)
        return response
    groupobj = None
    try:
        groupobj = Group.objects.get(groupname=groupname)
    except:
        message = error_msg('1112')
        response = HttpResponse(message)
        return response

    for dispname in displaynames_list:
        if states_list.__len__() > ctr:
            state = states_list[ctr]
        else:
            state = states_list[0] # case of a single record to save
        uobj = None
        try:
            uobj = User.objects.get(displayname=dispname)
        except:
            continue
        greqs = GroupJoinRequest.objects.filter(user=uobj, group=groupobj)
        chkblock = 0
        chkremv = 0
        if hit == 'multi': # Handling multiple records
            blockstates_parts = blockstates.split("##")
            removestates_parts = removestates.split("##")
            blockstates_parts.pop()
            removestates_parts.pop()
            chkblock = blockstates_parts[ctr]
            chkremv = removestates_parts[ctr]
            print dispname + "#####" + chkblock + "####" + chkremv
        else:
            if request.POST.has_key('chkblock_' + str(ctr)):
                chkblock = 1
            if request.POST.has_key('chkremv_' + str(ctr)):
                chkremv = 1
        for groupjoinreq in greqs:
            if groupjoinreq.outcome == 'accept' and state != 'accept':
                message = error_msg('1114')
                response = HttpResponse(message)
                return response
            groupjoinreq.outcome = state
            #groupjoinreq.active = False
            groupjoinreq.save()
        
        if state == "accept":
            grpmemberqset = GroupMember.objects.filter(member=uobj, group=groupobj)# Check if user is already a member
            groupmember = None
            if grpmemberqset.__len__() == 0:
                groupmember = GroupMember()
                groupmember.group = groupobj
                groupmember.member = uobj
                groupmember.membersince = skillutils.yetanotherpythontomysqldatetime(datetime.datetime.now())
            elif grpmemberqset.__len__() >= 1:
                groupmember = grpmemberqset[0]
            try:
                groupmember.status = True
                if groupmember.group.owner.displayname != groupmember.member.displayname:#user is not the owner of the group
                    groupmember.removed = int(chkremv)
                    groupmember.blocked = int(chkblock)
                elif groupmember.group.owner.displayname == groupmember.member.displayname and (int(chkremv) == 1 or int(chkblock) == 1):
                    message = error_msg('1117')
                    response = HttpResponse(message)
                    return response
            except:
                message = error_msg('1116')
                response = HttpResponse(message)
                return response
            if chkremv:
                groupmember.removeagent = 'owner'
                groupmember.lastremovaldate = skillutils.yetanotherpythontomysqldatetime(datetime.datetime.now())
            try:
                groupmember.save()
            except:
                message = error_msg('1118')
                response = HttpResponse(message)
                return response
            message = "accept##" + dispname + "||"
        elif state == "refuse":
            message = "refuse##" + dispname + "||" # Need to handle this 
        elif state == "close":
            message = "close##" + dispname + "||"
        try:
            ctr += 1
        except:
            print sys.exc_info()[1].__str__()
            ctr += 1
    message = error_msg('1113')
    response = HttpResponse(message)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def handleconnectinvitation(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    inviteid, sendername, invitationstatus = -1, "", "refuse"
    if request.POST.has_key('inviteid'):
        inviteid = int(request.POST['inviteid'])
    if request.POST.has_key('sendername'):
        sendername = request.POST['sendername']
    if request.POST.has_key('invitationstatus'):
        invitationstatus = request.POST['invitationstatus']
    fromuserqset = User.objects.filter(displayname = sendername)
    fromuserobj = None
    if fromuserqset.__len__() == 0:
        message = error_msg('1120')
        response = HttpResponse(message)
        return response
    else:
        fromuserobj = fromuserqset[0]
    conninviteqset = ConnectionInvitation.objects.filter(id=inviteid)
    if conninviteqset.__len__() == 0:
        message = error_msg('1121')
        response = HttpResponse(message)
        return response
    conninviteobj = conninviteqset[0]
    if invitationstatus == 'accept' or invitationstatus == 'refuse' or invitationstatus == 'close':
        conninviteobj.invitationstatus = invitationstatus
        try:
            conninviteobj.save()
        except:
            message = error_msg('1125')%sys.exc_info()[1].__str__()
            print sys.exc_info()[1].__str__()
            response = HttpResponse(message)
            return response
    else:
        pass
    # 2 records will be inserted by code below in Network_connection
    # - one with focususer set to the userobj, and other with connectedto 
    # as userobj
    if invitationstatus == 'accept':
        existingconnectionqset = Connection.objects.filter(focususer=userobj, connectedto=fromuserobj)
        existingconnectionqset2 = Connection.objects.filter(focususer=fromuserobj, connectedto=userobj)
        if len(list(existingconnectionqset)) > 0 or len(list(existingconnectionqset2)) > 0:
            message = error_msg('1126')
            response = HttpResponse(message)
            return response
        connobj = Connection()
        connobj.focususer = userobj
        connobj.connectedto = fromuserobj
        connobj.connectedthru = ""
        try:
            connobj.save()
        except:
            message = error_msg('1122')
            response = HttpResponse(message)
            return response
        connobj2 = Connection()
        connobj2.focususer = fromuserobj
        connobj2.connectedto = userobj
        connobj2.connectedthru = ""
        try:
            connobj2.save()
        except:
            message = error_msg('1122')
            response = HttpResponse(message)
            return response
        message = error_msg('1123')
        response = HttpResponse(message)
        return response
    else:
        message = error_msg('1124')
        response = HttpResponse(message)
        return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def postmessagecontent(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    targetgroups, targetconnections, targettests, newthread, msgtag, postcontent = "", "", "", 0, "", ""
    postdata = dict(request.POST)
    if postdata.has_key('targetgroups'):
        targetgroups = postdata['targetgroups']
        for i in range(0,targetgroups.__len__()):
            if targetgroups[i] == '':
                targetgroups.pop(i)
    if postdata.has_key('targetconnections'):
        targetconnections = postdata['targetconnections']
        for i in range(0,targetconnections.__len__()):
            if targetconnections[i] == '':
                targetconnections.pop(i)
    if postdata.has_key('targettests'):
        targettests = postdata['targettests']
        for i in range(0,targettests.__len__()):
            if targettests[i] == '':
                targettests.pop(i)
    if postdata.has_key('newthread'):
        newthread = postdata['newthread']
    if postdata.has_key('msgtag'):
        msgtag = str(postdata['msgtag'][0])
    if postdata.has_key('postcontent'):
        postcontent = str(postdata['postcontent'][0])
    if postcontent.strip() == "" or msgtag.strip() == "":
        message = error_msg('1131')
        response = HttpResponse(message)
        return response
    postcontent = postcontent.replace("\n", "<br>")
    targetgroupids = targetgroups
    targetconnectionids = targetconnections
    targettestids = targettests
    if (targetgroupids.__len__() > 0 and targetconnectionids.__len__() > 0) or (targetgroupids.__len__() > 0 and targettestids.__len__() > 0) or (targetconnectionids.__len__() > 0 and targettestids.__len__() > 0):
        message = error_msg('1127')
        response = HttpResponse(message)
        return response
    attachmentfile = ""
    if request.FILES.has_key('postattachment'):
        postattachmentpath = mysettings.MEDIA_ROOT + os.path.sep + userobj.displayname + os.path.sep + "posts" + os.path.sep
        postattachmentfilename = request.FILES['postattachment'].name.split(".")[0]
        fpath, message, attachmentfile = skillutils.handleuploadedfile2(request.FILES['postattachment'], postattachmentpath, postattachmentfilename)
    # Now, if targetgroupids.__len__() > 0, send it to the group's messages.
    # Basically, all these will be stored in the Network_post table with the 
    # appropriate 'posttargettype' values ('group', 'user' or 'test').
    message = ""
    if targetgroupids.__len__() > 0:
        for tgid in targetgroupids:
            post = Post()
            targetgroup = Group.objects.get(id=tgid)
            # Check if the user is blocked from posting to the group. If so, continue with the next group.
            grpmemqset = GroupMember.objects.filter(group=targetgroup, member=userobj).order_by('-membersince')
            if grpmemqset.__len__() == 0: # user is not a member of this group, hence she can't post.
                continue
            if grpmemqset.__len__() > 0:
                grpmemobj = grpmemqset[0]
                if grpmemobj.blocked or grpmemobj.removed: # If the group member is blocked or removed, she can't post either.
                    continue
            post.posttargettype = 'group'
            post.posttargetgroup = targetgroup
            post.postmsgtag = msgtag
            post.poster = userobj
            post.postcontent = postcontent
            post.scope = 'public'
            post.attachmentfile = attachmentfile
            try:
                post.save()
            except:
                print "Error: %s"%sys.exc_info()[1].__str__()
                message += error_msg('1128')%sys.exc_info()[1].__str__()
                message += "\n"
                continue
        message += error_msg('1129')
        response = HttpResponse(message)
        return response
    if targetconnectionids.__len__() > 0:
        for tconnid in targetconnectionids:
            targetconnection = Connection.objects.get(id=tconnid)
            # Check if the connection has blocked this user. If so, continue with the next connection in the list.
            if targetconnection.blocked or targetconnection.deleted:
                continue
            post = Post()
            post.posttargettype = 'user'
            post.posttargetuser = targetconnection.connectedto
            post.postmsgtag = msgtag
            post.poster = userobj
            post.postcontent = postcontent
            post.scope = 'public'
            post.attachmentfile = attachmentfile
            post.newmsg = True
            try:
                post.save()
            except:
                print "Error: %s"%sys.exc_info()[1].__str__()
                message += error_msg('1128')%sys.exc_info()[1].__str__()
                message += "\n"
                continue
        message += error_msg('1129')
        response = HttpResponse(message)
        return response
    if targettestids.__len__() > 0:
        for ttestid in targettestids:
            post = Post()
            targettest = Test.objects.get(id=ttestid)
            post.posttargettype = 'test'
            post.posttargettest = targettest
            post.postmsgtag = msgtag
            post.poster = userobj
            post.postcontent = postcontent
            post.scope = 'public'
            post.attachmentfile = attachmentfile
            post.newmsg = True
            try:
                post.save()
            except:
                print "Error: %s"%sys.exc_info()[1].__str__()
                message += error_msg('1128')%sys.exc_info()[1].__str__()
                message += "\n"
                continue
        message += error_msg('1129')
        response = HttpResponse(message)
        return response
    # If we have reached here, it means there are no targets specified for this message
    message = error_msg('1130')
    response = HttpResponse(message)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def postreplycontent(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    postid = -1
    if request.POST.has_key('postid'):
        postid = request.POST['postid']
    else:
        message = error_msg('1133')
        response = HttpResponse(message)
        return response
    postobj = Post.objects.get(id=postid)
    replycontent = request.POST['replycontent']
    replycontent = replycontent.replace("\n", "<br>")
    replyattachmentfile = ""
    if request.FILES.has_key('replyattachment'):
        replyattachmentpath = mysettings.MEDIA_ROOT + os.path.sep + userobj.displayname + os.path.sep + "posts" + os.path.sep
        replyattachmentfilename = request.FILES['replyattachment'].name.split(".")[0]
        fpath, message, replyattachmentfile = skillutils.handleuploadedfile2(request.FILES['replyattachment'], replyattachmentpath, replyattachmentfilename)
    # Point to note: A user blocked by another user can send a response to a message initiated by the user who has blocked the current user.
    postmsgtag = postobj.postmsgtag
    posttargettype = postobj.posttargettype
    posttargetuser = postobj.posttargetuser
    posttargetgroup = postobj.posttargetgroup
    posttargettest = postobj.posttargettest
    scope = postobj.scope
    relatedpost_id = postobj.id
    deleted = postobj.deleted
    hidden = postobj.hidden
    stars = postobj.stars
    replypostobj = Post()
    replypostobj.postmsgtag = postmsgtag
    replypostobj.postcontent = replycontent
    replypostobj.posttargettype = posttargettype
    replypostobj.posttargetgroup = posttargetgroup
    replypostobj.posttargetuser = posttargetuser
    replypostobj.posttargettest = posttargettest
    replypostobj.scope = scope
    replypostobj.relatedpost_id = relatedpost_id
    replypostobj.deleted = deleted
    replypostobj.hidden = hidden
    replypostobj.stars = stars
    replypostobj.attachmentfile = replyattachmentfile
    replypostobj.poster = userobj
    try:
        replypostobj.save()
    except:
        message = error_msg('1134')
        message += sys.exc_info()[1].__str__()
        print message
        response = HttpResponse(message)
        return response
    message = "You have successfully posted your reply message."
    response = HttpResponse(message)
    return response
    

@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def newmessageread(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    postid = -1
    if request.POST.has_key('postid'):
        postid = request.POST['postid']
    else:
        message = error_msg('1133')
        response = HttpResponse(message)
        return response
    postobj = Post.objects.get(id=postid)
    postobj.newmsg = False
    postobj.save() # Saved the record with newmsg set to False, meaning that the post is no longer new.
    response = HttpResponse(message)
    return response # We won't be using this response anywhere, but we need to send it since django views should send back an HttpResponse object.


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def sendmsgresponse(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    responsemsgfile = ""
    txtresponse = ""
    postid = 0
    if request.POST.has_key('postid'):
        postid = request.POST['postid']
    if request.POST.has_key('responsemsgfile' + postid):
        responsemsgfile = request.POST['responsemsgfile' + postid]
    if request.POST.has_key('txtresponse' + postid):
        txtresponse = request.POST['txtresponse' + postid]
    parentpostobj = None
    try:
        parentpostobj = Post.objects.get(id=postid)
    except:
        message = error_msg('1137')
        response = HttpResponse(message)
        return response
    responseattachmentfile = ""
    if request.FILES.has_key('responsemsgfile' + postid):
        responseattachmentpath = mysettings.MEDIA_ROOT + os.path.sep + userobj.displayname + os.path.sep + "posts" + os.path.sep
        responseattachmentfilename = request.FILES['responsemsgfile' + postid].name.split(".")[0]
        fpath, message, responseattachmentfile = skillutils.handleuploadedfile2(request.FILES['responsemsgfile' + postid], responseattachmentpath, responseattachmentfilename)
    postmsgtag = parentpostobj.postmsgtag
    childpostobj = Post()
    childpostobj.postmsgtag = postmsgtag
    childpostobj.postcontent = txtresponse
    childpostobj.poster = userobj
    childpostobj.posttargettype = 'user'
    childpostobj.posttargetuser = parentpostobj.poster
    childpostobj.scope = 'public'
    childpostobj.relatedpost_id = parentpostobj.id
    childpostobj.newmsg = True
    childpostobj.attachmentfile = responseattachmentfile
    childpostobj.save()
    message = "Successfully posted the response message."
    response = HttpResponse(message)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def msgsearch(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    searchphrase = ""
    if request.POST.has_key('searchphrase'):
        searchphrase = request.POST['searchphrase']
    else:
        message = error_msg('1138')
        response = HttpResponse(message)
        return response
    grpmemberqset = GroupMember.objects.filter(member=userobj, status=True, removed=False)
    groupslist = []
    for grpmemberobj in grpmemberqset:
        group = grpmemberobj.group
        groupslist.append(group)
    # Find all messages pertaining to this user. This will include:
    # 1. All messages received by the user.
    # 2. All messages sent by the user.
    # 3. All messages posted on the set of groups of which the concerned user is a member.
    # 4. All messages exchanged by the user with respect to the tests that the user has taken or associated with.
    # Note: The point #4 will be implemented later. Currently we will implement the first 3 points only.
    postsrecvdqset = Post.objects.filter(posttargetuser=userobj, posttargettype='user')
    postssentqset = Post.objects.filter(posttargettype='user', poster=userobj)
    postsgroupsqset = Post.objects.filter(posttargettype='group', posttargetgroup__in=groupslist)
    allpostslist = list(chain(postsrecvdqset, postssentqset, postsgroupsqset))
    #allpostslist = list(chain(postsrecvdqset, postssentqset))
    messagesdict = {}
    searchpattern = re.compile(searchphrase, re.IGNORECASE|re.DOTALL)
    for postobj in allpostslist:
        postcontent = postobj.postcontent
        postmsgtag = postobj.postmsgtag
        attachfilename = postobj.attachmentfile
        if not attachfilename:
            attachfilename = ""
        postername = postobj.poster.displayname
        # Currently, we are handling only 4 fields to search: postcontent, postmsgtag, attachmentfile and poster's displayname
        msgtagmatch = searchpattern.search(postmsgtag)
        postcontentmatch = searchpattern.search(postcontent)
        attachedfilematch = searchpattern.search(attachfilename)
        posternamematch = searchpattern.search(postername)
        searchrecord = ""
        if msgtagmatch or postcontentmatch or attachedfilematch or posternamematch:
            newflag = postobj.newmsg
            if newflag:
                searchrecord += "new##"
            attachtag = "<a href='" + "media/" + postobj.poster.displayname + "/posts/" + attachfilename + "'>" + attachfilename + "</a>"
            searchrecord += postobj.poster.displayname + "##" + str(postobj.createdon) + "##" + attachtag + "##" + postmsgtag + "##" + postcontent + "##searchphrase=" + searchphrase
            postid = postobj.id
            messagesdict[postid] = [searchrecord, ]
    messagesdictstr = json.dumps(messagesdict)
    messagesdictenc = base64.b64encode(messagesdictstr)
    response = HttpResponse(messagesdictenc)
    return response


"""
This function creates an HTTP request at the background and sends it to the method that emails a test to a set of users.
"""
def sendtestemails(request, testid, forcefreshurl, emailidlist):
    postdata = { "testid" : testid, }
    baseurl = skillutils.gethosturl(request)
    txtemailslist = ",".join(emailidlist)
    postdata['baseurl'] = baseurl
    postdata['txtemailslist'] = txtemailslist
    curtime = datetime.datetime.now()
    yyyy = str(curtime.year)
    mon = str(curtime.month)
    dd = str(curtime.day)
    hh = str(curtime.hour)
    mm = str(curtime.minute)
    ss = str(curtime.second)
    if mon.__len__() < 2:
        mon = '0' + mon
    if dd.__len__() < 2:
        dd = '0' + dd
    if hh.__len__() < 2:
        hh = '0' + hh
    if mm.__len__() < 2:
        mm = '0' + mm
    if hh.__len__() < 2:
        hh = '0' + hh
    validfrom = dd + "-" + mon + "-" + yyyy + " " + hh + ":" + mm + ":" + ss
    csrftoken = request.POST['csrfmiddlewaretoken']
    postdata['validfrom'] = validfrom
    """
    ddtill = dd
    montill = str(int(mon) + 1)
    if montill.__len__() < 2:
        montill = "0" + montill
    if montill > 12:
        yyyytill = int(yyyy) + 1
        yyyytill = str(yyyytill)
        montill = '01'
    else:
        yyyytill = yyyy
    postdata['validtill'] = ddtill + "-" + montill + "-" + yyyytill + " " + hh + ":" + mm + ":" + ss
    """
    postdata['validtill'] = ""
    postdata['forcefreshurl'] = forcefreshurl
    postdata['csrfmiddlewaretoken'] = csrftoken
    opener = urllib2.build_opener(urllib2.HTTPHandler, urllib2.HTTPSHandler, skillutils.NoRedirectHandler)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionqset = Session.objects.filter(sessioncode=sesscode)
    if not sessionqset or sessionqset.__len__() == 0:
        message = "Error: " + error_msg('1008')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.DASHBOARD_URL + "?msg=%s"%message)
        return response
    sessionobj = sessionqset[0]
    userobj = sessionobj.user
    postdata = urllib.urlencode(postdata)
    headers = {}
    for hdrkey in skillutils.gHttpHeaders.keys():
        headers[hdrkey] = skillutils.gHttpHeaders[hdrkey]
    headers['Host'] = request.get_host()
    headers['Cookie'] = "sessioncode=" + sesscode + ";usertype=" + usertype + ";csrftoken=" + csrftoken
    headers['Referer'] = baseurl + "/skillstest/network/"
    postrequest = urllib2.Request(baseurl + "/skillstest/test/sendtestinvitations/", postdata, headers)
    testqset = Test.objects.filter(id=testid)
    testname = ""
    if testqset and list(testqset).__len__() > 0:
        testname = testqset[0].testname
    try:
        opener.open(postrequest)
        message = "Successfully sent the test named '%s' email to %s members."%(testname, emailidlist.__len__())
    except:
        message = "Could not send emails for test identified by Id %s to all identified users: %s"%(testid, sys.exc_info()[1].__str__())
    # Send an email with 'message' to the user identified in 'userobj'
    subject = "Status of email sent to members of the selected group(s)"
    fromaddr = userobj.emailid
    email = fromaddr
    try:
        retval = send_mail(subject, message, fromaddr, [email,], False)
    except:
        message = error_msg('1141')
        print message
    return None


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def givetesttogroups(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = "";
    testid, groupidstr, groupidlist = "", "", []
    forcefreshurl = 0
    if request.POST.has_key('testid'):
        testid = request.POST['testid']
    if request.POST.has_key('groups'):
        groupidstr = request.POST['groups']
    if request.POST.has_key('forcefreshurl'):
        forcefreshurl = request.POST['forcefreshurl']
    if not testid or not groupidstr:
        message = error_msg('1139')
        response = HttpResponse(message)
        return response
    groupidlist = groupidstr.split("##")
    # Extract unique email Ids from all the selected groups
    uniqueemailids = {}
    for grpid in groupidlist:
        groupobj = Group.objects.get(id=grpid)
        grpmemberqset = GroupMember.objects.filter(group=groupobj)
        for grpmemberobj in grpmemberqset:
            memberobj = grpmemberobj.member
            memberemail = memberobj.emailid
            uniqueemailids[memberemail] = 1
    uniqueemailslist = uniqueemailids.keys()
    # Send an internal HTTP request to 'Tests.views.sendtestinvitations'. Create a background thread to do that.
    thread = Thread(target=sendtestemails, args = (request, testid, forcefreshurl, uniqueemailslist))
    thread.start()
    response = HttpResponse(error_msg('1140'))
    #thread.join()
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def gettestsandgroups(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    fmt = request.POST.get('format', 'json') # default format is 'json'. At present we will serve data as json encoded text only.
    testsqset = Test.objects.filter(creator=userobj)
    testsdict = {}
    for testobj in testsqset:
        testid = testobj.id
        testname = testobj.testname
        testsdict[testname] = testid
    groupsdict = {}
    groupsqset = Group.objects.filter(owner=userobj)
    for groupobj in groupsqset:
        groupid = groupobj.id
        groupname = groupobj.groupname
        groupsdict[groupname] = groupid
    respdict = { 'groups' : groupsdict, 'tests' : testsdict }
    respstr = json.dumps(respdict)
    response = HttpResponse(respstr)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def getconnectioninfo(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    visibility = 'public'
    if not request.POST.has_key('connid') and not request.POST.has_key('conndisplayname'):
        message = error_msg('1143')
        response = HttpResponse(message)
        return response
    connobj = None
    directconnectionflag = False
    connecteduser = None
    if request.POST.has_key('connid'):
        connid = request.POST['connid']
        try:
            connobj = Connection.objects.get(id=connid)
        except:
            message = error_msg('1144')
            response = HttpResponse(message)
            return response
        connecteduser = connobj.connectedto
        visibility = 'protected'
        directconnectionflag = True # Direct connection exists between userobj and connecteduser
    elif request.POST.has_key('conndisplayname'):
        conndisplayname = request.POST['conndisplayname']
        try:
            connecteduser = User.objects.get(displayname=conndisplayname)
        except:
            message = error_msg('1151')
            response = HttpResponse(message)
            return response
        # Check if a connection exists between userobj and connecteduser
        conqset = Connection.objects.filter(focususer=userobj).filter(connectedto=connecteduser)
        if conqset.__len__() > 0:
            visibility = 'protected' # protected visibility implicitly includes public visibility
            directconnectionflag = True
        else:
            visibility = 'public'
            directconnectionflag = False
    # Get '{{displayname}}', '{{profileimage}}', 
    displayname = connecteduser.displayname
    profileimage = connecteduser.userpic
    useremail = connecteduser.emailid
    goodname = connecteduser.firstname + " " + connecteduser.middlename + " " + connecteduser.lastname
    useractive = connecteduser.active
    usertestqset = []
    if visibility == 'protected':
        usertestqset = UserTest.objects.filter(user=connecteduser).filter(visibility__in=[1, 2]).filter(cancelled=False)
    elif visibility == 'public':
        usertestqset = UserTest.objects.filter(user=connecteduser).filter(visibility=2).filter(cancelled=False)
    else:
        pass
    # Tests with visibility set to 'Public' and 'Protected' are only displayed to connections.
    usertests = {'taken' : [], 'nottaken' : [], 'taking' : []}
    taken, nottaken, taking = [], [], []
    for usertestobj in usertestqset:
        testname = usertestobj.test.testname
        testscore = usertestobj.score
        testoutcome = usertestobj.outcome
        maxscore = usertestobj.test.maxscore
        passscore = usertestobj.test.passscore
        teststarttime = usertestobj.starttime
        testendtime = usertestobj.endtime
        if not usertestobj.first_eval_timestamp:
            usertestobj.first_eval_timestamp = 0
        evaluationtime = datetime.datetime.fromtimestamp(int(usertestobj.first_eval_timestamp)).strftime('%Y-%m-%d %H:%M:%S')
        testvalidfrom = usertestobj.validfrom
        testvalidtill = usertestobj.validtill
        testdict = { 'testname' : testname, 'testscore' : testscore, 'testoutcome' : testoutcome, 'teststarttime' : teststarttime, 'testendtime' : testendtime, 'evaluationtime' : evaluationtime, 'testvalidfrom' : testvalidfrom, 'testvalidtill' : testvalidtill, 'maxscore' : maxscore, 'passscore' : passscore}
        if int(usertestobj.status) == 2: # Test taken
            taken.append(testdict)
        elif int(usertestobj.status) == 1: # Test being taken
            taking.append(testdict)
        elif int(usertestobj.status) == 0: # Test not yet taken
            nottaken.append(testdict)
    usertests['taken'] = taken
    usertests['nottaken'] = nottaken
    usertests['taking'] = taking
    # Now get the tests owned by this user
    ownedtestsqset = []
    if visibility == 'protected':
        ownedtestsqset = Test.objects.filter(creator=connecteduser).filter(scope__in=['public', 'protected'])
    elif visibility == 'public':
        ownedtestsqset = Test.objects.filter(creator=connecteduser).filter(scope='public')
    ownedtests = []
    for testobj in ownedtestsqset:
        testname = testobj.testname
        topicname = testobj.topicname
        if topicname == "":
            topicname = testobj.topic
        testtype = testobj.testtype
        publishdate = testobj.publishdate
        maxscore = testobj.maxscore
        passscore = testobj.passscore
        testlinkid = testobj.testlinkid
        testgivenqset = UserTest.objects.filter(test=testobj).filter(cancelled=False).filter(active=True)
        wouldbeusersqset = WouldbeUsers.objects.filter(test=testobj).filter(cancelled=False).filter(active=True)
        # Count of users who have taken this test
        countuserstaken = testgivenqset.__len__() + wouldbeusersqset.__len__()
        evaluators = []
        evalgroupname = testobj.evaluator.evalgroupname
        if testobj.evaluator.groupmember1 and testobj.evaluator.groupmember1.displayname:
            evaluators.append(testobj.evaluator.groupmember1.displayname)
        if testobj.evaluator.groupmember2 and testobj.evaluator.groupmember2.displayname:
            evaluators.append(testobj.evaluator.groupmember2.displayname)
        if testobj.evaluator.groupmember3 and testobj.evaluator.groupmember3.displayname:
            evaluators.append(testobj.evaluator.groupmember3.displayname)
        if testobj.evaluator.groupmember4 and testobj.evaluator.groupmember4.displayname:
            evaluators.append(testobj.evaluator.groupmember4.displayname)
        if testobj.evaluator.groupmember5 and testobj.evaluator.groupmember5.displayname:
            evaluators.append(testobj.evaluator.groupmember5.displayname)
        if testobj.evaluator.groupmember6 and testobj.evaluator.groupmember6.displayname:
            evaluators.append(testobj.evaluator.groupmember6.displayname)
        if testobj.evaluator.groupmember7 and testobj.evaluator.groupmember7.displayname:
            evaluators.append(testobj.evaluator.groupmember7.displayname)
        if testobj.evaluator.groupmember8 and testobj.evaluator.groupmember8.displayname:
            evaluators.append(testobj.evaluator.groupmember8.displayname)
        if testobj.evaluator.groupmember9 and testobj.evaluator.groupmember9.displayname:
            evaluators.append(testobj.evaluator.groupmember9.displayname)
        if testobj.evaluator.groupmember10 and testobj.evaluator.groupmember10.displayname:
            evaluators.append(testobj.evaluator.groupmember10.displayname)
        evaluators_str = ",".join(evaluators)
        testsdict = {'testname' : testname, 'topicname' : topicname, 'testtype' : testtype, 'publishdate' : publishdate, 'maxscore' : maxscore, 'passscore' : passscore, 'testlinkid' : testlinkid, 'evaluators' : evaluators_str, 'countuserstaken' : countuserstaken}
        ownedtests.append(testsdict)
    # Get tests evaluated by this user. To do this, first find evaluator group names in which this user is a member
    evalgroupslist = []
    evaluatorsqset = Evaluator.objects.filter() # Get all evaluator groups
    for evaluatorobj in evaluatorsqset:
        if evaluatorobj.groupmember1 and evaluatorobj.groupmember1.displayname == connecteduser.displayname:
            evalgroupslist.append(evaluatorobj)
        elif evaluatorobj.groupmember2 and evaluatorobj.groupmember2.displayname == connecteduser.displayname:
            evalgroupslist.append(evaluatorobj)
        elif evaluatorobj.groupmember3 and evaluatorobj.groupmember3.displayname == connecteduser.displayname:
            evalgroupslist.append(evaluatorobj)
        elif evaluatorobj.groupmember4 and evaluatorobj.groupmember4.displayname == connecteduser.displayname:
            evalgroupslist.append(evaluatorobj)
        elif evaluatorobj.groupmember5 and evaluatorobj.groupmember5.displayname == connecteduser.displayname:
            evalgroupslist.append(evaluatorobj)
        elif evaluatorobj.groupmember6 and evaluatorobj.groupmember6.displayname == connecteduser.displayname:
            evalgroupslist.append(evaluatorobj)
        elif evaluatorobj.groupmember7 and evaluatorobj.groupmember7.displayname == connecteduser.displayname:
            evalgroupslist.append(evaluatorobj)
        elif evaluatorobj.groupmember8 and evaluatorobj.groupmember8.displayname == connecteduser.displayname:
            evalgroupslist.append(evaluatorobj)
        elif evaluatorobj.groupmember9 and evaluatorobj.groupmember9.displayname == connecteduser.displayname:
            evalgroupslist.append(evaluatorobj)
        elif evaluatorobj.groupmember10 and evaluatorobj.groupmember10.displayname == connecteduser.displayname:
            evalgroupslist.append(evaluatorobj)
    evaluatedtests = []
    for evalgrp in evalgroupslist:
        testqset = Test.objects.filter(evaluator=evalgrp)
        for testobj in testqset:
            testname = testobj.testname
            topicname = testobj.topicname
	    if topicname == "":
	        topicname = testobj.topic
	    testtype = testobj.testtype
	    publishdate = testobj.publishdate
	    maxscore = testobj.maxscore
	    passscore = testobj.passscore
	    testlinkid = testobj.testlinkid
	    testgivenqset = UserTest.objects.filter(test=testobj).filter(cancelled=False).filter(active=True)
	    wouldbeusersqset = WouldbeUsers.objects.filter(test=testobj).filter(cancelled=False).filter(active=True)
	    # Count of users who have taken this test
	    countuserstaken = testgivenqset.__len__() + wouldbeusersqset.__len__()
            testdict = {'testname' : testname, 'topicname' : topicname, 'testtype' : testtype, 'publishdate' : publishdate, 'maxscore' : maxscore, 'passscore' : passscore, 'testlinkid' : testlinkid, 'countuserstaken' : countuserstaken}
            evaluatedtests.append(testdict)
    # Now we have all our data, so we populate the template and return it as response
    contextdict = {'usertests' : usertests, 'ownedtests' : ownedtests, 'evaluatedtests' : evaluatedtests, 'displayname' : displayname, 'profileimage' : profileimage, 'useremail' : useremail, 'goodname' : goodname, 'useractive' : useractive, 'connectedid' : connecteduser.id, 'directconnectionflag' : directconnectionflag }
    tmpl = get_template("network/userprofile.html")
    contextdict.update(csrf(request))
    cxt = Context(contextdict)
    userprofhtml = tmpl.render(cxt)
    response = HttpResponse(userprofhtml)
    return response
    

@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def getgroupsownedinfo(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    connectedtoid = 0
    if request.POST.has_key('connectedtoid'):
        connectedtoid = request.POST['connectedtoid']
    else:
        message = "Error: %s"%error_msg('1145')
        response = HttpResponse(message)
        return response
    connecteduser = User.objects.get(id=connectedtoid)
    groupsownedqset = Group.objects.filter(owner=connecteduser).filter(status=True)
    groupsdict = {}
    for ownedgroupobj in groupsownedqset:
        groupname = ownedgroupobj.groupname
        groupdesc = ownedgroupobj.description
        memberscount = ownedgroupobj.memberscount
        basedontopic = ownedgroupobj.basedontopic
        entryfee = ownedgroupobj.entryfee
        currency = ownedgroupobj.currency
        groupsdict[groupname] = [groupdesc, memberscount, basedontopic, entryfee, currency, connecteduser.displayname ]
    groupsjson = json.dumps(groupsdict)
    response = HttpResponse(groupsjson)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def getgroupsmemberinfo(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    connectedtoid = 0
    if request.POST.has_key('connectedtoid'):
        connectedtoid = request.POST['connectedtoid']
    else:
        message = "Error: %s"%error_msg('1145')
        response = HttpResponse(message)
        return response
    groupsdict = {}
    connecteduser = User.objects.get(id=connectedtoid)
    groupsmemberqset = GroupMember.objects.filter(member=connecteduser).filter(status=True).filter(removed=False).filter(blocked=False)
    for membergroupobj in groupsmemberqset:
        groupname = membergroupobj.group.groupname
        groupdesc = membergroupobj.group.description
        basedontopic = membergroupobj.group.basedontopic
        membersince = membergroupobj.membersince
        membersince_str = str(membersince.year) + "-" + str(membersince.month) + "-" + str(membersince.day) + " " + str(membersince.hour) + ":" + str(membersince.minute) + ":" + str(membersince.second)
        ispaid = membergroupobj.group.ispaid
        groupsdict[groupname] = [groupdesc, basedontopic, membersince_str, ispaid, connecteduser.displayname ]
    groupsjson = json.dumps(groupsdict)
    response = HttpResponse(groupsjson)
    return response
        

@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def getconnectioninfolevel2(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    connectedtoid = 0
    if request.POST.has_key('connectedtoid'):
        connectedtoid = request.POST['connectedtoid']
    else:
        message = "Error: %s"%error_msg('1145')
        response = HttpResponse(message)
        return response
    connecteduser = User.objects.get(id=connectedtoid)
    # Get all connections made by this user
    connectionsdict = {}
    connectionsqset = Connection.objects.filter(focususer=connecteduser).filter(deleted=False)
    for connobj in connectionsqset:
        connectedusername = connobj.connectedto.displayname
        connectedgoodname = connobj.connectedto.firstname + " " + connobj.connectedto.middlename + " " + connobj.connectedto.lastname
        connectedfrom = connobj.connectedfrom
        connectedfrom_str = str(connectedfrom.year) + "-" + str(connectedfrom.month) + "-" + str(connectedfrom.day) + " " + str(connectedfrom.hour) + ":" + str(connectedfrom.minute) + ":" + str(connectedfrom.second)
        blocked = connobj.blocked
        connectedthru = connobj.connectedthru
        connlevel = '2' # Second level connection w.r.t loggedin user 'userobj'
        connectionsdict[connectedusername] = [ connectedgoodname, connectedfrom_str, blocked, connectedthru, connlevel ]
    connectionsinfojson = json.dumps(connectionsdict)
    response = HttpResponse(connectionsinfojson)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def blockuser(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    targetuser = None
    if not request.POST.has_key('targetuser'):
        message = error_msg('1146')
        response = HttpResponse(message)
        return response
    targetuserdispname = request.POST['targetuser']
    try:
        targetuser = User.objects.get(displayname=targetuserdispname)
    except:
        message = error_msg('1147')
        response = HttpResponse(message)
        return response
    connobj = Connection.objects.get(focususer=userobj, connectedto=targetuser)
    if request.POST.has_key('blocked') and int(request.POST['blocked']) == 1: # Block this user from accessing attributes of userobj
        connobj.blocked = True
        message = "Successfully blocked user identified by '%s'"%targetuserdispname
    elif request.POST.has_key('blocked') and int(request.POST['blocked']) == 0:
        connobj.blocked = False
        message = "Successfully unblocked user identified by '%s'"%targetuserdispname
    else:
        message = error_msg('1148')
    connobj.save()
    response = HttpResponse(message)
    return response
    

@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def unblockuser(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    contactid = 0
    if request.POST.has_key('contactid'):
        contactid = request.POST['contactid']
    if not contactid:# We still did not get a valid contactid
        message = error_msg('1149')
        response = HttpResponse(message)
        return response
    try:
        contactobj = Connection.objects.get(id=contactid)
    except:
        message = error_msg('1144')
        response = HttpResponse(message)
        return response
    contactobj.blocked = False
    contactobj.save()
    message = "Successfully unblocked the user identified by '%s'"%contactobj.connectedto.displayname
    response = HttpResponse(message)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def removeuser(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    targetuser = None
    if not request.POST.has_key('targetuser'):
        message = error_msg('1146')
        response = HttpResponse(message)
        return response
    targetuserdispname = request.POST['targetuser']
    try:
        targetuser = User.objects.get(displayname=targetuserdispname)
    except:
        message = error_msg('1147')
        response = HttpResponse(message)
        return response
    connobj = Connection.objects.get(focususer=userobj, connectedto=targetuser)
    if request.POST.has_key('removed') and int(request.POST['removed']) == 1: # Delete this connection
        connobj.deleted = True
        message = "Successfully deleted user identified by '%s'"%targetuserdispname
    elif request.POST.has_key('removed') and int(request.POST['removed']) == 0:
        connobj.deleted = False
        message = "Successfully restored user identified by '%s'"%targetuserdispname
    else:
        message = error_msg('1150')
    connobj.save()
    response = HttpResponse(message)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def sendmessage(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    targetemail = ""
    emailmessage = ""
    if not request.POST.has_key('targetuser'):
        message = error_msg('1152')
        response = HttpResponse(message)
        return response
    targetemail = request.POST['targetuser']
    targetuserobj = None
    try:
        targetuserobj = User.objects.get(emailid=targetemail)
    except:
        message = error_msg('1154')
        response = HttpResponse(message)
        return response
    if not request.POST.has_key('messagecontent'):
        message = error_msg('1153')
        response = HttpResponse(message)
        return response
    emailmessage = request.POST['messagecontent']
    fromemail = userobj.emailid
    subject = emailmessage[:20] + "..." # First 20 characters will be the subject.
    subject = subject.replace("\n", " ")
    retval = skillutils.sendemail(targetuserobj, subject, emailmessage, fromemail)
    if retval > 0:
        message = "Successfully sent email to user with email Id '%s'"%targetemail
    else:
        message = "Could not send email to user with email Id '%s'"%targetemail
    response = HttpResponse(message)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def managegroupmembers(request):
    if request.method != 'POST' and request.method != 'GET':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    if request.method == 'GET': # Return empty string
        return HttpResponse("")
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    groupname = None
    groupobj = None
    groupqset = []
    if request.POST.has_key('groupname'):
        groupname = request.POST['groupname']
    if groupname:
        groupqset = Group.objects.filter(groupname=groupname)
    if groupqset.__len__() == 0:
        message = error_msg('1088')
        response = HttpResponse(message)
        return response
    fromctr, toctr = 0, 100
    if request.POST.has_key('fromctr') and request.POST['fromctr'] != '':
        fromctr = int(request.POST['fromctr'])
    else:
        return HttpResponse("")
    if request.POST.has_key('toctr') and request.POST['toctr'] != '':
        toctr = int(request.POST['toctr'])
    else:
        return HttpResponse("")
    # Check if the user is the owner of the group. If not, return a error response.
    groupobj = groupqset[0]
    if groupobj.owner != userobj:
        message = error_msg('1155')
        response = HttpResponse("<font color='FF0000' style='font-weight:bold'>%s</font>"%message)
        return response
    # Get all members of the group along with their blocked/unblocked status.
    groupmembers = GroupMember.objects.filter(group=groupobj)[fromctr:toctr]
    groupmembersdict = {}
    savemembersurl = mysettings.SAVE_GROUP_MEMBERS_URL
    managemembersurl = mysettings.MANAGE_GROUP_MEMBERS_URL
    membersearchurl = mysettings.MEMBER_SEARCH_URL
    grpmemberscount = 0
    for grpmember in groupmembers:
        displayname = grpmember.member.displayname
        fullname = grpmember.member.firstname + " " + grpmember.member.middlename + " " + grpmember.member.lastname
        blocked = grpmember.blocked
        removed = grpmember.removed
        status = grpmember.status
        removeagent = grpmember.removeagent
        groupmembersdict[displayname] = [ fullname, blocked, removed, status, removeagent ]
        grpmemberscount += 1
    contextdict = { 'groupmembersdict' : groupmembersdict, 'groupname' : groupname, 'savemembersurl' : savemembersurl, 'fromctr' : int(toctr), 'toctr' : int(toctr) + 100, 'managemembersurl' : managemembersurl, 'grpmemberscount' : grpmemberscount, 'membersearchurl' : membersearchurl }
    if fromctr == 0:
        tmpl = get_template("network/groupmembers.html")
        contextdict.update(csrf(request))
        cxt = Context(contextdict)
        grpmembershtml = tmpl.render(cxt)
        response = HttpResponse(grpmembershtml)
    elif fromctr > 0:
        tmpl = get_template("network/groupmemberrows.html")
        contextdict.update(csrf(request))
        cxt = Context(contextdict)
        grpmembershtml = tmpl.render(cxt)
        response = HttpResponse(grpmembershtml)
    return response


# Should handle pagination.
@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def savegroupmembers(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    groupname = None
    membername = None
    blocked = None
    removed = None
    status = None
    if request.POST.has_key('membername'):
        membername = request.POST['membername']
    if request.POST.has_key('groupname'):
        groupname = request.POST['groupname']
    if request.POST.has_key('blockstatus'):
        blockstatus = request.POST['blockstatus']
    if request.POST.has_key('removedstatus'):
        removedstatus = request.POST['removedstatus']
    if request.POST.has_key('status'):
        status = request.POST['status']
    # First check if the user is the owner of the group
    groupobj = Group.objects.get(groupname=groupname)
    if groupobj.owner != userobj:
        message = error_msg('1155')
        response = HttpResponse(message)
        return response
    memberobj = None
    try:
        memberobj = User.objects.get(displayname=membername)
    except:
        message = error_msg('1156')
        response = HttpResponse(message)
        return response
    groupmemberqset = GroupMember.objects.filter(group=groupobj, member=memberobj)
    if groupmemberqset.__len__() == 0:
        message = error_msg('1156')
        response = HttpResponse(message)
        return response
    groupmemberobj = groupmemberqset[0]
    if blockstatus == "":
        groupmemberobj.blocked = False
    else:
        groupmemberobj.blocked = True
    if removedstatus == "":
        groupmemberobj.removed = False
    else:
        groupmemberobj.removed = True
    if status == "":
        groupmemberobj.status = False
    else:
        groupmemberobj.status = True
    groupmemberobj.save()
    message = "Successfully updated member info."
    response = HttpResponse(message)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def searchmember(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    displayname, firstname, lastname, groupname = "", "", "", ""
    if request.POST.has_key('displayname'):
        displayname = request.POST['displayname']
    if request.POST.has_key('firstname'):
        firstname = request.POST['firstname']
    if request.POST.has_key('lastname'):
        lastname = request.POST['lastname']
    if request.POST.has_key('groupname'):
        groupname = request.POST['groupname']
    groupqset = Group.objects.filter(groupname=groupname)
    if groupqset.__len__() == 0:
        message = "Error: " + error_msg('1088')
        response = HttpResponse(message)
        return response
    groupobj = groupqset[0]
    # Check if logged in user is the owner of the group. If not, display a error message and return
    if groupobj.owner != userobj:
        message = "Error: " + error_msg('1155')
        response = HttpResponse(message)
        return response
    fromctr, toctr = 0,100
    if request.POST.has_key('fromctr'):
        fromctr = request.POST['fromctr']
    if request.POST.has_key('toctr'):
        toctr = request.POST['toctr']
    grpmemberqset = GroupMember.objects.filter(group=groupobj)
    filteredset = GroupMember.objects.none()
    if displayname == "" and firstname == "" and lastname == "":
         filteredset = grpmemberqset
    if displayname != "":
         filteredset = filteredset | grpmemberqset.filter(member__displayname__icontains=displayname)
    if firstname != "":
         filteredset = filteredset | grpmemberqset.filter(member__firstname__icontains=firstname)
    if lastname != "":
         filteredset = filteredset | grpmemberqset.filter(member__lastname__icontains=lastname)
    filteredset = filteredset.distinct() # Gives the distinct records.
    # Now create the data structure.
    groupmembersdict = {}
    savemembersurl = mysettings.SAVE_GROUP_MEMBERS_URL
    managemembersurl = mysettings.MANAGE_GROUP_MEMBERS_URL
    membersearchurl = mysettings.MEMBER_SEARCH_URL
    grpmemberscount = 0
    # Now get the slice we want to show. Could not do so earlier as 'OR' operator doesn't work on sliced queryset.
    for grpmember in filteredset[fromctr:toctr]:
        displayname = grpmember.member.displayname
        fullname = grpmember.member.firstname + " " + grpmember.member.middlename + " " + grpmember.member.lastname
        blocked = grpmember.blocked
        removed = grpmember.removed
        status = grpmember.status
        removeagent = grpmember.removeagent
        groupmembersdict[displayname] = [ fullname, blocked, removed, status, removeagent ]
        grpmemberscount += 1
    contextdict = { 'groupmembersdict' : groupmembersdict, 'groupname' : groupname, 'savemembersurl' : savemembersurl, 'fromctr' : int(toctr), 'toctr' : int(toctr) + 100, 'managemembersurl' : managemembersurl, 'grpmemberscount' : grpmemberscount, 'membersearchurl' : membersearchurl }
    tmpl = get_template("network/groupmemberrows.html")
    contextdict.update(csrf(request))
    cxt = Context(contextdict)
    grpmembershtml = tmpl.render(cxt)
    response = HttpResponse(grpmembershtml)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def manageownedgroups(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    searchquery = ""
    if request.POST.has_key('searchquery'):
        searchquery = request.POST['searchquery']
    contextdict = {}
    groupsdict = {}
    groupsownerqset = None
    if not searchquery or searchquery == "":
        groupsownerqset = Group.objects.filter(owner=userobj)
    else:
        groupsownerqset = Group.objects.filter(owner=userobj, groupname__contains=searchquery)
    nonepattern = re.compile("/None$")
    for group in groupsownerqset:
        gid = str(group.id)
        groupname = str(group.groupname)
        tagline = str(group.tagline)
        description = str(group.description)
        maxmemberslimit = str(group.maxmemberslimit)
        status = str(group.status)
        grouptype = str(group.grouptype)
        allowentry = group.allowentry
        groupimagefile = "media/" + group.owner.displayname + "/groups/" + groupname + "/" + str(group.groupimagefile)
        if nonepattern.search(groupimagefile):
            groupimagefile = "static/images/grp_background.png"
        else:
            pass
        topic = str(group.basedontopic)
        ispaid = group.ispaid
        currency = str(group.currency)
        entryfee = str(group.entryfee)
        ownerpermreqd = str(group.require_owner_permission)
        try:
            bankacct = OwnerBankAccount.objects.get(groupowner=userobj,group=group)
            bankname = str(bankacct.bankname)
            bankbranch = str(bankacct.bankbranch)
            accountnumber = str(bankacct.accountnumber)
            ifscode = str(bankacct.ifsccode)
            accountownername = str(bankacct.accountownername)
        except:
            bankname = ""
            bankbranch = ""
            accountnumber = ""
            ifscode = ""
            accountownername = ""
        paidtransactionsqset = GroupPaidTransactions.objects.filter(group=group)
        earnings = 0.0
        inrtousdqset = ExchangeRates.objects.filter(curr_from='INR', curr_to='USD').order_by("-dateofrate")
        plntousdqset = ExchangeRates.objects.filter(curr_from='PLN', curr_to='USD').order_by("-dateofrate")
        eurtousdqset = ExchangeRates.objects.filter(curr_from='EUR', curr_to='USD').order_by("-dateofrate")
        inrexchgrate = 1
        plnexchgrate = 1
        eurexchgrate = 1
        if len(list(inrtousdqset)) > 0:
            inrexchgrate = inrtousdqset[0]
        if len(list(plntousdqset)) > 0:
            plnexchgrate = plntousdqset[0]
        if len(list(eurtousdqset)) > 0:
            eurexchgrate = eurtousdqset[0]
        for transobj in paidtransactionsqset:
            if transobj.currency == 'USD':
                earnings += transobj.amount
            elif transobj.currency == 'PLN':
                earnings += transobj.amount * plnexchgrate
            elif transobj.currency == 'INR':
                earnings += transobj.amount * inrexchgrate
            elif transobj.currency == 'EUR':
                earnings += transobj.amount * eurexchgrate
        if not groupsdict.has_key(gid):
            groupsdict[gid] = [ gid, groupname, tagline, description, maxmemberslimit, status, grouptype, allowentry, groupimagefile, topic, ispaid, currency, entryfee, ownerpermreqd, bankname, bankbranch, accountnumber, earnings, ifscode, accountownername, userobj.displayname ]
    contextdict['groups'] = groupsdict
    alltopics = mysettings.TEST_TOPICS
    contextdict['alltopics'] = alltopics
    contextdict['alltypes'] = mysettings.TEST_SCOPES
    contextdict['allcurrencies'] = mysettings.SUPPORTED_CURRENCIES
    contextdict['searchquery'] = searchquery
    contextdict['grpinfosaveurl'] = mysettings.GROUPINFO_SAVE_URL
    contextdict['managepostsurl'] = mysettings.MANAGE_POSTS_URL
    contextdict['joinrequestsinfo'] = "{}"
    tmpl = get_template("network/ownedgrps.html")
    contextdict.update(csrf(request))
    cxt = Context(contextdict)
    ownedgrpshtml = tmpl.render(cxt)
    response = HttpResponse(ownedgrpshtml)
    return response



@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def groupimagechange(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    grpid = request.POST['groupid']
    grpobj = None
    try:
        grpobj = Group.objects.get(id=grpid)
    except:
        message = "Could not identify the group object with which this image is to be saved"
        response = HttpResponse(message)
        return response
    grpname = grpobj.groupname
    if request.FILES.has_key('grouppic'):
        fpath, message, grouppic = skillutils.handleuploadedfile(request.FILES['grouppic'], mysettings.MEDIA_ROOT + os.path.sep + grpobj.owner.displayname + "/groups/" + grpname, grpname)
        grpobj.groupimagefile = grouppic
        try:
            grpobj.save()
            message = "success"
        except:
            message = error_msg('1041')
    else:
        message = "failed"
    return HttpResponse(message)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def groupinfosave(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    groupid = request.POST['groupid']
    grouptopic = request.POST['grouptopic']
    grouptype = request.POST['grouptype']
    groupobj = Group.objects.get(id=groupid)
    if not groupobj:
        message = "Could not identify the group to which the changes are to be made"
        response = HttpResponse(message)
        return response
    if groupobj.owner != userobj:
        message = "You are not the owner of this group. So you may not change anything pertaining to this group."
        response = HttpResponse(message)
        return response
    groupobj.basedontopic = grouptopic
    groupobj.grouptype = grouptype
    try:
        if request.POST.has_key('paid'):
            groupobj.ispaid = True
            if request.POST.has_key('entryfee'):
                groupobj.entryfee = request.POST['entryfee']
            if request.POST.has_key('currency'):
                groupobj.currency = request.POST['currency']
        else:
            groupobj.ispaid = False
        if request.POST.has_key('ownerpermreqd'):
            groupobj.require_owner_permission = True
        else:
            groupobj.require_owner_permission = False
        if request.POST.has_key('status'):
            groupobj.status = True
        else:
            groupobj.status = False
    except:
        message = sys.exc_info()[1].__str__()
        response = HttpResponse(message)
        return response
    groupobj.tagline = request.POST['tagline']
    groupobj.description = base64.b64decode(request.POST['description'])
    groupobj.maxmemberslimit = request.POST['maxuserslimit']
    ownerbankacctobj = None
    try:
        ownerbankacctqset = OwnerBankAccount.objects.filter(group=groupobj)
        ownerbankacctobj = ownerbankacctqset[0]
    except:
        if groupobj.ispaid == True:
            ownerbankacctobj = OwnerBankAccount() # Create a new bank account for this group
    if groupobj.ispaid == True:
        if request.POST.has_key('bankname'):
            ownerbankacctobj.bankname = request.POST['bankname']
        if request.POST.has_key('branchname'):
            ownerbankacctobj.bankbranch = request.POST['branchname']
        if request.POST.has_key('acctnumber'):
            ownerbankacctobj.accountnumber = request.POST['acctnumber']
        if request.POST.has_key('ifscode'):
            ownerbankacctobj.ifsccode = request.POST['ifscode']
        if request.POST.has_key('acctownername'):
            ownerbankacctobj.accountownername = request.POST['acctownername']
        ownerbankacctobj.groupowner = groupobj.owner
        ownerbankacctobj.group = groupobj
        try:
            ownerbankacctobj.save()
        except:
            message = "You will need to set up your bank account for this group. Please click on the 'edit' link in the 'Paid' column of the group to set it up: %s"%sys.exc_info()[1].__str__()
            response = HttpResponse(message)
            return response
    try:
        groupobj.save()
    except:
        message = "Could not save changes to the group object: %s"%sys.exc_info()[1].__str__()
        response = HttpResponse(message)
        return response
    message = "Your changes have been successfully saved."
    response = HttpResponse(message)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def manageposts(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    grpid = request.POST['groupid']
    grpobj = None
    try:
        grpobj = Group.objects.get(id=grpid)
    except:
        message = "Could not identify the group object with which this image is to be saved"
        response = HttpResponse(message)
        return response
    grpname = grpobj.groupname
    postsqset = Post.objects.filter(posttargetgroup=grpobj, deleted=False).order_by('-createdon')
    contextdict = {}
    contextdict['groupname'] = grpname
    contextdict['groupid'] = grpid
    contextdict['savepostinfourl'] = mysettings.SAVE_POST_INFO_URL
    postsdict = {}
    postssequence = []
    for postobj in postsqset:
        postid = postobj.id
        postmsgtag = postobj.postmsgtag
        postcontent = postobj.postcontent
        postername = postobj.poster.displayname
        attachmentfile = postobj.attachmentfile
        scope = postobj.scope
        deleted = postobj.deleted
        hidden = postobj.hidden
        stars = postobj.stars
        createdon = postobj.createdon
        postsdict[postid] = (postmsgtag, postcontent, postername, attachmentfile, scope, deleted, hidden, stars, createdon)
        postssequence.append(postid)
    contextdict['posts'] = postsdict
    contextdict['sequence'] = postssequence
    tmpl = get_template("network/postslist.html")
    contextdict.update(csrf(request))
    cxt = Context(contextdict)
    postslisthtml = tmpl.render(cxt)
    response = HttpResponse(postslisthtml)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def savepostsinfo(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    postid = request.POST['postid']
    try:
        postobj = Post.objects.get(id=postid)
    except:
        message = "Could not find the post message with the specified Id. Could not save the settings for this post."
        response = HttpResponse(message)
        return response
    scope, hidden, deleted = None, None, None
    if request.POST.has_key('scope'):
        scope = request.POST['scope']
    if request.POST.has_key('hidden'):
        hidden = request.POST['hidden']
    if request.POST.has_key('deleted'):
        deleted = request.POST['deleted']
    if scope is not None:
        postobj.scope = scope
    if hidden is not None:
        postobj.hidden = True
    else:
        postobj.hidden = False
    if deleted is not None:
        postobj.deleted = True
    else:
        postobj.deleted = False
    postobj.save()
    message = "The changes have been successfully saved."
    response = HttpResponse(message)
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def sendamessage(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    message = ""
    useremail = request.POST['useremail']
    emailmessage = request.POST['message']
    fromemail = userobj.emailid
    subject = ""
    targetuserobj = User.objects.get(emailid=useremail)
    if emailmessage.__len__() > 20:
        subject = emailmessage[:20] + "..." # First 20 characters will be the subject.
    else:
        subject = emailmessage
    subject = subject.replace("\n", " ")
    # Check if the targetuserobj has blocked the logged in user. If so, no email can be sent to the targetuserobj by this user.
    retval = skillutils.sendemail(targetuserobj, subject, emailmessage, fromemail)
    # Add appropriate info in the Network_post table.
    post = Post()
    post.posttargettype = 'user'
    post.posttargetuser = targetuserobj
    post.postmsgtag = subject
    post.poster = userobj
    post.postcontent = emailmessage
    post.scope = 'private'
    post.attachmentfile = None
    post.newmsg = True
    try:
        post.save()
    except:
        pass
    if retval > 0:
        message = "Successfully sent email to user with email Id '%s'"%useremail
    else:
        message = "Could not send email to user with email Id '%s'"%useremail
    response = HttpResponse(message)
    return response


"""
Need to do session checks inside the function.
"""
def showgroupprofile(request):
    if request.method != 'GET':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    if not request.COOKIES.has_key('sessioncode') or not request.COOKIES.has_key('usertype'):
        message = "Invalid session. Can't access the information requested."
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobjqset = Session.objects.filter(sessioncode=sesscode)
    if list(sessionobjqset).__len__() < 1 :
        message = "Invalid session object. Can't access the information requested."
        return HttpResponseBadRequest(message)
    userobj = sessionobjqset[0].user
    grpid = ""
    if request.GET.has_key('grp'):
        grpid = request.GET['grp']
    else:
        message = "Could not find a group id parameter with the request!"
        return HttpResponse(message)
    groupobj = None
    try:
        groupobj = Group.objects.get(id=grpid)
    except:
        message = "Could not find a group with the specified Id (%s)"%grpid
        return HttpResponse(message)
    datadict = {}
    # Get group data to display
    datadict['grpowner'] = groupobj.owner
    userdisplayname = groupobj.owner.displayname
    datadict['grpname'] = groupobj.groupname
    datadict['grpid'] = groupobj.id
    datadict['grptagline'] = groupobj.tagline
    datadict['grpdescription'] = groupobj.description
    datadict['grpmemberscount'] = groupobj.memberscount
    datadict['grptype'] = groupobj.grouptype
    datadict['grpcreationdate'] = groupobj.creationdate
    datadict['grpimagefile'] = "/media/" + userdisplayname + "/groups/" + groupobj.groupname + "/" + str(groupobj.groupimagefile)
    if not groupobj.groupimagefile:
        datadict['grpimagefile'] = ""
    datadict['grptopic'] = groupobj.basedontopic
    datadict['grpstars'] = groupobj.stars
    datadict['grppaid'] = groupobj.ispaid
    datadict['grpcurrency'] = groupobj.currency
    datadict['grpentryfee'] = groupobj.entryfee
    datadict['grpsubscriptionfee'] = groupobj.subscription_fee
    datadict['grpownerperm'] = groupobj.require_owner_permission
    datadict['joinrequesturl'] = mysettings.SEND_JOIN_REQUEST_URL
    datadict['getpaymentgwurl'] = mysettings.PAYMENT_GW_URL
    datadict['getsubscriptiongwurl'] = mysettings.SUBSCRIPTION_GW_URL
    datadict['exitgroupurl'] = mysettings.EXIT_GROUP_URL
    datadict['gentlereminderurl'] = mysettings.SEND_GENTLE_REMINDER_URL
    datadict['posts'] = []
    # **** The code below doesn't work as of now. Need to fix it ASAP.
    if groupobj.grouptype != 'PRIV':
        posts = Post.objects.filter(posttargetgroup = groupobj).order_by('createdon').reverse()[:5]
        # Got a list of the latest 5 posts on the group above.
        for post in posts:
            postcontent = post.postcontent
            postcreator = post.poster.displayname
            datadict['posts'].append({'content' : postcontent, 'poster' : postcreator })
    grpjoinreqset = GroupJoinRequest.objects.filter(user=userobj, group=groupobj).order_by('-requestdate')
    if list(grpjoinreqset).__len__() == 0:
        datadict['joinstatus'] = 0
    else:
        status = grpjoinreqset[0].outcome
        if status == 'accept' and (groupobj.entryfee > 0 or groupobj.ispaid == False):
            datadict['joinstatus'] = 1
        else:
            grppaidtxnqset = GroupPaidTransactions.objects.filter(group=groupobj, payer=userobj).order_by('-transdatetime')
            if list(grppaidtxnqset).__len__() > 0:
                targetdate = grppaidtxnqset[0].targetperiod
                tz_info = targetdate.tzinfo
                currdate = datetime.datetime.now(tz_info)
                if targetdate > currdate:
                    datadict['joinstatus'] = 1
                else:
                    datadict['joinstatus'] = 0
        if status != "accept" and groupobj.entryfee == 0 and groupobj.subscription_fee == 0:
            datadict['joinstatus'] = 2
    # Treat users who have exited the group before
    grpmemberqset = GroupMember.objects.filter(group=groupobj, member=userobj).order_by('-membersince')
    if list(grpmemberqset).__len__() > 0:
        if grpmemberqset[0].removed == True and grpmemberqset[0].blocked == False:
            datadict['joinstatus'] = 0
    tmpl = get_template("network/groupprofilepage.html")
    datadict.update(csrf(request))
    cxt = Context(datadict)
    grpprofilehtml = tmpl.render(cxt)
    return HttpResponse(grpprofilehtml)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def exitgroup(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    groupid = None
    if request.POST.has_key('groupid'):
        groupid = request.POST['groupid']
    else:
        message = "Couldn't find the required parameter 'groupid'. Can't process this request."
        return HttpResponse(message)
    groupobjqset = Group.objects.filter(id=groupid)
    groupobj = None
    if list(groupobjqset).__len__() > 0:
        groupobj = groupobjqset[0] # We will consider the first item only. However, we expect this to be 1.
    if not groupobj:
        message = "Couldn't find the group object indicated by the given groupId (%s)\nQuiting now.\n"%(groupid)
        return HttpResponse(message)
    # We have a valid group object. So we go to GroupMember class (table in mysql) to mark this record as 'removed'.
    grpmemberqset = GroupMember.objects.filter(group=groupobj, member=userobj)
    if list(grpmemberqset).__len__() < 1:
        message = "User is not a member of this group. So she cannot be removed.\n"
        return HttpResponse(message)
    grpmemberobj = grpmemberqset[0]
    grpmemberobj.removed = True
    grpmemberobj.lastremovaldate = datetime.datetime.now()
    grpmemberobj.save()
    message = "You have successfully exited from the group. You may join in later if you feel like."
    return HttpResponse(message)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def showwithdrawscreen(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    subsearnings = SubscriptionEarnings.objects.filter(user=userobj)
    # First, generate a unique code...
    securecode = skillutils.randomstringgen(6)
    # ... create a record for the activity in WithdrawalActivity...
    withdrawalobj = WithdrawalActivity()
    withdrawalobj.user = userobj
    withdrawalobj.sessioncode = sesscode
    withdrawalobj.securecode = securecode
    withdrawalobj.save()
    # ... and send it to the registered email address for this account.
    targetemailaddr = userobj.emailid
    emailsubject = "SecureCode for fund withdrawal"
    emailmessage = """
        Dear %s,

        It seems you are initiating a fund withdrawal activity. To continue, please copy the code '%s' and paste it in the appropriate location in your withdrawal form. Wish you a nice experience of fund withdrawal.

        Thanks,
        TestYard Team.
    """%(userobj.displayname, securecode)
    try:
        skillutils.sendemail(userobj, emailsubject, emailmessage, mysettings.MAILSENDER)
    except:
        message = "Couldn't send email containing the secure code. Error: %s\n"%sys.exc_info()[1].__str__()
        return HttpResponse(message)
    """
    Note: Since we can do multiple withdrawal activity in the same session, we will need to look for
    the securecode as well as the session Id and user Id when we go for authenticating the activity.
    [Implemented as above in 'dowithdrawal' function below.]
    """
    contextdict = {}
    if subsearnings.__len__() == 0:
        contextdict['balance'] = 0
        contextdict['earnings'] = 0
        contextdict['lasttransactiondate'] = ""
        contextdict['cutpercent'] = mysettings.CUT_FRACTION * 100
    else:
        subsearningobj = subsearnings[0]
        balance = subsearningobj.balance
        earnings = subsearningobj.earnings
        lasttransactdate = subsearningobj.lasttransactdate
        contextdict['balance'] = balance
        contextdict['earnings'] = earnings
        contextdict['lasttransactiondate'] = lasttransactdate
        contextdict['cutpercent'] = mysettings.CUT_FRACTION * 100
    contextdict['client_id'] = mysettings.WEPAY_CLIENT_ID
    contextdict['user_name'] = userobj.firstname + " " + userobj.lastname
    contextdict['email'] = userobj.emailid
    contextdict['redirect_uri'] = mysettings.APP_URL_PREFIX + mysettings.WEPAY_REGISTER_REDIRECT_URL
    # Select all available bank accounts of this user and create a select dropdown with it.
    bankacctqset = OwnerBankAccount.objects.filter(groupowner=userobj)
    if bankacctqset.__len__() < 1:
        message = "It looks like you do not have a bank account registered with TestYard. Please register an account by going to the 'setting' section of 'Manage Owned Groups' screen and then try to perform this activity again."
        return HttpResponse(message)
    bankinfo = {}
    for bankacct in bankacctqset:
        bankinfo[bankacct.bankname] = bankacct.id
    contextdict['bankaccts'] = bankinfo
    tmpl = get_template("subscription/withdrawalscreen.html")
    contextdict.update(csrf(request))
    cxt = Context(contextdict)
    withdrawhtml = tmpl.render(cxt)
    return HttpResponse(withdrawhtml)


""" This was for wepay - we do not need this just now.
@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def dowithdrawal(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    balance, withdrawamount, earnings, securecode = "", "", "", ""
    message = "At least one of the required argument is missing. Please try again."
    if request.POST.has_key('balance'):
        balance = request.POST['balance']
    else:
        response = HttpResponse(message)
        return response
    if request.POST.has_key('withdrawamount'):
        withdrawamount = request.POST['withdrawamount']
    else:
        response = HttpResponse(message)
        return response
    if request.POST.has_key('earnings'):
        earnings = request.POST['earnings']
    else:
        response = HttpResponse(message)
        return response
    if request.POST.has_key('securecode'):
        securecode = request.POST['securecode']
    else:
        response = HttpResponse(message)
        return response
    if request.POST.has_key('bankaccts'):
        bankacct = request.POST['bankaccts']
    else:
        response = HttpResponse(message)
        return response
    csrfmiddlewaretoken = request.POST['csrfmiddlewaretoken']
    customer_ip = ""
    if request.META.has_key('REMOTE_ADDR'): 
        customer_ip = request.META['REMOTE_ADDR']
    customer_ua = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36"
    if request.META.has_key('HTTP_USER_AGENT'):
        customer_ua = request.META['HTTP_USER_AGENT']
    if withdrawamount > balance:
        message = "Withdrawal amount cannot be greater than the balance amount in your account. Please rectify this and try again"
        return HttpResponse(message)
    # Check if the secure code is correct or not.
    withdrawalactivityqset = WithdrawalActivity.objects.filter(user=userobj, sessioncode=sesscode, securecode=securecode, securecodestatus=True)
    if withdrawalactivityqset.__len__() < 1:
        message = "The securecode was incorrect or your session got corrupted. Please try again"
        response = HttpResponse(message)
        return response
    # Set the used securecode status to False
    withdrawalactivityqset[0].securecodestatus = False
    
    # So everything is in order and we can do the transaction now. Get the account info for this user from the OwnerBankAccount table and start the transaction.
    bankacctqset = OwnerBankAccount.objects.filter(id=bankacct)
    if bankacctqset.__len__() < 1:
        message = "It looks like you do not have a bank account registered with TestYard. Please register an account by going to the 'setting' section of 'Manage Owned Groups' screen and then try to perform this activity again."
        return HttpResponse(message)
    contextdict = {}
    contextdict['client_id'] = mysettings.WEPAY_CLIENT_ID
    contextdict['redirect_uri'] = mysettings.APP_URL_PREFIX + mysettings.WEPAY_REGISTER_REDIRECT_URL
    contextdict['user_name'] = userobj.firstname + " " + userobj.lastname
    contextdict['email'] = userobj.emailid
    
    # Now, we make the call to 'https://wepay.com/v2/oauth2/authorize' with all the GET params and retrieve the 'code' value
    authorizeuri = mysettings.WEPAY_USER_REGISTER_URL
    no_redirect_opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler())
    httpHeaders = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'}
    authorizeuri = authorizeuri[:-1]
    data = { 'client_id' : mysettings.WEPAY_CLIENT_ID, 'scope' : 'manage_accounts,collect_payments,view_user,send_money,preapprove_payments', 'redirect_uri' : mysettings.APP_URL_PREFIX + mysettings.WEPAY_REGISTER_REDIRECT_URL, 'user_name' : userobj.firstname + " " + userobj.lastname, 'user_email' : userobj.emailid, 'state' : 'robot', 'popup' : '1'}
    getdata = urllib.urlencode(data)
    authorizeuri = authorizeuri + "?" + getdata
    pageRequest = urllib2.Request(authorizeuri, None, httpHeaders)
    pageResponse = None
    message = ""
    try:
        pageResponse = no_redirect_opener.open(pageRequest)
    except:
        pageResponse = None
        message = "Error: %s\n"%sys.exc_info()[1].__str__()
        return HttpResponse(message)
    responsecontent = skillutils.decodeGzippedContent(pageResponse.read())
    return HttpResponse(responsecontent)
"""


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def dowithdrawal(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    balance, withdrawamount, earnings, securecode = "", "", "", ""
    message = "At least one of the required argument is missing. Please try again."
    if request.POST.has_key('balance'):
        balance = request.POST['balance']
    else:
        response = HttpResponse(message)
        return response
    if request.POST.has_key('withdrawamount'):
        withdrawamount = request.POST['withdrawamount']
    else:
        response = HttpResponse(message)
        return response
    if request.POST.has_key('earnings'):
        earnings = request.POST['earnings']
    else:
        response = HttpResponse(message)
        return response
    if request.POST.has_key('securecode'):
        securecode = request.POST['securecode']
    else:
        response = HttpResponse(message)
        return response
    if request.POST.has_key('bankaccts'):
        bankacct = request.POST['bankaccts']
    else:
        response = HttpResponse(message)
        return response
    csrfmiddlewaretoken = request.POST['csrfmiddlewaretoken']
    customer_ip = ""
    if request.META.has_key('REMOTE_ADDR'): 
        customer_ip = request.META['REMOTE_ADDR']
    customer_ua = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36"
    if request.META.has_key('HTTP_USER_AGENT'):
        customer_ua = request.META['HTTP_USER_AGENT']
    if withdrawamount > balance:
        message = "Withdrawal amount cannot be greater than the balance amount in your account. Please rectify this and try again"
        return HttpResponse(message)
    # Check if the secure code is correct or not.
    withdrawalactivityqset = WithdrawalActivity.objects.filter(user=userobj, sessioncode=sesscode, securecode=securecode, securecodestatus=True)
    if withdrawalactivityqset.__len__() < 1:
        message = "The securecode was incorrect or your session got corrupted. Please try again"
        response = HttpResponse(message)
        return response
    # Set the used securecode status to False
    withdrawalactivityqset[0].securecodestatus = False
    
    # So everything is in order and we can do the transaction now. Get the account info for this user from the OwnerBankAccount table and start the transaction.
    bankacctqset = OwnerBankAccount.objects.filter(id=bankacct)
    ff = open("/home/supriyo/work/testyard/tmpfiles/bankqset.txt", "w")
    ff.write(str(bankacctqset[0].id))
    ff.close()
    if bankacctqset.__len__() < 1:
        message = "It looks like you do not have a bank account registered with TestYard. Please register an account by going to the 'settings and Join Requests' section of 'Manage Owned Groups' screen. Then please come to this screen to try to perform this activity again. That will register your account with our payment partner, and thereafter you would be able to transact easily."
        return HttpResponse(message)
    contextdict = {}
    # First check if the bank account has a value in razor_account_id field.
    if bankacctqset[0].razor_account_id == "":
        ff = open("/home/supriyo/work/testyard/tmpfiles/bankqset2.txt", "w")
        ff.write(str(bankacctqset[0].id))
        ff.close()
        msg = skillutils.onboardclientonrazor(bankacctqset[0].id)
        return HttpResponse("Your account is not included in our payment partner's website. So we are doing it now. Please try the transaction after 30 mins")
    transferuri = mysettings.RAZORPAY_BASEURI + "/transfers"
    
    opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler())
    httpHeaders = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/png,*/*;q=0.8'}
    exchgratesqset = ExchangeRates.objects.filter(curr_from='USD', curr_to='INR').order_by('-dateofrate')
    amounttowithdraw = exchgratesqset[0]*withdrawamount * 100 # Convert to paisa as Razorpay handles figures in paisa only.
    data = { 'account' : bankacctqset[0].razor_account_id, 'amount' : amounttowithdraw, 'currency' : 'INR'}
    postdata = urllib.urlencode(data)
    pageRequest = urllib2.Request(transferuri, postdata, httpHeaders)
    pageResponse = None
    message = ""
    try:
        pageResponse = opener.open(pageRequest)
    except:
        pageResponse = None
        message = "Error: %s\n"%sys.exc_info()[1].__str__()
        return HttpResponse(message)
    responsecontent = skillutils.decodeGzippedContent(pageResponse.read())
    responsedict = json.loads(responsecontent)
    rptrx = RazorPayTransaction()
    for rpkey in responsedict.keys():
        if rpkey == "id":
            withdrawalactivityqset[0].razorpaycode = responsedict[rpkey]
            rptrx.transaction_id = responsedict[rpkey]
        elif rpkey == "source":
            rptrx.source = mysettings.RAZORPAY_MERCHANT_ID
        elif rpkey == "recipient":
            rptrx.recipient_merchant_id = responsedict[rpkey]
            rptrx.recipient = userobj
        elif rpkey == "amount":
            rptrx.amount = responsedict[rpkey]
        elif rpkey == "currency":
            rptrx.currency = responsedict[rpkey]
        elif rpkey == "on_hold":
            rptrx.on_hold = responsedict[rpkey]
        elif rpkey == "tax":
            rptrx.tax = responsedict[rpkey]
        elif rpkey == "fees":
            rptrx.fees = responsedict[rpkey]
        elif rpkey == "created_at":
            rptrx.trxtimestamp = responsedict[rpkey]
    rptrx.save()
    withdrawalactivityqset[0].save()
    # Decrease the amount from the SubscriptionEarnings table.
    try:
        subscriptionearningsobj = SubscriptionEarnings.objects.get(user=userobj)
        subscriptionearningsobj.balance = subscriptionearningsobj.balance - withdrawamount # This is in USD
        subscriptionearningsobj.save()
    except:
        message = "Could not get the subscription earnings record. This money had to be refunded now."
        refundamount(rptrx.transaction_id, rptrx.amount)
    ff = open("/home/supriyo/work/testyard/tmpfiles/razorpayresponse.txt", "w")
    ff.write(responsecontent)
    ff.close()
    return HttpResponse(responsecontent)


"""
This method will get called if the subscriptionearnings record could not be found
or could not be appropriately changed for some reason.
"""
def refundamount(trxid, amount):
    pass


"""
This is the dummy authorize function which retrieves all params that
are to be sent to the wepay endpoint and it does this by using the 
data collected from the wepay form embedded in withdrawal.html and
then making a urllib2 request with that collected data.
"""

@csrf_exempt
def wepayauthorize(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    request_url = request.get_full_path()
    #no_redirect_opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), skillutils.NoRedirectHandler())
    httpHeaders = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'application/json', 'Accept-Language' : 'en-US,en;q=0.8', 'Accept-Encoding' : 'gzip,deflate,sdch', 'Connection' : 'keep-alive'}
    """
    ff = open("/home/supriyo/work/testyard/tmpfiles/authorizedump.txt", "w")
    try:
        ff.write(str(request.POST))
    except:
        pass
    try:
        ff.write(str(request.GET))
    except:
        pass
    ff.write("FULL URL: %s\n"%request_url)
    """
    #Send a request to mysettings.APP_URL_PREFIX + request.path + "?"
    """
    ff.write("\n+++++++++++++++++++++++++++++++++++++++++++++++++++++\n")
    ff.write(request.META['QUERY_STRING'])
    ff.close()
    """
    return HttpResponse("")



"""
This is the second stage of the withdrawal process. We need to 
get the code parameter from the request URL, and use it to get
the access_token.
"""
@csrf_protect
def wepayoauthredirect(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    codeval, username, useremail, bankacctid, securecode = "", "", "", "", ""
    if request.POST.has_key('code'):
        codeval = request.POST['code']
    if request.POST.has_key('username'):
        username = request.POST['username']
    if request.POST.has_key('useremail'):
        useremail = request.POST['useremail']
    if request.POST.has_key('bankacctvalue'):
        bankacctid = request.POST['bankacctvalue']
    if request.POST.has_key('securecode'):
        securecode = request.POST['securecode']
    """
    ff = open("/home/supriyo/work/testyard/tmpfiles/request_data.txt","w")
    ff.write(codeval + "####" + username + "####" + useremail + "####" + bankacctid)
    ff.close()
    """
    bankacctobj = None
    try:
        bankacctobj = OwnerBankAccount.objects.get(id=bankacctid)
    except:
        message = "Error: A bank account could not be associated with your account. Please enter bank account details while creating a paid group before continuing with this procedure."
        return HttpResponse(message)
    # Create a request here to get access_token
    request_uri = mysettings.WEPAY_OAUTH2_URI
    paramsdict = {'client_id' : mysettings.WEPAY_CLIENT_ID, 'redirect_uri' : mysettings.APP_URL_PREFIX + mysettings.WEPAY_REGISTER_REDIRECT_URL, 'client_secret' : mysettings.WEPAY_CLIENT_SECRET, 'code' : codeval}
    requestparams = urllib.urlencode(paramsdict)
    no_redirect_opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), skillutils.NoRedirectHandler())
    httpHeaders = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'application/json', 'Accept-Language' : 'en-US,en;q=0.8', 'Accept-Encoding' : 'gzip,deflate,sdch', 'Connection' : 'keep-alive'}
    pageRequest = urllib2.Request(request_uri, requestparams, httpHeaders)
    
    ff = open("/home/supriyo/work/testyard/tmpfiles/at_request_data.txt","w")
    ff.write(request_uri + "?" + requestparams)
    ff.close()

    message = ""
    try:
        pageResponse = no_redirect_opener.open(pageRequest)
    except:
        pageResponse = None
        message = sys.exc_info()[1].__str__()
        return HttpResponse(message)
    responsecontent = skillutils.decodeGzippedContent(pageResponse.read())
    
    ff = open("/home/supriyo/work/testyard/tmpfiles/response_data.txt","w")
    ff.write(responsecontent)
    ff.close()
    
    responsedict = json.loads(responsecontent)
    user_id, access_token, token_type, expires_in = -1, "", "", 0
    if responsedict.has_key('user_id'):
        user_id = responsedict['user_id']
    if responsedict.has_key('access_token'):
        access_token = responsedict['access_token']
    if responsedict.has_key('token_type'):
        token_type = responsedict['token_type']
    if responsedict.has_key('expires_in'):
        expires_in = responsedict['expires_in']
    userobj = None
    try:
        userobj = User.objects.get(emailid=useremail)
    except:
        message = "Could not determine the user from the given username and email Id. Please ensure that you are using the same email Id that is registered with your testyard account"
        return HttpResponse(message)
    # Now that we have got our access_token, we need to create a wepay account for this user.
    # If an account already exists, we will simply update the access_token field.
    wepayobj = None
    wepayacctid = ""
    try:
        wepayobj = WePay.objects.get(user=userobj)
        wepayacctid = wepayobj.wepayacctid
    except:
        wepayobj = WePay()
        wepayobj.user = userobj
    try:
        wepayobj.access_token = access_token
        wepayobj.token_type = token_type
        wepayobj.access_token_expires = expires_in
        wepayobj.wepay_state = "initiated"
        wepayobj.wepay_user_id = user_id
        wepayobj.wepay_authorized = True
        wepayobj.ownerbankaccount = bankacctobj
        #wepayobj.create_datetime = datetime.datetime.now()
        wepayobj.code = codeval
        wepayobj.save()
    except:
        message = "Error in creating/modifying a wepay object - %s"%sys.exc_info()[1].__str__()
        return HttpResponse(message)
    
    ff = open("/home/supriyo/work/testyard/tmpfiles/access_token.txt","w")
    ff.write(access_token + "####" + token_type + "####" + expires_in)
    ff.close()
    
    # Update WithdrawalActivity
    withdrawalobj = None
    try:
        withdrawalobj = WithdrawalActivity.objects.get(securecode=securecode)
    except:
        message = "A withdrawal activity could not be associated with this transaction. Please note that your securecode is %s and report this to customer care at customercare@testyard.in."%securecode
        return HttpResponse(message)
    withdrawalobj.wepaycode = codeval
    withdrawalobj.save()
    # Done with data saving, we now get on with the rest of the withdrawal process.
    # We will now go to the last step (step #4) of the process, where we either create 
    # WePay account (if it doesn't already exists), or do nothing (if it exists).
    if not wepayacctid: # We need to create one
        acct_create_uri = mysettings.WEPAY_ACCT_CREATE_URI
        # Account name will be the same as User object's 'displayname' field. This
        # field is unique for every user on testyard, and hence we may safely use it for this purpose.
        paramsdict = {'name' : userobj.displayname, 'description' : userobj.displayname + "'s account",}
        requestparams = urllib.urlencode(paramsdict)
        no_redirect_opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), skillutils.NoRedirectHandler())
        httpHeaders = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36', 'Accept-Language' : 'en-US,en;q=0.8', 'Accept-Encoding' : 'gzip,deflate,sdch', 'Connection' : 'keep-alive', 'Authorization' : 'Bearer %s'%access_token}
        pageRequest = urllib2.Request(acct_create_uri, requestparams, httpHeaders)
        try:
            pageResponse = no_redirect_opener.open(pageRequest)
        except:
            pageResponse = None
            message = sys.exc_info()[1].__str__()
            return HttpResponse(message)
        responsecontent = skillutils.decodeGzippedContent(pageResponse.read())
        responsecontentdict = json.loads(responsecontent)
        acct_id = responsecontentdict['account_id']
        state = responsecontentdict['state']
        owneruserid = responsecontentdict['owner_user_id']
        try:
            wepayuserobj = WePay.object.get(wepay_user_id=owneruserid)
        except:
            message = "Couldn't find the required fields in the JSON results."
            return HttpResponse(message)
        wepayuserobj.wepayacctid = acct_id
        wepayuserobj.wepay_state = state
        wepayuserobj.save()
    message = "Successfully settled the records for the WePay model."
    return HttpResponse(message)



def payumoneyfailure(request):
    pass

# Set the 'removed' flag in 'GroupMember' model to True.
@csrf_protect
def leavegroup(request): 
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponse(message)
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    groupname, groupid = "", ""
    if request.POST.has_key('groupname'):
        groupname = request.POST['groupname']
    if not groupname:
        return HttpResponse("Could not find required parameter groupname")
    grpqset = Group.objects.filter(groupname=groupname)
    if list(grpqset).__len__() == 0:
        return HttpResponse("Could not find the named group. Please check the group name and try again. If the problem persists, contact the support desk with the details of the operation")
    grpobj = grpqset[0]
    groupid = grpobj.id
    grpmemberqset = GroupMember.objects.filter(group=grpobj, member=userobj).order_by('-membersince')
    #Due to a previous bug, some groups will have the same member multiple times. 
    #The bug has been fixed but the erroneous records remain in DB.
    for grpmemberobj in grpmemberqset:
        grpmemberobj.removed = True
        grpmemberobj.removeagent = "user"
        grpmemberobj.lastremovaldate = datetime.datetime.now()
        grpmemberobj.save()
    message = "You have successfully left the group."
    return HttpResponse(message)




