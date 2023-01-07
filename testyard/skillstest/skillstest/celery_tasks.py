# skillstest/celery_tasks.py
# celery==3.1.25 for django==1.4.8

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "skillstest.settings")
emailqueueapp = Celery("skillstest")
emailqueueapp.config_from_object("django.conf:settings") # The celery variables in skills_settings are to be prefixed with 'CELERY_'.
emailqueueapp.autodiscover_tasks(packages=['skillstest.Tests.tasks',])

# Run from project (testyard/skillstest) directory: python -m skillstest.celery_tasks -A skillstest worker
