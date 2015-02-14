from django.db import models
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
from skillstest import settings as mysettings
from skillstest.errors import error_msg
import os, sys, re, time, datetime
import inspect


"""
'Topic' is basically category or domain. Every 'Test' is classified
as a specific 'Topic'. A 'Topic' is further subdivided into one or
more 'Subtopic'. So 'Test' objects actually belong to 'Subtopic's
rather than 'Topic's. The set of available 'Topic' and 'Subtopic's is
predefined.
objects
"""
class Topic(models.Model):
    topicname = models.CharField(max_length=150)
    user = models.ForeignKey(User, null=False)
    createdate = models.DateField(auto_now=True)
    isactive = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Topics Table"
        db_table = 'Tests_topic'

    def __unicode__(self):
        return "%s"%(self.topicname)


class Subtopic(models.Model):
    subtopicname = models.CharField(max_length=150)
    subtopicshortname = models.CharField(max_length=50)
    topic = models.ForeignKey(Topic, blank=False, null=False)
    createdate = models.DateField(auto_now=True)
    isactive = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Subtopics Table"
        db_table = 'Tests_subtopic'

    def __unicode__(self):
        return "%s (child of %s)"%(self.subtopicname, self.topic.topicname)


"""
Implement Grouping of Users so that Test objects may be evaluated by more than one User.
Note: The concept of Evaluator is different from sharing a test. Evaluator have access
to the answer scripts of candidates in addition to the access to the test itself. They
have the right to evaluate the test associated with them. Sharing, on the other hand only
provides the user with the right to access the challenges and the Test object (including
the rules of the test). They have no access whatsoever to the answer scripts of Users who
took the test. Also note that the creator of the Test is by default an evaluator too. This
may be overridden by setting creatorisevaluator field in Test class to False.
"""
class Evaluator(models.Model):
    evalgroupname = models.CharField(max_length=150, null=False, blank=False)
    # A group can have a maximum of 10 members (including creator of Test (if creator is Evaluators too)
    groupmember1 = models.ForeignKey(User, related_name="+", null=True, blank=True, default='')
    groupmember2 = models.ForeignKey(User, related_name="+", null=True, blank=True, default='')
    groupmember3 = models.ForeignKey(User, related_name="+", null=True, blank=True, default='')
    groupmember4 = models.ForeignKey(User, related_name="+", null=True, blank=True, default='')
    groupmember5 = models.ForeignKey(User, related_name="+", null=True, blank=True, default='')
    groupmember6 = models.ForeignKey(User, related_name="+", null=True, blank=True, default='')
    groupmember7 = models.ForeignKey(User, related_name="+", null=True, blank=True, default='')
    groupmember8 = models.ForeignKey(User, related_name="+", null=True, blank=True, default='')
    groupmember9 = models.ForeignKey(User, related_name="+", null=True, blank=True, default='')
    groupmember10 = models.ForeignKey(User, related_name="+", null=True, blank=True, default='')
    creationdate = models.DateTimeField(auto_now=True)


    class Meta:
        verbose_name = "Evaluator Table"
        db_table = 'Tests_evaluator'

    def __unicode__(self):
        return "%s"%(self.evalgroupname)


