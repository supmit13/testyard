from django.core.management.base import NoArgsCommand
from skillstest.Subscription.tasks import make_payouts

class Command(NoArgsCommand):
    help = "Make payouts by reading objects from Payouts model."

    def handle_noargs(self, **options):
        make_payouts()
        self.stdout.write('Successfully completed.')

"""
Run this as follows: 
python manage.py make_payouts <ENTER>
"""
