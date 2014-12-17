import os, sys, re, time

TEST_TOPICS = ("Programming", "Project Management", "Database Management", "Quality Assurance", \
               "Software Testing", "Business Development", "Product Development", "Customer Service",\
               "Software Architecture", "Delivery Management", "System Administration", "System Analyst",\
               "UI Design", "Web Design", "Application Development")

TEST_TYPES = ("Multiple Choice", "Fill up the Blanks", "Subjective", "Coding", "Algorithm", "Composite")
# A 'composite' test is test that contains more than one of the  other TEST_TYPES. The default choice is 'composite'.

TEST_SEARCH_SCOPE = ("Public Tests Only", "Only Tests Accessible by the Recruiter", "Private Tests Only", "All Tests")

BLACKLISTED_MEMBERS = ()

COMPILER_LOCATIONS = {'C' : '/usr/bin/gcc', \
                         'Perl' : '/usr/bin/perl', \
                         'Python' : '/home/supriyo/work/testyard/pyenv/bin/python', \
                         'Ruby' : '/usr/local/bin/ruby', \
                         'Curl' : '/usr/bin/curl', \
                         'Bash' : '/bin/bash', \
                         'Cshell' : '/bin/csh', \
                         'C++' : '/usr/bin/g++', \
                         'C#' : '/usr/bin/mono', \
                         'Java' : '/usr/bin/java', \
                         'JavaScript' : '/usr/bin/js', \
                         'Lua' : '/usr/local/bin/lua', \
                         'Objective-C' : '/usr/bin/clang', \
                         'PHP' : '/usr/bin/php5', \
                         'VB.NET' : '', \
                         'VBScript' : '', \
                         'Pascal' : '/usr/local/bin/fpc', \
                         'Fortran' : '/usr/bin/gfortran', \
                         'Lisp' : '', \
                         'SmallTalk' : '', \
                         'Scala' : '', \
                         'Tcl' : '/usr/bin/tclsh', \
                         'Ada95' : '', \
                         'Delphi' : '', \
                         'ColdFusion' : '',}
 

SESSION_EXPIRY_LIMIT = { 'CORP' : 86400, \
                         'CONS' : 86400, \
                         'ACAD' : 86400, \
                         'CERT' : 86400, }


