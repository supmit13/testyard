-- MySQL dump 10.13  Distrib 5.5.32, for debian-linux-gnu (i686)
--
-- Host: localhost    Database: testyard
-- ------------------------------------------------------
-- Server version	5.5.32-0ubuntu0.12.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `Auth_emailvalidationkey`
--

DROP TABLE IF EXISTS `Auth_emailvalidationkey`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Auth_emailvalidationkey` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `email` varchar(75) NOT NULL,
  `vkey` varchar(50) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `vkey` (`vkey`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Auth_privilege`
--

DROP TABLE IF EXISTS `Auth_privilege`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Auth_privilege` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `privname` varchar(50) NOT NULL,
  `privdesc` longtext NOT NULL,
  `createdate` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `privname` (`privname`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Auth_session`
--

DROP TABLE IF EXISTS `Auth_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Auth_session` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sessioncode` varchar(150) NOT NULL,
  `status` tinyint(1) NOT NULL,
  `userid_id` int(11) NOT NULL,
  `starttime` datetime NOT NULL,
  `endtime` datetime DEFAULT NULL,
  `sourceip` char(39) NOT NULL,
  `istest` tinyint(1) NOT NULL,
  `useragent` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `sessioncode` (`sessioncode`),
  KEY `Auth_session_e2fd1d24` (`userid_id`),
  CONSTRAINT `userid_id_refs_id_640456e3` FOREIGN KEY (`userid_id`) REFERENCES `Auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=65 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Auth_user`
--

DROP TABLE IF EXISTS `Auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `firstname` varchar(100) NOT NULL,
  `middlename` varchar(20) NOT NULL,
  `lastname` varchar(100) NOT NULL,
  `displayname` varchar(100) NOT NULL,
  `password` varchar(100) NOT NULL,
  `emailid` varchar(75) NOT NULL,
  `active` tinyint(1) NOT NULL,
  `istest` tinyint(1) NOT NULL,
  `joindate` datetime NOT NULL,
  `sex` varchar(3) NOT NULL,
  `usertype` varchar(4) NOT NULL,
  `mobileno` varchar(12) NOT NULL,
  `userpic` varchar(100) NOT NULL,
  `newuser` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `displayname` (`displayname`),
  UNIQUE KEY `emailid` (`emailid`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Auth_userprivilege`
--

DROP TABLE IF EXISTS `Auth_userprivilege`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Auth_userprivilege` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `userid_id` int(11) NOT NULL,
  `privilegeid_id` int(11) NOT NULL,
  `lastmod` datetime NOT NULL,
  `status` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `Auth_userprivilege_e2fd1d24` (`userid_id`),
  KEY `Auth_userprivilege_b05dc53f` (`privilegeid_id`),
  CONSTRAINT `privilegeid_id_refs_id_a9cfb08` FOREIGN KEY (`privilegeid_id`) REFERENCES `Auth_privilege` (`id`),
  CONSTRAINT `userid_id_refs_id_42ace1b3` FOREIGN KEY (`userid_id`) REFERENCES `Auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Subscription_plan`
--

DROP TABLE IF EXISTS `Subscription_plan`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Subscription_plan` (
  `planname` varchar(200) NOT NULL,
  `tests` varchar(200) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `validfor_unit` varchar(12) NOT NULL,
  `planvalidfor` int(11) NOT NULL,
  `adminuser_id` int(11) NOT NULL,
  `status` tinyint(1) NOT NULL,
  `discountpercent` double DEFAULT NULL,
  `discountamt` double DEFAULT NULL,
  `createdate` datetime NOT NULL,
  `commissiondate` datetime DEFAULT NULL,
  `decommissiondate` datetime DEFAULT NULL,
  PRIMARY KEY (`planname`),
  KEY `Subscription_plan_4e201023` (`adminuser_id`),
  CONSTRAINT `adminuser_id_refs_id_665322f6` FOREIGN KEY (`adminuser_id`) REFERENCES `Auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Subscription_transaction`
--

DROP TABLE IF EXISTS `Subscription_transaction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Subscription_transaction` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(100) NOT NULL,
  `user_id` int(11) NOT NULL,
  `planname` varchar(200) DEFAULT NULL,
  `usersession` varchar(50) NOT NULL,
  `payamount` decimal(10,2) NOT NULL,
  `transactiondate` datetime NOT NULL,
  `comments` longtext NOT NULL,
  `paymode` varchar(50) NOT NULL,
  `invoice_email` varchar(75) NOT NULL,
  `trans_status` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `Subscription_transaction_fbfc09f1` (`user_id`),
  CONSTRAINT `user_id_refs_id_8c4721ea` FOREIGN KEY (`user_id`) REFERENCES `Auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Subscription_userplan`
--

DROP TABLE IF EXISTS `Subscription_userplan`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Subscription_userplan` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `plan_id` varchar(200) NOT NULL,
  `user_id` int(11) NOT NULL,
  `totalcost` decimal(10,2) NOT NULL,
  `amountpaid` decimal(10,2) NOT NULL,
  `amountdue` decimal(10,2) NOT NULL,
  `lastpaydate` datetime NOT NULL,
  `planstartdate` datetime NOT NULL,
  `planenddate` datetime DEFAULT NULL,
  `planstatus` tinyint(1) NOT NULL,
  `subscribedon` datetime DEFAULT NULL,
  `discountpercentapplied` double DEFAULT NULL,
  `discountamountapplied` double DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `Subscription_userplan_a57fd7f1` (`plan_id`),
  KEY `Subscription_userplan_fbfc09f1` (`user_id`),
  CONSTRAINT `plan_id_refs_planname_47f755ee` FOREIGN KEY (`plan_id`) REFERENCES `Subscription_plan` (`planname`),
  CONSTRAINT `user_id_refs_id_34f93f73` FOREIGN KEY (`user_id`) REFERENCES `Auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Tests_challenge`
--

DROP TABLE IF EXISTS `Tests_challenge`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Tests_challenge` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `test_id` int(11) NOT NULL,
  `statement` longtext NOT NULL,
  `challengetype` varchar(4) NOT NULL,
  `option1` longtext,
  `option2` longtext,
  `option3` longtext,
  `option4` longtext,
  `option5` longtext,
  `option6` longtext,
  `challengescore` double NOT NULL,
  `negativescore` double NOT NULL,
  `mustrespond` tinyint(1) NOT NULL,
  `responsekey` longtext NOT NULL,
  `imageurl` varchar(200) DEFAULT NULL,
  `additionalurl` varchar(200) DEFAULT NULL,
  `timeframe` int(11) DEFAULT NULL,
  `subtopic_id` int(11) NOT NULL,
  `challengequality` varchar(3) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `Tests_challenge_a88de8dc` (`test_id`),
  KEY `Tests_challenge_d50c7adf` (`subtopic_id`),
  CONSTRAINT `subtopic_id_refs_id_5e9d0e88` FOREIGN KEY (`subtopic_id`) REFERENCES `Tests_subtopic` (`id`),
  CONSTRAINT `test_id_refs_id_7584e499` FOREIGN KEY (`test_id`) REFERENCES `Tests_test` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Tests_evaluator`
--

DROP TABLE IF EXISTS `Tests_evaluator`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Tests_evaluator` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `evalgroupname` varchar(150) NOT NULL,
  `groupmember1_id` int(11) DEFAULT NULL,
  `groupmember2_id` int(11) DEFAULT NULL,
  `groupmember3_id` int(11) DEFAULT NULL,
  `groupmember4_id` int(11) DEFAULT NULL,
  `groupmember5_id` int(11) DEFAULT NULL,
  `groupmember6_id` int(11) DEFAULT NULL,
  `groupmember7_id` int(11) DEFAULT NULL,
  `groupmember8_id` int(11) DEFAULT NULL,
  `groupmember9_id` int(11) DEFAULT NULL,
  `groupmember10_id` int(11) DEFAULT NULL,
  `creationdate` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `Tests_evaluator_769457e8` (`groupmember1_id`),
  KEY `Tests_evaluator_c640b8f` (`groupmember2_id`),
  KEY `Tests_evaluator_8f6f439a` (`groupmember3_id`),
  KEY `Tests_evaluator_b166ba03` (`groupmember4_id`),
  KEY `Tests_evaluator_279bd2e4` (`groupmember5_id`),
  KEY `Tests_evaluator_7873711d` (`groupmember6_id`),
  KEY `Tests_evaluator_3efef4da` (`groupmember7_id`),
  KEY `Tests_evaluator_f179706f` (`groupmember8_id`),
  KEY `Tests_evaluator_243e590` (`groupmember9_id`),
  KEY `Tests_evaluator_b69a883b` (`groupmember10_id`),
  CONSTRAINT `groupmember10_id_refs_id_431af34a` FOREIGN KEY (`groupmember10_id`) REFERENCES `Auth_user` (`id`),
  CONSTRAINT `groupmember1_id_refs_id_431af34a` FOREIGN KEY (`groupmember1_id`) REFERENCES `Auth_user` (`id`),
  CONSTRAINT `groupmember2_id_refs_id_431af34a` FOREIGN KEY (`groupmember2_id`) REFERENCES `Auth_user` (`id`),
  CONSTRAINT `groupmember3_id_refs_id_431af34a` FOREIGN KEY (`groupmember3_id`) REFERENCES `Auth_user` (`id`),
  CONSTRAINT `groupmember4_id_refs_id_431af34a` FOREIGN KEY (`groupmember4_id`) REFERENCES `Auth_user` (`id`),
  CONSTRAINT `groupmember5_id_refs_id_431af34a` FOREIGN KEY (`groupmember5_id`) REFERENCES `Auth_user` (`id`),
  CONSTRAINT `groupmember6_id_refs_id_431af34a` FOREIGN KEY (`groupmember6_id`) REFERENCES `Auth_user` (`id`),
  CONSTRAINT `groupmember7_id_refs_id_431af34a` FOREIGN KEY (`groupmember7_id`) REFERENCES `Auth_user` (`id`),
  CONSTRAINT `groupmember8_id_refs_id_431af34a` FOREIGN KEY (`groupmember8_id`) REFERENCES `Auth_user` (`id`),
  CONSTRAINT `groupmember9_id_refs_id_431af34a` FOREIGN KEY (`groupmember9_id`) REFERENCES `Auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Tests_sharetest`
--

DROP TABLE IF EXISTS `Tests_sharetest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Tests_sharetest` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `testcreator_id` int(11) NOT NULL,
  `sharedwith_id` int(11) NOT NULL,
  `sharedatetime` datetime NOT NULL,
  `test_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `Tests_sharetest_c967e5f7` (`testcreator_id`),
  KEY `Tests_sharetest_e4aa393d` (`sharedwith_id`),
  KEY `Tests_sharetest_a88de8dc` (`test_id`),
  CONSTRAINT `sharedwith_id_refs_id_8687dad0` FOREIGN KEY (`sharedwith_id`) REFERENCES `Auth_user` (`id`),
  CONSTRAINT `testcreator_id_refs_id_8687dad0` FOREIGN KEY (`testcreator_id`) REFERENCES `Auth_user` (`id`),
  CONSTRAINT `test_id_refs_id_31f72e13` FOREIGN KEY (`test_id`) REFERENCES `Tests_test` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Tests_subtopic`
--

DROP TABLE IF EXISTS `Tests_subtopic`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Tests_subtopic` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `subtopicname` varchar(150) NOT NULL,
  `subtopicshortname` varchar(50) NOT NULL,
  `topic_id` int(11) NOT NULL,
  `createdate` date NOT NULL,
  `isactive` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `Tests_subtopic_57732028` (`topic_id`),
  CONSTRAINT `topic_id_refs_id_bf3a8054` FOREIGN KEY (`topic_id`) REFERENCES `Tests_topic` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Tests_test`
--

DROP TABLE IF EXISTS `Tests_test`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Tests_test` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `testname` varchar(150) NOT NULL,
  `subtopic_id` int(11) NOT NULL,
  `creator_id` int(11) NOT NULL,
  `creatorisevaluator` tinyint(1) NOT NULL,
  `evaluator_id` int(11) DEFAULT NULL,
  `testtype` varchar(4) NOT NULL,
  `createdate` datetime NOT NULL,
  `maxscore` int(11) NOT NULL,
  `passscore` int(11) NOT NULL,
  `ruleset` varchar(4) NOT NULL,
  `duration` int(11) NOT NULL,
  `allowedlanguages` varchar(4) NOT NULL,
  `challengecount` int(11) NOT NULL,
  `activationdate` datetime NOT NULL,
  `status` tinyint(1) NOT NULL,
  `quality` varchar(4) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `Tests_test_d50c7adf` (`subtopic_id`),
  KEY `Tests_test_f97a5119` (`creator_id`),
  KEY `Tests_test_170dea88` (`evaluator_id`),
  CONSTRAINT `creator_id_refs_id_d29f6b50` FOREIGN KEY (`creator_id`) REFERENCES `Auth_user` (`id`),
  CONSTRAINT `evaluator_id_refs_id_c4cea575` FOREIGN KEY (`evaluator_id`) REFERENCES `Tests_evaluator` (`id`),
  CONSTRAINT `subtopic_id_refs_id_ae9af74e` FOREIGN KEY (`subtopic_id`) REFERENCES `Tests_subtopic` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Tests_topic`
--

DROP TABLE IF EXISTS `Tests_topic`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Tests_topic` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `topicname` varchar(150) NOT NULL,
  `createdate` date NOT NULL,
  `isactive` tinyint(1) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Tests_userresponse`
--

DROP TABLE IF EXISTS `Tests_userresponse`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Tests_userresponse` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `test_id` int(11) NOT NULL,
  `challenge_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `answer` longtext,
  `responsedatetime` datetime DEFAULT NULL,
  `attachments` varchar(100) DEFAULT NULL,
  `evaluation` double DEFAULT NULL,
  `evaluator_remarks` longtext,
  `evaluated_by_id` int(11) NOT NULL,
  `candidate_comment` longtext,
  `response_quality` varchar(3) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `Tests_userresponse_a88de8dc` (`test_id`),
  KEY `Tests_userresponse_dd8bebce` (`challenge_id`),
  KEY `Tests_userresponse_fbfc09f1` (`user_id`),
  KEY `Tests_userresponse_d20e438b` (`evaluated_by_id`),
  CONSTRAINT `challenge_id_refs_id_5cfa8871` FOREIGN KEY (`challenge_id`) REFERENCES `Tests_challenge` (`id`),
  CONSTRAINT `evaluated_by_id_refs_id_dfa3cedc` FOREIGN KEY (`evaluated_by_id`) REFERENCES `Auth_user` (`id`),
  CONSTRAINT `test_id_refs_id_4ce9e81f` FOREIGN KEY (`test_id`) REFERENCES `Tests_test` (`id`),
  CONSTRAINT `user_id_refs_id_dfa3cedc` FOREIGN KEY (`user_id`) REFERENCES `Auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `Tests_usertest`
--

DROP TABLE IF EXISTS `Tests_usertest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Tests_usertest` (
  `user_id` int(11) DEFAULT NULL,
  `emailaddr` varchar(75) NOT NULL,
  `testurl` varchar(200) NOT NULL,
  `test_id` int(11) NOT NULL,
  `validfrom` datetime NOT NULL,
  `validtill` datetime NOT NULL,
  `status` int(11) NOT NULL,
  `outcome` tinyint(1) DEFAULT NULL,
  `score` double NOT NULL,
  `starttime` datetime NOT NULL,
  `endtime` datetime NOT NULL,
  `ipaddress` char(39) NOT NULL,
  `clientsware` varchar(150) NOT NULL,
  `sessid` varchar(50) NOT NULL,
  PRIMARY KEY (`testurl`),
  KEY `Tests_usertest_fbfc09f1` (`user_id`),
  KEY `Tests_usertest_a88de8dc` (`test_id`),
  CONSTRAINT `test_id_refs_id_68cc46a6` FOREIGN KEY (`test_id`) REFERENCES `Tests_test` (`id`),
  CONSTRAINT `user_id_refs_id_4487dbd7` FOREIGN KEY (`user_id`) REFERENCES `Auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

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

/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2012-09-01 13:17:22
