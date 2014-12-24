import os, sys, re, time
import inspect

error_codes = { \
        '1001' : 'Unsupported request method', \
        '1002' : 'Authentication Failed - username or password didn\'t match', \
        '1003' : 'User is not active', \
        '1004' : 'Unhandled HTTP method called.', \
        '1011' : 'One or more fields have invalid values - the 2 password fields do not match.', \
        '1012' : 'One or more fields have invalid values - username cannot be empty.', \
        '1013' : 'One or more fields have invalid values - invalid email address', \
        '1014' : 'One or more fields have invalid values - invalid mobile number', \
        '1015' : 'One or more fields have invalid values - invalid value for sex', \
        '1016' : 'One or more fields have invalid values - invalid value for usertype', \
        '1017' : 'One or more fields have invalid values - firstname/middlename/lastname may contain alphabets only.', \
        '1018' : 'One or more fields have invalid values - invalid privilege value', \
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

