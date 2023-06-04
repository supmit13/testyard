from django.db import models
from  django.core.validators import validate_email

def profpicpath(instance, filename):
    return '/'.join([instance.user.displayname, 'images/profile', filename])


# Create your models here.
class User(models.Model):
    firstname = models.CharField(max_length=100)
    middlename = models.CharField(max_length=20)
    lastname = models.CharField(max_length=100)
    displayname = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    emailid = models.EmailField(unique=True, validators=[validate_email, ])
    active = models.BooleanField(default=False, help_text='Specifies whether the user is an active member or not.')
    istest = models.BooleanField(default=False, help_text='Specifies whether the user object is a result of some testing or not.')
    joindate = models.DateTimeField(auto_now_add=True) # set the field to now when the object is first created
    sex = models.CharField(max_length=3, choices=(('M', 'Male'),('F', 'Female'), ('U', 'Undisclosed')), default='U')
    # usertype defines the type of user: CORP users are corporates that conduct tests for recruitment or internal performance evaluation,
    # CONS are consultants that act as a middleman between corporates and candidates seeking opportunities, ACAD users conduct tests
    # for academic purposes, CERT users are those who conduct tests to certify a candidate's knowledge on a specific subject, and finally
    # OTHR users are the ones who do not fall in any of the above 4 categories.
    usertype = models.CharField(max_length=4, choices=(('CORP', 'Corporate'), ('CONS', 'Consultant'), ('ACAD', 'Academic'), ('CERT', 'Certification')))
    mobileno = models.CharField(max_length=12, blank=True)
    userpic = models.ImageField(max_length=100, upload_to=profpicpath, help_text='Path to user\'s profile image.')
    newuser = models.BooleanField(default=False, help_text='False if user hasn\'t validated her/his email address')
    #skinpic = models.ImageField(max_length=100, upload_to=profpicpath)


    class Meta:
        verbose_name = "User Information Table"
        db_table = 'Auth_user'

    def __unicode__(self):
        return "%s %s %s (%s)"%(self.firstname, self.middlename, self.lastname, self.displayname)



class Session(models.Model):
    sessioncode = models.CharField(max_length=50, unique=True)
    status = models.BooleanField(default=True) # Will be 'True' as soon as the user logs in, and will be 'False' when user logs out.
    # The 'status' will automatically be set to 'False' after a predefined period. So users will need to login again after that period.
    # The predefined value will be set in the settings file skills_settings.py. (skills_settings.SESSION_EXPIRY_LIMIT)
    user = models.ForeignKey(User, null=False, blank=False, db_column='userid_id')
    starttime = models.DateTimeField(auto_now_add=True) # Should be automatically set when the object is created.
    endtime = models.DateTimeField(default=None)
    sourceip = models.GenericIPAddressField(protocol='both', help_text="IP of the client's/user's host")
    istest = models.BooleanField(default=False) # Set it to True during testing the app.
    useragent = models.CharField(max_length=255, default="", help_text="Signature of the browser of the client/user") # Signature of the user-agent to guess the device used by the user.
    # This info may later be used for analytics.


    class Meta:
        verbose_name = "Session Information Table"
        db_table = 'Auth_session'
    
    def __unicode__(self):
        return self.sessioncode

    def isauthenticated(self):
        if self.status and self.user.active:
            return self.user
        else:
            return None

    def save(self, **kwargs):
        super(Session, self).save(kwargs)


class Privilege(models.Model):
    privname = models.CharField(max_length=50, unique=True)
    privdesc = models.TextField(default="")
    createdate = models.DateTimeField(auto_now_add=True) # Date and time at which this privilege was created.


    class Meta:
        verbose_name = "Authorization Information"
        verbose_name_plural = "Privileges Information"
        db_table = 'Auth_privilege'

    def __unicode__(self):
        return "%s - %s"%(self.privname, self.privdesc)


class UserPrivilege(models.Model):
    user = models.ForeignKey(User, db_column='userid_id')
    privilege = models.ForeignKey(Privilege, null=False, blank=False, db_column='privilegeid_id')
    lastmod = models.DateTimeField(auto_now=True) # Date and time at which this privilege was last modified.
    status = models.BooleanField(default=True) # This will be used in a case where the user has a privilege but
    # is not allowed to use it for a certain span of time. For example, a user may be allowed to conduct a test
    # only once in a month (a little far-fetched, but it might be necessary later).


    class Meta:
        verbose_name = "User Privileges Information"
        db_table = 'Auth_userprivilege'

    def __unicode__(self):
        return "user id: %s === privilege id: %s"%(self.user.id, self.privilege.id)


class EmailValidationKey(models.Model):
    email = models.EmailField(unique=True, validators=[validate_email, ])
    vkey = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Email Validation Keys"
        verbose_name_plural = "Email Validation Keys"
        db_table = 'Auth_emailvalidationkey'

    def __unicode__(self):
        return "%s - %s"%(self.email, self.vkey)


class OptionalUserInfo(models.Model):
    user = models.ForeignKey(User, null=False, blank=False, db_column='user_id')
    houseno_and_street_address = models.TextField(max_length=250)
    city = models.CharField(max_length=100)
    pin_or_zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    profession = models.CharField(max_length=50, choices=(('student', 'Student'), ('teacher', 'Teacher'), ('professional', 'Professional'), ('administrator', 'Administrator'), ('govtservice', 'Government Service'), ('business', 'Business'), ('other', 'Other')), default='student')
    age = models.IntegerField()
    reasonforuse = models.TextField(max_length=500) # Reason for using this web application
    selfdescription = models.TextField(max_length=500)
    highestqualification = models.CharField(max_length=50, choices=(('graduate', 'Graduate'), ('diploma', 'Diploma'), ('masters', 'Masters'), ('doctorate', 'Doctorate'), ('postdoctorate', 'PostDoctorate'), ('none', 'None')), default='graduate')
    fieldofstudy = models.CharField(max_length=100)
    workexperience = models.IntegerField()
    presentemployer_or_institution = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Optional User Information"
        db_table = 'Auth_optionaluserinfo'

    def __unicode__(self):
        return "%s - %s"%(self.user.displayname, self.houseno_and_street_address + ", " + self.city + ", " + self.country)



class ForgotPasswdTransactions(models.Model):
    user = models.ForeignKey(User, null=False, blank=False, db_column='user_id')
    transactionkey = models.CharField(max_length=255, null=False, blank=False)
    starttime = models.DateTimeField(auto_now_add=True)
    resetstatus = models.BooleanField(default=False)
    endtime = models.DateTimeField(default=None)
    
    class Meta:
        verbose_name = "Forgot Password Transaction"
        db_table = 'Auth_forgotpasswdtransaction'

    def __unicode__(self):
        return "%s - %s"%(self.user.displayname, self.transactionkey)
