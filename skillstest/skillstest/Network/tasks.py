import os, sys, re, time
import datetime
import urllib, urllib2
#from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
import gzip
from StringIO import StringIO
import simplejson as json
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



def fetch_exchange_rates_easy():
    supported_currencies_list = mysettings.SUPPORTED_CURRENCIES
    basecurrency = mysettings.DEFAULT_CURRENCY
    easyapi_username = mysettings.EASYAPI_USERNAME
    easyapi_passwd = mysettings.EASYAPI_PASSWORD
    easyapi_key = mysettings.EASYAPI_KEY
    ctr = 0
    for currency in supported_currencies_list:
        if currency == 'USD':
            continue
        easyapi_xmlrequest = {}
        easyapi_xmlrequest['request'] = """<easyapi_wrapper><login><apikey>%s</apikey></login><search><service>convert_webxcurrency</service><criteria><amount>1</amount><tocur>USD</tocur><fromcur>%s</fromcur></criteria></search></easyapi_wrapper>"""%(easyapi_key, currency)
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
        #print pagecontent
        pagecontent = decodeGzippedContent(pagecontent)
        exchpattern = re.compile(r"<exch_rate>([\d\.]+)</exch_rate>")
        exchmatch = exchpattern.search(pagecontent)
        exchrate = ''
        if exchmatch:
            exchrate = exchmatch.groups()[0]
        exchobj = ExchangeRates()
        exchobj.curr_from = currency
        exchobj.curr_to = 'USD'
        exchobj.conv_rate = exchrate
        exchobj.dateofrate = skillutils.pythontomysqldatetime2(str(datetime.datetime.now()))
        exchobj.save()
        ctr += 1
    print "Successfully fetched and stored currency conversion rates."


def fetch_exchange_rates_fixer():
    supported_currencies_list = mysettings.SUPPORTED_CURRENCIES
    basecurrency = mysettings.DEFAULT_CURRENCY
    fixer_emailid = mysettings.FIXERAPI_EMAILID
    fixer_passwd = mysettings.FIXERAPI_PASSWD
    fixer_key = mysettings.FIXERAPI_KEY
    fixer_url = "http://data.fixer.io/api/latest?access_key=%s"%fixer_key
    httpHeaders = { 'User-Agent' : r'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.10) Gecko/20111103 Firefox/3.6.24', }
    openerobj = urllib2.build_opener() # This is my normal opener....
    noredirect_openerobj = urllib2.build_opener(urllib2.HTTPHandler(), urllib2.HTTPSHandler(), NoRedirectHandler())
    httprequest = urllib2.Request(fixer_url, None, httpHeaders)
    try:
        pageResponse = noredirect_openerobj.open(httprequest)
    except:
        message = "Error: " + error_msg('1098') + " - " + sys.exc_info()[1].__str__()
        return message
    pagecontent = pageResponse.read()
    fixer_data_dict = json.loads(pagecontent)
    usd_rate = fixer_data_dict['rates']['USD']
    inr_rate = fixer_data_dict['rates']['INR']
    pln_rate = fixer_data_dict['rates']['PLN']
    timestamp = fixer_data_dict['timestamp']
    eur_rate = 1
    eur_usd_conv = eur_rate/usd_rate
    inr_usd_conv = (inr_rate) * eur_usd_conv
    pln_usd_conv = (pln_rate) * eur_usd_conv
    ts_datetime = skillutils.pythontomysqldatetime2(str(datetime.datetime.fromtimestamp(timestamp)))
    for currency in supported_currencies_list:
        if currency == 'USD':
            continue
        exchobj = ExchangeRates()
        exchobj.curr_from = currency
        exchobj.curr_to = 'USD'
        if currency == 'INR':
            exchrate = 1/inr_usd_conv
        elif currency == 'EUR':
            exchrate = 1/eur_usd_conv
        elif currency == 'PLN':
            exchrate = 1/pln_usd_conv
        else: # We do not consider currencies other than the 4 handled here.
            continue
        exchobj.conv_rate = exchrate
        #exchobj.dateofrate = skillutils.pythontomysqldatetime2(str(datetime.datetime.now()))
        exchobj.dateofrate = ts_datetime
        exchobj.save()
    print "Successfully fetched and stored currency conversion rates."
    
    
    
