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

COMMIT;
