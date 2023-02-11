import os, sys, re, time


BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

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
                         'Python' : '/home/supriyo/work/ty_newiface/pyenv/bin/python', \
                         'Python3' : '', \
                         'Ruby' : '/usr/local/bin/ruby', \
                         'Curl' : '/usr/bin/curl', \
                         'Bash' : '/bin/bash', \
                         'Cshell' : '/bin/csh', \
                         'C++' : '/usr/bin/g++', \
                         'C#' : '/usr/bin/mono', \
                         'F#' : '/usr/bin/fsharp', \
                         'Go' : '/usr/bin/go', \
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
                         'Rust' : '', \
                         'Scheme' : '', \
                         'Swift' : '', \
                         'ColdFusion' : '',}

CODE_EXECUTE_SERVICE_HOST = "127.0.0.1"
CODE_EXECUTE_SERVICE_PORT = 5555
SOCK_CONN_CREATE_TIMEOUT = 60 # timeout is 1 minute

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

###### HTTPS SETTINGS ######
URL_PROTOCOL = "https://"
APP_URL_PREFIX = "https://testyard.in/"

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_EXPIRE_AT_BROWSER_CLOSE=True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000 
###### HTTPS SETTINGS END HERE ######

MAX_INTERVIEWERS_COUNT = 10

##### EMAIL SETTINGS #######
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
#EMAIL_HOST_USER = 'codexaddict@gmail.com'
EMAIL_HOST_USER = 'testyard.in@gmail.com'
#EMAIL_HOST_PASSWORD = '###########'
EMAIL_HOST_PASSWORD = '############'
EMAIL_USE_TLS = True

MAILSENDER = "admin@testyard.in"
SUPPORTEMAIL = "support@testyard.in"
##### EMAIL SETTINGS END HERE #######

####### URLCONF SETTINGS #######
ROOT_URL = "/"
#HTTP_URL = "^http://54.201.126.160/"
HTTP_URL = "^http://testyard.in/"

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
SHOW_EVAL_SCREEN = "skillstest/test/showevaluationscreen/"
SHOW_EVALUATION_URL = "skillstest/test/evaluateresponseurl/"
GET_CURRENT_EVALUATION_DATA_URL = "skillstest/test/getcurrentevaldata/"
TEST_BULK_UPLOAD_URL = "skillstest/test/bulkupload/"
SHOW_TEST_INFO_URL = "skillstest/test/showtestinfo/"
SET_VISIBILITY_URL = "skillstest/test/visibility/"
GET_CANVAS_URL = "skillstest/test/getcanvas/"
SAVE_DRAWING_URL = "skillstest/test/savedrawing/"
DISQUALIFY_CANDIDATE_URL = "skillstest/test/disqualifycandidate/"
COPY_TEST_URL = "skillstest/test/copytest/"
GET_TEST_SCHEDULE_URL = "skillstest/test/setschedule/"
SET_TEST_SCHEDULE_URL = "skillstest/test/setvalue/"
SHOW_ALL_EMAILS_URL = "skillstest/test/showallemailids/"
UPDATE_SCHEDULE_URL = "skillstest/test/updschedule/"
ACTIVATE_TEST_BY_CREATOR = "skillstest/test/activatetest/"
DEACTIVATE_TEST_BY_CREATOR = "skillstest/test/deactivatetest/"
CAPTURE_AUDIOVISUAL_URL = "skillstest/test/recordaudiovisual/"
CREATE_INTERVIEW_URL = "skillstest/test/createinterview/"
CHECK_INT_NAME_AVAILABILITY_URL = "skillstest/test/checknameavail/"
CHALLENGE_STORE_URL = "skillstest/test/interview/addchallenge/"
BLOB_UPLOAD_URL = "skillstest/test/interview/uploadblob/"
ASK_QUESTION_URL = "skillstest/test/interview/askquestion/"
ATTEND_INTERVIEW_URL = "skillstest/test/interview/attend/"
UPDATE_INTERVIEW_META_URL = "skillstest/test/interview/updatemeta/"
UPLOAD_RECORDING_URL = "/skillstest/interview/uploadrecording/"
INTERVIEW_DATA_UPLOAD_URL = "/skillstest/interview/uploaddata/"
CODEPAD_EXECUTE_URL = "skillstest/test/execute/codepad/"
CODE_EXEC_URL = "skillstest/test/execute/code/"
REPORT_WINDOW_CHANGE_URL = "skillstest/test/reportwindowchange/"
GET_TIME_REMAINING_URL = "skillstest/test/timeremaining/"
POST_ON_LINKEDIN_URL = "skillstest/test/postonlinkedin/"
LINKEDIN_REDIRECT_URL = "skillstest/test/linkedin/"
LINKEDINPOSTSESS_URL = "skillstest/test/linkedin/informserver/"
WITHDRAWSCREEN_URL = "skillstest/subscription/withdrawscreen/"
DOWITHDRAWAL_URL = "skillstest/subscriptions/dowithdrawal/"
LATEX_KEYBOARD_URL = "skillstest/tests/latexkbd/"
CHK_INTERNET_CONN_URL = "skillstest/test/chkconnection/"

