import os, sys, re, time
import inspect
from skillstest import settings as mysettings

error_codes = { \
        '1111' : 'Please contact our support team at \'support@testyard.com\' for any issues. Please remember to send them a screenshot of your problem and the steps you performed that resulted in the issue. We will help you out at the earliest.', \

        '1001' : 'Unsupported request method', \
        '1002' : 'Authentication Failed - username or password didn\'t match', \
        '1003' : 'User is not active', \
        '1004' : 'Unhandled HTTP method called.', \
        '1005' : 'Uploaded file exceeds max file size limit', \
        '1006' : 'Session is corrupt or it has expired', \
        '1007' : 'Mismatch in your session and location information',\
        '1008' : 'Session doesn\'t exist. Please login into testyard to perform the requested action.', \
        
        '1011' : 'One or more fields have invalid values - the 2 password fields do not match.', \
        '1012' : 'One or more fields have invalid values - username cannot be empty.', \
        '1013' : 'One or more fields have invalid values - invalid email address', \
        '1014' : 'One or more fields have invalid values - invalid mobile number', \
        '1015' : 'One or more fields have invalid values - invalid value for sex', \
        '1016' : 'One or more fields have invalid values - invalid value for usertype', \
        '1017' : 'One or more fields have invalid values - firstname/middlename/lastname may contain alphabets only.', \
        '1018' : 'One or more fields have invalid values - invalid privilege value', \
        '1019' : 'Password strength is not adequate', \

        '1021' : 'Could not create directory to store attachment', \

        '1031' : 'You have been logged out from the system.', \

        '1041' : 'Failed to upload profile image', \

        '1042' : 'Error in test metadata: Incorrect date format submitted for date of activation. Format should be dd-MON-yyyy', \

        '1043' : 'Error in test metadata: Inappropriate number of days for given month in date of activation', \

        '1044' : 'Error in test metadata: Incorrect date format submitted for date of publication of test. Format should be dd-MON-yyyy', \

        '1045' : 'Error in test metadata: Inappropriate number of days for given month in date of publication of test', \

        '1046' : 'Error in test metadata: Date of activation of a test cannot be prior to its date of publication on testyard', \

        '1047' : 'Error in test metadata: Incorrect data type for total score or number of challenges or both', \

        '1048' : 'Error in evaluator group name: An evaluator group with the same name but with a different set of email ids already exist', \

        '1050' : 'Entered test metadata successfully', \
        '1051' : 'This challenge/question could not be associated with any test created by you. This may mean that your session has become corrupt due to some transient problem. Please login into your account once more and retry. We regret the inconvenience caused due to this condition.', \
        '1052' : 'Challenge/Question has been successfully saved.', \
        '1053' : 'No test type was specified with the request.', \
        '1054' : 'The specified challenge type is not recognized.', \
        '1055' : 'Bad request - no test Id was passed.', \
        '1056' : 'Test with the specified Id was not found', \

        '1057' : 'No key named challengeid from the POST request', \
        '1058' : 'Could not create test object. Please contact the administrator with the details of the operation you were performing.', \
        '1059' : 'No Test Id found in request', \
        '1060' : 'The challenges could not be edited as the test has either been published already or is in active state.', \
        '1061' : 'Couldn\'t find the test object associated with the given challenge.',\
        '1062' : 'Couldn\'t find the challenge associated with the given testlinkid',\
        '1063' : 'User is NOT permitted to view this test or any of its challenges in edit mode.',\
        '1064' : 'The selected test is being edited at the present moment. Please come back later to take this test.', \
        '1065' : 'The selected test is not active as yet. Please contact the entity that is conducting this test.', \
        '1066' : 'You cannot attempt this test more than once. You have already used up your chance.', \
        '1067' : 'You have already attempted this test the maximum number of times allowed for this test.',\
        '1068' : 'The time interval between 2 successive attempts to this test has not yet elapsed.', \
        '1069' : 'The requested operation could not be performed due to insufficient parameters.', \
        '1070' : 'You are not authorised to send out invitations for this test. If you want someone to take this test, you may send a request to the owner/creator of this test to let you copy it by either making it public for a while or by allowing you an exclusive privilege to copy it within a certain period of time. Once you make a copy of this test, the copied test will be your property and you would be able to send out invitations to candidates/users to take the test.', \
        '1071' : 'Incorrect method of request.', \
        '1072' : 'Bogus test response received.', \
        '1073' : 'No test invitation was sent to the user or the invitation was cancelled or inactive.', \
        '1074' : 'The test link you clicked is no longer valid.', \
        '1075' : 'You have already taken this test. ', \
        '1076' : 'You may not take this test as you are one of the evaluators or the creator of this test.', \
        '1077' : 'The email Id specified in your link to the test could not be found.', \
        '1078' : 'Your request could not be processed correctly. Please retry with valid request parameters.', \
        '1079' : 'Unrecognized table reference - the referred table does not exist.', \
        '1080' : 'Could not retrieve test or evaluator objects for the given test Id.', \
        '1081' : 'User is NOT permitted to evaluate this test.', \
        '1082' : 'No email Id found in request', \
        '1083' : 'You may not evaluate the candidate anymore. Your stipulated time of %s days for the purpose of evaluation has expired.'%(mysettings.NUM_DAYS_EVALUATION_COMMIT), \
        '1084' : 'Group with the name "%s" doesn\'t exist.',\
        '1085' : 'No group id found in request',\
        '1086' : 'Group with the given id does not exist.',\
        '1087' : 'One or more of the required parameters (groupmembername and groupname) is missing.',\
        '1088' : 'The group with the given name does not exist.',\
        '1089' : 'An unknown error occurred while trying to find the given group',\
        '1090' : 'Could not create/edit the bankaccount object or groupobj or both.',\
        '1091' : 'Successfully update the group and bank account info', \
        '1092' : 'Could not add member to the group',\
        '1093' : 'You have been added to the group successfully', \
        '1094' : 'Blocked from group as user has exceeded the maximum number of attempts of taking the test', \
        '1095' : 'Could not send email to group\'s owner',\
        '1096' : 'Could not send invitation of the entry test to the user',\
        '1097' : 'Failed to create group member - %s',\
	'1098' : 'Failed to connect to easyapi to retrieve exchange rates',\
        '1099' : 'Could not understand the date at which the rates are to be queried',\
        '1100' : 'HTTP request method not supported.', \
        '1101' : 'Could not make request to the targetted URL',\
        '1102' : 'This group is not owned by you',\
        '1103' : 'We did not get a location header, meaning we are not on the right track to payment. Please retry!',\
        '1104' : 'Could not find the userid in the request',\
        '1105' : 'Could not find the user identified by the id %s',\
        '1106' : 'Could not send the invitation to the user identified by %s',\
        '1107' : 'Successfully sent the invitation to the user identified by %s',\
        '1108' : 'You are already connected to the user identified by %s',\
        '1109' : 'You have already sent a connection invitation to the user identified by %s',\
        '1110' : 'The target user has refused your connect request in the past. Hence you may not send any further requests to the target user.',\
        '1111' : 'No groupname or user names contained in the request',\
        '1112' : 'Failed to create the group object from the provided groupname',\
        '1113' : 'Saved states of the users',\
    }

def error_msg(code):
    stackrecs = inspect.stack()
    if stackrecs.__len__() > 1:
        callstack = stackrecs[1]
        if callstack.__len__() > 3:
            caller = callstack[3]
            return caller + ": " + error_codes[code]
        else:
            return inspect.getmodule(callstack[0]) + ": " + error_codes[code]
    else:
        return error_codes[code]

