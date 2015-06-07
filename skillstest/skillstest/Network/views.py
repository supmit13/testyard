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

# Application specific libraries...
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
from skillstest.Subscription.models import Plan, UserPlan, Transaction
from skillstest.Tests.models import Topic, Subtopic, Evaluator, Test, UserTest, Challenge, UserResponse
from skillstest.Network.models import Connection, ConnectionInvitation, GroupMember, Group, Post, OwnerBankAccount
from skillstest import settings as mysettings
from skillstest.errors import error_msg
import skillstest.utils as skillutils


def get_network_template_vars(userobj):
    templatevars = {}
    templatevars['creategroupurl'] = mysettings.CREATE_NETWORK_GROUP_URL
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
        grouplink = "<a href='#/' onClick='javascript:showgrouppage(\"%s\");'>%s</a>"%(groupmember.member.displayname, groupmember.group.groupname)
        groups.append(grouplink)
    contextdict = { 'displayname' : userobj.displayname, 'msg' : '<b><i>it is social networking time!</i></b>', 'connections' : contacts, 'groups' : groups }
    inc_context = skillutils.includedtemplatevars("Network", request) # Since this is the 'Network' page for the user.
    for inc_key in inc_context.keys():
        contextdict[inc_key] = inc_context[inc_key]
    templatevars = get_network_template_vars(userobj)
    for tkey in templatevars.keys():
        contextdict[tkey] = templatevars[tkey]
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
    groupname, groupdescription, grouptopic, ispaid, isactive, allowentry, cleartest, grouptype, maxmemberscount, bankname, branchname, ifsccode, acctownername, acctnumber, testtoclear, entryfee =  ("" for i in range(0,16))
    if request.POST.has_key('groupname'):
        groupname = urllib.unquote(request.POST['groupname']).decode('utf8')
    if request.POST.has_key('groupdescription'):
        groupdescription = urllib.unquote(request.POST['groupdescription']).decode('utf8')
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
        message = "Group name added is not unique. Please rectify and try to create the group again."
        response = HttpResponse(message)
        return response
    grpobj = Group()
    grpmember = GroupMember()
    grpobj.owner = userobj
    grpobj.groupname = groupname
    grpobj.description = groupdescription
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


def isgroupnameunique(groupname):
    grpqsets = Group.objects.filter(groupname=groupname)
    if grpqsets.__len__() > 0:
        return False
    return True




