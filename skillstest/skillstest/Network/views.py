from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.core.context_processors import csrf
from django.views.generic import View
from django.http import HttpResponseBadRequest, HttpResponse , HttpResponseRedirect
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

# Application specific libraries...
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
from skillstest.Subscription.models import Plan, UserPlan, Transaction
from skillstest.Tests.models import Topic, Subtopic, Evaluator, Test, UserTest, Challenge, UserResponse, WouldbeUsers
from skillstest.Network.models import Connection, ConnectionInvitation, GroupMember, Group, Post, OwnerBankAccount, GroupJoinRequest, GentleReminder
from skillstest import settings as mysettings
from skillstest.errors import error_msg
import skillstest.utils as skillutils


def get_network_template_vars(userobj):
    templatevars = {}
    templatevars['creategroupurl'] = mysettings.CREATE_NETWORK_GROUP_URL
    templatevars['checkgrpnameavailabilityurl'] = mysettings.CHECK_GRPNAME_AVAIL_URL
    templatevars['searchgroupurl'] = mysettings.SEARCH_GROUP_URL
    templatevars['getgroupinfouri'] = mysettings.GET_GROUP_INFO_URI
    templatevars['showtestinfourl'] = mysettings.SHOW_TEST_INFO_URL
    templatevars['joinrequesturl'] = mysettings.SEND_JOIN_REQUEST_URL
    templatevars['gentlereminderurl'] = mysettings.SEND_GENTLE_REMINDER_URL
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
        contactlink = "<a href='#/' onClick='javascript:showconnectionsprofile(\"%s\");'>%s</a>"%(contact.id, contact.displayname)
        contacts.append(contactlink)
    for groupmember in groupmembersqset:
        grouplink = "<a href='#/' onClick='javascript:managegroup(\"%s\", \"%s\");'>%s</a>"%(groupmember.member.displayname, groupmember.group.groupname, groupmember.group.groupname)
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
    groupname, groupdescription, grouptopic, ispaid, isactive, allowentry, cleartest, grouptype, maxmemberscount, bankname, branchname, ifsccode, acctownername, acctnumber, testtoclear, entryfee, tagline =  ("" for i in range(0,17))
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
    testobj = None
    try:
    	if ispaid == 1:
	    bankname = request.POST['bankname']
	    branchname = request.POST['branchname']
	    ifsccode = request.POST['ifsccode']
	    acctownername = request.POST['acctownername']
	    acctnumber = request.POST['acctnumber']
            entryfee = request.POST['entryfee']
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
        if request.POST.has_key('cleartest') and request.POST['cleartest'] == '1':
            cleartest = True
            testtoclear = int(request.POST['testtoclear'])
            testobj = Test.objects.get(id=testtoclear)
        else:
            cleartest = False
            testtoclear = 0
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
    grpobj.entrytest = testobj
    if not entryfee or entryfee == "":
        entryfee = 0.0
    grpobj.entryfee = float(entryfee)
    grpmember.member = userobj
    grpmember.status = True
    grpmember.removed = False
    grpmember.blocked = False
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
        ownerbankacctobj.bankname = bankname
        ownerbankacctobj.bankbranch = branchname
        ownerbankacctobj.accountnumber = acctnumber
        ownerbankacctobj.ifsccode = ifsccode
        ownerbankacctobj.accountownername = acctownername
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
        grpdict['groupimagefile'] = groupobj.groupimagefile
        grpdict['stars'] = groupobj.stars
        grpdict['entrytestname'] = ""
        grpdict['entrytestid'] = ""
        if groupobj.entrytest is not None:
            grpdict['entrytestname'] = groupobj.entrytest.testname
            grpdict['entrytestid'] = str(groupobj.entrytest.id)
        grpdict['ispaid'] = groupobj.ispaid
        grpdict['entryfee'] = groupobj.entryfee
        grpdict['adminremarks'] = groupobj.adminremarks
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
    joinrequest = GroupJoinRequest()
    joinrequest.user = userobj
    joinrequest.group = groupobj
    joinrequest.outcome = 'open'
    joinrequest.active = True
    joinrequest.reason = ""
    # 1) Send an email to the group's owner
    # TODO: When displaying the group's data to its owner, we would list the requests received for that group from Network_groupjoinrequest
    # and tally the entries in Tests_usertest and Tests_wouldbeusers tables.
    groupowner = groupobj.owner
    subject = mysettings.GROUP_JOIN_REQUEST_SUBJECT%groupobj.groupname
    message = """I, %s, would like to join the group '%s' owned by you.
    Thanks,
    %s
	"""%(userobj.displayname, groupobj.groupname, userobj.displayname)
    fromaddr = userobj.emailid
    try:
        skillutils.sendemail(groupowner, subject, message, fromaddr)
    except:
        message = "Could not send email to group's owner"
        response = HttpResponse(message)
        return response
    # 2) Send a request to the test creator so that she/he sends an invitation to the user to take the qualifying test (if any).
    if groupobj.entrytest is not None: # The 'request' object needs to have the following params: testid, baseurl, txtemailslist, validfrom and validtill.
        subject = "Allow me to take the test named '%s'"%groupobj.entrytest.testname
        message = """
            Hi,

            I would like to take the test named '%s' created by you. I need to pass this test in order to 
            become a member of a group named '%s' on TestYard. Hence, please send me an invitation to take the
	    above mentioned test. (You would be able to send invitations for the test from "Groups You Own"
	    ==>> <group name> ==>> "Manage Group" screen, accessible on the right panel of the "Network" tab.)

	    Thanks,
            %s"""%(groupobj.entrytest.testname, groupobj.groupname, userobj.displayname)
        try:
            skillutils.sendemail(groupobj.entrytest.creator, subject, message, userobj.emailid)
        except:
            message = "Could not send request for invitation to the test to %s: %s"%(userobj.displayname, sys.exc_info()[1].__str__())
            response = HttpResponse(message)
            return response
    else:
        pass
        # 3) Check if it is a paid group. If so, collect the payment.
    try:
        joinrequest.save()
    except:
        message = "Could not save the join request: %s"%sys.exc_info()[1].__str__()
        response = HttpResponse(message)
        return response
    message = "Join request sent successfully."
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
    testid = None
    testobj = None
    if request.POST.has_key('testid'):
        testid = request.POST['testid']
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
	    if testid is not None:
                testqset = Test.objects.filter(id=testid)
                if testqset.__len__() > 0:
                    testobj = testqset[0]
                    utqset = UserTest.objects.filter(user=userobj,test=testobj, active=True, cancelled=False)
                    if utqset.__len__() == 0:
                        utqset = WouldbeUsers.objects.filter(user=userobj,test=testobj, active=True, cancelled=False)
                    if utqset.__len__() == 0:
                        emailmessage += """I would like to take the test named '%s' created by you. I need to pass this test in order to 
                        become a member of a group named '%s' (owned by you) on TestYard. Hence, please send me an invitation to take the
	                above mentioned test. (You would be able to send invitations for the test from 'Groups You Own' ==>> <group name>
                        ==>> 'Manage Group' screen, accessible on the right panel of the 'Network' tab).
                        """%(testobj.testname, groupobj.groupname)
                    else:
                        utobj = None
                        for utobj in utqset:
                            if utobj.status == 1 or utobj.status == 2:
                                break
                        if utobj.status == 0 or utobj.status == 1: # No gentle reminder should be sent. The user hasn't yet taken the test.
                            reminderflag = False
                        else:
                            emailmessage += """I have already taken the test for entry into the group named '%s'. Once it is evaluated, it 
                            would be possible for me to enter the group, (given that I pass the test). Could you please do the needful so that
                            it would be possible for me to use the platform if I am eligible to enter the group.
                            """
            else:
                emailmessage += """I have sent a request to you to join the group '%s'. Could you please allow me into the group so that I
                may access its resources and participate in all conversations.
                """%(groupobj.groupname)
	    emailmessage += """Thanks,
		%s
            """%(userobj.displayname)
            if testid and testqset.__len__() > 0:
                if reminderflag is True:
                    skillutils.sendemail(groupobj.entrytest.creator, emailsubject, emailmessage, userobj.emailid)
                else:
                    message = "You have not yet taken the test needed to be eligible to enter the group"
                    response = HttpResponse(message)
                    return response
            else:
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


