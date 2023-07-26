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
from skillstest.Subscription.models import Plan, UserPlan, Transaction, Coupon, UserCoupon, PlanExtensions
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


# TODO: Formulate purchase of plan workflow from subscribeplan above.
@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def buyplan(request):
    if request.method != 'GET':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode, usertype = "", ""
    if request.COOKIES.has_key('sessioncode'):
        sesscode = request.COOKIES['sessioncode']
    if request.COOKIES.has_key('usertype'):
        usertype = request.COOKIES['usertype']
    sessionobj, userobj = None, None
    if sesscode != "":
        sessionobj = Session.objects.filter(sessioncode=sesscode)
        userobj = sessionobj[0].user
    plans_dict = {}
    curdate = datetime.datetime.now()
    plans_dict['curdate'] = curdate
    plans_dict['login_url'] = mysettings.LOGIN_URL
    plans_dict['register_url'] = "/" + mysettings.REGISTER_URL
    plans_dict['logged_in_as'] = ""
    if sesscode != "" and sessionobj is not None:
        plans_dict['profile_image_tag'] = skillutils.getprofileimgtag(request)
    else:
        plans_dict['profile_image_tag'] = ""
    inc_context = skillutils.includedtemplatevars("", request)
    for inc_key in inc_context.keys():
        plans_dict[inc_key] = inc_context[inc_key]
    # TODO: Buy plan logic goes here....
    
    plans_dict['privacypolicy_url'] = skillutils.gethosturl(request) + "/" + mysettings.PRIVPOLICY_URL
    plans_dict['tou_url'] = skillutils.gethosturl(request) + "/" + mysettings.TERMSOFUSE_URL
    plans_dict['show_upgrade_plan_url'] = skillutils.gethosturl(request) + "/" + mysettings.UPGRADE_PLAN_SCREEN_URL
    if skillutils.isloggedin(request):
        plans_dict['logged_in_as'] = userobj.displayname
    tmpl = get_template("subscription/plansnpricing.html")
    plans_dict.update(csrf(request))
    cxt = Context(plans_dict)
    planshtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        planshtml = planshtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(planshtml)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def upgradeuserplanscreen(request):
    if request.method != 'GET':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode, usertype = "", ""
    if request.COOKIES.has_key('sessioncode'):
        sesscode = request.COOKIES['sessioncode']
    if request.COOKIES.has_key('usertype'):
        usertype = request.COOKIES['usertype']
    sessionobj, userobj = None, None
    if sesscode != "":
        sessionobj = Session.objects.filter(sessioncode=sesscode)
        userobj = sessionobj[0].user
    if userobj is None:
        message = "Error: Couldn't identify the user. This could be due to your session getting expired. Please login and try again."
        return HttpResponse(message)
    # Find the current plan in effect for the user
    currentdatetime = datetime.datetime.now()
    userplanqset = UserPlan.objects.filter(user=userobj, planstatus=True).order_by('-subscribedon')
    upgradeableplanslist = []
    context = {}
    if userplanqset.__len__() == 0 or "Free" in userplanqset[0].plan.planname: # User is under 'Free Plan'
        upgradeableplansqset = Plan.objects.filter(status=True)
        context['currentplanname'] = "Free Plan"
        context['currentuserplanid'] = ""
        for upgradeableplanobj in upgradeableplansqset:
            if 'Free' in upgradeableplanobj.planname:
                continue
            validfor = str(upgradeableplanobj.planvalidfor) + " " + str(upgradeableplanobj.validfor_unit)
            extra_amount_to_pay = float(upgradeableplanobj.price) + float(upgradeableplanobj.fixedcost)
            d = {'planname' : upgradeableplanobj.planname, 'testsninterviews' : upgradeableplanobj.testsninterviews, 'plandescription' : upgradeableplanobj.plandescription, 'candidates' : upgradeableplanobj.candidates, 'price' : format(float(upgradeableplanobj.price), ".2f"), 'fixedcost' : format(float(upgradeableplanobj.fixedcost), ".2f"), 'validfor' : validfor, 'extra_amount_to_pay' : format(extra_amount_to_pay, ".2f") }
            upgradeableplanslist.append(d)
    else: # We should only consider plans whose 'price' are greater than the user's current plan's price. Just kidding...
        existinguserplanobj = None
        for userplan in userplanqset:
            if userplan.planstartdate.replace(tzinfo=None) <= currentdatetime and userplan.planenddate.replace(tzinfo=None) >= currentdatetime:
                existinguserplanobj = userplan
                break
        if existinguserplanobj is None: # User is a Free Plan user
            upgradeableplansqset = Plan.objects.filter(status=True)
            context['currentplanname'] = "Free Plan"
            context['currentuserplanid'] = ""
            for upgradeableplanobj in upgradeableplansqset:
                if 'Free' in upgradeableplanobj.planname:
                    continue
                validfor = str(upgradeableplanobj.planvalidfor) + " " + str(upgradeableplanobj.validfor_unit)
                extra_amount_to_pay = float(upgradeableplanobj.price) + float(upgradeableplanobj.fixedcost)
                d = {'planname' : upgradeableplanobj.planname, 'testsninterviews' : upgradeableplanobj.testsninterviews, 'plandescription' : upgradeableplanobj.plandescription, 'candidates' : upgradeableplanobj.candidates, 'price' : format(float(upgradeableplanobj.price), ".2f"), 'fixedcost' : format(float(upgradeableplanobj.fixedcost), ".2f"), 'validfor' : validfor, 'extra_amount_to_pay' : format(extra_amount_to_pay, ".2f") }
                upgradeableplanslist.append(d)
        else:
            context['currentplanname'] = existinguserplanobj.plan.planname
            context['currentuserplanid'] = existinguserplanobj.id
            existinguserplantestsinterviews = existinguserplanobj.plan.testsninterviews
            upgradeableplansqset = Plan.objects.filter(status=True)
            for upgradeableplanobj in upgradeableplansqset:
                if upgradeableplanobj.planname == existinguserplanobj.plan.planname or upgradeableplanobj.testsninterviews <= existinguserplantestsinterviews: # Same plan as the one the user currently has, or a lower end plan, so skip.
                    continue
                validfor = str(upgradeableplanobj.planvalidfor) + " " + str(upgradeableplanobj.validfor_unit)
                extra_amount_to_pay = float(upgradeableplanobj.price) + float(upgradeableplanobj.fixedcost) - float(existinguserplanobj.plan.price) - float(existinguserplanobj.plan.fixedcost)
                # Note: We don't make allowance for the time remaining for the current plan to end for the user. Even if it is just 1 second, we request a full payment for the upgrade.
                d = {'planid' : upgradeableplanobj.id, 'planname' : upgradeableplanobj.planname, 'testsninterviews' : upgradeableplanobj.testsninterviews, 'plandescription' : upgradeableplanobj.plandescription, 'candidates' : upgradeableplanobj.candidates, 'price' : format(float(upgradeableplanobj.price), ".2f"), 'fixedcost' : format(float(upgradeableplanobj.fixedcost), ".2f"), 'validfor' : validfor, 'extra_amount_to_pay' : format(extra_amount_to_pay, ".2f") }
                upgradeableplanslist.append(d)
    context['upgradeableplanslist'] = upgradeableplanslist
    context['plan_upgrade_url'] = skillutils.gethosturl(request) + "/" + mysettings.UPGRADE_USERPLAN_URL
    tmpl = get_template("subscription/upgradeplanscreen.html")
    context.update(csrf(request))
    cxt = Context(context)
    upgradeplanhtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        upgradeplanhtml = upgradeplanhtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(upgradeplanhtml)


