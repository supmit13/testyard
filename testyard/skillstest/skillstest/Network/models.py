from django.db import models
from django.core.exceptions import ValidationError
from  django.core.validators import validate_email
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
from skillstest.Tests.models import Topic, Subtopic, Evaluator, Test, UserTest, Challenge, UserResponse
from skillstest import settings as mysettings
from skillstest.errors import error_msg
#import skillstest.utils as skillutils

import os, sys, re, time, datetime
import inspect

class Group(models.Model):
    owner = models.ForeignKey(User, related_name="+", null=False, blank=False, default='')
    groupname = models.CharField(max_length=200, blank=False, null=False)
    tagline = models.TextField(default="")
    description = models.TextField(default="")
    memberscount = models.IntegerField(default=0)
    maxmemberslimit = models.IntegerField(default=10000)
    status = models.BooleanField(default=True) # keep track of whether the group is active or not.
    grouptype = models.CharField(max_length=4, choices=((k,v) for k,v in mysettings.GROUP_TYPES_DICT.iteritems()), default='OPEN')
    creationdate = models.DateTimeField(auto_now=True,default=None)
    allowentry = models.BooleanField(default=True) # Keep track of whether users can be added to the group or not.
    groupimagefile = models.CharField(max_length=200, blank=True, null=True)
    basedontopic = models.CharField(max_length=200, blank=False, null=False) # Associated topic on which the group is based.
    # The topic should be one of the topics listed by skillutils.TEST_TOPICS or any custom topic added by the user while creating a test previously.
    adminremarks = models.TextField(default="")
    stars = models.IntegerField(default=0) # Indicates the popularity of the group.
    # TODO: Identify the set of criteria for which a group might gain or lose stars.
    #entrytest = models.ForeignKey(Test, related_name="+", null=True, blank=True, default=None) # A group might have an entry test. Users who pass the test would be allowed to be members of the group. Default is None (no test).
    max_tries_allowed = models.IntegerField(default=3) # Number of tries allowed before the user is no longer considered for the test.
    ispaid = models.BooleanField(default=False) # Whether entry into the group is paid or not.
    currency = models.CharField(max_length=3, blank=False, null=False, default='USD')
    entryfee = models.FloatField(default=0.0) # If paid, then this will contain the entry fee for the group.
    require_owner_permission = models.BooleanField(null=False, blank=False, default=False) # Require owner's permission before allowing any user to become a member.
    subscription_fee = models.FloatField(default=0.00)
    subscriptionperiod = models.IntegerField(default=0) # The default value of 0 denotes that the group has no subscription period. 
    # Note: 'subscriptionperiod' may be set to the subscription period in days, as determined by the owner of the group.

    class Meta:
        verbose_name = "Group Table"
        db_table = 'Network_group'

    def __unicode__(self):
        return "%s"%(self.member.firstname + "'s group")


class Post(models.Model):
    postmsgtag = models.CharField(max_length=255, null=True, blank=True, default='')
    postcontent = models.TextField(default="")
    poster = models.ForeignKey(User, related_name="+", null=False, blank=False, default='')
    posttargettype = models.CharField(max_length=200, blank=False, null=False) # Can be 'user', 'group' and/or 'test'. This will determine if 
    # the target of the post is another member or a group or a test.
    posttargetuser = models.ForeignKey(User, related_name="+", null=True, blank=True, default='')
    posttargetgroup = models.ForeignKey(Group, related_name="+", null=True, blank=True, default='')
    posttargettest = models.ForeignKey(Test, related_name="+", null=True, blank=True, default='')
    attachmentfile = models.CharField(max_length=200, blank=True, null=True) # image associated with the post, if any.
    scope = models.CharField(max_length=200, blank=False, null=False, default='public') # Can be either public, private or protected.
    relatedpost_id = models.IntegerField(default=None) # If the post is related to another post object from some other user/group
    deleted = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)
    stars = models.IntegerField(default=0)
    createdon = models.DateTimeField(auto_now=True,default=None)
    newmsg = models.BooleanField(default=False) # This is relevant only if the 'posttargettype' field has 'user' as its value.
    # If a message is not opened yet, this will be True.

    class Meta:
        verbose_name = "Posts Table"
        db_table = 'Network_post'

    def __unicode__(self):
        return "%s"%(self.poster + "'s post")



