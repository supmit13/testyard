import os, sys, re, time

TEST_TOPICS = ("Programming", "Project Management", "Database Management", "Quality Assurance", \
               "Software Testing", "Business Development", "Product Development", "Customer Service",\
               "Software Architecture", "Delivery Management", "System Administration", "System Analyst",\
               "UI Design", "Web Design", "Application Development")

TEST_TYPES = { 'MULT' : "Multiple Choice", 'FILB' : "Fill up the Blanks", 'SUBJ' :  "Subjective", 'CODN' : "Coding", 'ALGO' : "Algorithm", 'COMP' : "Composite"}
# A 'composite' test is test that contains more than one of the  other TEST_TYPES. The default choice is 'composite'.

TEST_SEARCH_SCOPE = ("Public", "Protected", "Private Tests Only", "All Tests")
"""
For now, we will keep all 'Test's private to the 'User' creating the 'Test'. 'Challenges' belonging to
a 'Test' are  searchable and viewable by all, but the 'Test' and the 'UserResponse'es are viewable by
the creator of the 'Test' only. So, 'TEST_SEARCH_SCOPE' will not be used for the first cut.
"""


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
 
# Some application related variables:
PROFILE_PHOTO_NAME = "profilepic"
PROFILE_PHOTO_EXT = ( "gif", "jpg", "jpeg", "png", "tiff", "tif" )

# Max size of file that may be uploaded by user
MAX_FILE_SIZE_ALLOWED = 10000000

"""
Passwords should have atleast this grade in a scale of 1 to 5.
Password strength is gauged by "check_passwd_strength()" function
(in static/pageutils.js) in frontend and by "check_password_strength()"
function (in skillstest/utils.py) in backend.
"""
MIN_ALLOWABLE_PASSWD_STRENGTH = 3

SESSION_EXPIRY_LIMIT = { 'CORP' : 86400, \
                         'CONS' : 86400, \
                         'ACAD' : 86400, \
                         'CERT' : 86400, }


LOGIN_URL = "skillstest/login/"
REGISTER_URL = "skillstest/newuser/"
DASHBOARD_URL = "skillstest/dashboard/"
PROFILE_URL = "skillstest/"
SUBSCRIPTION_URL = "skillstest/subscriptions/"
LOGIN_REDIRECT_URL = PROFILE_URL
CREATE_TEST_URL = "skillstest/create/"
EDIT_TEST_URL = "skillstest/edit/"
MANAGE_TEST_URL = "skillstest/manage/"
SEARCH_URL = "skillstest/search/"

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
        '&#39;' : '"',\
    }

EMAIL_PATTERN = re.compile(r"[\w\.]*@[\w\.]+")
MULTIPLE_WS_PATTERN = re.compile(r"^\s*$", re.MULTILINE | re.DOTALL)
PHONENUM_PATTERN = re.compile(r"^\d+$", re.MULTILINE | re.DOTALL)
REALNAME_PATTERN = re.compile(r"^([a-zA-Z\s]+)$", re.MULTILINE | re.DOTALL)

RULES_DICT = {} # Dictionary containing all rules that may be imposed on a test.

ANSWER_LANG_DICT = { 'enus' : 'English - US', 'enuk' : 'English', 'lat' : 'Latin', 'fr' : 'French', 'hndi' : 'Hindi' } # Allowed languages

SKILL_QUALITY = { 'BEG' : 'Beginner', 'INT' : 'Intermediate', 'PRO' : 'Proficient' }

PLAN_GUIDELINES = {} # A map of test types, duration, and their  associated costs - used in Subscription.model

PAYMENT_PLATFORMS = {}

# LinkedIn OAuth Details:
APP_NAME = 'TestYard'
OAUTH_API_KEY = '78wxi7pqmstzbg'
OAUTH_SECRET_KEY = 'fNRod3yXxOllBwJD'
OAUTH_USER_TOKEN = '9f88127b-21fb-46fb-8235-e3fe8ca05e5b'
OAUTH_USER_SECRET = '042a5b7c-2261-4979-b0c1-36ddfaec19b2'

