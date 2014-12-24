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


LOGIN_URL = "skillstest/login/"
REGISTER_URL = "skillstest/newuser/"
DASHBOARD_URL = "skillstest/dashboard/"
LOGIN_REDIRECT_URL = DASHBOARD_URL

TEST_RUN = False # Set this to True during testing the app.

HEXCODE_CHAR_MAP = { \
        '%20' : " ", \
        '%27' : "'", \
        '%22' : '"', \
        '%24' : '$', \
        '%25' : '%', \
        '%26' : '&', \
        '%2A' : '*', \
        '%2B' : '+', \
        '%2E' : '.', \
        '%2F' : '/', \
    }

HTML_ENTITIES_CHAR_MAP = { \
        '&lt;' : '<', \
        '&gt;' : '>', \
        '&amp;': '&', \
        '&nbsp;' : ' ', \
        '&quot;' : '"', \
        '&#91;' : '[', \
        '&#93;' : ']', \
    }

EMAIL_PATTERN = re.compile(r"[\w\.]*@[\w\.]+")
MULTIPLE_WS_PATTERN = re.compile(r"^\s*$", re.MULTILINE | re.DOTALL)
PHONENUM_PATTERN = re.compile(r"^\d+$", re.MULTILINE | re.DOTALL)
REALNAME_PATTERN = re.compile(r"^([a-zA-Z\s]+)$", re.MULTILINE | re.DOTALL)
