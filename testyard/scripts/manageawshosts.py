# User: testyard@aws
# Console Sign-in URL: https://294493204888.signin.aws.amazon.com/console
# Password: @kK70(#0
# AWS Account ID: 294493204888
# Access Key ID: AKIAUJEJJWGMB76V73J2
# Secret Access Key: 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
# Region: ap-south-1

# Tutorial: https://www.geeksforgeeks.org/launching-aws-ec2-instance-using-python/

import os, sys, re, time
import boto3


def getinstances(access_key_id, secret_access_key, hosttype='ec2', region='ap-south-1'):
    """
    Get a dictionary containing the information pertaining to the existing instances
    on the account (identified by access_key_id).
    """
    host = boto3.client(hosttype, region, aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
    response = host.describe_instances()
    return response
    
    
def createinstance(access_key_id, secret_access_key, hosttype='ec2', region='ap-south-1'):
    """
    Function to create an aws instance of type 'hosttype' at region 'region'
    """
    pass


def startinstance(instanceid, access_key_id, secret_access_key):
    """
    Function to start an aws instance identified by 'instanceid'
    """
    pass


def stopinstance(instanceid, access_key_id, secret_access_key):
    """
    Function to stop an aws instance identified by 'instanceid'
    """
    pass


def preparehost(instanceid, iamuser, iampasswd, access_key_id, secret_access_key):
    """
    Function to prepare an aws instance before deploying TestYard app.
    This involves installing services such as nginx, mysql, etc.,
    creating the python environment with all required modules, starting
    mysql service, setting up ssl certificates/keys, etc. The first
    argument identifies the host that is to be "prepared".
    """
    pass


def setupty(instanceid, iamuser, iampasswd, access_key_id, secret_access_key):
    """
    Function to set up the TestYard app. This involves fetching the codebase
    from github, setting up the testyard DB, configuring nginx and uwsgi to
    run the app, starting the services for urlshortener, signal server, redis,
    celery mail queue, starting the TURN server, and so on.
    """
    pass


def testsetup(instanceid, iamuser, iampasswd, access_key_id, secret_access_key):
    """
    Perform a functional test of all the components of the TestYard app on
    the instance identified by instanceid. Should return 'True' for success,
    and 'False' for failure. Write a log in a specified location on the instance,
    if possible. (Won't be able to do that if the instance does not start
    appropriately.)
    """
    pass


def teardowninstance(instanceid, iamuser, iampasswd, access_key_id, secret_access_key, bkupflag=True):
    """
    Tear down an existing instance and selectively destroy the resources used.
    May need to create backups for user data. By default the backup is created.
    """
    pass


def _sendemail(fromaddr, toaddr, subject, message, cc="", bcc=""):
    """
    Utility function to take care of emailing the concerned users and administrators
    about the status of an operation defined above.
    """
    pass


if __name__ == "__main__":
    instdict = getinstances('AKIAUJEJJWGMB76V73J2', '4DN7ZkXQ3NV9m4ZLVQeXOyPb+b8rjYWzr2EX5/Nh')
    print(instdict)
    



