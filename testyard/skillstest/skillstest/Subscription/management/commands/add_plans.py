from django.core.management.base import NoArgsCommand
from skillstest.Subscription.tasks import process_subscription_info

class Command(NoArgsCommand):
    help = "Read subscription info and populate the DB accordingly."

    def handle_noargs(self, **options):
        process_subscription_info()
        self.stdout.write('Successfully completed.')

"""
Run this as follows: 
python manage.py add_plans <ENTER>
"""
