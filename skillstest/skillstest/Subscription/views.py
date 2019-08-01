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
import urllib, urllib2, httplib
import simplejson as json
import md5

# Application specific libraries...
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
from skillstest.Subscription.models import Plan, UserPlan, Transaction, Coupon, UserCoupon
from skillstest.Tests.models import Topic, Subtopic, Evaluator, Test, UserTest, Challenge, UserResponse
from skillstest import settings as mysettings
from skillstest.errors import error_msg
import skillstest.utils as skillutils


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def subscriptions(request):
    message = ''
    if request.method != "GET" and request.method != 'POST': # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.SUBSCRIPTION_URL + "?msg=%s"%message)
        return response
    # If request method is 'GET', then retrieve Session and User info from the DB
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    plans = Plan.objects.all() # Getting all Plans.
    plans_dict = {}
    subscription_data_dict = {}
    curdatetime = datetime.datetime.now()
    planslistseq = []
    for pln in plans:
        planname = pln.planname
        planslistseq.append(planname)
        plandesc = pln.plandescription
        planid = pln.id
        createdate = pln.createdate
        startdate, starttime = str(createdate).split(" ")
        planstatus = pln.status
        discountpercent = pln.discountpercent
        discountamt = pln.discountamt
        userplanqset = UserPlan.objects.filter(user=userobj, plan=pln, planstatus=True).order_by('-planenddate')
        userplanobj = None
        if list(userplanqset).__len__() > 0:
            userplanobj = userplanqset[0]
        plansubscribed = ""
        if userplanobj:
            plansubscribed = True
        testscount = pln.tests
        interviewscount = pln.interviews
        candidates = pln.candidates
        price = pln.price
        plans_dict[planname] = [planname, plandesc, testscount, interviewscount, candidates, price, planid, createdate, discountpercent, discountamt, plansubscribed]
    subscription_data_dict['plans'] = plans_dict
    subscription_data_dict['plansseq'] = planslistseq
    subscription_data_dict['displayname'] = userobj.displayname
    subscription_data_dict['plansubscribeurl'] = mysettings.PLAN_SUBSCRIBE_URL
    subscription_data_dict['paymentgwoptionsurl'] = mysettings.PAYMENT_GW_OPTIONS_URL
    subscription_data_dict['profile_image_tag'] = skillutils.getprofileimgtag(request)
    subscription_data_dict['authbearerurl'] = mysettings.PAYU_AUTH_BEARER_CODE_URL
    subscription_data_dict['posid'] = mysettings.PAYU_POS_ID
    subscription_data_dict['payuclientsecret'] = mysettings.PAYU_CLIENT_SECRET
    subscription_data_dict['plansubscribepaypalurl'] = mysettings.SUBSCRIBE_PAYPAL_URL
    inc_context = skillutils.includedtemplatevars("Subscription", request) # Since this is the 'Profile' page for the user.
    for inc_key in inc_context.keys():
        subscription_data_dict[inc_key] = inc_context[inc_key]
    tmpl = get_template("subscription/subscription.html")
    subscription_data_dict.update(csrf(request))
    cxt = Context(subscription_data_dict)
    subscriptionhtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        subscriptionhtml = subscriptionhtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(subscriptionhtml)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def subscribeplan(request):
    message = ''
    if request.method != "GET" and request.method != 'POST': # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.SUBSCRIPTION_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    planid = request.POST['planid']
    couponcode = request.POST['couponcode']
    planobj = None
    try:
        planobj = Plan.objects.get(id=planid)
    except:
        message = "Could not find the plan submitted: %s"%sys.exc_info()[1].__str__()
        response = HttpResponse(message)
        return response
    couponobj = None
    discount = 0.00
    totalamt = planobj.price
    if couponcode != "":
        try:
            couponobj = Coupon.objects.get(coupon_code=couponcode)
            curdatetime = datetime.datetime.now()
            couponobj.valid_from = couponobj.valid_from.replace(tzinfo=None)
            couponobj.valid_till = couponobj.valid_till.replace(tzinfo=None)
            if not couponobj.status or couponobj.valid_from > curdatetime or couponobj.valid_till < curdatetime:
                totalamt = planobj.price
                return HttpResponse(couponobj.valid_from)
            else:
                totalamt = skillutils.applycoupon(couponobj, planobj)
        except:
            pass
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
    urlnotify = mysettings.URL_PROTOCOL + request.META['SERVER_NAME'] + "/" + mysettings.MY_PAYU_NOTIFY_URL_PATH
    data = { 'notifyUrl' : urlnotify, 'customerIp' : client_ip, 'merchantPosId' : payuposid, 'description' : planobj.planname, 'currencyCode' : 'PLN', 'totalAmount' : str(int(totalamt * 100)), 'buyer' : { "email": userobj.emailid,  "phone": "9711998537", "firstName": userobj.firstname, "lastName": userobj.lastname, "language": "en"  }, 'settings' : { "invoiceDisabled":"true" }, 'products' : [{ "name": planobj.planname, "unitPrice": str(int(planobj.price * 100)),  "quantity": "1"  }]}
    jsondata = json.dumps(data)
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
    if redirectUri != "":
        response = HttpResponse(redirectUri)
    else:
        tmpl = get_template("subscription/completefreetransactions.html")
        contextdict = { 'order_id' : orderId }
        contextdict.update(csrf(request))
        cxt = Context(contextdict)
        completefreetranshtml = tmpl.render(cxt)
        response = HttpResponse(completefreetranshtml)
    # Create the transaction record here with the trans_status field set to False.
    transobj = Transaction()
    transobj.username = userobj.displayname
    transobj.user = userobj
    transobj.orderId = orderId
    if planobj is not None:
        transobj.plan = planobj
    else:
        transobj.plan = None
    transobj.usersession = sesscode
    transobj.payamount = totalamt
    transobj.transactiondate = datetime.datetime.now()
    transobj.comments = ""
    transobj.paymode = 'PAYU'
    transobj.invoice_email = userobj.emailid
    transobj.trans_status = False
    transobj.clientIp = ""
    transobj.extOrderId = ""
    if redirectUri == "":
        transobj.clientIp = client_ip
        transobj.extOrderId = orderId
        transobj.trans_status = True
        transobj.comments = "Free subscription"
    transobj.save()
    return response


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def subscribepaypal():
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.SUBSCRIPTION_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    planid = request.POST['planid']
    couponcode = request.POST['couponcode']
    planobj = None
    try:
        planobj = Plan.objects.get(id=planid)
    except:
        message = "Could not find the plan submitted: %s"%sys.exc_info()[1].__str__()
        response = HttpResponse(message)
        return response
    couponobj = None
    discount = 0.00
    totalamt = planobj.price
    if couponcode != "":
        try:
            couponobj = Coupon.objects.get(coupon_code=couponcode)
            curdatetime = datetime.datetime.now()
            couponobj.valid_from = couponobj.valid_from.replace(tzinfo=None)
            couponobj.valid_till = couponobj.valid_till.replace(tzinfo=None)
            if not couponobj.status or couponobj.valid_from > curdatetime or couponobj.valid_till < curdatetime:
                totalamt = planobj.price
                return HttpResponse(couponobj.valid_from)
            else:
                totalamt = skillutils.applycoupon(couponobj, planobj)
        except:
            pass
    paypal_subscribe_url = mysettings.SUBSCRIBE_PAYPAL_URL
    no_redirect_opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), skillutils.NoRedirectHandler())
    httpHeaders = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : 'application/json', 'Accept-Language' : 'en-US,en;q=0.8', 'Accept-Encoding' : 'gzip,deflate,sdch', 'Connection' : 'keep-alive', 'Cache-Control' : 'no-cache', 'Pragma' : 'no-cache' }
    httpHeaders['Authorization'] = "Bearer %s"%mysettings.PAYPAL_SANDBOX_ACCESS_TOKEN
    httpHeaders['Content-Type'] = "application/json"
    ordersUrl = mysettings.PAYPAL_SANDBOX_ORDERS_URL
    data = { "intent":"sale", "redirect_urls":{ "return_url": mysettings.PAYPAL_RETURN_URL, "cancel_url" : mysettings.PAYPAL_CANCEL_URL }, "payer":{ "payment_method":"paypal" },"transactions":[{"amount":{ "total": str(totalamt), "currency":"USD"  }} ]}
    jsondata = json.dumps(data)
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
    #contentDict = json.loads(jsonContent)
    return HttpResponse(jsonContent)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def showpaymentgwoptions(request):
    message = ''
    if request.method != 'POST': # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.SUBSCRIPTION_URL + "?msg=%s"%message)
        return response
    sesscode = request.COOKIES['sessioncode']
    usertype = request.COOKIES['usertype']
    sessionobj = Session.objects.filter(sessioncode=sesscode)
    userobj = sessionobj[0].user
    planid = None
    if not request.POST.has_key('planid'):
        message = "Invalid request - no plan Id was found in the request."
        return HttpResponse(message)
    planid = request.POST['planid']
    planname = ""
    try:
        planobj = Plan.objects.get(id=planid)
        planname = planobj.planname
    except:
        pass
    contextdict = { 'planid' : planid, 'planname' : planname }
    # Render content using 'contextdict'
    tmpl = get_template("subscription/paymentgwoptions.html")
    contextdict.update(csrf(request))
    cxt = Context(contextdict)
    try:
        paymentgwoptionshtml = tmpl.render(cxt)
    except:
        print sys.exc_info()[1].__str__()
        message = error_msg('1132')
        response = HttpResponse(message)
        return response
    response = HttpResponse(paymentgwoptionshtml)
    return response


