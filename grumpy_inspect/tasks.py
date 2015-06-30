import datetime
import logging
import ldap3

from celery import Celery

from flask import render_template
from flask.ext.mail import Message

from grumpy_inspect.app import app as flask_app
from grumpy_inspect.connectors import process_connectors
from grumpy_inspect.models import db, VirtualMachine, Notification
from grumpy_inspect.utils import query_emails_for_users


config = flask_app.config
app = Celery('tasks', broker=config['MESSAGE_QUEUE_URI'], backend=config['MESSAGE_QUEUE_URI'])
app.conf.CELERY_TASK_SERIALIZER = 'json'
app.conf.CELERYBEAT_SCHEDULE = {
    'query-idle-vms-minute': {
        'task': 'grumpy_inspect.tasks.query_idle_vms',
        'schedule': datetime.timedelta(seconds=config['CHECK_SAMPLES_INTERVAL']),
        'options': {'expires': 120},
    },
    'collect_usage': {
        'task': 'grumpy_inspect.tasks.collect_usage',
        'schedule': datetime.timedelta(seconds=config['COLLECT_SAMPLES_INTERAL']),
        'options': {'expires': 120},
    },
}
app.conf.CELERY_TIMEZONE = 'UTC'


@app.task(name="grumpy_inspect.tasks.notify_users")
def notify_users(notifications):
    if not notifications:
        return
    try:
        emails = query_emails_for_users(notifications.keys())
    except ldap3.core.exceptions.LDAPSocketOpenError:
        logging.error("No LDAP connectivity, unable to notify users")
        # If actual sending is suppressed and also LDAP is unreachable
        # print messages to console for debugging purposes. Else return.
        if not config['MAIL_SUPPRESS_SEND']:
            return
    with flask_app.app_context():
        for user, notification in notifications.items():
            msg = Message('Low cloud resource utilization')
            try:
                msg.recipients = [emails[user]]
            except Exception:
                logging.warn("no email for user %s" % user)
                continue
            msg.sender = config['SENDER_EMAIL']

            # For a multi-part message, set both html and plain text ("body") content
            for (field, template) in (('html', 'report.html'), ('body', 'report.txt')):
                setattr(msg, field, render_template(
                    template, config=config, notification=notification))

            mail = flask_app.extensions.get('mail')
            if not mail:
                raise RuntimeError("mail extension is not configured")

            if not config['MAIL_SUPPRESS_SEND']:
                # this is not strictly necessary, as flask_mail will also suppress sending if
                # MAIL_SUPPRESS_SEND is set
                mail.send(msg)
            else:
                logging.info('Mail sending suppressed in config')
                logging.info('Sending following message to: %s' % user)
                logging.info("#"*80)
                logging.info(msg.body)
                logging.info("^"*80)


@app.task(name="grumpy_inspect.tasks.query_idle_vms")
def query_idle_vms():
    notifications_by_user = {}
    grace_period = datetime.timedelta(seconds=config['LOW_UTILIZATION_GRACE_PERIOD'])
    for vm in VirtualMachine.query.all():
        if not vm.username:
            logging.warn("VM %s has no value in username field, unable to report")
            continue

        # Do not consider VMs which have been running less than grace_period
        if vm.first_seen + grace_period > datetime.datetime.utcnow():
            continue
        # Do not consider VMs which have been reported to user or which user
        # has acked if the event happened within grace_period
        if vm.user_confirmed_at or vm.user_notified_at:
            last_action = vm.user_notified_at
            if vm.user_confirmed_at:
                last_action = vm.user_confirmed_at
            expires = last_action + grace_period
            if expires > datetime.datetime.utcnow():
                continue

        report = vm.check_samples()
        notification = None
        for check, check_result in report['checks'].items():
            # consider VM idle if all samples in list check_results are True
            if all(check_result):
                if not notification:
                    notification = Notification.query.filter_by(username=vm.username).first()
                if not notification:
                    notification = Notification(vm.username)
                    db.session.add(notification)
                notifications_by_user[vm.username] = notification.identifier
        if notification:
            now = datetime.datetime.utcnow()
            notification.last_sent = now
            vm.user_notified_at = now
        db.session.commit()
    notify_users.delay(notifications_by_user)


@app.task(name="grumpy_inspect.tasks.collect_usage")
def collect_usage():
    process_connectors()
