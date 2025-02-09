from django.db import models
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
from skillstest import settings as mysettings
from skillstest.errors import error_msg
import os, sys, re, time, datetime
import inspect


class TeachSession(models.Model):
    sessionid = models.CharField(max_length=100)
    sessionname = models.CharField(max_length=255)
    sessiondescription = models.TextField(max_length=1000)
    conductor = models.ForeignKey(User, null=False, blank=False, db_column='user_id')
    sessiontopic = models.CharField(max_length=100)
    consumerscount = models.IntegerField(default=0)
    sessionstart = models.DateTimeField(auto_now_add=True)
    sessionend = models.DateTimeField(default=None)
    sessionstatus = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Teaching Session"
        db_table = 'Teach_teachsession'

    def __unicode__(self):
        return "%s - %s"%(self.sessionname, self.conductor.displayname)
        
        
class SessionConsumer(models.Model):
    consumer = models.ForeignKey(User, null=False, blank=False, db_column='user_id')
    teachsess = models.ForeignKey(TeachSession, null=False, blank=False, db_column='sessionid')
    consumersessurl = models.CharField(max_length=255) # This would be sent to the consumer's registered email Id when the conductor sends the invitation to the user to join.
    sessionpasscode = models.CharField(max_length=100) # This is the code that this consumer would need to type in to enter the session.
    blocked = models.BooleanField(default=False)
    blockedtime = models.DateTimeField(default=None)
    connectionstatus = models.BooleanField(default=False) # Once the user enters the passcode and connects, this would be set to True. Once the user/consumer disconnects or the session ends, this would be set to False again.
    connectionstarttime = models.DateTimeField(default=None)
    connectionendtime = models.DateTimeField(default=None)
    
    class Meta:
        verbose_name = "Consumer of a Teaching Session"
        db_table = 'Teach_teachsessionconsumer'

    def __unicode__(self):
        return "%s - %s"%(self.teachsess.sessionname, self.consumer.displayname)


class Institution(models.Model):
    inst_name = models.CharField(max_length=255, null=False, blank=False)
    inst_location = models.TextField()
    inst_univname = models.CharField(max_length=255, null=True, blank=True, default='')
    create_date = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(User, null=False, blank=False, db_column='creator_id')


class Course(models.Model):
    pass


class CourseParticipant(models.Model):
    pass


class CourseMaterial(models.Model):
    pass



