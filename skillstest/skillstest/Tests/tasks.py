from django.conf import settings
import skillstest.utils as skillutils
from skillstest import settings as mysettings
from skillstest.Tests.models import Test, UserTest, WouldbeUsers, Challenge

import os, sys, datetime
from django.core.mail import send_mail

"""
This scans all tests and activates the ones whose publish and 
activate dates are in the past. It also sets the 'status' flag
to 1 if the test is complete with all questions set and scores
equalling the 'fullmarks' of the test.
"""
def scan_and_activate():
    logpath = mysettings.LOG_PATH
    logobj = skillutils.Logger(logpath + os.path.sep + "tests_tasks.log")
    # Fetch all tests with activation date equals to or less than current datetime
    currentdatetime = datetime.datetime.now()
    currentdatetimeparts = str(currentdatetime).split(" ")
    currentdate = currentdatetimeparts[0]
    testobjects = Test.objects.filter(activationdate__lt=currentdate).filter(status=0)
    for testobj in testobjects:
        challenges = Challenge.objects.filter(test=testobj)
        fullscore = float(testobj.maxscore)
        totalchallengescore = 0
        for challenge in challenges:
            totalchallengescore += float(challenge.challengescore)
        if totalchallengescore < fullscore:
            logobj.logmessage("Test with name '%s' is incomplete. It contains questions/challenges worth %s out of a predefined total of %s\n"%(testobj.testname, totalchallengescore, fullscore))
            # Shoot an email to the owner of the test and request her/him to take necessary action.
            email = testobj.creator.emailid
            emailsubject = "Your test named '%s' is incomplete and hence it cannot be published and/or activated today."%testobj.testname
            emailmessage = """
            Dear %s,

            Your test titled '%s' is not going to be published or activated today as it failed the test
            for completion. Any test with a total score greater than the cumulative scores of all its
            challenges is considered incomplete and hence neither published nor activated even if its
            designated publication date or activation date occurs.

            To remedy the situation, we request you to either add challenges to your test and place suffi-
            cient weightage on them so that the cumulative scores of all the challenges match the total
            score of the test, or diminish the total score of the test to match the cumulative scores of
            all the challenges in it, or perform a combination of the above actions. Alternatively, you may
            also set the publication and/or activation dates to a time in the future to avoid taking any of
            the above decisions right now.

            If you feel that the test is no longer required, you may also choose to delete it, which will
            automatically stop these emails regarding the test to be sent to you. However, please note that
            once a test is deleted, there is absolutely no way of retrieving it or the challenges in it.

            We look forward to partner with you in your skills testing requirements.

            Best Regards,

            The TestYard Team.
            """%(testobj.creator.displayname, testobj.testname)
            fromaddr = "testyardteam@testyard.com"
            retval = 0
            try:
                retval = send_mail(emailsubject, emailmessage, fromaddr, [email,], False)
                logobj.logmessage("Email for test '%s' sent to '%s'\n"%(testobj.testname, testobj.creator.emailid))
            except:
                logobj.logmessage("%s : %s"%(testobj.testname, sys.exc_info()[1].__str__()))
        else:
            testobj.status = 1 # activated
            logobj.logmessage("Test with name '%s' is activated\n"%(testobj.testname))
            testobj.save()


"""
Just the opposite of the above function.
"""
def scan_and_deactivate():
    pass