# This table keeps track of all individual transactions performed on any paid group
class GroupPaidTransactions(models.Model):
    group = models.ForeignKey(Group, related_name="+", null=False, blank=False)
    payer = models.ForeignKey(User, related_name="+", null=False, blank=False)
    amount = models.IntegerField(null=False, blank=False, default=0)
    currency = models.CharField(max_length=3, null=False, blank=False)
    transdatetime = models.DateTimeField(auto_now=True) # Date and time at which the transaction was made.
    targetperiod = models.DateTimeField()
    reason = models.CharField(max_length=25, choices=(('entryfee', 'Entry Fee'), ('subscriptionfee', 'Subscription Fee')), default='entryfee')
    stripechargeid = models.CharField(max_length=35, blank=False, default=None)
    razorpaymentid = models.CharField(max_length=100, blank=False, default=None)
    payeripaddress = models.CharField(max_length=20, null=True, blank=True, default='')

    class Meta:
        verbose_name = "GroupPaidTransactions Table"
        db_table = 'Network_grouppaidtransactions'


class GroupMember(models.Model):
    group = models.ForeignKey(Group, null=False, blank=False)
    member = models.ForeignKey(User, null=False, blank=False)
    membersince = models.DateTimeField(auto_now=True, default=None)
    status = models.BooleanField(default=True) # 'active' or 'inactive' -- True or False.
    removed = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False) # Posts to the group from this member will be blocked.
    # The following field specifies who removed the user from the group. 
    # A member may be removed from the group by herself/himself, or the owner.
    removeagent = models.CharField(null=True, blank=True, default=None, max_length=10) # May have one of the following 3 values: user, owner, null.
    lastremovaldate = models.DateTimeField(default=None)
    grppaidtxn = models.ForeignKey(GroupPaidTransactions, null=True)

    class Meta:
        verbose_name = "GroupMember Table"
        db_table = 'Network_groupmember'

    """
    def add(self, member, group):
        if self.memberscount + 1 > self.maxmemberslimit:
            return 0
        self.members.append(member)
        self.memberscount += 1
        return self.memberscount

    def remove(self, member, group):
        allmembers = self.members
        foundflag = 0
        ctr = 0
        for usr in allmembers:
            if usr.emailid == member.emailid:
                foundflag = 1
                break
            ctr += 1
        if foundflag:
            return self.members.pop(ctr)
        else:
            return -1
    """

class Connection(models.Model):
    focususer = models.ForeignKey(User, related_name="+", null=False, blank=False)
    connectedto = models.ForeignKey(User, null=True, blank=True)
    connectedfrom = models.DateTimeField(default=None, auto_now=True) # Date and time of creation of this connection
    deleted = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False) # Posts from the 'connectedto' user will be blocked.
    connectedthru = models.CharField(max_length=200, blank=True, null=True) # If connected through facebook or linkedin or through any other channel.

    class Meta:
        verbose_name = "Connections Table"
        db_table = 'Network_connection'


class ConnectionInvitation(models.Model):
    fromuser = models.ForeignKey(User, related_name="+", null=False, blank=False)
    touser = models.ForeignKey(User, related_name="+", null=False, blank=False)
    invitationcontent = models.TextField(default=mysettings.CONNECT_INVITATION_TEXT)
    invitationstatus = models.CharField(max_length=6, choices=(('open', 'Opened'), ('closed', 'Closed'), ('accept', 'Accepted'), ('refuse', 'Refused')), default='open')
    invitationdate = models.DateTimeField(auto_now=True, default=None)

    class Meta:
        verbose_name = "Connection Invitation Table"
        db_table = 'Network_connectioninvitation'


class OwnerBankAccount(models.Model):
    groupowner = models.ForeignKey(User, related_name="+", null=False, blank=False)
    group = models.ForeignKey(Group, null=False, blank=False)
    bankname = models.CharField(max_length=255, null=False, blank=False)
    bankbranch = models.CharField(max_length=255, null=False, blank=False)
    accountnumber = models.CharField(max_length=50, null=False, blank=False)
    ifsccode = models.CharField(max_length=25, null=False, blank=False)
    accountownername = models.CharField(max_length=255, null=False, blank=False)
    creationdate = models.DateTimeField(auto_now=True, default=None)
    razor_account_id = models.CharField(max_length=100, default="")

    class Meta:
        verbose_name = "ownerbankaccount Table"
        db_table = 'Network_ownerbankaccount'