CREATE_NETWORK_GROUP_URL = "skillstest/network/group/create/"
CHECK_GRPNAME_AVAIL_URL = "skillstest/network/group/checkavailability"
SEARCH_GROUP_URL = "skillstest/network/group/search"
GET_GROUP_INFO_URI = "skillstest/network/group/getinfo/"
SEND_JOIN_REQUEST_URL = "skillstest/network/group/sendjoinrequest/"
SEND_GENTLE_REMINDER_URL = "skillstest/network/group/sendgentlereminder/"
GET_GROUP_DATA_URL = "skillstest/network/group/groupdata/"
GROUP_IMG_UPLOAD_URL = "skillstest/network/group/imgupload/"
SAVE_GROUP_DATA_URL = "skillstest/network/group/save/"
PAYMENT_GW_URL = "skillstest/network/payu/"
SUBSCRIPTION_GW_URL = "skillstest/network/subscription/"
PAYU_CONFIRM_URL = "skillstest/network/payu/confirm/"
STRIPE_CONFIRM_URL = "skillstest/network/stripe/confirm/"
STRIPE_SUCCESS_URL = "skillstest/network/stripe/success/"
STRIPE_CANCEL_URL = "skillstest/network/stripe/cancel/"
RAZORPAY_SUCCESS_URL = "skillstest/network/razorpay/success/"
RAZORPAY_FAILURE_URL = "skillstest/network/razorpay/failure/"
CURRENCY_RATE_URL = "skillstest/network/currencyrate/"
SEARCH_USER_URL = "skillstest/network/searchuser/"
SEND_CONNECTION_URL = "skillstest/network/connect/sendrequest"
SAVE_GROUP_JOIN_STATUS_URL = "skillstest/network/group/savejoinstatus/"
CONNECTION_INVITE_HANDLER_URL = "skillstest/network/connect/handleinvitation/"
POST_MESSAGE_CONTENT_URL = "skillstest/network/postcontent/"
POST_REPLY_CONTENT_URL = "skillstest/network/postreply/"
NEXT_POST_LIST_URL = "skillstest/network/posts/paginatedcontent/"
NEW_MESSAGE_READ_URL = "skillstest/network/posts/newmsgread/"
SEND_MSG_RESPONSE_URL = "skillstest/network/posts/sendmsgresponse/"
MESSAGE_SEARCH_URL = "skillstest/network/posts/msgsearch/"
TEST_TO_GROUPS_URL = "skillstest/network/testtogroups/"
GET_TEST_GROUPS_URL = "skillstest/network/gettests/"
GET_CONNECTION_INFO_URL = "skillstest/network/connection/info/"
GET_GROUPS_OWNED_URL = "skillstest/network/groups/owned/"
GET_GROUPS_MEMBER_URL = "skillstest/network/groups/member/"
GET_CONN_DICT_URL = "skillstest/network/connection/conn/"
BLOCK_USER_URL = "skillstest/network/connection/block/"
UNBLOCK_USER_URL = "skillstest/network/connection/unblock/"
REMOVE_USER_URL = "skillstest/network/connection/remove/"
SEND_MESSAGE_URL = "skillstest/network/connection/sendmessage/"
MANAGE_GROUP_MEMBERS_URL = "skillstest/network/group/managemembers/"
SAVE_GROUP_MEMBERS_URL = "skillstest/network/group/savemembersinfo/"
MEMBER_SEARCH_URL = "skillstest/network/groupmember/search/"
MANAGE_OWNED_GROUPS_URL = "skillstest/network/group/manageowned/"
GROUPIMG_CHANGE_URL = "skillstest/network/changegrpimg/"
GROUPINFO_SAVE_URL = "skillstest/network/group/grpinfosave/"
MANAGE_POSTS_URL = "skillstest/network/group/manageposts/"
SAVE_POST_INFO_URL = "skillstest/network/group/savepostsinfo/"
SEND_A_MESSAGE_URL = "skillstest/network/sendmsg/"
DOWNLOAD_ATTACHMENT_URL = "skillstest/network/inbox/download/"
GROUP_PROFILE_URL = "skillstest/network/showgroupprofile/"
EXIT_GROUP_URL = "skillstest/network/exitgroup/"
PAYUMONEY_SUCCESS_URL = "skillstest/network/payumoney/success/"
PAYUMONEY_FAILURE_URL = "skillstest/network/payumoney/failure/"
LEAVE_GROUP_URL = "skillstest/network/leavegroup/"

