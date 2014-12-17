from django.db import models

def profpicpath(instance, filename):
    return '/'.join([instance.user.displayname, 'images/profile', filename])


# Create your models here.
class User(models.Model):
    firstname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=20)
    lastname = models.CharField(max_length=100)
    displayname = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    emailid = models.EmailField(unique=True)
    active = models.BooleanField(default=False)
    istest = models.BooleanField(default=False)
    joindate = models.DateTimeField(auto_now_add=True) # set the field to now when the object is first created
    sex = models.CharField(max_length=3, choices=(('M', 'Male'),('F', 'Female'), ('U', 'Undisclosed')), default='U')
    # usertype defines the type of user: CORP users are corporates that conduct tests for recruitment or internal performance evaluation,
    # CONS are consultants that act as a middleman between corporates and candidates seeking opportunities, ACAD users conduct tests
    # for academic purposes, CERT users are those who conduct tests to certify a candidate's knowledge on a specific subject, and finally
    # OTHR users are the ones who do not fall in any of the above 4 categories.
    usertype = models.CharField(max_length=4, choices=(('CORP', 'Corporate'), ('CONS', 'Consultant'), ('ACAD', 'Academic'), ('CERT', 'Certification')))
    mobileno = models.CharField(max_length=12, blank=True)
    userpic = models.ImageField(max_length=100, upload_to=profpicpath)
    #skinpic = models.ImageField(max_length=100, upload_to=profpicpath)

    def __unicode__(self):
        return "%s %s %s (%s)"%(self.firstname, self.middlename, self.lastname, self.displayname)


class Session(models.Model):
    sessioncode = models.CharField(max_length=50, unique=True)
    status = models.BooleanField(default=True) # Will be 'True' as soon as the user logs in, and will be 'False' when user logs out.
    # The 'status' will automatically be set to 'False' after a predefined period. So users will need to login again after that period.
    # The predefined value will be set in the settings file skills_settings.py. (skills_settings.SESSION_EXPIRY_LIMIT)
    userid = models.ForeignKey(User)
    starttime = models.DateTimeField(auto_now_add=True) # Should be automatically set when the object is created.
    endtime = models.DateTimeField(default=None)
    sourceip = models.GenericIPAddressField(protocol='both')
    istest = models.BooleanField(default=False) # Set it to True during testing the app.
    useragent = models.CharField(max_length=255, default="") # Signature of the user-agent to guess the device used by the user.
    # This info may later be used for analytics.
    
    def __unicode__(self):
        return self.sessioncode



class Privilege(models.Model):
    privname = models.CharField(max_length=50, unique=True)
    privdesc = models.TextField(default="")
    createdate = models.DateTimeField(auto_now_add=True) # Date and time at which this privilege was created.

    def __unicode__(self):
        return "%s - %s"%(self.privname, self.privdesc)


class UserPrivilege(models.Model):
    userid = models.ForeignKey(User)
    privilegeid = models.ForeignKey(Privilege)
    lastmod = models.DateTimeField(auto_now=True) # Date and time at which this privilege was last modified.
    status = models.BooleanField(default=True) # This will be used in a case where the user has a privilege but
    # is not allowed to use it for a certain span of time. For example, a user may be allowed to conduct a test
    # only once in a month (a little far-fetched, but it might be necessary later).

    def __unicode__(self):
        return "user id: %s === privilege id: %s"%(self.userid, self.privilegeid)
    

