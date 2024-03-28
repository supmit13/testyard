BEGIN;

use testyard;
CREATE TABLE `Auth_user` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `firstname` varchar(100) NOT NULL,
    `middlename` varchar(20) NOT NULL,
    `lastname` varchar(100) NOT NULL,
    `displayname` varchar(100) NOT NULL UNIQUE,
    `password` varchar(100) NOT NULL,
    `emailid` varchar(75) NOT NULL UNIQUE,
    `active` bool NOT NULL,
    `istest` bool NOT NULL,
    `joindate` datetime NOT NULL,
    `sex` varchar(3) NOT NULL,
    `usertype` varchar(4) NOT NULL,
    `mobileno` varchar(12) NOT NULL,
    `userpic` varchar(100) NOT NULL
)
;
CREATE TABLE `Auth_session` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `sessioncode` varchar(50) NOT NULL UNIQUE,
    `status` bool NOT NULL,
    `userid_id` integer NOT NULL,
    `starttime` datetime NOT NULL,
    `endtime` datetime NOT NULL,
    `sourceip` char(39) NOT NULL,
    `istest` bool NOT NULL,
    `useragent` varchar(255) NOT NULL
)
;
ALTER TABLE `Auth_session` ADD CONSTRAINT `userid_id_refs_id_640456e3` FOREIGN KEY (`userid_id`) REFERENCES `Auth_user` (`id`);
CREATE TABLE `Auth_privilege` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `privname` varchar(50) NOT NULL UNIQUE,
    `privdesc` longtext NOT NULL,
    `createdate` datetime NOT NULL
)
;
CREATE TABLE `Auth_userprivilege` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `userid_id` integer NOT NULL,
    `privilegeid_id` integer NOT NULL,
    `lastmod` datetime NOT NULL,
    `status` bool NOT NULL
)
;
ALTER TABLE `Auth_userprivilege` ADD CONSTRAINT `privilegeid_id_refs_id_a9cfb08` FOREIGN KEY (`privilegeid_id`) REFERENCES `Auth_privilege` (`id`);
ALTER TABLE `Auth_userprivilege` ADD CONSTRAINT `userid_id_refs_id_42ace1b3` FOREIGN KEY (`userid_id`) REFERENCES `Auth_user` (`id`);
CREATE INDEX `Auth_session_e2fd1d24` ON `Auth_session` (`userid_id`);
CREATE INDEX `Auth_userprivilege_e2fd1d24` ON `Auth_userprivilege` (`userid_id`);
CREATE INDEX `Auth_userprivilege_b05dc53f` ON `Auth_userprivilege` (`privilegeid_id`);

ALTER TABLE Auth_session MODIFY endtime datetime null;
ALTER TABLE Auth_session MODIFY sessioncode varchar(150) NOT null;

insert into Auth_privilege (privname, privdesc, createdate) values ('admin', 'Admin user can create test, add questions to it, assess responses from assessees, as well as play the role of assessees', NOW());

insert into Auth_privilege (privname, privdesc, createdate) values ('creator', 'Creators can add questions to an existing test, assess responses from assessees, as well as play the role of assessees', NOW());

insert into Auth_privilege (privname, privdesc, createdate) values ('assessor', 'Assessors can  assess responses from assessees and play the role of assessees', NOW());

insert into Auth_privilege (privname, privdesc, createdate) values ('assessee', 'Assessees can only take tests', NOW());