TESTS_CHALLENGE_SEARCH_URL = "skillstest/search/testschallengesearch/"
GROUP_SEARCH_URL = "skillstest/search/groupsearch/"
USER_SEARCH_URL = "skillstest/search/user/"
SEARCH_TEST_INFO_URL = "skillstest/search/testinfo/"
DISPLAY_SEARCHED_CHALLENGES_URL = "skillstest/search/showchallenges/"
LISTEN_AUDIO_URL = "skillstest/interview/audio/"
GROUP_DATA_URL = "skillstest/search/groupdata/"

SAVE_OPTIONAL_INFO_URL = "skillstest/optionaluserinfo/"

DETAIL_HELP_URL = "skillstest/helpndocs/detailedhelp/"

ANALYTICS_URL = "skillstest/analytics/"
GET_TESTS_BY_TOPIC_URL = "skillstest/analytics/gettestsbytopic/"
COMPARE_WITH_TOPPERS_URL = "skillstest/analytics/comparewithtoppers/"
COMPARE_WITH_ALL_URL = "skillstest/analytics/comparewithall/"
COMPARE_TOPIC_SCORES_URL = "skillstest/analytics/comparetopicscores/"
COMPARE_CHALLENGE_SCORES_URL = "skillstest/analytics/comparechallengescores/"
COMPARE_SCORES_MMM_URL = "skillstest/analytics/comparescoresmmm/"
COMPARE_COHORT_URL = "skillstest/analytics/comparecohort/"
COMPARE_SBT_URL = "skillstest/analytics/comparesbt/"
COMPARE_PPT_URL = "skillstest/analytics/compareppt/"
COMPARE_TTPERF_URL = "skillstest/analytics/comparettperf/"
COMPARE_PERFT_URL = "skillstest/analytics/compareperft/"
COMPARE_PASSFAIL_URL = "skillstest/analytics/comparepassfail/"
CREATOR_COMPSCORE_URL = "skillstest/analytics/creator/comparescores/"
CREATOR_TESTPOP_URL = "skillstest/analytics/creator/testpopularity/"
CREATOR_TESTTIMES_URL = "skillstest/analytics/creator/testtimes/"
CREATOR_TESTMMM_URL = "skillstest/analytics/creator/testmmm/"
CREATOR_TESTUSAGE_URL = "skillstest/analytics/creator/testusage/"
CREATOR_TESTCOHORT_URL = "skillstest/analytics/creator/testcohort/"
EVALUATOR_DISPLAY_URL = "skillstest/analytics/evaluator/display/"
EVALUATOR_PASS_RATIO_URL = "skillstest/analytics/evaluator/passratio/"
EVALUATOR_COUNT_TESTS_URL = "skillstest/analytics/evaluator/testscount/"
EVALUATOR_ANSTIME_URL = "skillstest/analytics/evaluator/ansbytime/"

PLAN_SUBSCRIBE_URL = "skillstest/subscriptions/subscribe/"
PAYMENT_GW_OPTIONS_URL = "skillstest/subscriptions/paymentgwoptions/"
PAYU_NOTIFY_URL = "skillstest/subscription/notify/"
SUBSCRIBE_PAYPAL_URL = "skillstest/subscriptions/paypal/subscribe/"

WEPAY_REGISTER_REDIRECT_URL = "skillstest/network/wepay/registerstatus/"
WEPAY_DUMMY_AUTHORIZE_URL = "v2/oauth2/authorize"

