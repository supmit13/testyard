import os, sys, re, time
import urllib, urllib2
#from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup


# This command will fetch the conversion rates from http://theeasyapi.com/ using
# the API and store it in the 'Network_exchangerates' table.

from django.core.management.base import NoArgsCommand
from skillstest.Network.tasks import fetch_exchange_rates

class Command(NoArgsCommand):
    help = "Fetch currency exchange rates from theeasyapi."

    def handle_noargs(self, **options):
        fetch_exchange_rates()
        self.stdout.write('Successfully completed.')
