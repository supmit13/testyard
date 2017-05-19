import csv
import os, sys, re, time
import datetime

from django.conf import settings
import skillstest.utils as skillutils
from skillstest import settings as mysettings
from skillstest.Tests.models import Test, UserTest, WouldbeUsers, Challenge, UserResponse
from skillstest.Subscription.models import Plan, UserPlan, Transaction


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




