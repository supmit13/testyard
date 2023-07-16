# Tutorial: https://www.geeksforgeeks.org/launching-aws-ec2-instance-using-python/
# Doc: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html
# Info: 
# https://www.ipswitch.com/blog/how-to-create-an-ec2-instance-with-python
# https://docs.aws.amazon.com/toolkit-for-visual-studio/latest/user-guide/tkv-create-ami-from-instance.html

import os, sys, re, time
import uuid, glob, random
import boto3, botocore
from botocore.exceptions import ClientError
import mysql.connector
import simplejson as json


TARGET_AMI = 'ami-0bafdc79150fae5df' # This AMI has docker-CE installed on it along with an updated apt repo.
TARGET_INSTANCE_TYPE = 't2.micro'
TY_SECURITY_GROUP = "sg-0fad5a10d984b4a78" # HTTP/HTTPS from anywhere, ssh from anywhere. Also port 8888 open for incoming traffic for signal server from local. (launch-wizard-6)
SVC_SECURITY_GROUP = "" # Port for coturn and urlshortener (8080) - access from anywhere.
KEYS_DIR = "./keys"
REPOHOSTIP = "13.232.197.1"


def createdbconnection(dbuser='root', dbpasswd='Spmprx13@', dbhost='localhost', dbport='3306', dbname='amazondb'):
    dbconn = mysql.connector.connect(host=dbhost, user=dbuser, password=dbpasswd, port=dbport, database=dbname, auth_plugin='mysql_native_password', autocommit=True)
    return dbconn


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
    

def _createkeypair(ec2client, keyname=None):
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
        return ()


def createkeypair(ec2client, keyname=None):
    """
    Function to create keypair on aws: Calls _createkeypair with the ec2 client object
    and optionally a keyname. Once keypair is created, it records it in the DB after
    storing the private key in a file.
    """
    try:
        dbconn = createdbconnection()
        dbcursor = dbconn.cursor()
    except:
        print("Error creating DB connection or DB cursor object: %s"%sys.exc_info()[1].__str__())
        return None
    try:
        rtup = _createkeypair(ec2client, keyname)
        if rtup.__len__() > 1:
            jsondata = rtup[1]
            if 'KeyFingerprint' in jsondata.keys():
                keyfingerprint = jsondata['KeyFingerprint']
                keyfilename = keyfingerprint.replace(":", "_") + ".pem"
                keyfilepath = KEYS_DIR + os.path.sep + keyfilename
                privatekey = str(jsondata['KeyMaterial'])
                kfp = open(keyfilepath, "w")
                kfp.write(privatekey)
                kfp.close()
                keyname = jsondata['KeyName']
                keypairid = jsondata['KeyPairId']
                keysql = "insert into aws_keypairs (fingerprint, keyfilename, keyname, keypairid) values ('%s', '%s', '%s', '%s')"%(keyfingerprint, keyfilename, keyname, keypairid)
                dbcursor.execute(keysql)
                lastid = dbcursor.lastrowid
                #print(lastid)
            else:
                print("Failed to create keypair - %s"%keyresponse)
    except:
        print("Failed to create keypair: %s"%sys.exc_info()[1].__str__())
        keyname = ""
    return keyname

    
def _createinstance(ec2client, keypairname, elasticipaddr, secgroup=TY_SECURITY_GROUP):
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