CREATE TABLE `Tests_topic` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `topicname` varchar(150) NOT NULL,
    `topicshortname` varchar(50) NOT NULL,
    `createdate` date NOT NULL,
    `isactive` bool NOT NULL
)
;
CREATE TABLE `Tests_subtopic` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `subtopicname` varchar(150) NOT NULL,
    `subtopicshortname` varchar(50) NOT NULL,
    `topic_id` integer NOT NULL,
    `createdate` date NOT NULL,
    `isactive` bool NOT NULL
)
;
ALTER TABLE `Tests_subtopic` ADD CONSTRAINT `topic_id_refs_id_bf3a8054` FOREIGN KEY (`topic_id`) REFERENCES `Tests_topic` (`id`);
CREATE TABLE `Tests_evaluator` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `evalgroupname` varchar(150) NOT NULL,
    `groupmember1_id` integer,
    `groupmember2_id` integer,
    `groupmember3_id` integer,
    `groupmember4_id` integer,
    `groupmember5_id` integer,
    `groupmember6_id` integer,
    `groupmember7_id` integer,
    `groupmember8_id` integer,
    `groupmember9_id` integer,
    `groupmember10_id` integer,
    `creationdate` datetime NOT NULL
)
;
ALTER TABLE `Tests_evaluator` ADD CONSTRAINT `groupmember1_id_refs_id_431af34a` FOREIGN KEY (`groupmember1_id`) REFERENCES `Auth_user` (`id`);
ALTER TABLE `Tests_evaluator` ADD CONSTRAINT `groupmember2_id_refs_id_431af34a` FOREIGN KEY (`groupmember2_id`) REFERENCES `Auth_user` (`id`);
ALTER TABLE `Tests_evaluator` ADD CONSTRAINT `groupmember3_id_refs_id_431af34a` FOREIGN KEY (`groupmember3_id`) REFERENCES `Auth_user` (`id`);
ALTER TABLE `Tests_evaluator` ADD CONSTRAINT `groupmember4_id_refs_id_431af34a` FOREIGN KEY (`groupmember4_id`) REFERENCES `Auth_user` (`id`);
ALTER TABLE `Tests_evaluator` ADD CONSTRAINT `groupmember5_id_refs_id_431af34a` FOREIGN KEY (`groupmember5_id`) REFERENCES `Auth_user` (`id`);
ALTER TABLE `Tests_evaluator` ADD CONSTRAINT `groupmember6_id_refs_id_431af34a` FOREIGN KEY (`groupmember6_id`) REFERENCES `Auth_user` (`id`);
ALTER TABLE `Tests_evaluator` ADD CONSTRAINT `groupmember7_id_refs_id_431af34a` FOREIGN KEY (`groupmember7_id`) REFERENCES `Auth_user` (`id`);
ALTER TABLE `Tests_evaluator` ADD CONSTRAINT `groupmember8_id_refs_id_431af34a` FOREIGN KEY (`groupmember8_id`) REFERENCES `Auth_user` (`id`);
ALTER TABLE `Tests_evaluator` ADD CONSTRAINT `groupmember9_id_refs_id_431af34a` FOREIGN KEY (`groupmember9_id`) REFERENCES `Auth_user` (`id`);
ALTER TABLE `Tests_evaluator` ADD CONSTRAINT `groupmember10_id_refs_id_431af34a` FOREIGN KEY (`groupmember10_id`) REFERENCES `Auth_user` (`id`);
CREATE TABLE `Tests_test` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `testname` varchar(150) NOT NULL,
    `subtopic_id` integer NOT NULL,
    `creator_id` integer NOT NULL,
    `creatorisevaluator` bool NOT NULL,
    `evaluator_id` integer,
    `testtype` varchar(4) NOT NULL,
    `createdate` datetime NOT NULL,
    `maxscore` integer NOT NULL,
    `passscore` integer NOT NULL,
    `ruleset` varchar(4) NOT NULL,
    `duration` integer NOT NULL,
    `allowedlanguages` varchar(4) NOT NULL,
    `challengecount` integer NOT NULL,
    `activationdate` datetime NOT NULL,
    `status` bool NOT NULL,
    `quality` varchar(4) NOT NULL
)
;
ALTER TABLE `Tests_test` ADD CONSTRAINT `creator_id_refs_id_d29f6b50` FOREIGN KEY (`creator_id`) REFERENCES `Auth_user` (`id`);
ALTER TABLE `Tests_test` ADD CONSTRAINT `evaluator_id_refs_id_c4cea575` FOREIGN KEY (`evaluator_id`) REFERENCES `Tests_evaluator` (`id`);
ALTER TABLE `Tests_test` ADD CONSTRAINT `subtopic_id_refs_id_ae9af74e` FOREIGN KEY (`subtopic_id`) REFERENCES `Tests_subtopic` (`id`);
CREATE TABLE `Tests_usertest` (
    `user_id` integer,
    `emailaddr` varchar(75) NOT NULL,
    `testurl` varchar(200) NOT NULL PRIMARY KEY,
    `test_id` integer NOT NULL,
    `validfrom` datetime NOT NULL,
    `validtill` datetime NOT NULL,
    `status` integer NOT NULL,
    `outcome` bool,
    `score` double precision NOT NULL,
    `starttime` datetime NOT NULL,
    `endtime` datetime NOT NULL,
    `ipaddress` char(39) NOT NULL,
    `clientsware` varchar(150) NOT NULL,
    `sessid` varchar(50) NOT NULL
)
;
ALTER TABLE `Tests_usertest` ADD CONSTRAINT `user_id_refs_id_4487dbd7` FOREIGN KEY (`user_id`) REFERENCES `Auth_user` (`id`);
ALTER TABLE `Tests_usertest` ADD CONSTRAINT `test_id_refs_id_68cc46a6` FOREIGN KEY (`test_id`) REFERENCES `Tests_test` (`id`);
CREATE TABLE `Tests_challenge` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `test_id` integer NOT NULL,
    `statement` longtext NOT NULL,
    `challengetype` varchar(4) NOT NULL,
    `option1` longtext,
    `option2` longtext,
    `option3` longtext,
    `option4` longtext,
    `option5` longtext,
    `option6` longtext,
    `challengescore` double precision NOT NULL,
    `negativescore` double precision NOT NULL,
    `mustrespond` bool NOT NULL,
    `responsekey` longtext NOT NULL,
    `imageurl` varchar(200),
    `additionalurl` varchar(200),
    `timeframe` integer,
    `subtopic_id` integer NOT NULL,
    `challengequality` varchar(3) NOT NULL
)
;
ALTER TABLE `Tests_challenge` ADD CONSTRAINT `test_id_refs_id_7584e499` FOREIGN KEY (`test_id`) REFERENCES `Tests_test` (`id`);
ALTER TABLE `Tests_challenge` ADD CONSTRAINT `subtopic_id_refs_id_5e9d0e88` FOREIGN KEY (`subtopic_id`) REFERENCES `Tests_subtopic` (`id`);
CREATE TABLE `Tests_userresponse` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `test_id` integer NOT NULL,
    `challenge_id` integer NOT NULL,
    `user_id` integer NOT NULL,
    `answer` longtext,
    `responsedatetime` datetime,
    `attachments` varchar(100),
    `evaluation` double precision,
    `evaluator_remarks` longtext,
    `evaluated_by_id` integer NOT NULL,
    `candidate_comment` longtext,
    `response_quality` varchar(3) NOT NULL
)
;
ALTER TABLE `Tests_userresponse` ADD CONSTRAINT `test_id_refs_id_4ce9e81f` FOREIGN KEY (`test_id`) REFERENCES `Tests_test` (`id`);
ALTER TABLE `Tests_userresponse` ADD CONSTRAINT `user_id_refs_id_dfa3cedc` FOREIGN KEY (`user_id`) REFERENCES `Auth_user` (`id`);
ALTER TABLE `Tests_userresponse` ADD CONSTRAINT `evaluated_by_id_refs_id_dfa3cedc` FOREIGN KEY (`evaluated_by_id`) REFERENCES `Auth_user` (`id`);
ALTER TABLE `Tests_userresponse` ADD CONSTRAINT `challenge_id_refs_id_5cfa8871` FOREIGN KEY (`challenge_id`) REFERENCES `Tests_challenge` (`id`);
CREATE TABLE `Tests_sharetest` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `testcreator_id` integer NOT NULL,
    `sharedwith_id` integer NOT NULL,
    `sharedatetime` datetime NOT NULL,
    `test_id` integer NOT NULL
)
;
ALTER TABLE `Tests_sharetest` ADD CONSTRAINT `testcreator_id_refs_id_8687dad0` FOREIGN KEY (`testcreator_id`) REFERENCES `Auth_user` (`id`);
ALTER TABLE `Tests_sharetest` ADD CONSTRAINT `sharedwith_id_refs_id_8687dad0` FOREIGN KEY (`sharedwith_id`) REFERENCES `Auth_user` (`id`);
ALTER TABLE `Tests_sharetest` ADD CONSTRAINT `test_id_refs_id_31f72e13` FOREIGN KEY (`test_id`) REFERENCES `Tests_test` (`id`);
CREATE INDEX `Tests_subtopic_57732028` ON `Tests_subtopic` (`topic_id`);
CREATE INDEX `Tests_evaluator_769457e8` ON `Tests_evaluator` (`groupmember1_id`);
CREATE INDEX `Tests_evaluator_c640b8f` ON `Tests_evaluator` (`groupmember2_id`);
CREATE INDEX `Tests_evaluator_8f6f439a` ON `Tests_evaluator` (`groupmember3_id`);
CREATE INDEX `Tests_evaluator_b166ba03` ON `Tests_evaluator` (`groupmember4_id`);
CREATE INDEX `Tests_evaluator_279bd2e4` ON `Tests_evaluator` (`groupmember5_id`);
CREATE INDEX `Tests_evaluator_7873711d` ON `Tests_evaluator` (`groupmember6_id`);
CREATE INDEX `Tests_evaluator_3efef4da` ON `Tests_evaluator` (`groupmember7_id`);
CREATE INDEX `Tests_evaluator_f179706f` ON `Tests_evaluator` (`groupmember8_id`);
CREATE INDEX `Tests_evaluator_243e590` ON `Tests_evaluator` (`groupmember9_id`);
CREATE INDEX `Tests_evaluator_b69a883b` ON `Tests_evaluator` (`groupmember10_id`);
CREATE INDEX `Tests_test_d50c7adf` ON `Tests_test` (`subtopic_id`);
CREATE INDEX `Tests_test_f97a5119` ON `Tests_test` (`creator_id`);
CREATE INDEX `Tests_test_170dea88` ON `Tests_test` (`evaluator_id`);
CREATE INDEX `Tests_usertest_fbfc09f1` ON `Tests_usertest` (`user_id`);
CREATE INDEX `Tests_usertest_a88de8dc` ON `Tests_usertest` (`test_id`);
CREATE INDEX `Tests_challenge_a88de8dc` ON `Tests_challenge` (`test_id`);
CREATE INDEX `Tests_challenge_d50c7adf` ON `Tests_challenge` (`subtopic_id`);
CREATE INDEX `Tests_userresponse_a88de8dc` ON `Tests_userresponse` (`test_id`);
CREATE INDEX `Tests_userresponse_dd8bebce` ON `Tests_userresponse` (`challenge_id`);
CREATE INDEX `Tests_userresponse_fbfc09f1` ON `Tests_userresponse` (`user_id`);
CREATE INDEX `Tests_userresponse_d20e438b` ON `Tests_userresponse` (`evaluated_by_id`);
CREATE INDEX `Tests_sharetest_c967e5f7` ON `Tests_sharetest` (`testcreator_id`);
CREATE INDEX `Tests_sharetest_e4aa393d` ON `Tests_sharetest` (`sharedwith_id`);
CREATE INDEX `Tests_sharetest_a88de8dc` ON `Tests_sharetest` (`test_id`);