"""
@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
"""
def payunotify(request):
    """
    This method receives the notification request from PayU.
    We will analyze this request for the 'OpenPayu-Signature'
    header and the data concerning the order placed.
    """
    if not request.META.has_key('OpenPayu-Signature'):
        message = "Could not find the 'OpenPayu-Signature' header."
        response = HttpResponseBadRequest(message)
        return response
    ff = open("/home/supriyo/work/testyard/tmpfiles/notifypayu.txt", "w")
    ff.write("Received notify call\n")
    # If we got the OpenPayu-Signature header, then we will verify it.
    openPayUSig = request.META['OpenPayu-Signature']
    openPayUSigParts = openPayUSig.split(";")
    inSignature = ""
    algo = ""
    for sigParts in openPayUSigParts:
        key, value = sigParts.split("=")
        if key == 'signature':
            inSignature = value
        elif key == 'algorithm':
            algo = value
        else:
            pass
    jsonContent = request.body
    ff.write(jsonContent)
    ff.close()
    # Verify the signature
    concatvalue = jsonContent + mysettings.PAYU_SECOND_ID
    m = md5.new()
    m.update(concatvalue)
    digestvalue = m.digest()
    if digestvalue != inSignature:
        message = "The 2 signatures do not match. Quiting...\n"
        response = HttpResponseBadRequest(message)
        return response
    #At this point, the 2 signatures match. So we go ahead with the order request received from PayU.
    jsonDict = json.loads(jsonContent)
    # Get the data from the jsonDict, and enter the appropriate data in the DB.
    orderData = jsonDict['order']
    orderId, extOrderId, orderCreateDate, customerIp, merchantPosId, description, currencyCode, totalAmount, status, name, value, paymentId = "", "", "", "", "", "", "", "", "", "", "", ""
    localReceiptDateTime = jsonDict['localReceiptDateTime']
    properties = jsonDict['properties']
    if properties.__len__() > 0:
        name = properties[0]['name']
        value = properties[0]['value']
        if name == "PAYMENT_ID":
            paymentId = value
        else:
            paymentId = None
    orderId = orderData['orderId']
    notifyUrl = orderData['notifyUrl']
    extOrderId = orderData['extOrderId']
    orderCreateDate = orderData['orderCreateDate']
    customerIp = orderData['customerIp']
    merchantPosId = orderData['merchantPosId']
    description = orderData['description']
    currencyCode = orderData['currencyCode']
    totalAmount = orderData['totalAmount']
    status = orderData['status']
    if status != "COMPLETED":
        message = "PayU payment process is in progress."
        response = HttpResponseBadRequest(message)
        return response
    # Add records in the following tables: Subscription_transaction, Subscription_usercoupon and Subscription_userplan.
    transobj = Transaction.objects.get(orderId=orderId)
    transobj.comments = description
    transobj.clientIp = customerIp
    transobj.trans_status = True # True value
    transobj.extOrderId = extOrderId
    transobj.save()
    grpobj = transobj.group
    userobj = transobj.user
    # ... and now we go for GroupPaidTransactions.
    grppaidtxnobj = GroupPaidTransactions()
    grppaidtxnobj.group = grpobj
    grppaidtxnobj.payer = userobj
    grppaidtxnobj.amount = totalAmount
    grppaidtxnobj.currency = 'USD' # Since we converted the transaction amount into USD, we put USD in every record here.
    grppaidtxnobj.transdatetime = datetime.datetime.now()
    grppaidtxnobj.payeripaddress = customerIP
    grppaidtxnobj.save()
    try:
        grpjoinreqobj = GroupJoinRequest.objects.get(orderId=orderId)
        grpjoinreqobj.outcome = "accept"
        grpjoinreqobj.active = True
        grpjoinreqobj.reason = "payment completed"
        grpjoinreqobj.save()
    except:
        message = "Could not update the GroupJoinRequest table for order Id %s. Error: %s\n"%(orderId, sys.exc_info()[1].__str__())
        return HttpResponse(message)
    # GroupMember should be updated too.
    # Here we go for updating SubscriptionEarnings table...
    seqset = SubscriptionEarnings.objects.filter(user=grpobj.owner)
    seobj = None
    if seqset.__len__() < 1:
        seobj = SubscriptionEarnings() # First transaction for the user.
        seobj.user = grpobj.owner
    else:
        seobj = seqset[0]
    seobj.earnings += transobj.payamount
    seobj.balance += transobj.payamount
    seobj.lasttransactdate = datetime.datetime.now()
    seobj.save()
    # Associate the member with the group.
    grpmemobj = None
    # First, check if the user was already a member. If so, use that membership record.
    try:
        grpmemobj = GroupMember.objects.get(group=grpobj, member=userobj)
    except:
        grpmemobj = GroupMember()
    grpmemobj.group = grpobj
    grpmemobj.member = userobj
    grpmemobj.membersince = datetime.datetime.now()
    grpmemobj.status = True
    grpmemobj.removed = False
    grpmemobj.blocked = False
    grpmemobj.removeagent = ""
    grpmemobj.lastremovaldate = ""
    grpmemobj.save()
    message = "Order has been successfully placed"
    response = HttpResponse(message)
    return response








