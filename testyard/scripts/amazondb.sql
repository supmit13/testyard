create database amazondb;

use amazondb;

create table aws_keypairs (
	id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
	fingerprint varchar(70) NOT NULL DEFAULT '',
	keyfilename varchar(100) NOT NULL,
	keyname varchar(50) NOT NULL DEFAULT '',
	keypairid varchar(30) NOT NULL DEFAULT ''
);

create table aws_instance (
	id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
	instanceid varchar(255) NOT NULL DEFAULT '',
	instancetype varchar(255) NOT NULL DEFAULT '',
	keyname varchar(50)  NOT NULL DEFAULT '',
	launchdatetime DATETIME NOT NULL,
	privatednsname varchar(255) NOT NULL DEFAULT '',
	privateipaddress varchar(100) NOT NULL DEFAULT '',
	publicdnsname VARCHAR(255) NOT NULL DEFAULT '',
	publicipaddress varchar(100) NOT NULL DEFAULT '',
	subnetid varchar(100) NOT NULL DEFAULT '',
	vpcid varchar(100)  NOT NULL DEFAULT '',
	architecture text,
	blockdevicename varchar(100)  NOT NULL DEFAULT '',
	volumeid varchar(100)  NOT NULL DEFAULT '',
	hypervisor varchar(255)  NOT NULL DEFAULT '',
	netinterfaceattachmentid varchar(100) NOT NULL DEFAULT '',
	networkgroups text,
	netmacaddress varchar(255)  NOT NULL DEFAULT '',
	netinterfaceid varchar(255)  NOT NULL DEFAULT '',
	netownerid varchar(255)  NOT NULL DEFAULT '',
	netsubnetid varchar(255)  NOT NULL DEFAULT '',
	netvpcid varchar(255) NOT NULL DEFAULT '',
	rootdevicename varchar(255)  NOT NULL DEFAULT '',
	rootdevicetype varchar(255) NOT NULL DEFAULT '',
	securitygroups text,
	platformdetails text,
	instanceownerid varchar(255)  NOT NULL DEFAULT '',
	instancereservationid varchar(255) NOT NULL DEFAULT '',
	creationdate DATETIME NOT NULL DEFAULT NOW()
);