CREATE TABLE `Subscription_plan` (
    `planname` varchar(200) NOT NULL PRIMARY KEY,
    `tests` varchar(200) NOT NULL,
    `price` numeric(10, 2) NOT NULL,
    `validfor_unit` varchar(12) NOT NULL,
    `planvalidfor` integer NOT NULL,
    `adminuser_id` integer NOT NULL,
    `status` bool NOT NULL,
    `discountpercent` double precision,
    `discountamt` double precision,
    `createdate` datetime NOT NULL,
    `commissiondate` datetime,
    `decommissiondate` datetime
)
;
ALTER TABLE `Subscription_plan` ADD CONSTRAINT `adminuser_id_refs_id_665322f6` FOREIGN KEY (`adminuser_id`) REFERENCES `Auth_user` (`id`);
CREATE TABLE `Subscription_userplan` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `plan_id` varchar(200) NOT NULL,
    `user_id` integer NOT NULL,
    `totalcost` numeric(10, 2) NOT NULL,
    `amountpaid` numeric(10, 2) NOT NULL,
    `amountdue` numeric(10, 2) NOT NULL,
    `lastpaydate` datetime NOT NULL,
    `planstartdate` datetime NOT NULL,
    `planenddate` datetime,
    `planstatus` bool NOT NULL,
    `createdon` datetime NOT NULL,
    `discountpercentapplied` double precision,
    `discountamountapplied` double precision
)
;
ALTER TABLE `Subscription_userplan` ADD CONSTRAINT `user_id_refs_id_34f93f73` FOREIGN KEY (`user_id`) REFERENCES `Auth_user` (`id`);
ALTER TABLE `Subscription_userplan` ADD CONSTRAINT `plan_id_refs_planname_47f755ee` FOREIGN KEY (`plan_id`) REFERENCES `Subscription_plan` (`planname`);
CREATE TABLE `Subscription_transaction` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `username` varchar(100) NOT NULL,
    `user_id` integer NOT NULL,
    `planname` varchar(200),
    `usersession` varchar(50) NOT NULL,
    `payamount` numeric(10, 2) NOT NULL,
    `transactiondate` datetime NOT NULL,
    `comments` longtext NOT NULL,
    `paymode` varchar(50) NOT NULL,
    `invoice_email` varchar(75) NOT NULL,
    `trans_status` bool NOT NULL
)
;
ALTER TABLE `Subscription_transaction` ADD CONSTRAINT `user_id_refs_id_8c4721ea` FOREIGN KEY (`user_id`) REFERENCES `Auth_user` (`id`);
CREATE INDEX `Subscription_plan_4e201023` ON `Subscription_plan` (`adminuser_id`);
CREATE INDEX `Subscription_userplan_a57fd7f1` ON `Subscription_userplan` (`plan_id`);
CREATE INDEX `Subscription_userplan_fbfc09f1` ON `Subscription_userplan` (`user_id`);
CREATE INDEX `Subscription_transaction_fbfc09f1` ON `Subscription_transaction` (`user_id`);