class GroupJoinRequest(models.Model):
    group = models.ForeignKey(Group, related_name="+", null=False, blank=False)
    user = models.ForeignKey(User, related_name="+", null=False, blank=False)
    requestdate = models.DateTimeField(auto_now=True, default=None) # Date and time of sending the request
    outcome = models.CharField(max_length=6, choices=(('open', 'Open'), ('close', 'Close'), ('accept', 'Accept'), ('refuse', 'Refuse')), default='open') # What happened to the request - is it still open, or accepted or closed... or whatever.
    reason = models.TextField(default="") # If the request was refused, why was it done so.
    active = models.BooleanField(default=True) # A request is automatically deactivated after a fixed amount of time (determined by mysettings.REQUEST_ACTIVE_INTERVAL)
    orderId = models.CharField(max_length=60, null=True, blank=True, default=None) # This is the order Id for join requests to paid groups.

    class Meta:
        verbose_name = "groupjoinrequest Table"
        db_table = 'Network_groupjoinrequest'

    
class GentleReminder(models.Model):
    grpjoinrequest = models.ForeignKey(GroupJoinRequest, related_name="+", null=False, blank=False)
    reminderdate = models.DateTimeField(auto_now=True, default=None) # Date and time of sending the reminder

    class Meta:
        verbose_name = "gentlereminder Table"
        db_table = 'Network_gentlereminder'


class ExchangeRates(models.Model):
    curr_from = models.CharField(max_length=3, null=False, blank=False)
    curr_to = models.CharField(max_length=3, null=False, blank=False)
    conv_rate = models.CharField(max_length=20, null=True, blank=True, default='')
    dateofrate = models.DateTimeField(default=None) # Date on which the conversion rate is valid
    fetchtime = models.DateTimeField(auto_now=True) # date and time on which the rates were fetched.

    class Meta:
        verbose_name = "Exchange Rates Table"
        db_table = 'Network_exchangerates'

# All amounts are stored as US dollars.
class SubscriptionEarnings(models.Model):
    user = models.ForeignKey(User, related_name="+", null=False, blank=False)
    balance = models.IntegerField(default=0) # This is the amount left after all withdrawals from the earnings.
    earnings = models.IntegerField(default=0) # This is the total amount earned since the account came into existence.
    lasttransactdate = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "SubscriptionEarnings Table"
        db_table = 'Network_subscriptionearnings'



class WithdrawalActivity(models.Model):
    user = models.ForeignKey(User, related_name="+", null=False, blank=False)
    sessioncode = models.CharField(max_length=150, null=False, blank=False)
    securecode = models.CharField(max_length=8, null=False, blank=False)
    activitytime = models.DateTimeField(auto_now=True)
    securecodestatus = models.BooleanField(default=True)
    wepaycode = models.CharField(max_length=255)
    razorpaycode = models.CharField(max_length=200)

    class Meta:
        verbose_name = "WithdrawalActivity Table"
        db_table = 'Network_withdrawal'


class WePay(models.Model):
    user = models.ForeignKey(User, related_name="+", null=False, blank=False)
    access_token = models.CharField(max_length=200, null=True)
    token_type = models.CharField(max_length=20, null=False, default="bearer")
    access_token_expires = models.BigIntegerField(null=True, default=0)
    wepay_state = models.CharField(max_length=200, null=False, default="not initiated")
    wepay_user_id = models.BigIntegerField(null=True, default=-1)
    wepay_authorized = models.BooleanField(default=False)
    ownerbankaccount = models.ForeignKey(OwnerBankAccount, related_name="+", null=False, blank=True)
    create_datetime = models.DateTimeField(auto_now=True)
    code = models.CharField(max_length=255)
    wepayacctid = models.CharField(max_length=255)

    class Meta:
        verbose_name = "WePay Table"
        db_table = 'Network_wepay'

# NOTE: The following model would not be used anymore as we are doing away with the withdrawal mechanism.
class RazorPayTransaction(models.Model):
    bankacct = models.ForeignKey(OwnerBankAccount, related_name="+", null=False, blank=False)
    source = models.CharField(max_length=50,null=False, blank=False)
    recipient_merchant_id = models.CharField(max_length=50, null=False, blank=False)
    transaction_id = models.CharField(max_length=100, null=False, blank=False) # id field of the razorpay /transfer response
    recipient = models.ForeignKey(User, related_name="+", null=False, blank=False)
    amount = models.FloatField(null=False, blank=False)
    currency = models.CharField(max_length=20, null=False, blank=False, default="INR")
    on_hold = models.BooleanField(default=False)
    tax = models.FloatField(null=False, blank=False, default=0.00)
    fees = models.FloatField(null=False, blank=False, default=0.00)
    trxtimestamp = models.BigIntegerField(null=True, default=0)

    class Meta:
        verbose_name = "RazorPay Transaction Table"
        db_table = 'Network_razorpaytransaction'