MOBILE_VERIFY_CREDS_URL = "skillstest/mobile/verifycreds/"
MOBILE_LIST_TESTS_INTERVIEWS_URL = "skillstest/mobile/listtestsinterviews/"
MOBILE_TEST_CREATE_URL = "skillstest/mobile/tests/create/"
MOBILE_CHALLENGE_ADDITION_URL = "skillstest/mobile/tests/addchallenge/"
MOBILE_LIST_CREATOR_TESTS_URL = "skillstest/mobile/tests/showcreatortests/"
MOBILE_TEST_SET_SCHEDULE_URL = "skillstest/mobile/tests/setschedule/"
MOBILE_SEARCH_TEST_URL = "skillstest/mobile/tests/searchtests/"
MOBILE_PENDING_TESTS_URL = "skillstest/mobile/tests/showpending/"
MOBILE_OPEN_TEST_URL = "skillstest/mobile/tests/opentest/"
MOBILE_CREATE_INTERVIEW_URL = "skillstest/mobile/interview/create/"
MOBILE_LIST_INTERVIEW_URL = "skillstest/mobile/tests/listscheduledinterviews/"
####### URLCONF SETTINGS END HERE #######

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
        #'breaknotallowed' : 'Breaks are NOT allowed while taking the test', \
        #'responsenoreturn' : 'Responded challenges may not be revisited', \
        #'norevisit' : 'Attempted challenges may not be revisited', \
        'showatonce' : 'Show all challenges at the begining of the test', \
        'showonebyone' : 'Display challenges to the user one at a time.',\
        'noconsultextmat' : 'User may not consult online material on the subject of the test', \
        #'allowchallengenavigation' : 'Allow user to navigate between challenges', \
        #'windowalwaysontop' : 'The test window will be on top always. This will stop "cheats" from searching for answers on the internet while taking a test.', \ # This seems impossible to implement with all popular browsers.
	'activatecameraduringtest' : 'Stream video of the test taker during the test.',\
        }

ANSWER_LANG_DICT = { 'enus' : 'English - US', 'enuk' : 'English - UK', 'lat' : 'Latin', 'fr' : 'French', \
                     'hndi' : 'Hindi', 'bngw' : 'Bengali - WB', 'bnge' : 'Bengali - Bangladesh', } # Allowed languages

SKILL_QUALITY = { 'BEG' : 'Beginner', 'INT' : 'Intermediate', 'PRO' : 'Proficient' }

PLAN_GUIDELINES = {} # A map of test types, duration, and their  associated costs - used in Subscription.models

PAYMENT_PLATFORMS = {}

# LinkedIn OAuth Details:
APP_NAME = 'TestYard'
OAUTH_API_KEY = '#######'
OAUTH_SECRET_KEY = '############'
OAUTH_USER_TOKEN = '################'
OAUTH_USER_SECRET = '##################'
#REDIRECT_URI = "https://192.168.0.103/skillstest/test/linkedin/"
REDIRECT_URI = "https://testyard.in/skillstest/test/linkedin/"
TESTYARD_GROUP_ID = "testyard" # This is the Id of the TestYard group on LinkedIn.

# Number of complimentary tests a newly registered user can conduct:
NEW_USER_FREE_TESTS_COUNT = 100
# Types of tests the user can conduct as part of complimentary test:
NEW_USER_FREE_TESTS_TYPES = 'MULT|FILB|SUBJ|CODN|ALGO|COMP'

MONTHS_DICT = {'JAN' : '01', 'FEB' : '02', 'MAR' : '03', 'APR' : '04', 'MAY' : '05', 'JUN' : '06', 'JUL' : '07', 'AUG' : '08', 'SEP' : '09', 'OCT' : '10', 'NOV' : '11', 'DEC' : '12'}
REV_MONTHS_DICT = {'01' : 'JAN', '02' : 'FEB', '03' : 'MAR', '04' : 'APR', '05' : 'MAY', '06' : 'JUN', '07' : 'JUL', '08' : 'AUG', '09' : 'SEP', '10' : 'OCT', '11' : 'NOV', '12' : 'DEC'}

SEPARATOR_PATTERN = re.compile('#||#', re.MULTILINE|re.DOTALL)
DES3_SECRET_KEY = '###########' # AES key must be either 16, 24, or 32 bytes long

# Bitly Details:
BITLY_OAUTH_ACCESS_TOKEN = "#############"
BITLY_LINK_API_ADDRESS = "https://api-ssl.bitly.com"

