create database amazondb;

use amazondb;

create table aws_keypairs (
	id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
	fingerprint varchar(70) NOT NULL DEFAULT '',
	keyfilename varchar(100) NOT NULL,
	keyname varchar(50) NOT NULL DEFAULT '',
	keypairid varchar(30) NOT NULL DEFAULT ''
);

