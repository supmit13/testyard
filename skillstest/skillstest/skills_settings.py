import os, sys, re, time

TEST_TOPICS = ("Programming", "Project Management", "Database Management", "Quality Assurance", \
               "Software Testing", "Business Development", "Product Development", "Customer Service",\
               "Software Architecture", "Delivery Management", "System Administration", "System Analyst",\
               "UI Design", "Web Design", "Application Development", "Other")

# Keys of the following dict should NOT be multi-word strings.
TEST_TYPES = { 'MULT' : "Multiple Choice", 'FILB' : "Fill up the Blanks", 'SUBJ' :  "Subjective", 'CODN' : "Coding", 'ALGO' : "Algorithm", 'COMP' : "Composite"}
# A 'composite' test is test that contains more than one of the  other TEST_TYPES. The default choice is 'composite'.

TEST_SCOPES = ( 'public', 'protected', 'private' )

TEST_SEARCH_SCOPE = ("Public", "Protected", "Private Tests Only", "All Tests")
"""
For now, we will keep all 'Test's private to the 'User' creating the 'Test'. 'Challenges' belonging to
a 'Test' are  searchable and viewable by all, but the 'Test' and the 'UserResponse'es are viewable by
the creator of the 'Test' only. So, 'TEST_SEARCH_SCOPE' will not be used for the first cut.
"""


BLACKLISTED_MEMBERS = ()

# The keys in the following dict should NOT be multi-word strings.
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
PROFILE_PHOTO_HEIGHT = 102 # in pixels
PROFILE_PHOTO_WIDTH = 102 # in pixels

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


URL_PROTOCOL = "http://"

# Email settings
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'codexaddict@gmail.com'
EMAIL_HOST_PASSWORD = 'xtmt365i'
EMAIL_USE_TLS = True

MAILSENDER = "test@testyard.com"


LOGIN_URL = "skillstest/login/"
REGISTER_URL = "skillstest/newuser/"
DASHBOARD_URL = "skillstest/dashboard/"
PROFILE_URL = "skillstest/profile/"
SUBSCRIPTION_URL = "skillstest/subscriptions/"
LOGIN_REDIRECT_URL = PROFILE_URL
CREATE_TEST_URL = "skillstest/tests/create/"
EDIT_TEST_URL = "skillstest/tests/edit/"
MANAGE_TEST_URL = "skillstest/tests/"
INVITATION_ACTIVATION_URL = "skilltest/test/invitation/activation/"
INVITATION_CANCEL_URL = "skilltest/test/invitation/cancellation/"
TEST_SUMMARY_URL = "skillstest/tests/summary/"
DELETE_CHALLENGE_URL = "skillstest/tests/challenges/delete/"
SAVE_CHANGES_URL = "skillstest/tests/challenges/savechanges/"
ADD_MORE_URL = "skillstest/tests/challenges/addmore/"
EDIT_EXISTING_TEST_URL = "skillstest/tests/editexistingtest/"
VIEW_TEST_URL = "skillstest/tests/viewtest/"
MANAGE_INVITATIONS_URL = "skillstest/tests/invitations/manage/"
SEARCH_URL = "skillstest/tests/search/"
NETWORK_URL = "skillstest/network/"
ANALYTICS_URL = "skillstest/analytics/"
ABOUTUS_URL = "skillstest/aboutus/"
HELP_URL = "skillstest/helpndoc/"
CAREER_URL = "skillstest/careers/"
LOGOUT_URL = "skillstest/logout/"
availabilityURL = "skillstest/checkavail/"
ACCTACTIVATION_URL = "skillstest/activate/"
PROFIMG_CHANGE_URL = "/skillstest/changeimg/"
CLEAR_NEGATIVE_SCORE_URL = "skillstest/tests/clearnegscore/"
DELETE_TEST_URL = "skillstest/tests/deletetest/"
SHOW_USER_VIEW_URL = "skillstest/tests/challenge/showuserview/"
EDIT_CHALLENGE_URL = "skillstest/tests/challenge/edit/"
SHOW_TEST_CANDIDATE_MODE_URL = "skillstest/test/showtestcandidatemode/"
SEND_TEST_INVITATION_URL = "skillstest/test/sendtestinvitations/"
SEND_TEST_DATA_URL = "skillstest/test/sendtestdata/"
TEST_EVALUATION_URL = "skillstest/test/evaluate/"
EVALUATE_RESPONSE_URL = "skillstest/test/assessresponse/"
GET_CURRENT_EVALUATION_DATA_URL = "skillstest/test/getcurrentevaldata/"
TEST_BULK_UPLOAD_URL = "skillstest/test/bulkupload/"

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