def createinstance(ec2client, keypairname, elasticipaddr, secgroup=TY_SECURITY_GROUP):
    """
    Function to create an aws ec2 instance of type t2.micro (or as specified by TARGET_INSTANCE_TYPE).
    Calls _createinstance() and stores the instance details in DB.
    """
    try:
        dbconn = createdbconnection()
        dbcursor = dbconn.cursor()
    except:
        print("Error creating DB connection or DB cursor object: %s"%sys.exc_info()[1].__str__())
        return None
    try:
        instobj = _createinstance(ec2client, keypairname, elasticipaddr, secgroup)
        instanceid = instobj['InstanceId']
        instancetype = instobj['InstanceType']
        keyname = instobj['KeyName']
        launchdatetime = instobj['LaunchTime']
        pvtdnsname = instobj['PrivateDnsName']
        pvtipaddress = instobj['PrivateIpAddress']
        pubdnsname = instobj['PublicDnsName']
        pubipaddress = instobj['PublicIpAddress']
        subnetid = instobj['SubnetId']
        vpcid = instobj['VpcId']
        architecture = instobj['Architecture']
        blockdevicename = instobj['BlockDeviceMappings'][0]['DeviceName']
        volumeid = instobj['BlockDeviceMappings'][0]['Ebs']['VolumeId']
        hypervisor = instobj['Hypervisor']
        netifaceattachmentid = instobj['NetworkInterfaces'][0]['Attachment']['AttachmentId']
        networkgroups = json.dumps(instobj['NetworkInterfaces'][0]['Groups'])
        netmacaddress = instobj['NetworkInterfaces'][0]['MacAddress']
        netifaceid = instobj['NetworkInterfaces'][0]['NetworkInterfaceId']
        netownerid = instobj['NetworkInterfaces'][0]['OwnerId']
        subnetid = instobj['NetworkInterfaces'][0]['SubnetId']
        netvpcid = instobj['NetworkInterfaces'][0]['VpcId']
        rootdevicename = instobj['RootDeviceName']
        rootdevicetype = instobj['RootDeviceType']
        securitygroups = json.dumps(instobj['SecurityGroups'])
        platformdetails = instobj['PlatformDetails']
        instownerid = instobj['OwnerId']
        instreservationid = instobj['ReservationId']
        instancesql = "insert into aws_instance (instanceid, instancetype, keyname, launchdatetime, privatednsname, privateipaddress, publicdnsname, publicipaddress, subnetid, vpcid, architecture, blockdevicename, volumeid, hypervisor, netinterfaceattachmentid, networkgroups, netmacaddress, netinterfaceid, netownerid, netsubnetid, netvpcid, rootdevicename, rootdevicetype, securitygroups, platformdetails, instanceownerid, instancereservationid, creationdate) values ('%s', '%s', '%s', %s, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', NOW())"%(instanceid, instancetype, keyname, launchdatetime, pvtdnsname, pvtipaddress, pubdnsname, pubipaddress, subnetid, vpcid, architecture, blockdevicename, volumeid, hypervisor, netifaceattachmentid, networkgroups, netmacaddress, netifaceid, netownerid, subnetid, netvpcid, rootdevicename, rootdevicetype, securitygroups, platformdetails, instownerid, instreservationid)
        dbcursor.execute(instancesql)
        lastid = dbcursor.lastrowid
        return instanceid
    except:
        print("Failed to create instance object: %s"%sys.exc_info()[1].__str__())
        return -1



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


def preparehosts(tyinstanceid, svcinstanceid, keyname, ec2client):
    """
    Function to prepare a set of 2 aws instances in order to deploy
    the TestYard app. This involves logging into the instances and 1)
    pulling the docker image containing TestYard django app + mysql DB
    (testyard schema) + signal server + redis/celery/sendmail from the
    repository into tyinstanceid, 2) pulling the docker image containing
    the coturn setup + urlshortener services into svcinstanceid. 
    3) Run both images in their respective instances. Finally, edit 
    skills_settings.py in tyinstanceid to contain the IP address of 
    svcinstanceid, and edit urlhortener's config.py and coturn config 
    to contain IP address of tyinstanceid. 
    Note: Need to open port 8888 for incoming http traffic on tyinstanceid.
    Note: Need to open port for coturn traffic on svcinstanceid.
    """
    tydockerimgurl = ""
    svcdockerimgurl = ""
    awsdbconn = mysql.connector.connect(host='localhost', user='root', password='Spmprx13@', port=3306, database='amazondb', auth_plugin='mysql_native_password', autocommit=True)
    awscursor = awsdbconn.cursor()
    keysql = "select keyfilename, keypairid from aws_keypairs where keyname='%s'"%keyname
    awscursor.execute(keysql)
    allkeyrecs = awscursor.fetchall()
    if allkeyrecs.__len__() == 0:
        print("Couldn't find key with name %s"%keyname)
        return None
    keypairid = allkeyrecs[0][1]
    keyfilename = allkeyrecs[0][0]
    keyfilepath = KEYS_DIR + os.path.sep + keyfilename
    instancesql = "select instanceid, publicipaddress from aws_instance where instanceid in ('%s', '%s')"(tyinstanceid, svcinstanceid)
    awscursor.execute(instancesql)
    allinstances = awscursor.fetchall()
    instancesdict = {}
    for instancerec in allinstances:
        instanceid = instancerec[0]
        instanceip = instancerec[1]
        instancesdict[instanceid] = instanceip
    #kfp = open(keyfilepath, "r")
    #secretkey = kfp.read()
    #kfp.close()
    #client = createawsclient(keypairid, secretkey)
    #tycommands = "sshpass -f '/path/to/passwordfile' scp ubuntu@%s:/home/ubuntu/dockerimages/tyimage.tar /home/ubuntu/."%REPOHOSTIP
    tycommand = "scp -i %s /home/supmit/work/ty_newiface/docker/tyimage.tar ubuntu@%s:/home/ubuntu/"(keyfilepath, instancesdict[tyinstanceid])
    svccommand = "scp -i %s /home/supmit/work/ty_newiface/docker/svcimage.tar ubuntu@%s:/home/ubuntu/"(keyfilepath, instancesdict[svcinstanceid])
    os.system(tycommand)
    os.system(svccommand)
    #tycommands = "scp ubuntu@%s:/home/ubuntu/dockerimages/tyimage.tar /home/ubuntu/"%REPOHOSTIP
    #svccommands = "scp ubuntu@%s:/home/ubuntu/dockerimages/svcimage.tar /home/ubuntu/"%REPOHOSTIP
    #tyresp = client.send_command(DocumentName="AWS-RunShellScript", Parameters={'commands': tycommands}, InstanceIds=[tyinstanceid,])
    #svcresp = client.send_command(DocumentName="AWS-RunShellScript", Parameters={'commands': svccommands}, InstanceIds=[svcinstanceid,])
    # Next, run the images in both hosts to create the corresponding docker instances.
    tycommands = "docker load -i /home/ubuntu/tyimage.tar;docker run -it -d tyimage;"
    svccommands = "docker load -i /home/ubuntu/svcimage.tar;docker run -it -d svcimage;"
    tyresp = client.send_command(DocumentName="AWS-RunShellScript", Parameters={'commands': tycommands}, InstanceIds=[tyinstanceid,])
    svcresp = client.send_command(DocumentName="AWS-RunShellScript", Parameters={'commands': svccommands}, InstanceIds=[svcinstanceid,])
    # At this point both instances have the corresponding docker images running. So we need to run the services inside them now.
    
    awscursor.close()
    awsdbconn.close()


