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
    userpic = models.ImageField(max_length=100, upload_to=picpath)
    #skinpic = models.ImageField(max_length=100, upload_to=picpath)
    


class Session(models.Model):
    pass

