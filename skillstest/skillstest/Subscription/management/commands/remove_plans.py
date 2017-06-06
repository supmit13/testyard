from django.core.management.base import NoArgsCommand
from skillstest.Subscription.tasks import remove_plan

class Command(NoArgsCommand):
    help = "Read plans info and delete the records accordingly."

    def handle_noargs(self, **options):
        remove_plan()
        self.stdout.write('Successfully completed.')

"""
Run this as follows: 
python manage.py remove_plans <ENTER>
"""
