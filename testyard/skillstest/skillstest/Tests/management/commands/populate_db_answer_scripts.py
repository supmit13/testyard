from django.core.management.base import NoArgsCommand
from skillstest.Tests.tasks import process_answer_scripts

class Command(NoArgsCommand):
    help = "Read answer scripts and populate the DB accordingly."

    def handle_noargs(self, **options):
        process_answer_scripts()
        self.stdout.write('Successfully completed.')

"""
Run this as follows: 
python manage.py populate_db_answer_scripts <ENTER>
"""
