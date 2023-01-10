# skillstest/celery_tasks.py
# celery==3.1.25 for django==1.4.8

import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "skillstest.settings")
emailqueueapp = Celery("skillstest.Tests.tasks", broker="redis://127.0.0.1:6379")
emailqueueapp.config_from_object("django.conf:settings")
emailqueueapp.autodiscover_tasks(packages=['skillstest.Tests.tasks',])

# Run from project (testyard/skillstest) directory: python -m celery -A skillstest.Tests.tasks worker --broker=redis://127.0.0.1:6379
# Check redis data: https://stackoverflow.com/questions/37953019/wrongtype-operation-against-a-key-holding-the-wrong-kind-of-value-php