"""
The 'Test' object defines the test. This model stores such information
as the type of test, the max points in it, the minimum points/grades a
test taker needs to achieve in order to pass it, etc.
"""
class Test(models.Model):
    testname = models.CharField(max_length=150)
    topic = models.ForeignKey(Topic, blank=True, default='') # If topic is custom topic created by user, then this will point to the 'Tests_topic' record.
    topicname = models.CharField(max_length=200, blank=True) # If topic is one of the built-in topics, then this will hold the name of it. In that case, topic will be ''.
    subtopic = models.ForeignKey(Subtopic, null=True, blank=True)
    creator = models.ForeignKey(User, blank=False, null=False) # In case the 'creator' is some board or association, one of its members
    # will need to come forward to be accountable for the  test.
    creatorisevaluator = models.BooleanField(default=True)
    evaluator = models.ForeignKey(Evaluator, blank=True, null=True) # This is the evaluator group name.
    testtype = models.CharField(max_length=4, choices=((k,v) for k,v in mysettings.TEST_TYPES.iteritems()), default='COMP')
    createdate = models.DateTimeField(auto_now_add=True)
    maxscore = models.IntegerField(default=0, null=False, blank=False)
    passscore = models.IntegerField(null=True, blank=False)
    ruleset = models.CharField(max_length=200, blank=True, default='') # ruleset defines the rules for taking the test. See mysettings.RULES_DICT
    duration = models.IntegerField(default=0, null=False, blank=False)
    allowedlanguages = models.CharField(max_length=200, default='enus') # see mysettings.ANSWER_LANG_DICT. If more than one language is allowed, then the language keys should be separated from each other by '#||#'
    challengecount = models.IntegerField(default=0, null=False, blank=False)
    activationdate = models.DateTimeField(auto_now=True)
    publishdate = models.DateTimeField(null=False, blank=True)
    status = models.BooleanField(default=True) # Determines if the 'Test' is being edited (or created).
    # 'User's may create a 'Test' over a period of time, adding questions every now and then.
    allowmultiattempts = models.BooleanField(default=False)
    maxattemptscount = models.IntegerField(default=1, blank=False) # If allowmultiattempts is False, then maxattemptscount = 1
    attemptsinterval = models.IntegerField(default=None, null=True, blank=False);
    randomsequencing = models.BooleanField(default=True, null=False, blank=False)
    multimediareqd = models.BooleanField(default=False, null=False, blank=False)
    testlinkid = models.CharField(max_length=200, null=False, blank=False)
    progenv = models.CharField(max_length=100, null=True, default=None)
    scope = models.CharField(max_length=50, null=False, default='public')
    quality = models.CharField(max_length=4, choices=((k,v) for k,v in mysettings.SKILL_QUALITY.iteritems()), default='INT') # Determines the class of users the 'Test' is for.
    # Proficient/Beginner/Intermediate etc. Refer to mysettings.SKILL_QUALITY

    class Meta:
        verbose_name = "Tests Table"
        db_table = 'Tests_test'

    def __unicode__(self):
        return "Test: %s"%(self.testname)


"""
Identifies the set of 'User's who have been invited to take a 'Test'.
Basically, this will contain the Ids of the 'User's and the corresponding
URL to access the 'Test' by the 'User'. These URLs will be unique and
will point to the start of  the 'Test' for a particular 'User'.
Note: There can be cases where a user doesn't exist in the system yet but a
hyperlink to a test has been generated and sent to a email address. When
the would-be-user accesses the test URL, she/he is asked to register.
Once the user registers, the system will store a reference to the User
object and the record in 'UserTest' will be updated. Prior to that, the
system will store the test link by associating it with the email address
to which the link was sent.
"""
class UserTest(models.Model):
    user = models.ForeignKey(User, blank=True, null=True) # May be null
    emailaddr = models.EmailField(null=False, blank=False) # Email address to which the link to the 'Test' was sent.
    testurl = models.URLField(null=False, blank=False, help_text='URL to access the test by the user', primary_key=True)
    test = models.ForeignKey(Test, blank=False, null=False)
    validfrom = models.DateTimeField(null=False, blank=False, default=datetime.datetime.now())
    #validtill = models.DateTimeField(default=validfrom + datetime.timedelta(hours=Test.objects.get('id'=Test().id).duration))
    #validtill = models.DateTimeField(default=datetime.datetime.time(validfrom) + datetime.timedelta(hours=3))
    # Need to find a method to set validtill depending on 'validfrom' value... For now I am leaving them the same.
    validtill = models.DateTimeField(null=False, blank=False, default=datetime.datetime.now())
    status = models.IntegerField(default=1, choices=((0, 'Not taken'), (1, 'Taking'), (2, 'Taken'))) # Determines whether the test has been taken, is being taken or will be taken.
    outcome = models.NullBooleanField(default=None) # Result of the test, if taken. Default is null.
    score = models.FloatField(default=0) # Score of the user.
    starttime = models.DateTimeField(default=None) # Instant at which the user started taking the test. This might be the same as 'validfrom' value.
    endtime = models.DateTimeField(default=None) # Instant at which the user completed the test. This might be same as 'validtill' value.
    ipaddress = models.GenericIPAddressField(default='') # IP address from which the user logged in to take the test.
    clientsware = models.CharField(max_length=150, default='') # User-agent (browser signature) of the user.
    sessid = models.CharField(max_length=50, default='')


    class Meta:
        verbose_name = "UserTest Table"
        db_table = 'Tests_usertest'

    def __unicode__(self):
        return "Test: %s (for '%s')"%(self.testurl, self.emailaddr)


