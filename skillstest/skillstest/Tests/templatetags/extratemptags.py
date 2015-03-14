import sys, os, re, time
from django import template


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
    return the_list[index]