# TODO: Implement the following (Basically payment gateway integration).
@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def upgradeuserplan(request):
    if request.method != 'POST':
        message = error_msg('1004')
        return HttpResponseBadRequest(message)
    sesscode, usertype = "", ""
    if request.COOKIES.has_key('sessioncode'):
        sesscode = request.COOKIES['sessioncode']
    if request.COOKIES.has_key('usertype'):
        usertype = request.COOKIES['usertype']
    sessionobj, userobj = None, None
    if sesscode != "":
        sessionobj = Session.objects.filter(sessioncode=sesscode)
        userobj = sessionobj[0].user
    if userobj is None:
        message = "Error: Couldn't identify the user. This could be due to your session getting expired. Please login and try again."
        return HttpResponse(message)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def cancelsubscription(request):
    pass


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


# TODO: Implement subscription/plan dashboard with workflow similar to subscriptions() function above.
@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def showsubscriptiondashboard(request):
    message = ''
    if request.method != 'GET': # Illegal bad request... 
        message = error_msg('1004')
        response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.PLANS_URL + "?msg=%s"%message)
        return response
    sesscode = ""
    try:
        sesscode = request.COOKIES['sessioncode']
        usertype = request.COOKIES['usertype']
        sessionobj = Session.objects.filter(sessioncode=sesscode)
        userobj = sessionobj[0].user
    except:
        sessionobj = None
        userobj = None
    uid = -1
    if userobj is None or sessionobj is None:
        # Redirect to login page
        return HttpResponseRedirect(mysettings.LOGIN_URL)
    else:
        try:
            uid = int(userobj.id)
        except:
            pass
    context = {}
    if skillutils.isloggedin(request):
        context['logged_in_as'] = userobj.displayname
    dbconn, dbcursor = skillutils.connectdb()
    userplanssql = "select p.planname as planname, u.displayname as username, u.id as userid, up.totalcost as totalcost, up.amountpaid as amountpaid, up.planstatus as planstatus, up.subscribedon as subscribedon, up.discountamountapplied as discountamountapplied, up.planstartdate as planstartdate, up.planenddate as planenddate, up.amountdue as amountdue, up.id as userplanid, p.id as planid from Subscription_plan p, Subscription_userplan up, Auth_user u where up.user_id=%s and up.user_id=u.id and up.plan_id=p.id order by up.subscribedon desc"%uid    
    dbcursor.execute(userplanssql)
    userplanrows = dbcursor.fetchall()
    userplanslist = []
    basicplan_aggregated_spending = 0
    businessplan_aggregated_spending = 0
    unlimitedplan_aggregated_spending = 0
    basicplan_tests_count = 0
    basicplan_interviews_count = 0
    businessplan_tests_count = 0
    businessplan_interviews_count = 0
    unlimitedplan_tests_count = 0
    unlimitedplan_interviews_count = 0
    newcursor = dbconn.cursor()
    for userplan in userplanrows:
        updict = {}
        updict['planname'] = userplan[0]
        if userplan[0] == "Basic Plan":
            try:
                basicplan_aggregated_spending += float(userplan[4])
            except:
                pass
        if userplan[0] == "Business Plan":
            try:
                businessplan_aggregated_spending += float(userplan[4])
            except:
                pass
        if userplan[0] == "Unlimited Plan":
            try:
                unlimitedplan_aggregated_spending += float(userplan[4])
            except:
                pass
        updict['username'] = userplan[1]
        updict['userid'] = userplan[2]
        try:
            updict['totalcost'] = format(userplan[3], ".2f")
        except:
            updict['totalcost'] = userplan[3]
        try:
            updict['amountpaid'] = format(userplan[4], ".2f")
        except:
            updict['amountpaid'] = userplan[4]
        updict['planstatus'] = userplan[5]
        try:
            updict['subscribedon'] = userplan[6].strftime("%Y-%m-%d %H:%M:%S")
        except:
            updict['subscribedon'] = userplan[6]
        try:
            updict['discountamountapplied'] = format(userplan[7], ".2f")
        except:
            updict['discountamountapplied'] = userplan[7]
        try:
            updict['planstartdate'] = userplan[8].strftime("%Y-%m-%d %H:%M:%S")
        except:
            updict['planstartdate'] = userplan[8]
        try:
            updict['planenddate'] = userplan[9].strftime("%Y-%m-%d %H:%M:%S")
        except:
            updict['planenddate'] = userplan[9]
        testscountsql = "select count(*) from Tests_test where createdate >= '%s' and createdate < '%s' and creator_id=%s"%(updict['planstartdate'], updict['planenddate'], uid)
        newcursor.execute(testscountsql)
        alltestrows = newcursor.fetchall()
        testscount = 0
        if alltestrows.__len__() > 0:
            testscount = alltestrows[0][0]
        if userplan[0] == "Basic Plan":
            basicplan_tests_count += testscount
        elif userplan[0] == "Business Plan":
            businessplan_tests_count += testscount
        elif userplan[0] == "Unlimited Plan":
            unlimitedplan_tests_count += testscount
        interviewscountsql = "select count(*) from Tests_interview where createdate >= '%s' and createdate < '%s' and interviewer_id=%s"%(updict['planstartdate'], updict['planenddate'], uid)
        newcursor.execute(interviewscountsql)
        allinterviewrows = newcursor.fetchall()
        interviewscount = 0
        if allinterviewrows.__len__() > 0:
            interviewscount = allinterviewrows[0][0]
        if userplan[0] == "Basic Plan":
            basicplan_interviews_count += interviewscount
        elif userplan[0] == "Business Plan":
            businessplan_interviews_count += interviewscount
        elif userplan[0] == "Unlimited Plan":
            unlimitedplan_interviews_count += interviewscount
        try:
            updict['amountdue'] = format(userplan[10], ".2f")
        except:
            updict['amountdue'] = userplan[10]
        updict['userplanid'] = userplan[11]
        updict['planid'] = userplan[12]
        userplanslist.append(updict)
    context['message'] = "You are subscribed to our Free Plan."
    context['noplans'] = 0 # Set it to 1 when ready with some subscription to show
    if userplanslist.__len__() > 1:
        context['message'] = "You have subscribed %s times in the past"%userplanslist.__len__()
        context['noplans'] = 0
    context['userplanslist'] = userplanslist
    context['basicplan_aggregated_spending'] = format(basicplan_aggregated_spending, ".2f")
    context['businessplan_aggregated_spending'] = format(businessplan_aggregated_spending, ".2f")
    context['unlimitedplan_aggregated_spending'] = format(unlimitedplan_aggregated_spending, ".2f")
    context['basicplan_tests_count'] = basicplan_tests_count
    context['basicplan_interviews_count'] = basicplan_interviews_count
    context['businessplan_tests_count'] = businessplan_tests_count
    context['businessplan_interviews_count'] = businessplan_interviews_count
    context['unlimitedplan_tests_count'] = unlimitedplan_tests_count
    context['unlimitedplan_interviews_count'] = unlimitedplan_interviews_count
    context['planextrate'] = mysettings.PLAN_EXTENSION_RATE
    context['coupon_discount_url'] = skillutils.gethosturl(request) + "/" + mysettings.FETCH_COUPON_DISCOUNT_URL
    context['search_test_subscription_url'] = skillutils.gethosturl(request) + "/" + mysettings.SEARCH_TEST_SUBSCRIPTION_URL
    couponslist = []
    curdate = datetime.datetime.now()
    couponsql = "select id, coupon_code, coupon_description, discount_value, max_use_count, currency_unit from Subscription_coupon where valid_from < %s and valid_till > %s and status=TRUE"
    dbcursor.execute(couponsql, (curdate, curdate))
    couponrecs = dbcursor.fetchall()
    usercouponsql = "select count(coupon_id), coupon_id from Subscription_usercoupon group by coupon_id"
    dbcursor.execute(usercouponsql)
    usercouponrecs = dbcursor.fetchall()
    usercouponsdict = {}
    for usercoup in usercouponrecs:
        usercouponsdict[str(usercoup[1])] = usercoup[0]
    for couponrec in couponrecs:
        couponid = couponrec[0]
        couponcode = couponrec[1]
        coupondesc = couponrec[2]
        discountval = couponrec[3]
        maxcount = couponrec[4]
        currencyunit = couponrec[5]
        if str(couponid) in usercouponsdict.keys():
            if usercouponsdict[str(couponid)] > maxcount:
                continue
        d = {'couponid' : couponid, 'couponcode' : couponcode, 'coupondesc' : coupondesc, 'discountval' : discountval, 'currencyunit' : currencyunit}
        couponslist.append(d)
    # Get all available coupons from DB along with their discount percentages.
    context['couponslist'] = couponslist
    inc_context = skillutils.includedtemplatevars("", request)
    for inc_key in inc_context.keys():
        context[inc_key] = inc_context[inc_key]
    context['plan_extension_url'] = skillutils.gethosturl(request) + "/" + mysettings.PLAN_EXTEND_URL
    skillutils.disconnectdb(dbconn, dbcursor) # Important to close DB connections
    tmpl = get_template("subscription/plansdashboard.html")
    context.update(csrf(request))
    cxt = Context(context)
    plansdashboardhtml = tmpl.render(cxt)
    for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
        plansdashboardhtml = plansdashboardhtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
    return HttpResponse(plansdashboardhtml)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def fetchcoupondiscount(request):
    if request.method != 'POST':
        message = "Error: Invalid method of call"
        response = HttpResponse(message)
        return response
    sesscode = ""
    try:
        sesscode = request.COOKIES['sessioncode']
        usertype = request.COOKIES['usertype']
        sessionobj = Session.objects.filter(sessioncode=sesscode)
        userobj = sessionobj[0].user
    except:
        sessionobj = None
        userobj = None
    if userobj is None or sessionobj is None:
        message = "Error: User is not logged in or session has expired."
        response = HttpResponse(message)
        return response
    else:
        pass
    couponcode = ""
    if 'couponcode' not in request.POST.keys():
        message = "Error: Required variable couponcode missing from request"
        return HttpResponse(message)
    couponcode = request.POST['couponcode']
    dbconn, dbcursor = skillutils.connectdb()
    couponsql = "select id, coupon_code, discount_value, max_use_count from Subscription_coupon where valid_from < %s and valid_till > %s and status=TRUE and coupon_code=%s"
    curdate = datetime.datetime.now()
    discount = 0.00
    dbcursor.execute(couponsql, (curdate, curdate, couponcode))
    couponrecs = dbcursor.fetchall()
    if couponrecs.__len__() == 0:
        message = "Error: The coupon code entered could not be found in the system."
        return HttpResponse(message)
    for couponrec in couponrecs:
        couponid = couponrec[0]
        couponcode = couponrec[1]
        discountval = couponrec[2]
        maxcount = couponrec[3]
        usercouponsql = "select count(*) from Subscription_usercoupon where coupon_id=%s"
        dbcursor.execute(usercouponsql, (couponid,))
        usercouponrecs = dbcursor.fetchall()
        if usercouponrecs.__len__() > 0:
            usedcount = int(usercouponrecs[0][0])
            if maxcount > usedcount:
                discount = 0.00
                break
            else:
                discount = float(discountval)
                break
        else:
            discount = float(discountval)
            break
    skillutils.disconnectdb(dbconn, dbcursor) # Important to close DB connections
    return HttpResponse(discount)


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def searchtestinterview(request):
    if request.method != 'POST':
        message = "Error: Invalid method of call"
        response = HttpResponse(message)
        return response
    sesscode = ""
    try:
        sesscode = request.COOKIES['sessioncode']
        usertype = request.COOKIES['usertype']
        sessionobj = Session.objects.filter(sessioncode=sesscode)
        userobj = sessionobj[0].user
    except:
        sessionobj = None
        userobj = None
    if userobj is None or sessionobj is None:
        message = "Error: User is not logged in or session has expired."
        response = HttpResponse(message)
        return response
    else:
        pass
    searchkey, itemtype = "", "test" # We choose 'test' as the default type.
    if 'rdtestint' in request.POST.keys():
        itemtype = request.POST['rdtestint']
    else:
        message = "Error: Required parameter 'rdtestint' missing."
        return HttpResponse(message)
    if 'searchkey' in request.POST.keys():
        searchkey = request.POST['searchkey']
    if itemtype != "test" and itemtype != "interview":
        message = "Error: item type could not be recognized"
        return HttpResponse(message)
    if searchkey == "":
        message = "Error: Invalid search key specified."
        return HttpResponse(message)
    dbconn, dbcursor = skillutils.connectdb()
    if itemtype == "test":
        searchsql = "select createdate, testname from Tests_test where creator_id=" + str(userobj.id) + " and testname like '%" + searchkey + "%'"
        try:
            dbcursor.execute(searchsql)
        except:
            message = "Error: The sql statement to find the tests and interviews matching the search key failed."
            return HttpResponse(message)
    elif itemtype == "interview":
        searchsql = "select createdate, title from Tests_interview where interviewer_id=" + str(userobj.id) + " and title like '%" + searchkey + "%'"
        try:
            dbcursor.execute(searchsql)
        except:
            message = "Error: The sql statement to find the tests and interviews matching the search key failed."
            return HttpResponse(message)
    else:
        message = "Error: item type could not be recognized"
        return HttpResponse(message)
    allrecs = dbcursor.fetchall()
    userplanidlist = []
    for rec in allrecs:
        createdate = rec[0]
        userplansql = "select id, plan_id from Subscription_userplan where user_id=%s and planstartdate < %s and planenddate > %s"
        dbcursor.execute(userplansql, (userobj.id, createdate, createdate))
        userplanrecords = dbcursor.fetchall()
        for userplanrec in userplanrecords:
            userplanidlist.append(userplanrec[0])
    skillutils.disconnectdb(dbconn, dbcursor) # Important to close DB connections
    return HttpResponse(json.dumps(userplanidlist))


