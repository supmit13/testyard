import sys, os, re, time
from django import template
from django.template.defaultfilters import stringfilter

"""
Create and register a filter to extract values from a dict with keys
containing space characters in a django template. 
"""
register = template.Library()

"""
Filter to retrieve values  from a dict with keys
that contain special characters.
"""
@register.filter(name='dictlookup')
def dictlookup(the_dict, key):
    return the_dict.get(key, '')


"""
A filter to retrieve a value from a list whose index is given.
Need this to use with the filter defined above.
"""
@register.filter(name='getval')
def getval(the_list, index):
    if the_list.__len__() < index:
        return ""
    if the_list.__len__() > 0:
        return the_list[index]
    else:
        return ""


"""
Concatenate 2 strings in django templates. Strings
may be in javascript variables.
"""
@register.filter(name='addstr')
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)

"""
Search and replace a sequence of characters with another sequence.
"""
@register.filter(name='replace')
@stringfilter
def replace ( string, args ): 
    search  = args.split(args[0])[1]
    replace = args.split(args[0])[2]

    return re.sub( search, replace, string )