"""
A 'Challenge' describes a question that a test taker needs to answer.
'Challenge's always belong to one or more 'Test's.
"""
class Challenge(models.Model):
    test = models.ForeignKey(Test, blank=False, null=False)
    statement = models.TextField(blank=False, null=False) # The statement or question
    # The following field will be useful in case of 'composite' tests.
    challengetype = models.CharField(max_length=4, choices=((k,v) for k,v in mysettings.TEST_TYPES.iteritems()), default='COMP')
    maxresponsesizeallowable = models.IntegerField(default=-1, null=True, blank=True) # The default value of -1 means no limit.
    # The following 6 fields will be used only if the challengetype is MULT. Will be empty otherwise.
    option1 = models.TextField(blank=True, null=True, default='')
    option2 = models.TextField(blank=True, null=True, default='')
    option3 = models.TextField(blank=True, null=True, default='')
    option4 = models.TextField(blank=True, null=True, default='')
    option5 = models.TextField(blank=True, null=True, default='')
    option6 = models.TextField(blank=True, null=True, default='')
    option7 = models.TextField(blank=True, null=True, default='')
    option8 = models.TextField(blank=True, null=True, default='')
    challengescore = models.FloatField(default=0) # Score or points of the particular Challenge.
    negativescore = models.FloatField(default=0) # 0 means no negative marks if the User's response is wrong.
    # Otherwise, any positive floating point value specifies the negative score if the user's response is wrong.
    mustrespond = models.BooleanField(default=False) # Specifies if the 'User' must respond to  the challenge.
    # If this is True and the User doesn't  respond to the Challenge, it is considered as wrong response, and
    # hence open to negative marking (if negative marking is allowed for that Challenge).
    responsekey = models.TextField(blank=False, null=True, default=None) # The correct answer statement. (Note: This is the statement, not the index associated with it).
    mediafile = models.CharField(max_length=100, null=True, blank=True, help_text='File name of the image/audio/other multimedia file associated with the challenge')
    additionalurl = models.URLField(null=True, blank=True, help_text='URL of any other material associated with the challenge')
    timeframe = models.IntegerField(default=-1, null=True, blank=True) # A value of -1 (or any other negative integer) denotes no limit.
    # Most often, a Test will have a duration specified but a Challenge in it won't have any limit. But there can be some cases where
    # the assessor wants to limit the timeframe for a specific Challenge (question). This field will be used in such cases.
    #dependency = models.ForeignKey(Challenge, null=True, default=None) # Dependency to any other Challenge object.
    subtopic = models.ForeignKey(Subtopic, null=True, blank=False) # Specifies the subtopic to which this Challenge belongs.
    challengequality = models.CharField(max_length=3, choices=((k,v) for k,v in mysettings.SKILL_QUALITY.iteritems()))
    testlinkid = models.CharField(max_length=200, null=False, blank=False)

    class Meta:
        verbose_name = "Challenge Table"
        db_table = 'Tests_challenge'

    def __unicode__(self):
        return "%s (available options: '%s', '%s', '%s', '%s', '%s', '%s')"%(self.statement, self.option1, self.option2, self.option3, self.option4, self.option5, self.option6)



