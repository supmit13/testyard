import os, sys, re, time
import inspect

error_codes = { \
        '1001' : 'Unsupported request method', \
        '1002' : 'Authentication Failed - username or password didn\'t match', \
        '1003' : 'User is not active', \
        '1004' : 'Unhandled HTTP method called.', \
        '1005' : 'Uploaded file exceeds max file size limit', \
        '1006' : 'Session is corrupt or it has expired', \
        '1007' : 'Mismatch in your session and location information',\
        
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

