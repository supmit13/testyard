from django.conf import settings
import skillstest.utils as skillutils
from skillstest import settings as mysettings
from skillstest.Tests.models import Test, UserTest, WouldbeUsers, Challenge, UserResponse

import os, sys, datetime, re
import glob, base64
import simplejson as json
import urllib,urllib2
from BeautifulSoup import BeautifulSoup
import shutil

import celery
from celery import shared_task
from django.core.mail import send_mail


hex_to_ascii = {'%20' : ' ', '%21' : '!', '%22' : '"', '%23' : '#', '%24' : '$', '%25' : '%', '%26' : '&', \
          '%27' : "'", '%28' : '(', '%29' : ')', '%2A' : '*', '%2B' : '+', '%2C' : ',', '%2D' : '-', '%2E' : '.', '%2F' : '/', '%30' : '0',\
	  '%31' : '1', '%32' : '2', '%33' : '3', '%34' : '4', '%35' : '5', '%36' : '6', '%37' : '7', '%38' : '8', '%39' : '9', '%3A' : ':',\
	  '%3B' : ';', '%3C' : '<', '%3D' : '=', '%3E' : '>', '%3F' : '?', '%40' : '@', '%41' : 'A', '%42' : 'B', '%43' : 'C', '%44' : 'D',\
	  '%45' : 'E', '%46' : 'F', '%47' : 'G', '%48' : 'H', '%49' : 'I', '%4A' :  'J', '%4B' : 'K', '%4C' : 'L', '%4D' : 'M', '%4E' : 'N',\
	  '%4F' : 'O', '%50' : 'P', '%51' : 'Q', '%52' : 'R', '%53' : 'S', '%54' : 'T', '%55' : 'U', '%56' : 'V', '%57' : 'W', '%58' : 'X',\
	  '%59' : 'Y', '%5A' : 'Z', '%5B' : '[', '%5C' : '\\', '%5D' : ']', '%5E' : '^', '%5F' : '_', '%60' : '`', '%61' : 'a', '%62' : 'b',\
	  '%63' : 'c', '%64' : 'd', '%65' : 'e', '%66' : 'f', '%67' : 'g', '%68' : 'h', '%69' : 'i', '%6A' : 'j', '%6B' : 'k', '%6C' : 'l',\
	  '%6D' : 'm', '%6E' : 'n', '%6F' : 'o', '%70' : 'p', '%71' : 'q', '%72' : 'r', '%73' : 's', '%74' : 't', '%75' : 'u', '%76' : 'v',\
	  '%77' : 'w', '%78' : 'x', '%79' : 'y', '%7A' : 'z', '%7B' : '{', '%7C' : '|' , '%7D' : '}', '%7E' : '~' }


utf8_to_ascii = {'%E2%80%90' : '-', '%E2%80%97' : '_', '%E2%80%9C' : '"', '%E2%80%9D' : '"', '%E2%80%98' : "'", '%E2%80%99' : "'"}
# More should be added later. Please note that we have not put the utf-8 characters, but we have replaced them using similar ascii
# characters. This is because we intend to handle ASCII questionaires as of now. Later when we start supporting other languages,
# we will replace them with real utf-8 characters and add more of them here.