@skillutils.is_session_valid
@skillutils.session_location_match
@csrf_protect
def extenduserplan(request):
    message = ""
    sesscode = ""
    try:
        sesscode = request.COOKIES['sessioncode']
        usertype = request.COOKIES['usertype']
        sessionobj = Session.objects.filter(sessioncode=sesscode)
        userobj = sessionobj[0].user
    except:
        sessionobj = None
        userobj = None
    if userobj is None or sessionobj is None:
        # Redirect to login page
        return HttpResponseRedirect(mysettings.LOGIN_URL)
    else:
        pass
    context = {}
    if skillutils.isloggedin(request):
        context['logged_in_as'] = userobj.displayname
    else:
        context['logged_in_as'] = ""
    if request.method == 'GET':
        userplanid = -1
        if 'userplanid' in request.GET.keys():
            userplanid = request.GET['userplanid']
        else:
            message = "Error: Required parameter userplanid is missing. The server can't process this request."
            response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.PLANS_URL + "?msg=%s"%message)
            return response
        # First, make sure that the userplan identified by the given userplanid belongs to the current logged in user
        userplanobj = None
        try:
            userplanobj = UserPlan.objects.get(id=userplanid)
        except:
            message = "Error: Could not find the userplan object identified by the given userplanid. "
            response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.PLANS_URL + "?msg=%s"%message)
            return response
        if userplanobj.user != userobj: # The userplan does not belong to this user.
            message = "Error: The userplan identified by the given Id doesn't belong to you. This incident will be reported."
            response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.PLANS_URL + "?msg=%s"%message)
            return response
        if not userplanobj.plan.status:
            message = "Error: The requested subscription plan is no longer available for use. Please select a different subscription plan to continue. We are sorry for the inconvenience."
            response = HttpResponse(message)
            return response
        # Display the plans extension interface. It should also display the history of this specific userplan.
        planextensionslist = []
        planextensionsqset = PlanExtensions.objects.filter(userplan=userplanobj).order_by('-paymentdate')
        for planext in planextensionsqset:
            d = {'planextid' : planext.id, 'planname' : planext.userplan.plan.planname, 'username' : planext.user.displayname, 'periodstart' : planext.periodstart.strftime("%Y-%m-%d %H:%M:%S"), 'periodend' : planext.periodend.strftime("%Y-%m-%d %H:%M:%S"), 'invitescount' : planext.allowedinvites, 'amountpaid' : "{0:.2f}".format(planext.amountpaid), 'paymentdate' : planext.paymentdate.strftime("%Y-%m-%d %H:%M:%S"), 'status' : planext.extensionstatus, 'blocked' : planext.blocked}
            planextensionslist.append(d)
        context['planextensions'] = planextensionslist
        if planextensionslist.__len__() == 0:
            context['message'] = "You have not extended any subscription plan as yet."
        else:
            context['message'] = ""
        context['plan_extension_url'] = skillutils.gethosturl(request) + "/" + mysettings.PLAN_EXTEND_URL
        context['userplanid'] = userplanid
        context['planextrate'] = mysettings.PLAN_EXTENSION_RATE
        couponslist = []
        curdate = datetime.datetime.now()
        dbconn, dbcursor = skillutils.connectdb()
        couponsql = "select id, coupon_code, coupon_description, discount_value, max_use_count, currency_unit from Subscription_coupon where valid_from < %s and valid_till > %s and status=TRUE"
        dbcursor.execute(couponsql, (curdate, curdate))
        couponrecs = dbcursor.fetchall()
        usercouponsql = "select count(coupon_id), coupon_id from Subscription_usercoupon group by coupon_id"
        dbcursor.execute(usercouponsql)
        usercouponrecs = dbcursor.fetchall()
        usercouponsdict = {}
        for usercoup in usercouponrecs:
            usercouponsdict[str(usercoup[1])] = usercoup[0]
        for couponrec in couponrecs:
            couponid = couponrec[0]
            couponcode = couponrec[1]
            coupondesc = couponrec[2]
            discountval = couponrec[3]
            maxcount = couponrec[4]
            currencyunit = couponrec[5]
            if str(couponid) in usercouponsdict.keys():
                if usercouponsdict[str(couponid)] > maxcount:
                    continue
            d = {'couponid' : couponid, 'couponcode' : couponcode, 'coupondesc' : coupondesc, 'discountval' : discountval, 'currencyunit' : currencyunit}
            couponslist.append(d)
        # Get all available coupons from DB along with their discount percentages.
        context['couponslist'] = couponslist
        skillutils.disconnectdb(dbconn, dbcursor)
        context['amt_payable'] = "US$ " + "{0:.2f}".format(context['planextrate'] * 50); # We are setting 50 as the default value for invites count.
        tmpl = get_template("subscription/extenduserplan.html")
        context.update(csrf(request))
        cxt = Context(context)
        planextensionhtml = tmpl.render(cxt)
        for htmlkey in mysettings.HTML_ENTITIES_CHAR_MAP.keys():
            planextensionhtml = planextensionhtml.replace(htmlkey, mysettings.HTML_ENTITIES_CHAR_MAP[htmlkey])
        return HttpResponse(planextensionhtml)
    elif request.method == 'POST': # process this request and extend the userplan by adding a record in th PlanExtensions model.
        """
        a) Check if the user logged in is the same as the user whose plan is being extended.
        b) Check if the subscription plan is still active, or if any extension of the same plan is active. If yes, don't proceed.
        c) Check for coupon code. If found, apply the discount available for that coupon and populate the appropriate fields.
        """
        userplanid = -1
        if 'userplanid' in request.GET.keys():
            userplanid = request.GET['userplanid']
        else:
            message = "Error: Required parameter userplanid is missing. The server can't process this request."
            response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.PLANS_URL + "?msg=%s"%message)
            return response
        # First, make sure that the userplan identified by the given userplanid belongs to the current logged in user
        userplanobj = None
        try:
            userplanobj = UserPlan.objects.get(id=userplanid)
        except:
            message = "Error: Could not find the userplan object identified by the given userplanid. "
            response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.PLANS_URL + "?msg=%s"%message)
            return response
        if userplanobj.user != userobj: # The userplan does not belong to this user.
            message = "Error: The userplan identified by the given Id doesn't belong to you. This incident will be reported."
            response = HttpResponseBadRequest(skillutils.gethosturl(request) + "/" + mysettings.PLANS_URL + "?msg=%s"%message)
            return response
        if not userplanobj.plan.status:
            message = "Error: The requested subscription plan is no longer available for use. Please select a different subscription plan to continue. We are sorry for the inconvenience."
            response = HttpResponse(message)
            return response
        if userplanobj.planstatus is True:
            message = "The UserPlan associated with this request is still active. You may extend a userplan only when the userplan itself is not active anymore."
            response = HttpResponse(message)
            return response
        # Get the coupons data in a variable
        curdate = datetime.datetime.now()
        dbconn, dbcursor = skillutils.connectdb()
        couponsql = "select id, coupon_code, coupon_description, discount_value, max_use_count, currency_unit from Subscription_coupon where valid_from < %s and valid_till > %s and status=TRUE"
        dbcursor.execute(couponsql, (curdate, curdate))
        couponrecs = dbcursor.fetchall()
        usercouponsql = "select count(coupon_id), coupon_id from Subscription_usercoupon group by coupon_id"
        dbcursor.execute(usercouponsql)
        usercouponrecs = dbcursor.fetchall()
        usercouponsdict = {}
        coupondiscountdict = {}
        for usercoup in usercouponrecs:
            usercouponsdict[str(usercoup[1])] = usercoup[0]
        for couponrec in couponrecs:
            couponid = couponrec[0]
            couponcode = couponrec[1]
            coupondesc = couponrec[2]
            discountval = couponrec[3]
            maxcount = couponrec[4]
            currencyunit = couponrec[5]
            if str(couponid) in usercouponsdict.keys():
                if usercouponsdict[str(couponid)] > maxcount:
                    continue
            coupondiscountdict[couponcode] = discountval
        skillutils.disconnectdb(dbconn, dbcursor)
        # Get the values entered by the user
        userplanid, invitescount, period, yescoupon, couponcode, amtpayable = -1, 0, 30, 0, None, 0.00
        if 'userplanid' in request.POST.keys():
            try:
                userplanid = int(request.POST['userplanid'])
            except:
                message = "Invalid value for userplan Id. Please rectify it and try again."
                response = HttpResponse(message)
                return response
        else:
            message = "The request did not come with the required userplanid value. Please rectify the mistake and try again."
            response = HttpResponse(message)
            return response
        if 'selinvitescount' in request.POST.keys():
            try:
                invitescount = int(request.POST['selinvitescount'])
            except:
                message = "Invalid value for the count of invites selected. Expected an integer value."
                response = HttpResponse(message)
                return response
        else:
            message = "The request did not come with the required invites count. Please rectify the mistake and try again."
            response = HttpResponse(message)
            return response
        if 'selperiod' in request.POST.keys():
            try:
                period = int(request.POST['selperiod'])
            except:
                message = "Invalid value for period. Please specify an integer value in days."
                response = HttpResponse(message)
                return response
        else:
            message = "The request did not come with the required period value in days. Please rectify the mistake and try again."
            response = HttpResponse(message)
            return response
        if 'yescoupon' in request.POST.keys():
            try:
                yescoupon = int(request.POST['yescoupon'])
            except:
                pass # We will merely assume that the user did not specify a coupon code.
        else:
            yescoupon = 0
        if 'txtcoupon' in request.POST.keys() and yescoupon == 1:
            couponcode = request.POST['txtcoupon']
        else:
            pass
        if 'amtpayable' in request.POST.keys():
            try:
                amtpayable = float(request.POST['amtpayable'])
            except:
                pass # This is a hidden field value. And anyway, we are going to compute it. So no action is taken.
        else:
            pass
        # Next, make the computation based on the values received. Compare it with the value sent.
        amounttopay = float(invitescount) * float(mysettings.PLAN_EXTENSION_RATE)
        if yescoupon > 0 and couponcode is not None:
            try:
                amounttopay = amounttopay - coupondiscountdict[couponcode] * amounttopay/100
            except:
                message = "Could not apply discount for the coupon code entered by you. Please check with support for the availability of that coupon, or try another coupon code."
                response = HttpResponse(message)
                return response
        # TODO: Finally, we are done with the processing on our part, so we need to integrate with the payment gateway.
        # TODO: The data has to be inserted in the Subscription_planextension table in DB. Add a record for this user and plan in the table. 
        #TODO: Also, add a record in the Subscription_usercoupon table, if the user used a coupon to extend the plan.
