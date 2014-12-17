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
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY
)
;
COMMIT;

