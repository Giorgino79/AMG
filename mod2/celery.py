"""
Celery Configuration - ModularBEF

Configurazione Celery per tasks asincroni e scheduling.
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('modularbef')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Celery Beat Schedule - Tasks periodici
app.conf.beat_schedule = {
    'sync-all-emails-every-3-minutes': {
        'task': 'mail.tasks.sync_all_emails',
        'schedule': 180.0,  # 3 minuti in secondi
        'options': {
            'expires': 120,  # Task scade dopo 2 minuti se non eseguito
        }
    },
}

# Timezone
app.conf.timezone = 'Europe/Rome'