"""
This scans all tests and activates the ones whose publish and 
activate dates are in the past. It also sets the 'status' flag
to 1 if the test is complete with all questions set and scores
equaling the specified 'total marks' of the test.
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


"""
Reads the dumped answer scripts (in json) from 
the mysettings.ANSWER_SCRIPT_DUMP_PATH and populates
the userresponse table with the data from the scripts.
Updates the usertest and the wouldbeuser tables too.
"""
def process_answer_scripts():
    targetreaddir = mysettings.MEDIA_ROOT + os.path.sep + mysettings.ANSWER_SCRIPT_DUMP_PATH
    targetwritedir = mysettings.MEDIA_ROOT + os.path.sep + mysettings.ANSWER_SCRIPT_DUMP_PATH + os.path.sep + mysettings.PROCESSED_SCRIPT_DUMP
    jsonfiles = glob.glob(targetreaddir + os.path.sep + "*_*" + os.path.sep + "*.json")
    for jsonfile in jsonfiles:
        print jsonfile
        fp = open(jsonfile, "rb")
        jsonstrdata = fp.read()
        fp.close()
        jsondata = json.loads(jsonstrdata)
        starttime, endtime, tabid, tabref, useremail, testid, testpagesenc, clientIP, useragent = "", "", "", "", "", "", "", "", ""
        for dk in jsondata.keys():
            if dk == 'starttime':
                starttime = jsondata[dk]
            elif dk == 'endtime':
                endtime = jsondata[dk]
            elif dk == 'useremail':
                useremail = jsondata[dk]
            elif dk == 'tabid':
                tabid = jsondata[dk]
            elif dk == 'tabref':
                tabref = jsondata[dk]
            elif dk == 'testid':
                testid = jsondata[dk]
            elif dk == 'clientIP':
                clientIP = jsondata[dk]
            elif dk == 'useragent':
                useragent = jsondata[dk]
            elif dk == 'testpages':
                testpagesenc = jsondata[dk]
            else:
                pass
        missing_padding = 4 - len(testpagesenc) % 4
        padding = "=" * missing_padding
        testpagesstr = (base64.b64decode(testpagesenc + padding)).decode('iso-8859-1') 
        for hexkey in skillutils.hextoascii.keys():
            testpagesstr = testpagesstr.replace(hexkey, skillutils.hextoascii[hexkey])
        testpagesstr = re.sub("value='([^']*)<([^']*)'", r"value='\1&lt;\2'", testpagesstr, flags=re.DOTALL)
        testpagesstr = re.sub("value='([^']*)>([^']*)'", r"value='\1&gt;\2'", testpagesstr, flags=re.DOTALL)
        #print testpagesstr
        testpages = json.loads(testpagesstr, strict=False)
        testendmessage = testpages.pop() # The last entity contains the test end message
        for challengeresp in testpages:
            testobj = Test.objects.get(id=testid)
            # First, create an UserResponse object
            userrespobj = UserResponse()
            userrespobj.test = testobj
            userrespobj.tabref = tabref
            userrespobj.tabid = int(tabid)
            userrespobj.responsedatetime = starttime
            userrespobj.emailaddr = useremail
            resp = challengeresp[0]
            timereqd = challengeresp[1]
            challengestatement = challengeresp[2].decode("utf-8")
            challengestatement = challengestatement.replace("%E2%80%9C", utf8_to_ascii["%E2%80%9C"])
            challengestatement = challengestatement.replace("%E2%80%9D", utf8_to_ascii["%E2%80%9D"])
            challengestatement = challengestatement.replace("%25", "%")
            try:
                challengeobj = Challenge.objects.filter(test=testobj).filter(statement=challengestatement)[0]
            except:
                for k in hex_to_ascii.keys():
                    challengestatement = challengestatement.replace(k, hex_to_ascii[k])
                challengeobj = Challenge.objects.filter(test=testobj).filter(statement=challengestatement)[0]
                if not challengeobj:
                    print "Could not find the challenge '%s'"%challengestatement
                    continue 
            userrespobj.challenge = challengeobj
            inputdatatag, inputdata = None, ""
            # Now parse the resp variable to find the user's response
            soup = BeautifulSoup(resp)
            #print resp
            challengetypetag = soup.find('input', {'name' : 'challengetype'})
            challengetype = challengetypetag['value']
            if challengetype == 'SUBJ' or challengetype == 'ALGO' or challengetype == 'CODN':
                inputdatatag = soup.find("textarea")
                inputdata = inputdatatag.renderContents()
                if inputdata == "" and inputdatatag.has_key("value"):
                    inputdata = inputdatatag["value"]
            elif challengetype == 'FILB':
                inputdatatag = soup.find("input", {'type' : 'text'})
                inputdata = inputdatatag['value']
            elif challengetype == 'MULT':
                inputdatatag = soup.findAll("input", {'type' : 'checkbox', 'checked' : True})
                if inputdatatag.__len__() == 0:
                    inputdatatag = soup.findAll("input", {'type' : 'radio', 'checked' : True})
                for j in range(0, inputdatatag.__len__()):
                    inputdata = inputdata + "#||#" + inputdatatag[j]['value']
                    #print inputdatatag[j]['value']
            else:
                print "Unhandled challenge type"
                continue
            inputdata = re.sub(re.compile("^\s*#\|\|#"), "", inputdata)
            #print "#### " + inputdata
            userrespobj.answer = inputdata
            userrespobj.attachments = None
            userrespobj.save()
        # Now edit the usertest or wouldbeusers table
        if tabref == 'usertest':
            utqset = UserTest.objects.filter(id=tabid)
        else:
            utqset = WouldbeUsers.objects.filter(id=tabid)
        if utqset.__len__() == 0:
            print "Could not find the usertest record related to this session"
            continue
        utobj = utqset[0]
        utobj.status = 2 # Test has been taken
        # Need to store ipaddress and client software too.
        utobj.ipaddress = clientIP
        utobj.clientsware = useragent
        utobj.starttime = starttime
        utobj.endtime = endtime
        # Save the modified UserTest/WouldbeUsers object.
        utobj.save()
        # Now, move the json dump files to another location...
        jsonfilecomponents = jsonfile.split(os.path.sep)
        jsonfilecomponents.pop()
        jsondir = os.path.sep.join(jsonfilecomponents)
        shutil.move(jsondir, targetwritedir)
        #print jsondir
    # Thats it, we are done. 
    print "Added challenge responses into UserResponse and updated UserTest/WouldbeUsers successfully. Exiting...\n"
        

"""
This is a celery task.
Set up as per: https://realpython.com/asynchronous-tasks-with-django-and-celery/
"""
@celery.task(name="skillstest.Tests.tasks.send_emails")
def send_emails(subject, messagebody, fromaddr, toaddress, b=False):
    retval = send_mail(subject, message, fromaddr, [toaddress,], b)
    return retval

# Run celery command inside testyard/skillstest: python -m skillstest.celery_tasks -A skillstest worker