ALTER TABLE Subscription_userplan CHANGE createdon subscribedon datetime;

ALTER TABLE Auth_user add column newuser boolean default True not  null;

CREATE TABLE `Auth_emailvalidationkey` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `email` varchar(75) NOT NULL,
    `vkey` varchar(50) NOT NULL UNIQUE
);

ALTER TABLE Tests_topic drop column topicshortname;
ALTER TABLE Test_topic add column user_id int not NULL references Auth_user(id);

alter table Tests_test add column publishdate datetime;

alter table Tests_test add column testlinkid varchar(200) not null;

alter table Tests_test add column topic_id int(11) not null references Tests_topic(id);

alter table Tests_test add column topicname varchar(200) default "";

alter table Tests_test modify subtopic_id int default NULL;

alter table Tests_challenge add column testlinkid varchar(200) not null;

alter table Tests_test modify passscore int(11) default NULL;

alter table Tests_test add column allowmultiattempts tinyint(1) default False;
alter table Tests_test add column maxattemptscount int(11) default 1 not NULL;
alter table Tests_test add column attemptsinterval int(11) default NULL;
alter table Tests_test add column attemptsintervalunit char(1) default NULL;

alter table Tests_test add column randomsequencing tinyint(1) default True not null;

alter table Tests_test add column multimediareqd tinyint(1) default False not null;

alter table Tests_test add column progenv varchar(100) default null;
alter table Tests_test add column scope varchar(50) default 'public' not null;

alter table Tests_test modify column allowedlanguages varchar(200) default 'enus' not null;
alter table Tests_test modify column ruleset varchar(200) default '' not null;

alter table Tests_challenge add column option7 longtext  default NULL;
alter table Tests_challenge add column option8 longtext  default NULL;

alter table Tests_challenge drop column imageurl;
alter table Tests_challenge add column mediafile varchar(255) default '';

alter table Tests_challenge add column maxresponsesizeallowable int (11) default -1;

alter table Tests_challenge modify column responsekey longtext default NULL;
alter table Tests_challenge modify column subtopic_id int(11) default NULL;

alter table Tests_test add column negativescoreallowed boolean default false;
alter table Tests_test modify column activationdate datetime default NULL;

alter  table Tests_challenge add column oneormore boolean default true;

create table Tests_wouldbeusers (
	emailaddr varchar(150) DEFAULT NULL,
	test_id int DEFAULT NULL,
	testurl varchar(200) DEFAULT NULL,
	validfrom datetime DEFAULT NULL,
	validtill datetime DEFAULT NULL
);
alter table Tests_wouldbeusers add column id int auto_increment primary key NOT NULL;

alter table Tests_usertest modify starttime datetime default 0;
alter table Tests_usertest modify endtime datetime default NULL;
alter table Tests_usertest modify ipaddress char(39) default '';
alter table Tests_usertest modify clientsware char(150) default '';
alter table Tests_usertest modify sessid char(50) default '';
alter table Tests_usertest modify score double default NULL;

alter table Tests_usertest add column active boolean default true;
alter table Tests_wouldbeusers add column active boolean default true;

alter table Tests_usertest drop primary key;
alter table Tests_usertest add column id int auto_increment primary key;

alter table Tests_usertest add column cancelled boolean default false;
alter table Tests_wouldbeusers add column cancelled boolean default false;

alter table Tests_wouldbeusers add column status int(11) NOT NULL;
alter table Tests_wouldbeusers add column outcome tinyint(1) DEFAULT NULL;
alter table Tests_wouldbeusers add column score double DEFAULT NULL;
alter table Tests_wouldbeusers add column starttime datetime DEFAULT NULL;
alter table Tests_wouldbeusers add column endtime datetime DEFAULT NULL;
alter table Tests_wouldbeusers add column ipaddress char(39) DEFAULT '';
alter table Tests_wouldbeusers add column clientsware char(150) DEFAULT '';

alter table Tests_usertest add column stringid varchar(15) NOT NULL;
alter table Tests_wouldbeusers add column stringid varchar(15) NOT NULL;

alter table Tests_usertest modify column stringid varchar(100);
alter table Tests_wouldbeusers modify column stringid varchar(100);

alter table Tests_userresponse drop foreign key user_id_refs_id_dfa3cedc;
alter table Tests_userresponse drop column user_id;

alter table Tests_userresponse add column emailaddr varchar (255) NOT NULL;

alter table Tests_userresponse modify column evaluated_by_id int  DEFAULT NULL;

/* alter table Tests_userresponse add column usertest_id int not null, add foreign key fk_usertest (usertest_id) references Tests_usertest (id) on delete cascade; */

alter table Tests_userresponse add column tabref varchar(40) not null;
alter table Tests_userresponse add column tabid int not null;

alter table Tests_usertest add column evaluator_comment longtext default "";
alter table Tests_wouldbeusers add column evaluator_comment longtext default "";