LOG_PATH = "/home/supriyo/work/ty_newiface/logs"
SUBSCRIPTION_INFO_PATH = "/home/supriyo/work/ty_newiface/testyard/skillstest/etc_conf/plans.csv"
COUPON_INFO_PATH = "/home/supriyo/work/ty_newiface/testyard/skillstest/etc_conf/coupons.csv"
PLAN_REMOVAL_PATH = "/home/supriyo/work/ty_newiface/testyard/skillstest/etc_conf/plan_delete.csv"
COUPON_REMOVAL_PATH = "/home/supriyo/work/ty_newiface/testyard/skillstest/etc_conf/coupons_delete.csv"

# Private groups needs the owner to allow members to be a part of it. Open groups may be joined by anyone. A hidden group will not
# be listed by a search of the group by its name, but accessing its page will allow an user to request its owner to allow her/him in 
# the group. A hidden group is also private in nature.
GROUP_TYPES_DICT = { 'PRIV' : 'Private', 'OPEN' : 'Public', 'HIDN' : 'Hidden' }

CONNECT_INVITATION_TEXT = "I would like to connect with you on TestYard."

BANKS_DICT = {  'SBI_INDIA' : 'State Bank of India', \
            'PNB_INDIA' : 'Punjab National Bank', \
        'PNSB_INDIA' : 'Punjab and Sind Bank', \
        'AXIS_INDIA' : 'Axis Bank',\
        'ICICI_INDIA' : 'ICICI Bank', \
        'HDFC_INDIA' : 'HDFC Bank',\
        'CITI_INDIA' : 'Citi Bank', \
        'RBS_INDIA' : 'Royal Bank of Scotland',\
        'SBM_INDIA' : 'State Bank of Mysore', \
        'SBT_INDIA' : 'State Bank of Travancore', \
        'SBJ_INDIA' : 'State Bank of Bikaner and Jaipur', \
        'SBP_INDIA' : 'State Bank of Patiala', \
        'SBH_INDIA' : 'State Bank of Hyderabad',\
        'CORP_INDIA' : 'Corporation Bank', \
        'DHANALAKSHMI_INDIA' : 'Dhanalakshmi Bank',\
        'INDIANBANK' : 'Indian Bank',\
        'HSBC_INDIA' : 'HSBC Bank', \
        'STANCHART_INDIA' : 'Standard Chartered Bank',\
        'BOI_INDIA' : 'Bank of India',\
        'IOB_INDIA' : 'Indian Overseas Bank',\
        'CANBANK_INDIA' : 'Canara Bank', \
        'DENA_INDIA' : 'Dena Bank', \
        'BOB_INDIA' : 'Bank of Baroda', \
        'VIJ_INDIA' : 'Vijaya Bank', \
        'UCO_INDIA' : 'UCO Bank', \
        'UBI_INDIA' : 'Union Bank of India',\
        'SYND_INDIA' : 'Syndicate Bank', \
        'UTD_INDIA' : 'United Bank of India',\
        'OBC_INDIA' : 'Oriental Bank of Commerce',\
        'CBI_INDIA' : 'Central Bank of India',\
        'ANDH_INDIA' : 'Andhra Bank',\
        'ALHD_INDIA' : 'Allahabad Bank',\
        'MAH_INDIA' : 'Maharashtra Bank',\
        'IDBI_INDIA' : 'IDBI Bank',\
        'KKBK_INDIA' : 'Kotak Mahindra Bank',\
}

PLN_TO_USD = 0.26

REQUEST_ACTIVE_INTERVAL = 90 # Amount of time (in days) for which a request to join a group or to connect with another user remains valid.
GROUP_JOIN_REQUEST_SUBJECT = "Testyard user has requested your permission to join the group '%s'"

CONNECT_INVITATION_CONTENT = "I would like to connect with you on TestYard"

DEFAULT_PHONENO_PLACEHOLDER = 9999999999

# Payment gateway settings
ACTIVE_PAYMENT_GATEWAY = "razorpay" # Options are stripe and razorpay. All lowercase - keep in mind.
# PayU settings
#PAYU_POS_ID = 145227
PAYU_POS_ID = "301085"
PAYU_CLIENT_SECRET = "#############"
#PAYU_SECOND_ID = '##########'
PAYU_SECOND_ID = '##########'
PAYU_POS_AUTH_KEY = "####"
PAYU_ORDER_CREATION_URL = "https://secure.snd.payu.com/api/v2_1/orders"
PAYU_START_URL = "http://developers.payu.com/en/quick_start.html"

