from django.db import models
from django.core.exceptions import ValidationError
from  django.core.validators import validate_email
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
from skillstest.Tests.models import Topic, Subtopic, Evaluator, Test, UserTest, Challenge, UserResponse
from skillstest.Network.models import Group
from skillstest import settings as mysettings
from skillstest.errors import error_msg
import os, sys, re, time, datetime
import inspect


"""
Pricing will be based on 2 main factors:

1. Number of candidates taking the test
2. Number of tests.

The reason behind choosing the first factor as primary one is simple - number of candidates is directly 
proportional to the amount of load on the system. The more the load, higher is the price.

Since a coding test consumes more resources (compiler, environment, etc) than any other form of test (
subjective, algo writing, multiple choice, etc), it would be costlier than the other types of tests. A
map of test types, duration, and their  associated costs is listed in skills_settings.py. It is expected
to be used as a guideline only for fixing up the costs associated with a 'Plan'. The actual cost of a
'Plan' will be stored in the database in the table associated with the following model. The charge 
for conducting the tests will be billed to the conductor and not the candidates, with only one exception:
certification type tests (for MCSD, MCP, CCNA, CNE, BrainBench certifications, etc) along with their
practise tests sessions will be billed to the candidates (since the conductor of the tests conduct them
as a service from which candidates stand to gain financially and intellectually if they pass these tests).
"""
class Plan(models.Model):
    planname = models.CharField(max_length=200, null=False,blank=False)
    tests = models.IntegerField(null=False, blank=False, default=0) # Number of tests included in the plan.
    interviews = models.IntegerField(null=False, blank=False, default=0) # Number of interviews included in the plan.
    plandescription = models.TextField(default='')
    candidates = models.IntegerField(null=False, blank=False, default=0) # Number of candidates to whom each test may be given.
    price = models.DecimalField(max_digits=10, decimal_places=2) # Price per unit. Unit would be based on context, fixed by the 'admin '.
    # The privilege of the user is determined from the UserPrivilege model. Normal users, like test creators, evaluator, assessees, etc
    # will NOT have an entry in the UserPrivilege table. The only entries in the UserPrivilege table will be that of site-admins.
    validfor_unit = models.CharField(max_length=12, choices=(('D', 'Days'),('M', 'Months'),('Y', 'Years')), default='M')
    planvalidfor = models.IntegerField(null=False, blank=False, default=1) # Default duration of a Plan is 1 month.
    status = models.BooleanField(default=True) # status of the availability of a plan
    discountpercent = models.FloatField(null=True, blank=True, default=0.0)
    discountamt = models.FloatField(null=True, blank=True, default=0.0)
    createdate = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Subscription Plan Table"
        db_table = 'Subscription_plan'
    
    def __unicode__(self):
        return "Tests: %s in %s %s, Price: %s\n"%(self.tests, self.planvalidfor.__str__(), self.validfor_unit, self.price.__str__())


class Coupon(models.Model):
    coupon_code = models.CharField(max_length=100, null=False, blank=False, unique=True)
    coupon_description = models.TextField(default='')
    valid_from = models.DateTimeField(auto_now=True)
    valid_till = models.DateTimeField(default=None)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    max_use_count = models.IntegerField(default=0)
    currency_unit = models.CharField(max_length=3, null=False, blank=False, default='USD')
    status = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Coupons Table"
        db_table = 'Subscription_coupon'
    
    def __unicode__(self):
        return "Coupon Code: %s\n"%(self.couponcode)



"""
Information of plans bought by various Users. This will just list out which user chose
which plan and since when. The actual transaction level info is not stored in this table.
For transaction level data, please refer to the model named 'Transactions' (next model).
"""
class UserPlan(models.Model):
    plan = models.ForeignKey(Plan, null=False, blank=False)
    user = models.ForeignKey(User, null=False, blank=False)
    totalcost = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0.00)
    amountpaid = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0.00)
    amountdue = models.DecimalField(max_digits=10, decimal_places=2, null=False, blank=False, default=0.00)
    lastpaydate = models.DateTimeField(auto_now_add=True)
    planstartdate = models.DateTimeField(default=datetime.datetime.now(), null=False, blank=False) # Date on which this plan was started for this user.
    planenddate = models.DateTimeField(default=datetime.datetime.now(), null=True, blank=True) # Date on which this plan ended for this user.
    planstatus = models.BooleanField(default=True) # Whether the plan is valid and in use by the user or not.
    # Status of plans that have already crossed their planenddate are automatically made False.
    subscribedon = models.DateTimeField(auto_now=True) # Creation date of the record. Mostly same as 'planstartdate'
    discountpercentapplied = models.FloatField(null=True, blank=True, default=0.0)
    discountamountapplied = models.FloatField(null=True, blank=True, default=0.0)
    coupon = models.ForeignKey(Coupon, null=True, blank=True)


    class Meta:
        verbose_name = "User Plan Table"
        db_table = 'Subscription_userplan'
    
    def __unicode__(self):
        return "Plan Name: %s of User: %s\n"%(self.plan.planname, self.user.displayname)


"""
Validator to ensure that the user with the displayname actually exists.
"""
def validate_user(username):
    userobj = User.objects.filter(displayname=username)
    if not userobj or userobj.__len__() == 0: # Note: userobj is a queryset object, not a User object
        raise ValidationError("No user named '%s' exists"%username)


"""
Validator to ensure that the sessioncode actually exists and is valid.
"""
def validate_session(sesscode):
    sessobj = Session.objects.filter(sessioncode=sesscode)
    if not sessobj or sessobj.__len__() == 0: # Note: sessobj is a queryset object, not a Session object
        raise ValidationError("No session with code '%s' exists"%sesscode)


"""
Transaction related info of Users (who bought plans and/or tests).
"""
class Transaction(models.Model):
    username = models.CharField(max_length=100, null=False, blank=False, validators=[ validate_user, ])
    user = models.ForeignKey(User, null=False, blank=False)
    orderId = models.CharField(max_length=40, null=False, blank=False)
    plan = models.ForeignKey(Plan, null=True, blank=True) # This will have a value if user registers for a subscription plan.
    group = models.ForeignKey(Group, null=True, blank=True) # This will have a value when a user registers for a paid  group.
    usersession = models.CharField(max_length=100, blank=False, null=False, validators=[ validate_session, ])
    payamount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    transactiondate = models.DateTimeField(auto_now=True)
    comments = models.TextField(default='')
    paymode = models.CharField(max_length=50, null=False, blank=False, default='PAYU')
    invoice_email = models.EmailField(validators=[validate_email, ])
    trans_status = models.BooleanField(default=False)
    clientIp = models.CharField(max_length=20, null=False, blank=True)
    extOrderId = models.CharField(max_length=40, null=True, blank=True)
    txnid_stripe = models.CharField(max_length=200, blank=False)
    paymentid_razorpay = models.CharField(max_length=100, blank=True, default='')

    class Meta:
        verbose_name = "Transactions Table"
        db_table = 'Subscription_transaction'
    
    def __unicode__(self):
        return "Plan Name: %s of User: %s\n"%(self.planname, self.username)


class UserCoupon(models.Model):
    coupon = models.ForeignKey(Coupon, blank=False, null=False)
    user = models.ForeignKey(User, blank=False, null=False)
    usedate = models.DateTimeField(auto_now=True)
    transaction = models.ForeignKey(Transaction, blank=False, null=True)

    class Meta:
        verbose_name = "UserCoupon Table"
        db_table = 'Subscription_usercoupon'





