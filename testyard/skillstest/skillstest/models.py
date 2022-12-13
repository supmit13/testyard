from django.db import models
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
from skillstest import settings as mysettings
from skillstest.errors import error_msg
import os, sys, re, time, datetime
import inspect


class Careers(models.Model):
    position_longname = models.CharField(max_length=200)
    position_shortname = models.CharField(max_length=50)
    position_code = models.CharField(max_length=10)
    position_description = models.TextField(null=True, blank=True, default="")
    openingdate = models.DateTimeField(auto_now=True)
    closingdate = models.DateTimeField(default=None)
    status = models.BooleanField(default=True) # Once the opening expires (may be because it is fulfilled or may be because the need is gone), the status changes to False.
    maxsalaryoffered = models.IntegerField()
    maxsalarytimeunit = models.CharField(max_length=20, default='per annum')
    urgencyindays = models.IntegerField(default=30) # This is the notice period allowed for the candidates.
    position_type = models.CharField(max_length=100, default='permanent') # Whether is the position is contractual or permanent.
    experiencedesired = models.IntegerField() # How much experience does the candidate need to have in order to be able to apply.
    skillset = models.TextField(null=True, blank=True, default="")
    position_location = models.CharField(max_length=200, default='New Delhi')
    department = models.CharField(max_length=200) # Whether it is a developer position or QA or admin...
    position_budget = models.IntegerField() # This includes the amount of money that may be spent in fulfilling the position.
    contactperson = models.CharField(max_length=255) # The name of the person who submitted the requirement for this position.
    contactemail = models.CharField(max_length=255)
    submissiondatetime = models.DateTimeField(auto_now=True) # Date and Time at which the position has been submitted.
    conditions = models.TextField(null=True, blank=True, default="") # If there is any condition imposed on this opening.

    class Meta:
        verbose_name = "Careers Table"
        db_table = 'careers'

    def __unicode__(self):
        return "Position: %s "%(self.position_shortname)