alter table Tests_usertest add column first_eval_timestamp int (11) default NULL;
alter table Tests_wouldbeusers add column first_eval_timestamp int (11) default NULL;

alter table Tests_usertest add column visibility int(11) default 0;
alter table Tests_wouldbeusers add column visibility int(11) default 0;


create table Network_group (
	id int(11) NOT NULL AUTO_INCREMENT,
	owner_id int(11) NOT NULL,
	groupname varchar (255) NOT NULL,
	tagline text DEFAULT "",
	description text DEFAULT "",
	memberscount int(11) DEFAULT 0,
	maxmemberslimit int(11) DEFAULT 10000,
	status boolean DEFAULT true,
	grouptype varchar(255) DEFAULT "",
	creationdate datetime,
	allowentry boolean DEFAULT true,
	groupimagefile varchar(255) DEFAULT "",
	basedontopic varchar(200) DEFAULT "",
	adminremarks text DEFAULT "",
	stars int(11) DEFAULT 0,
	entrytest_id int(11) DEFAULT NULL,
	ispaid boolean DEFAULT false,
	entryfee float DEFAULT 0.0,
	primary key (`id`),
	FOREIGN KEY (`owner_id`) REFERENCES `Auth_user` (`id`),
	FOREIGN KEY (`entrytest_id`) REFERENCES `Tests_test` (`id`)
);


create table Network_post (
	id int(11) NOT NULL AUTO_INCREMENT,
	poster_id int(11) NOT NULL,
	posttargettype varchar(200) NOT NULL,
	posttargetuser_id int(11) DEFAULT NULL,
	posttargetgroup_id int(11) DEFAULT NULL,
 	imagefile varchar(255) DEFAULT '',
	videofile varchar(255) DEFAULT '',
	scope varchar(255) DEFAULT 'public',
	relatedpost_id int(11) DEFAULT NULL,
	deleted boolean DEFAULT false,
	hidden boolean DEFAULT false,
	stars int(11) DEFAULT 0,
	primary key (`id`),
	FOREIGN KEY (`poster_id`) REFERENCES `Auth_user` (`id`),
	FOREIGN KEY (`relatedpost_id`) REFERENCES `Network_post` (`id`),
 	FOREIGN KEY (`posttargetuser_id`) REFERENCES `Auth_user` (`id`),
	FOREIGN KEY (`posttargetgroup_id`) REFERENCES `Network_group` (`id`)
);


create table Network_groupmember (
	id int(11) NOT NULL AUTO_INCREMENT,
	group_id int(11) NOT NULL,
	member_id int(11) NOT NULL,
	membersince datetime DEFAULT NULL,
	status boolean DEFAULT true,
	removed boolean DEFAULT false,
	blocked boolean DEFAULT false,
	primary key (`id`),
	FOREIGN KEY (`member_id`) REFERENCES `Auth_user` (`id`),
	FOREIGN KEY (`group_id`) REFERENCES `Network_group` (`id`)
);


create table Network_connection (
	id int(11) NOT NULL AUTO_INCREMENT,
	focususer_id int(11) NOT NULL,
	connectedto_id int(11) NOT NULL,
	connectedfrom datetime DEFAULT NULL,
	deleted boolean DEFAULT false,
	blocked boolean DEFAULT false,
	connectedthru varchar(200) DEFAULT '',
	primary key (`id`),
	FOREIGN KEY (`focususer_id`) REFERENCES `Auth_user` (`id`),
	FOREIGN KEY (`connectedto_id`) REFERENCES `Auth_user` (`id`)
);


create table Network_connectioninvitation (
	id int(11) NOT NULL AUTO_INCREMENT,
	fromuser_id int(11) NOT NULL,
	touser_id int(11) NOT NULL,
	invitationcontent text DEFAULT "",
	invitationstatus varchar(5) DEFAULT "open",
	invitationdate datetime DEFAULT NULL,
	primary key (`id`),
	FOREIGN KEY (`fromuser_id`) REFERENCES `Auth_user` (`id`),
	FOREIGN KEY (`touser_id`) REFERENCES `Auth_user` (`id`)
);


create table Network_ownerbankaccount (
	id int(11) NOT NULL AUTO_INCREMENT,
	groupowner_id int(11) NOT NULL,
	bankname varchar(255) NOT NULL,
	accountnumber varchar(50) NOT NULL,
	ifsccode varchar(10) NOT NULL,
	accountownername varchar(255) NOT NULL,
 	creationdate datetime DEFAULT NULL,
	primary key (`id`),
	FOREIGN KEY (`groupowner_id`) REFERENCES `Auth_user` (`id`)
);

alter table Network_ownerbankaccount add column bankbranch varchar(255) NOT NULL;

alter table Network_post add column posttargettest_id int(11) DEFAULT NULL;

alter table Network_post add column postcontent text DEFAULT NULL;

create table Network_groupjoinrequest (
	id int(11) NOT NULL AUTO_INCREMENT,
	group_id int(11) NOT NULL,
	user_id int(11) NOT NULL,
	requestdate datetime DEFAULT NULL,
	outcome varchar(6) DEFAULT 'open',
	reason text DEFAULT "",
	active boolean default true,
	primary key (`id`),
	FOREIGN KEY (`group_id`) REFERENCES `Network_group` (`id`),
	FOREIGN KEY (`user_id`) REFERENCES `Auth_user` (`id`)
)ENGINE=Innodb;

create table Network_gentlereminder (
	id int(11) NOT NULL AUTO_INCREMENT,
	grpjoinrequest_id int(11) NOT NULL,
	reminderdate datetime DEFAULT NULL,
	primary key(`id`),
	FOREIGN KEY (`grpjoinrequest_id`) REFERENCES `Network_groupjoinrequest` (`id`)
)ENGINE=Innodb;

alter table Network_ownerbankaccount add column group_id INT(11) NOT NULL;