class StripeConnectedAccount(models.Model):
    stripeid = models.CharField(max_length=200, blank=False, null=False, default='')
    stripeproductid = models.CharField(max_length=200, blank=False, null=False, default='')
    stripepriceid = models.CharField(max_length=200, blank=False, null=False, default='')
    owner = models.ForeignKey(User, related_name="+", null=False, blank=False)
    group = models.ForeignKey(Group, related_name="+", null=True, blank=True, default='')
    acctstatus = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now=True)
    accessed = models.DateTimeField(default=datetime.datetime.now())

    class Meta:
        verbose_name = "Stripe Connected Accounts Table"
        db_table = 'Network_stripeconnectedaccounts'

"""
Models a RazorPay Customer object and an associated Fund Account.
"""
class RazorPayCustomerAccount(models.Model):
    customerid = models.CharField(max_length=200, blank=False, null=False, default='')
    customercreatedat = models.DateTimeField(blank=False, null=False)
    fundaccountid = models.CharField(max_length=200, blank=False, null=False, default='')
    gstin = models.CharField(max_length=20, blank=False, null=False, default='000000000000000')
    owner = models.ForeignKey(User, related_name="+", null=False, blank=False)
    group = models.ForeignKey(Group, null=True, blank=True, default='')
    acctstatus = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now=True)
    accessed = models.DateTimeField(default=datetime.datetime.now())

    class Meta:
        verbose_name = "RazorPay Customer and associated Fund Account Table"
        db_table = 'Network_razorpaycustomeraccount'


class RazorPayOrdersPayments(models.Model):
    orderid = models.CharField(max_length=200, blank=False, null=False, default='')
    oreceipt = models.CharField(max_length=40, blank=False, null=False)
    ostatus = models.CharField(max_length=20, default="created") # Can have values 'created', 'paid' or 'failed' as in https://razorpay.com/docs/api/orders (RazorPay Order states)
    orderamount = models.IntegerField(default=0) # Should contain the order amount in Indian paise (INR * 100)
    ocurrency = models.CharField(max_length=5, default='INR') # This would always be INR. Storing for the sake of completeness.
    ouser = models.ForeignKey(User, related_name="+", null=False, blank=False)
    ogroup = models.ForeignKey(Group, null=True, blank=True, default='')
    reason = models.CharField(max_length=25, choices=(('entryfee', 'Entry Fee'), ('subscriptionfee', 'Subscription Fee')), default='entryfee')
    sessionid = models.CharField(max_length=150, blank=False, null=False, default='')
    paymentid = models.CharField(max_length=200, blank=False, null=False, default='')
    razorpaysignature = models.CharField(max_length=200, blank=False, null=False, default='')
    ocreated = models.DateTimeField(auto_now=True)
    oupdated = models.DateTimeField(default=datetime.datetime.now())

    class Meta:
        verbose_name = "RazorPay Order and associated Payment details Table"
        db_table = 'Network_razorpayorderspayments'


"""
This model will contain the payouts to be made with the payout related info as a string in the field payoutinfo.
A background process would pick the payouts records based on its status (1 if payout has already been made and 0
if not), and make the payouts. Once a record has been processed, its status would be set to value 1.
"""
class Payouts(models.Model):
    payoutinfo = models.TextField()
    gateway = models.CharField(max_length=20, default='RazorPay')
    status = models.BooleanField(default=False)
    payoutid = models.CharField(max_length=100, default='')
    created = models.DateTimeField(auto_now=True) # This defines when the payout record was created.
    processed = models.DateTimeField(auto_now_add=True)
    gwpayoutstatus = models.CharField(max_length=20, default='') # To store razorpay payout status
    gwstatusdetails = models.TextField() # To store status errors in razorpay payout requests
    gw_utr = models.CharField(max_length=100, default='') # Razorpay payout utr values.

    class Meta:
        verbose_name = "Payouts table - would contain the details of payouts to make"
        db_table = 'Network_payouts'