def setupawshosts(targetdate=None):
    """
    Function to check the 'Subscription_userplan' table in 'testyard'
    database for entries for the given date (passed in as argument).
    It will check for subscribers of the "Unlimited Plan". It will
    check if the required amount has been paid. If yes, it will create
    2 aws instances where the testyard application and the coturn services
    would be deployed. If the date passed in as argument is None, then it
    will look for records for the current date. If it is passed as an
    argument, it should be a string in the format 'YYYY-MM-DD'.
    """
    tydbconn = mysql.connector.connect(host='localhost', user='root', password='Spmprx13@', port=3306, database='testyard', auth_plugin='mysql_native_password', autocommit=True)
    tycursor = tydbconn.cursor()
    if targetdate is None:
        targetdate = datetime.datetime.now()
    else:
        try:
            targetdate = datetime.datetime.strptime(targetdate, "%Y-%m-%d %H:%M:%S")
        except:
            print("Error: %s"%sys.exc_info()[1].__str__())
            return None
    subscriptionqry = "select up.user_id, up.totalcost, up.amountpaid, up.discountamountapplied, u.displayname, u.emailid from Subscription_userplan up, Subscription_plan p, Auth_user u where up.planstatus=TRUE and p.planname='Unlimited Plan' and p.id=up.plan_id and p.status=TRUE and up.subscribedon=%s and up.user_id=u.id and u.active=TRUE and u.newuser=FALSE"
    tycursor.execute(subscriptionqry, (targetdate,))
    subscriptionrecords = tycursor.fetchall()
    allusers = {} # This will hold the valid displayname values and the corresponding email Ids.
    for srec in subscriptionrecords:
        uid = srec[0]
        totalcost = srec[1]
        amtpaid = srec[2]
        discountamt = srec[3]
        displayname = srec[4]
        emailid = srec[5]
        if amtpaid + discountamt < totalcost:
            continue # Skip users who haven't paid the entire amount (with discount)
        allusers[displayname] = emailid
    # Now we need to start creating the aws instances for the users in allusers dict.
    ec2client = createawsclient('ACCESS_KEY_ID', 'SECRET_ACCESS_KEY')
    for username in allusers.keys():
        emailid = allusers[username]
        # Create 2 elastic IP addresses for the 2 instances we will create
        testyardip = createelasticip(ec2client)
        servicesip = createelasticip(ec2client)
        # Create a keypair, and we will use the same keypair for both instances.
        kpair = createkeypair(ec2client, username) # We are using the username as the keypair name.
        # Create an instance for the testyard application
        tyinstid = createinstance(ec2client, kpair, testyardip)
        # Create an instance for the helper services
        svcinstid = createinstance(ec2client, kpair, servicesip)
        # Now we have our instances ready (It already contains docker since the AMI used had docker). 
        # Time to login and pull the appropriate docker images from the repos. Call 
        preparehosts(tyinstid, svcinstid, kpair, ec2client)


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
    if sys.argv.__len__() > 1:
        keyname = sys.argv[1]
    else:
        keyname = None
    try:
        ec2client = createawsclient('ACCESS_KEY_ID', 'SECRET_ACCESS_KEY')
        instdict = getinstances(ec2client)
        print(instdict)
        createkeypair(ec2client)
    except:
        print("Error: %s"%sys.exc_info()[1].__str__())
        # Log the error with user information - which user request was being processed.
    


#https://stackoverflow.com/questions/42645196/how-to-ssh-and-run-commands-in-ec2-using-boto3
