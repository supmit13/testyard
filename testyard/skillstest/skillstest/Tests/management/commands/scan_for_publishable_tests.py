from django.core.management.base import NoArgsCommand
from skillstest.Tests.tasks import scan_and_activate, scan_and_deactivate

class Command(NoArgsCommand):
    help = "Scan and find tests that are publishable and 'activable' (excuse the english)."

    def handle_noargs(self, **options):
        scan_and_activate()
        self.stdout.write('Successfully completed.')

"""
Run this as follows: 
python manage.py scan_for_publishable_tests <ENTER>
"""