alter table Network_group add column max_tries_allowed INT(11) NOT NULL;

alter table Network_group add column require_owner_permission BOOLEAN DEFAULT FALSE;

alter table Network_group add column currency varchar(3) NOT NULL DEFAULT 'INR';

create table Network_joinrequeststatus(
	id int(11) NOT NULL AUTO_INCREMENT,
	joinrequest_id int(11) NOT NULL,
	payment_status boolean DEFAULT FALSE,
	test_status int(11) DEFAULT 0,
	primary key(`id`),
	FOREIGN KEY (`joinrequest_id`) REFERENCES `Network_groupjoinrequest` (`id`)
)ENGINE=Innodb;

drop table Network_joinrequeststatus;

create table Network_exchangerates(
	id int(11) NOT NULL AUTO_INCREMENT,
	curr_from varchar (4) NOT NULL,
	curr_to varchar(4) NOT NULL,
	conv_rate varchar(20) NOT NULL,
	dateofrate datetime default NULL,
	fetchtime datetime NOT NULL,
	primary key (`id`)
) ENGINE=Innodb;

ALTER table Network_groupjoinrequest add column orderId varchar(60) default '';

alter table Subscription_transaction add column orderId varchar(60) NOT NULL;
alter table Subscription_transaction add column group_id int(11) default NULL;

alter table Subscription_transaction modify column usersession varchar(100) NOT NULL;

alter table Network_groupmember add column `removeagent` varchar(10) default null;
alter table Network_groupmember add column `lastremovaldate` datetime default null;

alter table Network_connectioninvitation modify column invitationstatus varchar(10) default 'open';

alter table Network_post drop column imagefile;
alter table Network_post drop column videofile;
alter table Network_post add column attachmentfile varchar(512) default '';

alter table Network_post add column postmsgtag varchar(255) default '';
alter table Network_post add column createdon datetime not NULL;

alter table Network_post add column newmsg boolean default false;

create table Tests_emailfailure (
    id int(11) NOT NULL AUTO_INCREMENT,
    user_id int(11) NOT NULL,
    sessionid varchar(50) NOT NULL,
    failedemailid varchar(100) NOT NULL,
    script varchar(100) default '',
    failuredatetime datetime NOT NULL,
    failurereason text default '',
    tryagain int(11) default 0,
    primary key (`id`),
    FOREIGN KEY (`user_id`) REFERENCES `Auth_user` (`id`)
)ENGINE=Innodb;

alter table Tests_emailfailure modify sessionid varchar(100) NOT NULL;

alter table Tests_challenge convert to character set utf8mb4;

alter table Tests_usertest add column evalcommitstate boolean default false;
alter table Tests_wouldbeusers add column evalcommitstate boolean default false;

alter table Tests_usertest add column disqualified boolean default false;
alter table Tests_wouldbeusers add column disqualified boolean default false;

create table Auth_optionaluserinfo(
    id int(11) NOT NULL AUTO_INCREMENT,
    user_id int(11) NOT NULL,
    houseno_and_street_address varchar(250) default "",
    city varchar(100) default "",
    pin_or_zip_code varchar(20) default "",
    country varchar(100) default "",
    profession varchar(50) default "student",
    age int(11) default NULL,
    reasonforuse text default "",
    selfdescription text default "",
    highestqualification varchar(50) default "graduate",
    fieldofstudy varchar(100) default "",
    workexperience int(11) default 0,
    presentemployer_or_institution varchar(100) default "",
    primary key (`id`),
    FOREIGN KEY (`user_id`) REFERENCES `Auth_user` (`id`)
)ENGINE=Innodb;

create table Tests_schedule(
    id int(11) NOT NULL AUTO_INCREMENT,
    test_id int(11) NOT NULL,
    slot varchar(100) NOT NULL,
    primary key(`id`),
    FOREIGN KEY (`test_id`) REFERENCES `Tests_test` (`id`)
)ENGINE=Innodb;

alter table Tests_usertest add column schedule_id int(11) default NULL;
alter table Tests_wouldbeusers add column schedule_id int(11) default NULL;	

alter table Tests_schedule add column createdon datetime NOT NULL;

CREATE TABLE `careers` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `position_longname` varchar(200) NOT NULL,
    `position_shortname` varchar(50) NOT NULL,
    `position_code` varchar(10) NOT NULL UNIQUE,
    `position_description` text default "",
    `openingdate` datetime NOT NULL,
    `closingdate` datetime NOT NULL,
    `status` bool NOT NULL,
    `maxsalaryoffered` int(11),
    `maxsalarytimeunit` varchar(20) default "per annum",
    `urgencyindays` integer NOT NULL DEFAULT 30,
    `position_type` varchar(100) DEFAULT "permanent",
    `experiencedesired` integer NOT NULL,
    `skillset` text DEFAULT "",
    `position_location` varchar(200) NOT NULL DEFAULT "New Delhi",
    `department` varchar(200) NOT NULL,
    `position_budget` integer DEFAULT 0,
    `contactperson` varchar(255),
    `submissiondatetime` datetime NOT NULL,
    `conditions` text default ""
);

alter table careers add column contactemail varchar(255) NOT NULL;

