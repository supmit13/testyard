# Tutorial: https://www.geeksforgeeks.org/launching-aws-ec2-instance-using-python/
# Doc: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html
# Info: 
# https://www.ipswitch.com/blog/how-to-create-an-ec2-instance-with-python
# https://docs.aws.amazon.com/toolkit-for-visual-studio/latest/user-guide/tkv-create-ami-from-instance.html

import os, sys, re, time
import uuid, glob, random
import boto3
from botocore.exceptions import ClientError


TARGET_AMI = 'ami-0bafdc79150fae5df' # This AMI has docker-CE installed on it along with an updated apt repo.
TARGET_INSTANCE_TYPE = 't2.micro'
TY_SECURITY_GROUP = "sg-0fad5a10d984b4a78" # HTTP/HTTPS from anywhere, ssh from anywhere. Also port 8888 open for incoming traffic for signal server from local. (launch-wizard-6)
SVC_SECURITY_GROUP = "" # Port for coturn and urlshortener (8080) - access from anywhere.


def _genrandomstring():
    """
    Generate a random string. 
    This will be used as keyname while creating
    keypair for an ec2 instance.
    """
    random = str(uuid.uuid4())
    random = random.replace("-","")
    tstr = str(int(time.time() * 1000))
    random = random + tstr
    return random
    

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


def createelasticip(ec2client):
    """
    Info: https://stackoverflow.com/questions/35656820/in-aws-how-to-create-elastic-ip-with-boto3-or-more-generaly-with-python
    Creates an elastic IP for use when creating ec2 instances.
    Returns the IP address.
    """
    addr = ec2client.allocate_address(Domain='vpc')
    return addr['PublicIp'] # This is the elastic IP returned.
    

def createkeypair(ec2client, keyname=None):
    """
    Doc: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/ec2-example-key-pairs.html
    Generate a key pair to use with a ec2 instance. 
    Value of 'keyname' would be used as name. If this is None,
    then a random string will be generated and used as name.
    Returns the keyname and the response as a 2 element tuple.
    """
    if keyname is None:
        keyname = _genrandomstring()
    try:
        response = ec2client.create_key_pair(KeyName=keyname)
        return (keyname, response)
    except:
        print("Error while creating keypair with name '%s': %s"%(keyname, sys.exc_info()[1].__str__()))
        return None

    
def createinstance(ec2client, keypairname, elasticipaddr, secgroup=TY_SECURITY_GROUP):
    """
    Function to create an aws instance of type 'hosttype' at region 'region';
    The Turn-server image Id is being used - Ubuntu 22.04.
    MinCount and MaxCount are both 1, so only 1 instance will be created.
    The default security group is TY_SECURITY_GROUP.
    Returns the instance object.
    """
    try:
        instanceobjs = ec2client.create_instances(ImageId=TARGET_AMI, MinCount=1, MaxCount=1, InstanceType=TARGET_INSTANCE_TYPE, KeyName=keypairname, SecurityGroupIds=[secgroup,])
        # The ec2client object was created with the host type and region values given, so the instance will have the same host type and region.
        instid = instanceobjs[0]['InstanceId']
        r = ec2client.associate_address(InstanceId=instid, PublicIp=elasticipaddr)
        return instanceobjs[0] # an ec2.instance object
    except:
        print("Error occurred while creating instances: %s"%sys.exc_info()[1].__str__())
        return None


def startinstance(instanceid, ec2client):
    """
    Doc: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/ec2-example-managing-instances.html
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


def imposesecurityrestrictions(instanceid, ec2client, restrictions={}):
    """
    Impose restrictions in addition to the security group being used.
    """
    pass


def preparehosts(tyinstanceid, svcinstanceid, ec2client):
    """
    Function to prepare a set of 2 aws instances in order to deploy
    the TestYard app. This involves 1) pulling the docker image 
    containing TestYard django app + mysql DB (testyard schema) + signal
    server + redis/celery/sendmail from the repository into tyinstanceid,
    2) pulling the docker image containing the coturn setup + urlshortener
    services into svcinstanceid. 3) Run both images in their respective 
    instances. Finally, edit skills_settings.py in tyinstanceid to
    contain the IP address of svcinstanceid, and edit urlhortener's 
    config.py and coturn config to contain IP address of tyinstanceid.
    Note: Need to open port 8888 for incoming http traffic on tyinstanceid.
    Note: Need to open port for coturn traffic on svcinstanceid.
    """
    pass


def setupty(tyinstanceid, svcinstanceid, ec2client):
    """
    Function to set up the TestYard system services. This involves
    1) starting nginx in the tyinstanceid container, 2) starting mysql
    in tyinstanceid container, 3)  starting uwsgi in the tyinstanceid 
    container 4) starting redis and celery (for email dispatching) in 
    the tyinstanceid container, 5) starting signal server in the 
    tyinstanceid container. 6) run the coturn service in the svcinstanceid
    container, 7) run the mysql service in the svcinstanceid container, 8)
    run the uvicorn urlshortener service in the svcinstanceid container. 
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
    