MY_PAYU_NOTIFY_URL_PATH = "skillstest/subscription/notify/"

PAYU_AUTH_BEARER_CODE_URL = "https://secure.snd.payu.com/pl/standard/user/oauth/authorize"
PAYU_ORDERS_URL = "https://secure.snd.payu.com/api/v2_1/orders"
PAYU_DOMAIN = "secure.snd.payu.com"

#WEPAY_BASEURL = "https://stage.wepayapi.com/v2/"
WEPAY_BASEURL = "https://wepayapi.com/v2/" # Production URL

WEPAY_CLIENT_ID = "6963"
#WEPAY_CLIENT_SECRET = "#####"
WEPAY_CLIENT_SECRET = "##########"
WEPAY_ACCESS_TOKEN = "#################"
WEPAY_ACCOUNT_ID = "#########"
WEPAY_OAUTH2_URL = "https://www.wepay.com/v2/oauth2/authorize?client_id=6963&redirect_uri=https%3A%2F%2Ftestyard.in%2F&scope=manage_accounts%2Ccollect_payments%2Cview_user%2Csend_money%2Cpreapprove_payments%2Cmanage_subscriptions"
WEPAY_USER_REGISTER_URL = WEPAY_BASEURL + "oauth2/authorize/"
#WEPAY_OAUTH2_URI = "https://stage.wepayapi.com/v2/oauth2/token"
WEPAY_OAUTH2_URI = "https://wepayapi.com/v2/oauth2/token"
#WEPAY_ACCT_CREATE_URI = "https://stage.wepayapi.com/v2/account/create"
WEPAY_ACCT_CREATE_URI = "https://wepayapi.com/v2/account/create"

WEPAY_ACCOUNT_USERNAME = "testyard.in@gmail.com"
WEPAY_ACCOUNT_PASSWORD = "#########"

RAZORPAY_USEREMAIL = "testyard.in@gmail.com"
PAZORPAY_PASSWORD = "########"
# RAZORPAY TEST KEY
RAZORPAY_KEY = "##########"
RAZORPAY_SECRET = "##########"
#RAZORPAY_BASEURI = "https://%s:%s@api.razorpay.com/v1"%(RAZORPAY_KEY, RAZORPAY_SECRET)
RAZORPAY_BASEURI = "https://api.razorpay.com/v1"
RAZORPAY_DASHBOARD = "https://dashboard.razorpay.com/#/app/dashboard"
ADD_ACCOUNT_URL = "https://dashboard.razorpay.com/#/app/route/accounts"
RAZORPAY_MERCHANT_ID = "##########"
RAZORPAY_BANK_ACCOUNT = "##########"

PAYPAL_SANDBOX_URL = "https://api.sandbox.paypal.com"
PAYPAL_LIVE_URL = "https://api.paypal.com"

PAYPAL_SANDBOX_ACCT = "supmit-facilitator@gmail.com"
PAYPAL_SANDBOX_ACCESS_TOKEN = "##########"
PAYPAL_SANDBOX_ACCESS_TOKEN_EXPIRY = "2027-06-02"
PAYPAL_SANDBOX_ORDERS_URL = "https://api.sandbox.paypal.com/v1/payments/payment"
PAYPAL_RETURN_URL = "http://www.paypal.com/return"
PAYPAL_CANCEL_URL = "http://www.paypal.com/cancel"

# DEV CODE US
STRIPE_API_KEY_US="############"
STRIPE_API_SECRET_US="#########"

# LIVE CODE INDIA
STRIPE_API_KEY="############"
STRIPE_API_SECRET="############"

STRIPE_ACCT_LINK_REFRESH_URL="skillstest/network/stripe/refresh/"
STRIPE_ACCT_LINK_RETURN_URL="skillstest/network/stripe/return/"

SUPPORTED_CURRENCIES = ('INR', 'USD', 'EUR', 'PLN')
DEFAULT_CURRENCY = 'PLN'
CUT_FRACTION = 0.02 # 2% is for testyard. The rest goes to the user.

CUSTOMER_IP_ADDRESS = '192.168.0.103'