create table `Tests_interview` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `title` varchar(200) NOT NULL UNIQUE,
    `challengescount` integer DEFAULT 5,
    `maxresponsestarttime` integer DEFAULT 300,
    `topic_id` integer,
    `topicname` varchar(200),
    `interviewer_id` integer NOT NULL,
    `medium` varchar(15) NOT NULL DEFAULT 'audio',
    `language` varchar(20) NOT NULL DEFAULT 'english',
    `challengeseparatorcharacter` varchar(4) NOT NULL DEFAULT '#',
    `responseendcharacter` varchar(4) NOT NULL DEFAULT '#',
    `createdate` datetime NOT NULL,
    `publishdate` datetime,
    `status` boolean DEFAULT true,
    `maxscore` integer DEFAULT 0,
    `maxduration` integer DEFAULT 3600,
    `randomsequencing` boolean DEFAULT true,
    `interviewlinkid` varchar(200) NOT NULL,
    `scope` varchar(50) NOT NULL DEFAULT 'public',
    `quality` varchar(4) NOT NULL DEFAULT 'INT',
    `challengesfilepath` text NOT NULL,
    `introfilepath` text,
    `filetype` varchar(4) DEFAULT 'wav',
    `realtime` boolean DEFAULT true,
    FOREIGN KEY (`topic_id`) REFERENCES `Tests_topic` (`id`),
    FOREIGN KEY (`interviewer_id`) REFERENCES `Auth_user` (`id`)
)ENGINE=Innodb;

alter table Tests_interview drop index title;

create table `Tests_interviewquestions` (
    `id` INTEGER AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `interview_id` INTEGER NOT NULL,
    `questionfilename` varchar(255) NOT NULL,
    `questionnumber` INTEGER NOT NULL,
    `deleted` BOOLEAN DEFAULT false,
    `maxscore` INTEGER DEFAULT 0,
    `interviewlinkid` varchar(200) NOT NULL,
    `timelimit` INTEGER DEFAULT 600,
    `status` BOOLEAN DEFAULT false,
    FOREIGN KEY (`interview_id`) REFERENCES `Tests_interview` (`id`)
)ENGINE=Innodb;																																	
create table `Tests_interviewresponses` (
    `id` INTEGER AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `interview_id` INTEGER NOT NULL,
    `question_id` INTEGER NOT NULL,
    `interviewlinkid` VARCHAR(200) NOT NULL,
    `responsefilename` VARCHAR(200) DEFAULT '',
    FOREIGN KEY (`interview_id`) REFERENCES `Tests_interview` (`id`),
    FOREIGN KEY (`question_id`) REFERENCES `Tests_interviewquestions` (`id`)
)ENGINE=Innodb;


create table `Tests_interviewcandidates` (
    `id` INTEGER AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `interview_id` INTEGER NOT NULL,
    `emailaddr` VARCHAR (200) NOT NULL,
    `scheduledtime` DATETIME default NULL,
    `actualstarttime` DATETIME default NULL,
    `interviewlinkid` VARCHAR(200) NOT NULL,
    `totaltimetaken` INTEGER DEFAULT NULL,
    FOREIGN KEY (`interview_id`) REFERENCES `Tests_interview` (`id`)
)ENGINE=Innodb;


ALTER table `Tests_interview` drop column `challengeseparatorcharacter`;
ALTER table `Tests_interview` drop column `responseendcharacter`;

ALTER table `Tests_interviewcandidates` add column `interviewurl` text default '';

alter table Tests_interview add column autouploadrecording boolean default True;
alter table Tests_interview drop column autouploadrecording;


create table `Subscription_coupon` (
    `id` INTEGER AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `coupon_code` VARCHAR(100) NOT NULL,
    `coupon_description` VARCHAR (255) DEFAULT "",
    `valid_from` DATETIME DEFAULT NULL,
    `valid_till` DATETIME DEFAULT NULL,
    `discount_value` DOUBLE precision,
    `max_use_count` INTEGER DEFAULT 0,
    `status` BOOLEAN DEFAULT FALSE,
    `currency_unit` VARCHAR(3) DEFAULT "USD"
)ENGINE=Innodb;


alter table Subscription_plan modify column tests integer default 0 not null;
alter table Subscription_plan add column interviews integer default 0 not null;
alter table Subscription_plan add column plandescription text default '';
alter table Subscription_plan add column candidates integer default 0 not null;
alter table Subscription_plan drop foreign key adminuser_id_refs_id_665322f6;
alter table Subscription_plan drop column adminuser_id;
alter table Subscription_plan drop column commissiondate;
alter table Subscription_plan drop column decommissiondate;

alter table Subscription_transaction drop column planname;
alter table Subscription_transaction add column plan_id integer NOT  NULL;

