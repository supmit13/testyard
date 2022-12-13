import csv
import os, sys, re, time
import datetime
import simplejson as json
import urllib2, urllib
import StringIO, gzip

from django.conf import settings
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

import skillstest.utils as skillutils
from skillstest import settings as mysettings
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
from skillstest.Tests.models import Test, UserTest, WouldbeUsers, Challenge, UserResponse
from skillstest.Subscription.models import Plan, UserPlan, Transaction, Coupon, UserCoupon
from skillstest.Network.models import Connection, ConnectionInvitation, GroupMember, Group, Post, OwnerBankAccount, GroupJoinRequest, GentleReminder, ExchangeRates, SubscriptionEarnings, GroupPaidTransactions, WithdrawalActivity, WePay, RazorPayTransaction, StripeConnectedAccount, RazorPayCustomerAccount, RazorPayOrdersPayments, Payouts



def decodeGzippedContent(encoded_content):
    response_stream = StringIO.StringIO(encoded_content)
    decoded_content = ""
    try:
        gzipper = gzip.GzipFile(fileobj=response_stream)
        decoded_content = gzipper.read()
    except: # Maybe this isn't gzipped content after all....
        decoded_content = encoded_content
    return(decoded_content)

_decodeGzippedContent = decodeGzippedContent


def make_payouts():
    payoutsqset = Payouts.objects.filter(status=False)
    if payoutsqset.__len__() == 0:
        return None
    rzpclient = skillutils.initrazorpay()
    for payout in payoutsqset:
        gateway = payout.gateway
        payoutinfo = payout.payoutinfo
        payoutdict = json.loads(payoutinfo)
        if gateway == "RazorPay":
            customerid = payoutdict['customerid']
            fundacctid = payoutdict['fundaccountid']
            custgstin = payoutdict['gstin']
            payerbankacct = payoutdict['payeraccount']
            payoutamt = payoutdict['payoutamount']
            groupid = payoutdict['groupid']
            userid = payoutdict['userid']
            rzppaymentid = payoutdict['razorpay_paymentid']
            rzporderid = payoutdict['razorpay_orderid']
            reason = payoutdict['reason']
            if 'payreason' in payoutdict.keys():
                payreason = payoutdict['payreason']
            else:
                payreason = ""
            currency = payoutdict['currency']
            customer_ip = payoutdict['customer_ip']
            sesscode = payoutdict['sesscode']
            groupowneremail = payoutdict['groupowneremail']
            groupobj = Group.objects.get(id=groupid)
            userobj = User.objects.get(id=userid)
            grppaidtransaction = GroupPaidTransactions()
            grppaidtransaction.group = groupobj
            grppaidtransaction.payer = userobj
            if str(customerid) != "-1" and str(fundacctid) != "-1":
                grppaidtransaction.amount = int(payoutamt) # Order amount is in paise or cents.
            else:
                grppaidtransaction.amount = 0 # We won't be able to make the payout as we don't have fund account Id.
            grppaidtransaction.currency = currency
            grppaidtransaction.transdatetime = datetime.datetime.now()
            if payreason == 'entryfee' or payreason == '':
                grppaidtransaction.targetperiod = datetime.datetime.now() + datetime.timedelta(days=36500)
            else:
                grppaidtransaction.targetperiod = datetime.datetime.now() + datetime.timedelta(days=groupobj.subscriptionperiod)
            grppaidtransaction.reason = payreason
            grppaidtransaction.razorpaymentid = rzppaymentid
            grppaidtransaction.payeripaddress = customer_ip
            grpmember = GroupMember()
            grpmember.group = groupobj
            grpmember.member = userobj
            grpmember.membersince = datetime.datetime.now()
            grpmember.status = True
            grpmember.removed = False
            grpmember.blocked = False
            # TODO: Create a transaction record with the platform as user.
            """
            txnobj = Transaction()
            txnobj.username = userobj.displayname
            txnobj.user = userobj
            txnobj.orderId = rzporderid
            txnobj.plan = None
            txnobj.group = groupobj
            txnobj.usersession = sesscode
            txnobj.payamount = float(payoutamt)
            txnobj.transactiondate = datetime.datetime.now()
            txnobj.comments = reason
            txnobj.paymode = "RazorPay"
            txnobj.invoice_email = userobj.emailid
            txnobj.trans_status = True
            txnobj.clientIp = customer_ip
            txnobj.extOrderId = ""
            txnobj.paymentid_razorpay = rzppaymentid
            """
            if str(customerid) == "-1" and str(fundacctid) == "-1": # Send an email to the user (group's owner) about the situation (the group's owner does not have a RazorPay Customer and Fund account).
                subject = "You have earned a paid subscriber"
                message = """
                Dear Sir/Madam,
                This is to notify you that you have a paid subscriber in your group named '%s'. In order to access the payment made by the subscriber, you need to complete your group registration with us and create a 'Customer' account with RazorPay (our payment gateway) to facilitate the process. To do so, please login into your account on TestYard by clicking &lt;a href='https://testyard.in'&gt;here&lt;/a&gt;, or simply follow &lt;a href=''&gt;this link&lt;a&gt; to go to the group registration completion page.

                Thanks for your patronage on the TestYard platform.
                TestYard
                """%(groupobj.groupname)
                toemailid = groupowneremail
                fromemail = mysettings.MAILSENDER
                try:
                    retval = send_mail(subject, message, toemailid, [fromemail,], False)
                except:
                    print("Error: %s"%sys.exc_info()[1].__str__()) # TODO: log this exception, with the details of the situation.
                    logger.error("Error: %s"%sys.exc_info()[1].__str__())
            # The user who paid the amount should still become a member of the group. So we need to go ahead.
            # Make the payout call on RazorPay
            payouturl = "https://%s:%s@api.razorpay.com/v1/payouts"%(mysettings.RAZORPAY_KEY, mysettings.RAZORPAY_SECRET)
            opener = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler())
            # Add Razorpay creds in header
            httpHeaders = { 'User-Agent' : r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36',  'Accept' : '*/*', 'Cache-Control' : 'no-cache'}
            if str(fundacctid) != "-1":
                data = { 'account_number': payerbankacct, 'fund_account_id': fundacctid, 'amount': int(payoutamt), 'currency': currency, 'mode' : "IMPS", 'purpose' : 'payout', 'queue_if_low_balance' : True, 'reference_id' : rzppaymentid, 'narration' : reason, 'notes' : {'userip' : customer_ip, 'gstin' : custgstin}}
                postdata = urllib.urlencode(data)
                pageRequest = urllib2.Request(payouturl, postdata, httpHeaders)
                pageResponse= None
                try:
                    pageResponse = opener.open(pageRequest)
                    pageResponseContent = _decodeGzippedContent(pageResponse.read())
                except:
                    print("Error: %s"%sys.exc_info()[1].__str__()) # TODO: This error should be logged.
                    logger.error("Error: %s"%sys.exc_info()[1].__str__())
                    pageResponseContent = "{}"
                payoutresponse = json.loads(pageResponseContent)
                #print(payoutresponse)
                payoutid = -1
                if 'id' not in payoutresponse.keys() or payoutresponse['id'] == "": # Failure in payout
                    print(payoutresponse) # TODO: Log this erroroneous response. Payout was not possible, so grppaidtransaction amount should be made 0.
                    logger.error("Error: %s"%payoutresponse.__str__())
                    grppaidtransaction.amount = 0
                else:
                    payoutid = payoutresponse['id']
                payout.payoutid = payoutid
                payoutstatus = payoutresponse['status']
                utr = payoutresponse['utr']
                statusdetails = payoutresponse['status_details']
                payout.status = True
                payout.processed = datetime.datetime.now()
            try:
                payout.save()
                grppaidtransaction.save()
                grpmember.grppaidtxn = grppaidtransaction
                grpmember.save() # User becomes member of the group
            except:
                print("Error: %s"%sys.exc_info()[1].__str__())
                logger.error("Error: %s"%sys.exc_info()[1].__str__())
                continue
    print("Done!")
            


def process_subscription_info():
    infile = mysettings.SUBSCRIPTION_INFO_PATH # Path to the subscription info csv file
    with open(infile, 'rb') as csvfile:
        subsreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        rowctr = 0
        doublequotepattern = re.compile('"')
        for row in subsreader:
            if rowctr == 0: # Skip the first row as it will contain field headers
                rowctr += 1
                continue
            planname = row[0]
            plandescription = row[1]
            testscount = row[2]
            testscount = re.sub(doublequotepattern, "", testscount)
            interviewcount = row[3]
            interviewcount = re.sub(doublequotepattern, "", interviewcount)
            planfee = row[4]
            planfee = re.sub(doublequotepattern, "", planfee)
            planperiod = row[5]
            plancandidates = row[6]
            plancandidates = re.sub(doublequotepattern, "", plancandidates)
            discountpercent = row[7]
            discountpercent = re.sub(doublequotepattern, "", discountpercent)
            discountamt = (float(discountpercent)/100)*float(planfee)
            planperiodunit = 'M'
            planstatus = True
            plancreatedate = datetime.datetime.now()
            plan = Plan()
            plan.planname = planname
            plan.plandescription = plandescription
            plan.tests = testscount
            plan.interviews = interviewcount
            plan.price = planfee
            plan.validfor_unit = planperiodunit
            plan.planvalidfor = planperiod
            plan.status = planstatus
            plan.discountpercent = discountpercent
            plan.discountamt = discountamt
            plan.createdate = plancreatedate
            plan.candidates = plancandidates
            plan.save()
            rowctr += 1
            #print '##'.join(row)
            #print "@@ " + str(row.__len__()) + " @@\n"
    print "Processed and added %d plans from %s to database.\n"%(rowctr-1, infile)


def add_coupon():
    infile = mysettings.COUPON_INFO_PATH # Path to the subscription info csv file
    with open(infile, 'rb') as csvfile:
        couponreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        rowctr = 0
        doublequotepattern = re.compile('"')
        for row in couponreader:
            if rowctr == 0: # Skip the first row as it will contain field headers
                rowctr += 1
                continue
            elif row.__len__() == 0:
                continue
            try:
                couponcode = row[0]
                coupondesc = row[1]
                couponvalue = row[2]
                couponstartdate = row[3]
                couponenddate = row[4]
                couponstatus = row[5]
                couponcurunit = row[6]
                maxusecount = row[7]
                if couponcurunit == '':
                    couponcurunit = 'USD'
            except:
                print "Error extracting records from CSV file in row %s - %s\n"%(str(rowctr), sys.exc_info()[1].__str__())
                rowctr += 1
                continue
            try:
                coupon = Coupon()
                coupon.coupon_code = couponcode
                coupon.coupon_description = coupondesc
                coupon.valid_from = couponstartdate
                coupon.valid_till = couponenddate
                coupon.discount_value = couponvalue
                coupon.max_use_count = maxusecount
                coupon.currency_unit = couponcurunit
                if couponstatus == "True" or couponstatus == "1":
                    coupon.status = True
                else:
                    coupon.status = False
                coupon.save()
            except:
                print "Error creating coupon object with coupon code %s - %s\n"%(couponcode, sys.exc_info()[1].__str__())
                rowctr += 1
                continue
            rowctr += 1
        print "Processed and added %d coupons from %s to database.\n"%(rowctr-1, infile)