# Easy API params:
EASYAPI_USERNAME = 'supmit'
EASYAPI_PASSWORD = '###########'
EASYAPI_KEY = '######'
EASYAPI_URL = 'https://xmlfeed.theeasyapi.com'

# Fixer API Params:
FIXERAPI_EMAILID = 'testyard.in@gmail.com'
FIXERAPI_PASSWD = '#########'
FIXERAPI_KEY = '#######'
FIXERAPI_URL = 'http://data.fixer.io/api/latest'

GO_DADDY_CUST_NUM = ########
GO_DADDY_PASSWD = "#########"

MAX_POSTS_IN_PAGE = 10

#LEFT_PANEL_CHALLENGE_LENGTH = 25

ANSWER_SCRIPT_DUMP_PATH = "answerscripts" # This will be inside MEDIA_ROOT
PROCESSED_SCRIPT_DUMP = "processed"

###### AMAZON AWS API INFO ######

ACCESS_KEY_ID = "#######"
SECRET_ACCESS_KEY = "###########+"

AMAZON_ACCT_EMAIL = "supmit2k3@yahoo.com"
AMAZON_ACCT_PASSWD = "########"

AMAZON_ACCT_ID = "########"

IAM_USER = "supmit"
IAM_PASSWD = "############"

IAM_SIGNIN_URL = "https://704972534197.signin.aws.amazon.com/console/" # This will change if we ever change the values for IAM_USER or IAM_PASSWD.
###### AMAZON AWS SETTINGS END ######

########### REPL SETTINGS ############
REPL_HOST = "api.repl.it"
REPL_SECRET = "##########"
REPL_USERNAME = "supmit"
REPL_PASSWORD = "##########"
REPL_EMAIL = "codexaddict@gmail.com"
########## REPL SETTINGS END ##########

########## CODE EXECUTION SERVICE HOST #############
CODE_EXEC_HOST_IP = "192.168.1.35" # If this changes, you need to change the same on listener.ini too
CODE_EXEC_HOST_PORT = "8787"
CODE_MAX_SIZE = 20000
MAX_CONN_BACKLOGS_LEN = 10

########## CODE EXECUTION SERVICE PARAMS END HERE #############

########### MAX VMWare Player Instances ###########
#MAX_VM_INSTANCES_LIN = 10 #Number of VM instances that may be run conurrently.

# NOTE:\n **** THIS SHOULD NOT BE DONE LOCAL/EXPERIMENTAL INSTALLATIONS WHERE RUNNING 10 VMs CONCURRENTLY MAY FREEZE THE OS.THIS SHOULD BE
# DONE ON ANOTHER SYSTEM THAT HAS ENOUGH CPU's AND MEMORY TO HANDLE THE OPERATION. IDEALLY I WOULD LIKE THE MACHINE (PHYSICAL OR 
# OTHERWISE) TO HAVE 16 GIGS MEMORY AND 8 DUAL CORE PROCESSORS (preferably AMD). ****\n
# 
# Disclaimer: Please also note that such a system should have a very powerful auxilliary cooling system especially for the AMD CPUs, as 
# AMD CPUs have the notorious habit of heating up exorbitantly while performing little complex executions of code. AMD has  a lot of cool 
# features as well, so I am not discouraging anyone to use it, but this heating is a known issue. Kindly use your judgement to buy your 
# components.

# S.

MAX_VM_INSTANCES_LIN = 7 # figure for tests implementation.
MAX_VM_INSTANCES_WIN = 5
################################################### 

# PEM passphrase for local nginx: spmprx
# Certificate generation command: openssl req -x509 -newkey rsa:2048 -keyout testyard.key -out testyard.crt -days 365

TWILIO_EMAIL = "testyard.in@gmail.com"
TWILIO_PASSWD = "#########"
TWILIO_AUTH_TOKEN = "########"
TWILIO_ACCT_SID = "##########"

####################################################

# Max Response size allowable in answers to tests if the creator of the test fails to specify any limit
MAXRESPONSECHARCOUNT= 4000

# MAX number of invitations that can be sent out at one go.
MAX_INVITES_PER_SESSION = 20

# Celery config params
CELERY_BROKER_URL = "redis://127.0.0.1:6379"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379"
# Also execute 'export C_FORCE_ROOT="true"' from commandline. This will set C_FORCE_ROOT env variable to True.

PAGE_CHUNK_SIZE = 40



