from django.db import models
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
from skillstest import settings as mysettings
from skillstest.errors import error_msg
import os, sys, re, time, datetime
import inspect

"""
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
"""

class Institution(models.Model):
    inst_name = models.CharField(max_length=255, null=False, blank=False)
    inst_location = models.TextField()
    inst_univname = models.CharField(max_length=255, null=True, blank=True, default='')
    create_date = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(User, null=False, blank=False, db_column='creator_id')


class Department(models.Model):
    dept_name = models.CharField(max_length=255, null=False, blank=False)
    dept_inst = models.ForeignKey(Institution, null=False, blank=False, db_column='dept_inst_id')
    dept_location = models.CharField(max_length=255, null=True, blank=True)


class Course(models.Model):
    course_name = models.CharField(max_length=255, null=False, blank=False)
    course_inst = models.ForeignKey(Institution, null=False, blank=False, db_column='course_inst_id') # This is for redundancy
    course_dept = models.ForeignKey(Department, null=False, blank=False, db_column='course_dept_id')
    course_credits = models.IntegerField(default=0)
    course_start_date = models.DateTimeField(auto_now_add=True, null=False)
    course_end_date = models.DateTimeField(null=False, blank=False)
    course_sessions_count = models.IntegerField(default=0)
    course_teacher = models.ForeignKey(User, null=False, blank=False, db_column='course_teacher_id')
    course_details = models.TextField()


class CourseParticipant(models.Model):
    course = models.ForeignKey(Course, null=False, blank=False, db_column='course_id')
    participant = models.ForeignKey(User, null=False, blank=False, db_column='participant_id')
    join_date = models.DateTimeField(auto_now_add=True)


class CourseMaterial(models.Model):
    course = models.ForeignKey(Course, null=False, blank=False, db_column='course_id')
    material_name = models.CharField(max_length=255, null=False, blank=False)
    material_file = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, null=False, blank=False, db_column='created_by_id')


class CourseSession(models.Model):
    session_agenda = models.CharField(max_length=255, null=False, blank=False)
    session_course = models.ForeignKey(Course, null=False, blank=False, db_column='session_course_id')
    session_start = models.DateTimeField(null=False)
    session_end = models.DateTimeField(null=True)
    video_record = models.TextField() # This could be an URL or a path
    extra_materials = models.TextField() # This could be a comma separated list of URLs or paths
    participants_count = models.IntegerField(default=1) # Number of participants in the session (apart from the lecturer).
    session_conductor = models.ForeignKey(User, null=False, blank=False, db_column='session_conductor_id') # The lecturer or prof.
    session_location = models.CharField(max_length=255, null=True, blank=True)
    session_status = models.BooleanField(default=True) # True for "active" session, False for "completed/closed" session.
    islivestreamed = models.BooleanField(default=False) # Whether the session is being streamed live on some URL. Default is False.
    livestream_url = models.TextField() # URL of the livestream, if applicable.


class CourseSessionParticipants(models.Model):
    session = models.ForeignKey(CourseSession, null=False, blank=False, db_column='session_id')
    participant = models.ForeignKey(User, null=False, blank=False, db_column='participant_id')








