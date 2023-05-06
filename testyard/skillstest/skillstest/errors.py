import os, sys, re, time
import inspect
from skillstest import settings as mysettings

error_codes = { \
        '1111' : 'Please contact our support team at \'support@testyard.com\' for any issues. Please remember to send them a screenshot of your problem and the steps you performed that resulted in the issue. We will help you out at the earliest.', \

        '1001' : 'Unsupported request method', \
        '1002' : 'Authentication Failed - username or password didn\'t match', \
        '1003' : 'User is not active', \
        '1004' : 'Unhandled HTTP method called.', \
        '1005' : 'Uploaded file exceeds max file size limit (%s MB)'%(mysettings.MAX_FILE_SIZE_ALLOWED/1000000), \
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
        '1049' : 'User had already started taking this test before. She/He may not restart taking it again.',\

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
        '1060' : 'The challenges could not be displayed in edit mode or saved as the test has either been published already or is in active state.', \
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
        '1114' : 'You are trying to modify one or more accepted members outcome. Once a user has been accepted by the group, you may not change the join requests outcome',\
        '1115' : 'Could not find group member with the given group object and user object.',\
        '1116' : 'Could not set groupmember values',\
        '1117' : 'Group member is the owner of the group - owner cannot be blocked or removed from the group',\
        '1118' : 'Could not save groupmember object',\
        '1119' : 'Could not find the user object for the given displayname',\
        '1120' : 'Could not identify the user from whom the invitation came.',\
        '1121' : 'Could not find the invitation record from the given Id',\
        '1122' : 'Could not connect to the specified user. Sorry for this inconvenience.',\
        '1123' : 'Successfully added connection to your list of contacts',\
        '1124' : 'Successfully modified the status of the invitation.', \
        '1125' : 'Could not update the invitation status - %s',\
        '1126' : 'You are already connected to the user you are trying to connect to.',\
        '1127' : 'You cannot post or send a message to more than one type of entity at the same time. You must either choose user(s), OR group(s) OR test(s).',\
        '1128' : 'Could not post message - Error: %s',\
        '1129' : 'Message has been posted successfully',\
        '1130' : 'Your message could not be sent as you did not specify any target for the message',\
        '1131' : 'There is no content to post. You have specified an empty message',\
        '1132' : 'Could not display the screen due to a technical issue. Please contact the site administrator as admin@testyard.com',\
        '1133' : 'Did not find any post Id from the request. Check the data you are sending.',\
        '1134' : 'Could not post your message due to some technical issue. Contact our support to resolve this.',\
        '1135' : 'Could not open a related post due to a technical error.',\
        '1136' : 'One or more parameters are missing or has invalid value.',\
        '1137' : 'Post with the given Id does not exist.',\
        '1138' : 'No search phrase or term was found in request',\
        '1139' : 'No test Id or groups has been specified in request.',\
        '1140' : 'The test is being sent to all members of the selected group(s). An email specfying the number of users to whom the test has been sent to will be dispatched to your registered email address once the process completes. It might take a while depending on the number of users the test is being sent.',\
        '1141' : 'Failed to send the confirmation email to the test owner.',\
        '1142' : 'This image is not connected to any test. You first need to create a test or edit an existing one to save this image.',\
        '1143' : 'Could not find a valid connection Id in the request',\
        '1144' : 'Could not create a connection object from the given connection Id',\
        '1145' : 'Could not find a connected user Id from request',\
        '1146' : 'Could not find a target user (connection) from the request.',\
        '1147' : 'Could not find the user identified by the given displayname',\
        '1148' : 'Could not find the action to perform from the POST request',\
        '1149' : 'Could not find a valid contact Id from the request',\
        '1150' : 'Could not find an action in the request or the action value is invalid',\
        '1151' : 'User with the given display name does not exist.',\
        '1152' : 'Could not find the email Id of the recipient in the POST request',\
        '1153' : 'Could not find any message content in the POST request',\
        '1154' : 'Could not find the user object with the specified email address',\
        '1155' : 'You are not the owner of this group. Hence you are not entitled to view the manage members screen for this group.',\
        '1156' : 'User with the given username does not belong to this group.',\
        '1157' : 'Could not find the required parameter named emailid in the request.',\
        '1158' : 'Candidate cannot be disqualified by any user other than the owner of the test.',\
        '1159' : 'User with the given email Id and attempted test could not be found.',\
        '1160' : 'Could not send test results intimation email to candidate.',\
        '1161' : 'Could not save the data',\
        '1162' : 'You may not schedule a test while it is being edited (or created).',\
        '1163' : 'You may not schedule a test that is not yet activated or published.',\
        '1164' : 'The test is scheduled to start from %s and will end on %s. Please return to this page in that interval to take the test.',\
        '1165' : 'The test is already over. It was scheduled to start at %s and end at %s.',\

        '1166' : 'An interview with the same title already exists in your account. Please choose a different name and try again.',\
        '1167' : 'This challenge is not associated with an interview. It will not be saved.',\
        '1168' : 'Could not find a binary object containing the content submitted by the user.',\
        '1169' : 'Error: Could not find the interview identified by the submitted interviewlinkid',\
        '1170' : 'Error: An interview with the same linkid exists. Please refresh the "Tests" tab and click on the "Create an Interview" link to create another interview with a unique link id. You will not be able to add questions to this interview unless you perform this step.',\
        '1171' : 'Could not find an interviewlinkid with the request. Please restart the process of creating test as it seems that the data for this test has become corrupt.',\
        '1172' : 'An error occurred while storing the questions in DB. Please contact the administrator at admin@testyard.com with the name of the interview.',\
        '1173' : 'Error: Missing the link id parameter. System can\'t figure out which interview to link to.',\
        '1174' : 'Could not find data in the request.',\
        '1175' : 'Date value is not in the correct format. It should be in the yyyy-mm-dd format.',\
        '1176' : 'Evaluator with the given email Id could not be found. ',\
        '1177' : 'Test name is empty or invalid',\
        '1178' : 'Your session has expired or it got lost in transit.',\
        '1179' : 'The username field is empty. Aborting the requested operation.',\
        '1180' : 'The user with the given username does not exist.',\
        '1181' : 'User mismatch - seems like you have a session that does not belong to you. Please logout and login again to continue.',\
        '1182' : 'The details pertaining to you have been captured by the application. Your content is now being posted.', \
        '1183' : 'The Linkedin post data doesn\'t exist in our records. Please try to post again.',\
        '1184' : 'The records for posting on linkedin do not match at the two phases. This might occur if you take a long time in the process of posting your test/interview result, or if your connection is not stable. If you keep encountering this issue, please feel free to contact our support staff at support@testyard.in.',\
        '1185' : 'Required parameter schedule Id missing.',\
        '1186' : 'Could not find schedule object matching the given Id.',\
        '1187' : 'Could not find required parameters start and/or end.',\
        '2099' : 'Requested user is not the same as the user in session. Possibly, your session is corrupt or non-existent. Please login to try again.', \
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

