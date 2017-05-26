import csv
import os, sys, re, time
import datetime

from django.conf import settings
import skillstest.utils as skillutils
from skillstest import settings as mysettings
from skillstest.Tests.models import Test, UserTest, WouldbeUsers, Challenge, UserResponse
from skillstest.Subscription.models import Plan, UserPlan, Transaction, Coupon, UserCoupon


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



