BEGIN;
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
COMMIT;
