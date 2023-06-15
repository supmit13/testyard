# Tutorial: https://www.geeksforgeeks.org/launching-aws-ec2-instance-using-python/
# Doc: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html

import os, sys, re, time
import boto3
from botocore.exceptions import ClientError


def createawsclient(access_key_id, secret_access_key, hosttype='ec2', region='ap-south-1'):
    """
    Create an aws boto3 client object and return it.
    """
    clientobj = boto3.client(hosttype, region, aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
    return clientobj
    

def getinstances(ec2client):
    """
    Get a dictionary containing the information pertaining to the existing instances
    on the account (identified by access_key_id).
    """
    response = ec2client.describe_instances()
    return response
    
    
def createinstance(ec2client, hosttype='ec2', region='ap-south-1', keypair='ec2-keypair'):
    """
    Function to create an aws instance of type 'hosttype' at region 'region';
    The Turn-server image Id is being used - Ubuntu 22.04.
    MinCount and MaxCount are both 1, so only 1 instance will be created.
    """
    try:
        instanceobjs = ec2client.create_instances(ImageId='ami-024c319d5d14b463e', MinCount=1, MaxCount=1, InstanceType='t2.micro', KeyName=keypair) # TODO: See how to pass hosttype and region as parameters
        return instanceobjs
    except:
        print("Error occurred while creating instances: %s"%sys.exc_info()[1].__str__())
        return None


def startinstance(instanceid, ec2client):
    """
    Function to start an aws instance identified by 'instanceid'.
    ec2client is an object of boto3.client, and it is used to 
    perform the operation.
    """
    try:
        ec2client.start_instances(InstanceIds=[instanceid], DryRun=True)
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            raise
    # If we are here, then the above executed successfully
    try:
        response = ec2client.start_instances(InstanceIds=[instanceid], DryRun=False)
        print(response)
        return response
    except ClientError as e:
        print(e)


def stopinstance(instanceid, ec2client):
    """
    Function to stop an aws instance identified by 'instanceid'.
    ec2client is an object of boto3.client, and it performs the
    stop operation.
    """
    try:
        ec2client.stop_instances(InstanceIds=[instanceid], DryRun=True)
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            raise
    # Above code executed successfully if we are here.
    try:
        response = ec2client.stop_instances(InstanceIds=[instanceid], DryRun=False)
        print(response)
        return response
    except ClientError as e:
        print(e)


def rebootinstance(instanceid, ec2client):
    """
    Reboots an ec2 instance identified by 'instanceid'.
    ec2client is an object of boto3.client
    """
    try:
        ec2client.reboot_instances(InstanceIds=[instanceid,], DryRun=True)
    except ClientError as e:
        if 'DryRunOperation' not in str(e):
            print("You don't have permission to reboot instances.")
            raise
    # Dry run is successfully completed
    try:
        response = ec2client.reboot_instances(InstanceIds=[instanceid,], DryRun=False)
        print('Success', response)
        return response
    except ClientError as e:
        print('Error', e)



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
    ec2client = createawsclient('ACCESS_KEY_ID', 'SECRET_ACCESS_KEY')
    instdict = getinstances(ec2client)
    print(instdict)
    



