import os, sys, re, time
import urllib, urllib2
#from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup


# This command will fetch the conversion rates from http://theeasyapi.com/ using
# the API and store it in the 'Network_exchangerates' table.
# Schedule: To be run from cron once every day.

from django.core.management.base import NoArgsCommand
from skillstest.Network.tasks import fetch_exchange_rates_fixer

class Command(NoArgsCommand):
    help = "Fetch currency exchange rates from theeasyapi."

    def handle_noargs(self, **options):
        fetch_exchange_rates_fixer()
        self.stdout.write('Successfully completed.')