set FOREIGN_KEY_CHECKS=0;
drop table Subscription_plan;
CREATE TABLE `Subscription_plan` (
  id integer AUTO_INCREMENT NOT NULL,
  planname varchar(200) NOT NULL unique,
  tests int(11) NOT NULL DEFAULT '0',
  price decimal(10,2) NOT NULL,
  validfor_unit varchar(12) NOT NULL,
  planvalidfor int(11) NOT NULL,
  status tinyint(1) NOT NULL,
  discountpercent double DEFAULT NULL,
  discountamt double DEFAULT NULL,
  createdate datetime NOT NULL,
  interviews int(11) NOT NULL DEFAULT '0',
  plandescription text,
  candidates int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

create table `Subscription_couponuser` (
    `id` INTEGER AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `coupon_id` INTEGER NOT NULL,
    `user_id` INTEGER NOT NULL,
    `usedate` DATETIME NOT NULL,
    `plan_id` INTEGER NOT NULL,
    FOREIGN KEY (`coupon_id`) REFERENCES `Subscription_coupon` (`id`),
    FOREIGN KEY (`user_id`) REFERENCES `Auth_user` (`id`),
    FOREIGN KEY (`plan_id`) REFERENCES `Subscription_plan` (`id`)
)ENGINE=Innodb;

rename table `Subscription_couponuser` to `Subscription_usercoupon`;

create table `Network_subscriptionearnings` (
    `id` INTEGER AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` INTEGER NOT NULL,
    `balance` INTEGER default 0,
    `earnings` INTEGER default 0,
    `lasttransactdate` datetime NOT NULL,
    FOREIGN KEY (`user_id`) REFERENCES `Auth_user` (`id`)
)ENGINE=Innodb;


create table `Network_grouppaidtransactions` (
    `id` INTEGER AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `group_id` INTEGER NOT NULL,
    `payer_id` INTEGER NOT NULL,
    `amount` INTEGER default 0,
    `currency` VARCHAR(3) default 'USD',
    `transdatetime` DATETIME NOT NULL,
    `payeripaddress` VARCHAR(20) default '',
    FOREIGN KEY (`payer_id`) REFERENCES `Auth_user` (`id`),
    FOREIGN KEY (`group_id`) REFERENCES `Network_group` (`id`)
)ENGINE=Innodb;

SET FOREIGN_KEY_CHECKS=0;
alter table Subscription_usercoupon drop foreign key Subscription_usercoupon_ibfk_3;
alter table Subscription_usercoupon drop column plan_id;
SET FOREIGN_KEY_CHECKS=1;

alter table Subscription_usercoupon add column transaction_id INT, add FOREIGN KEY fk_trans(transaction_id) references Subscription_transaction(id) ON DELETE CASCADE;

alter table Subscription_userplan add column coupon_id INT, add FOREIGN KEY fk_coupon(coupon_id) references Subscription_coupon(id) ON DELETE CASCADE;

alter table Subscription_transaction add column clientIp varchar(20) not NULL;
alter table Subscription_transaction add column extOrderId varchar(40) default '';

alter table Subscription_transaction modify column plan_id int NULL;

create table `Tests_postlinkedin` (
    `id` INTEGER AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `test_id` INTEGER DEFAULT -1,
    `interview_id` INTEGER DEFAULT -1,
    `role` VARCHAR(20) NOT NULL,
    `user_id` INTEGER NOT NULL,
    `sessionid` VARCHAR(50) NOT NULL,
    `csrftoken` VARCHAR(100) NOT NULL,
    `postmessage` TEXT DEFAULT "",
    `current_ts` TIMESTAMP NOT NULL
)ENGINE=Innodb;


create table `Network_withdrawal` (
    `id` INTEGER AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` INTEGER NOT NULL,
    `sessioncode` VARCHAR(150) NOT NULL,
    `securecode` varchar(8) NOT NULL,
    `activitytime` DATETIME NOT NULL
)ENGINE=Innodb;

create table Tests_captcha (
    id int NOT NULL primary key AUTO_INCREMENT,
    captchatext varchar(255) NOT NULL,
    captchakey varchar(50) NOT NULL,
    captchatime DATETIME NOT NULL,
    success BOOLEAN default FALSE,
    validityperiod int NOT NULL DEFAULT 90
)ENGINE=Innodb;



alter table Tests_interview add column scheduledtime datetime default NULL;

alter table Tests_interview add column interviewers_count int(8) default 1;
alter table Tests_interview add column interviewer_ids varchar(200) default NULL;

alter table Tests_interview modify column interviewer_ids  text default '';

alter table Tests_challenge add column proglang varchar(200) default '';

alter table Tests_usertest add column windowchangeattempts int(8) default 0;
alter table Tests_wouldbeusers add column windowchangeattempts int(8) default 0;

alter table Network_ownerbankaccount modify column ifsccode varchar(25);

CREATE TABLE Network_wepay (id int(8) NOT NULL AUTO_INCREMENT PRIMARY KEY, user_id int NOT NULL, access_token varchar(200) default "", token_type varchar(20) default "bearer", access_token_expires int(8), wepay_state varchar(200) default "", wepay_user_id int(8) default -1, wepay_authorized BOOLEAN default False, ownerbankaccount_id int(8) NOT NULL, create_datetime Datetime NOT NULL, FOREIGN KEY(user_id) REFERENCES Auth_user(id), FOREIGN KEY (ownerbankaccount_id) REFERENCES Network_ownerbankaccount(id));

alter table Network_withdrawal add column securecodestatus boolean not null default true

alter table Network_wepay add column code varchar(200);
alter table Network_withdrawal add column wepaycode varchar(255);
alter table Network_wepay add column wepayacctid varchar(255) default "";
alter table Network_wepay modify column wepay_user_id bigint;

alter table Network_ownerbankaccount add column razor_account_id varchar(100) default "";
alter table Network_withdrawal add column razorpaycode varchar(200) default "";

create table Network_razorpaytransaction (id int NOT NULL PRIMARY KEY AUTO_INCREMENT, bankacct_id INT NOT NULL, recipient_id INT NOT NULL, amount double NOT NULL DEFAULT 0.00, currency varchar(20) DEFAULT "INR", on_hold boolean default False, tax double default 0.00, fees double default 0.00, trxtimestamp INT(11) NOT NULL, FOREIGN KEY (bankacct_id) REFERENCES Network_ownerbankaccount(id),  FOREIGN KEY (recipient_id) REFERENCES Auth_user(id));

alter table Network_razorpaytransaction add column source varchar(50) NOT NULL;
alter table Network_razorpaytransaction add column recipient_merchant_id varchar(50) NOT NULL;

alter table Network_group add column subscription_fee float default 0.00;

alter table Network_grouppaidtransactions add column targetperiod datetime;
alter table Network_grouppaidtransactions add column reason varchar(25) ;
alter table Network_grouppaidtransactions add CONSTRAINT chk_reason CHECK (reason in ('entryfee', 'subscriptionfee'));

alter table Network_grouppaidtransactions add column stripechargeid varchar(35);
alter table Subscription_transaction add column txnid_stripe varchar(35);

alter table Network_groupmember add column grppaidtxn_id int(8) default null, ADD FOREIGN KEY fk_grppaidtxn(grppaidtxn_id) REFERENCES Network_grouppaidtransactions(id) ON DELETE CASCADE;

alter table Network_subscriptionearnings add column grppaidtxn_id int(8) default null, ADD FOREIGN KEY fk_grppaidtxn2(grppaidtxn_id) REFERENCES Network_grouppaidtransactions(id) ON DELETE CASCADE;

COMMIT;

