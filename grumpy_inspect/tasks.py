from celery import Celery
from celery.schedules import crontab

from grumpy_inspect.settings import BaseConfig
from grumpy_inspect.connectors import process_active_vms

config = BaseConfig()
app = Celery('tasks', broker=config['MESSAGE_QUEUE_URI'], backend=config['MESSAGE_QUEUE_URI'])
app.conf.CELERY_TASK_SERIALIZER = 'json'
app.conf.CELERYBEAT_SCHEDULE = {
    'query-idle-vms-minute': {
        'task': 'grumpy_inspect.tasks.query_idle_vms',
        'schedule': crontab(minute='*/1'),
        'options': {'expires': 60},
    },
    'collect_usage': {
        'tasks': 'grumpy_inspect.tasks.collect_usage',
        'schedule': crontab(hour='*/1'),
        'options': {'expires': 60},
    },
}
app.conf.CELERY_TIMEZONE = 'UTC'


@app.task(name="grumpy_inspect.tasks.query_idle_vms")
def query_idle_vms():
    pass


@app.task(name="grumpy_inspect.tasks.collect_usage")
def collect_usage():
    process_active_vms(config)