INV_HEXCODE_CHAR_MAP = { \
        " " : '%20', \
        "'" : '%27', \
	'"' : '%22', \
	'$' : '%24', \
	'&' : '%26', \
	'*' : '%2A', \
	'+' : '%2B', \
	'.' : '%2E', \
	'/' : '%2F', \
    }

INV_HTML_ENTITIES_CHAR_MAP = { \
	'<' : '&lt;', \
	'>' : '&gt;', \
	'&' : '&amp;', \
	' ' : '&nbsp;', \
	'"' : '&quot;', \
	'[' : '&#91;', \
	']' : '&#93;', \
	'"' : '&#39;', \
    }

EMAIL_PATTERN = re.compile("[\w\.]*\@[\w\.]*", re.MULTILINE|re.DOTALL)
MULTIPLE_WS_PATTERN = re.compile(r"^\s*$", re.MULTILINE | re.DOTALL)
PHONENUM_PATTERN = re.compile(r"^\d+$", re.MULTILINE | re.DOTALL)
REALNAME_PATTERN = re.compile(r"^([a-zA-Z\s]*)$", re.MULTILINE | re.DOTALL)

# Number of days after which you cannot modify an evaluation. This is counted from the time at which you evaluate a test for the first time.
NUM_DAYS_EVALUATION_COMMIT = 10

# Dictionary containing all rules that may be imposed on a test.
RULES_DICT = { \
        'breaknotallowed' : 'Breaks are NOT allowed while taking the test', \
        'responsenoreturn' : 'Responded challenges may not be revisited', \
        'norevisit' : 'Attempted challenges may not be revisited', \
        'showatonce' : 'Show all challenges at the begining of the test', \
        'allowchallengenavigation' : 'Allow user to navigate between challenges', \
        }

ANSWER_LANG_DICT = { 'enus' : 'English - US', 'enuk' : 'English - UK', 'lat' : 'Latin', 'fr' : 'French', \
                     'hndi' : 'Hindi', 'bngw' : 'Bengali - WB', 'bnge' : 'Bengali - Bangladesh', } # Allowed languages

SKILL_QUALITY = { 'BEG' : 'Beginner', 'INT' : 'Intermediate', 'PRO' : 'Proficient' }

PLAN_GUIDELINES = {} # A map of test types, duration, and their  associated costs - used in Subscription.models

PAYMENT_PLATFORMS = {}

# LinkedIn OAuth Details:
APP_NAME = 'TestYard'
OAUTH_API_KEY = '78wxi7pqmstzbg'
OAUTH_SECRET_KEY = 'fNRod3yXxOllBwJD'
OAUTH_USER_TOKEN = '9f88127b-21fb-46fb-8235-e3fe8ca05e5b'
OAUTH_USER_SECRET = '042a5b7c-2261-4979-b0c1-36ddfaec19b2'

# Number of complimentary tests a newly registered user can conduct:
NEW_USER_FREE_TESTS_COUNT = 7
# Types of tests the user can conduct as part of complimentary test:
NEW_USER_FREE_TESTS_TYPES = 'MULT|FILB|SUBJ|CODN|ALGO|COMP'

MONTHS_DICT = {'JAN' : '01', 'FEB' : '02', 'MAR' : '03', 'APR' : '04', 'MAY' : '05', 'JUN' : '06', 'JUL' : '07', 'AUG' : '08', 'SEP' : '09', 'OCT' : '10', 'NOV' : '11', 'DEC' : '12'}
REV_MONTHS_DICT = {'01' : 'JAN', '02' : 'FEB', '03' : 'MAR', '04' : 'APR', '05' : 'MAY', '06' : 'JUN', '07' : 'JUL', '08' : 'AUG', '09' : 'SEP', '10' : 'OCT', '11' : 'NOV', '12' : 'DEC'}

SEPARATOR_PATTERN = re.compile('#||#', re.MULTILINE|re.DOTALL)
DES3_SECRET_KEY = 'fNRod3yXxOllBwJD' # AES key must be either 16, 24, or 32 bytes long

# Bitly Details:
BITLY_OAUTH_ACCESS_TOKEN = "3e39f615e31db424691323ba1cfcbe759deade18"
BITLY_LINK_API_ADDRESS = "https://api-ssl.bitly.com"

LOG_PATH = "/home/supriyo/work/testyard/logs"

# Private networks needs the owner to allow members to be a part of it. Open networks may be joined by anyone. A hidden network will not
# be listed by a search of the network by its name, but accessing its page will allow an user to request its owner to allow her/him in 
# the network. A hidden network is also private in nature.
NETWORK_TYPES_LIST = { 'PRIV' : 'Private', 'OPEN' : 'Public', 'HIDN' : 'Hidden' } 


