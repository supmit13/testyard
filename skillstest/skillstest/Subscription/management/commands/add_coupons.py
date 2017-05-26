from django.core.management.base import NoArgsCommand
from skillstest.Subscription.tasks import add_coupon

class Command(NoArgsCommand):
    help = "Read coupons info and populate the DB accordingly."

    def handle_noargs(self, **options):
        add_coupon()
        self.stdout.write('Successfully completed.')

"""
Run this as follows: 
python manage.py add_coupons <ENTER>
"""