"""
This model represents what the user responded with to a 'Challenge'
presented to her/him. Basically, records in this table will represent
the transaction between the user and the system while taking the test.
Evaluator will evaluate these responses and update this object
"""
class UserResponse(models.Model):
    test = models.ForeignKey(Test, blank=False, null=False)
    challenge = models.ForeignKey(Challenge, blank=False, null=False)
    user = models.ForeignKey(User, blank=False, null=False)
    answer = models.TextField(blank=True, null=True) # This is the response that the User made.
    responsedatetime = models.DateTimeField(blank=True, null=True, default=None) # Instant at which the User submits the response.
    attachments = models.FileField(upload_to="DUMMY", blank=True, null=True, default=None) # The path will be in the format MEDIA_ROOT/<useremail>/<Test Id>/<Challenge Id>/filename.
    # This path will be stored in the DB. There needs to be a mechanism to upload a file for each Challenges. The mechanism to store the attachment in the
    # specified path will be imposed in code.
    evaluation = models.FloatField(null=True, blank=True, default=-1) # How much the candidate scored in this Challenge (of which this UserResponse is).
    # -1 means that the response hasn't been evaluated yet.
    evaluator_remarks = models.TextField(null=True, blank=True, default="") # It may contain the remarks of more than one User of the Evaluator Group.
    # In such cases, the comments/remarks will be separated by '|'. Not imposed by DB, but rather by code.
    evaluated_by = models.ForeignKey(User, related_name="+", blank=False, null=False) # This User will be one of the Evaluator group for this test.
    candidate_comment = models.TextField(null=True, blank=True, default=None)
    response_quality = models.CharField(max_length=3, choices=((k,v) for k,v in mysettings.SKILL_QUALITY.iteritems()))
    # This will be entered by one of the evaluator.


    class Meta:
        verbose_name = "UserResponse Table"
        db_table = 'Tests_userresponse'

        
    def __unicode__(self):
        return "%s"%(self.answer)


    """
    Returns None on success, error message on failure.
    """
    def create_attachment_path(self, filename):
        media_root = mysettings.MEDIA_ROOT
        attachmentpath = media_root + os.path.sep + self.user.emailid + os.path.sep + self.test.id + os.path.sep + self.challenge.id + os.path.sep + filename
        try:
            if not os.path.exists(os.path.dirname(attachmentpath)):
                os.makedirs(os.path.dirname(attachmentpath))
            self.attachments = attachmentpath
            return None
        except:
            if mysettings.DEBUG:
                print "Could not create attachment path %s: Error: %s\n"%(attachmentpath, sys.exc_info()[1].__str__())
            self.attachments = None
            message = error_msg('1021')
            message = "%s: %s Error: %s\n"%(inspect.stack()[0][3], message, sys.exc_info()[1].__str__())
            return message


"""
The creator of a test may choose to share a 'Test' with another 'User'.
This table keeps info regarding such relationships. Note: sharing a 'Test'
will enable the second 'User' to view the 'Challenge's and the available
options for responding to it only. Responses of the  test takers will not
be accessible to the second user. Such information is accessible only
by the creator of the 'Test'. But the second user may copy the same 'Test'
and become the creator of the copied version of the 'Test'. 'User's
taking this 'Test' will be judged by the second 'User' and in that case
the primary 'User' will not be able to access the responses of the 'User's
taking the copied 'Test'.

class ShareTest(models.Model):
    testcreator = models.ForeignKey(User, related_name="+", null=False, blank=False) # A Test object is bound to have a creator.
    sharedwith = models.ForeignKey(User, related_name="+", null=False, blank=False) # User object with whom the Test is being shared.
    sharedatetime = models.DateTimeField(auto_now=True)
    test = models.ForeignKey(Test, null=False, blank=False) # The Test object that is being shared.

    class Meta:
        verbose_name = "ShareTest Table"
        db_table = 'Tests_sharetest'

    def __unicode__(self):
        return "%s"%(self.test.testname)

"""



