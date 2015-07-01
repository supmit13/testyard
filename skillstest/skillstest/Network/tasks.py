import os, sys, re, time
import datetime
import urllib, urllib2
#from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
import gzip
from StringIO import StringIO

from skillstest import settings as mysettings
from skillstest.errors import error_msg
import skillstest.utils as skillutils
from skillstest.Network.models import ExchangeRates


class NoRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        infourl = urllib.addinfourl(fp, headers, req.get_full_url())
        infourl.status = code
        infourl.code = code
        return infourl

    http_error_300 = http_error_302
    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302 

def decodeGzippedContent(encoded_content):
    response_stream = StringIO(encoded_content)
    decoded_content = ""
    try:
        gzipper = gzip.GzipFile(fileobj=response_stream)
        decoded_content = gzipper.read()
    except: # Maybe this isn't gzipped content after all....
        decoded_content = encoded_content
    return(decoded_content)



def fetch_exchange_rates():
    supported_currencies_list = mysettings.SUPPORTED_CURRENCIES
    basecurrency = mysettings.DEFAULT_CURRENCY
    easyapi_username = mysettings.EASYAPI_USERNAME
    easyapi_passwd = mysettings.EASYAPI_PASSWORD
    easyapi_key = mysettings.EASYAPI_KEY
    ctr = 0
    for currency in supported_currencies_list:
        if currency == 'INR':
            continue
        easyapi_xmlrequest = {}
        easyapi_xmlrequest['request'] = """<easyapi_wrapper><login><apikey>%s</apikey></login><search><service>convert_webxcurrency</service><criteria><amount>1</amount><tocur>INR</tocur><fromcur>%s</fromcur></criteria></search></easyapi_wrapper>"""%(easyapi_key, currency)
        requestdata = urllib.urlencode(easyapi_xmlrequest)
        openerobj = urllib2.build_opener() # This is my normal opener....
        noredirect_openerobj = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), NoRedirectHandler()) 
        easyapi_url = mysettings.EASYAPI_URL
        httpHeaders = { 'User-Agent' : r'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.10) Gecko/20111103 Firefox/3.6.24', }
        httprequest = urllib2.Request(easyapi_url, requestdata, httpHeaders)
        try:
            pageResponse = noredirect_openerobj.open(httprequest)
        except:
            message = "Error: " + error_msg('1098') + " - " + sys.exc_info()[1].__str__()
            return message
        pagecontent = pageResponse.read()
        pagecontent = decodeGzippedContent(pagecontent)
        exchpattern = re.compile(r"<exch_rate>([\d\.]+)</exch_rate>")
        exchmatch = exchpattern.search(pagecontent)
        exchrate = ''
        if exchmatch:
            exchrate = exchmatch.groups()[0]
        exchobj = ExchangeRates()
        exchobj.curr_from = currency
        exchobj.curr_to = 'INR'
        exchobj.conv_rate = exchrate
        exchobj.dateofrate = skillutils.pythontomysqldatetime2(str(datetime.datetime.now()))
        exchobj.save()
        ctr += 1
    print "Successfully fetched and stored currency conversion rates."
    
