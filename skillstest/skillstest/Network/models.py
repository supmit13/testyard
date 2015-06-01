from django.db import models
from django.core.exceptions import ValidationError
from  django.core.validators import validate_email
from skillstest.Auth.models import User, Session, Privilege, UserPrivilege
from skillstest.Tests.models import Topic, Subtopic, Evaluator, Test, UserTest, Challenge, UserResponse
from skillstest import settings as mysettings
from skillstest.errors import error_msg
import os, sys, re, time, datetime
import inspect


class Post(models.Model):
    pass


class Network(models.Model):
    owner = models.ForeignKey(User, related_name="+", null=True, blank=True, default='')
    networkname = models.CharField(max_length=200, blank=False, null=False)
    tagline = models.TextField(default="")
    description = models.TextField(default="")
    members = models.ManyToManyField(User)
    memberscount = models.IntegerField(default=0)
    status = models.BooleanField(default=True)
    networktype = models.CharField(max_length=4, choices=((k,v) for k,v in mysettings.NETWORK_TYPES_LIST.iteritems()), default='OPEN')
    posts = models.ManyToManyField(Post)

    class Meta:
        verbose_name = "Network Table"
        db_table = 'Tests_network'

    def __unicode__(self):
        return "%s"%(self.member.firstname + "'s network")

    def add(self, member):
        pass

    def remove(self, member):
        pass



