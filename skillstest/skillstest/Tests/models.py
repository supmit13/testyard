from django.db import models
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
from skillstest import settings as mysettings
import os, sys, re, time, datetime


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
    topicshortname = models.CharField(max_length=50)
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
The 'Test' object defines the test. This model stores such information
as the type of test, the max points in it, the minimum points/grades a
test taker needs to achieve in order to pass it, etc.
"""
class Test(models.Model):
    testname = models.CharField(max_length=150)
    subtopic = models.ForeignKey(Subtopic, null=False, blank=False)
    creator = models.ForeignKey(User, blank=False, null=False)
    testtype = models.CharField(max_length=4, choices=((k,v) for k,v in mysettings.TEST_TYPES.iteritems())(), default='COMP')
    createdate = models.DateTimeField(auto_now_add=True)
    maxscore = models.IntegerField(default=0, null=False, blank=False)
    passscore = models.IntegerField(default=0, null=False, blank=False)
    ruleset = models.CharField(max_length=4, choices=()) # ruleset defines the rules for taking the test. See mysettings.RULES_DICT
    duration = models.IntegerField(default=0, null=False, blank=False)
    allowedlanguages = models.CharField(max_length=4, choices=((k,v) for k,v in mysettings.ANSWER_LANG_DICT.iteritems())(), default='enus') # see mysettings.ANSWER_LANG_DICT
    challengecount = models.IntegerField(default=0, null=False, blank=False)
    activationdate = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=True) # Determines if the 'Test' creation is complete.
    # 'User's may create a 'Test' over a period of time, adding questions every now and then.
    quality = models.CharField(max_length=4, choices=((k,v) for k,v in mysettings.SKILL_QUALITY.iteritems())(), default='INT') # Determines the class of users the 'Test' is for.
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
    validtill = models.DateTimeField(default=self.validfrom + self.time.duration)
    status = models.IntegerField(default=1, choices=((0, 'Not taken'), (1, 'Taking'), (2, 'Taken'))) # Determines whether the test has been taken, is being taken or will be taken.
    outcome = models.NullBooleanField(default=None) # Result of the test, if taken. Default is null.
    score = models.FloatField(default=0)
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
    challengetype = models.CharField(max_length=4, choices=((k,v) for k,v in mysettings.TEST_TYPES.iteritems())(), default='COMP')
    # The following 6 fields will be used only if the challengetype is MULT. Will be empty otherwise.
    option1 = models.TextField(blank=True, null=True, default='')
    option2 = models.TextField(blank=True, null=True, default='')
    option3 = models.TextField(blank=True, null=True, default='')
    option4 = models.TextField(blank=True, null=True, default='')
    option5 = models.TextField(blank=True, null=True, default='')
    option6 = models.TextField(blank=True, null=True, default='')

    class Meta:
        verbose_name = "Challenge Table"
        db_table = 'Tests_challenge'

    def __unicode__(self):
        return "%s (available options: '%s', '%s', '%s', '%s', '%s', '%s')"%(self.statement, self.option1, self.option2, self.option3, self.option4, self.option5, self.option6)


"""
This model represents what the user responded with to a 'Challenge'
presented to her/him. Basically, records in this table will represent
the transaction between the user and the system while taking the test.
"""
class UserResponse(models.Model):
    pass


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
"""
class ShareTest(models.Model):
    pass
