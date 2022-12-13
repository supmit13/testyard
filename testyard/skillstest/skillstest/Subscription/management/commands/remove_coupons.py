from django.core.management.base import NoArgsCommand
from skillstest.Subscription.tasks import remove_coupon

class Command(NoArgsCommand):
    help = "Read coupons info and delete the records accordingly."

    def handle_noargs(self, **options):
        remove_coupon()
        self.stdout.write('Successfully completed.')

"""
Run this as follows: 
python manage.py remove_coupons <ENTER>
"""
