"""
SQLAlchemy models for Grumpy Inspect
"""
import datetime
import json
import uuid
from flask.ext.sqlalchemy import SQLAlchemy

from grumpy_inspect.app import app
from grumpy_inspect import checkers

MAX_SAMPLES = 10

ENABLED_CHECKERS = {
    'cpu_util': checkers.cpu_idle,
}

db = SQLAlchemy(app)
db.create_all()


def load_column(column):
    """
    Load data in as JSON object if possible.
    If successfull return the loaded object, else return empty object.
    """
    try:
        value = json.loads(column)
    except ValueError:
        value = {}
    return value


class Sample(db.Model):
    """
    Sample is one metering result produced by a checker and associated with one
    VirtualMachine.
    """
    __tablename__ = 'samples'
    identifier = db.Column('id', db.String(36), primary_key=True)
    measured_at = db.Column(db.DateTime)
    kind = db.Column(db.String(64))
    value = db.Column(db.PickleType)
    vm_id = db.Column(db.String, db.ForeignKey('vms.id'))

    def __init__(self, kind, value):
        self.identifier = uuid.uuid4().hex
        self.measured_at = datetime.datetime.utcnow()
        self.kind = kind
        self.value = value


class VirtualMachine(db.Model):
    """
    VirtualMachine corresponds to one real virtual machine on cloud.
    """
    __tablename__ = 'vms'
    identifier = db.Column('id', db.String(36), primary_key=True)
    username = db.Column(db.String(128))
    user_notified_at = db.Column(db.DateTime)
    user_confirmed_at = db.Column(db.DateTime)
    first_seen = db.Column(db.DateTime)
    util_report = db.Column(db.Text)
    samples = db.relationship("Sample")

    def __init__(self, identifier, username):
        self.username = username
        self.identifier = identifier
        self.first_seen = datetime.datetime.utcnow()

    def add_sample(self, kind, value):
        """Create new metering sample for VirtualMachine"""
        sample = Sample(kind, value)
        sample.vm_id = self.identifier
        self.samples.append(sample)

    def old_samples(self):
        """Return samples which are considered obsolete"""
        return self.samples[:-MAX_SAMPLES]

    def get_samples(self, kind):
        return Sample.query.filter_by(vm_id=self.identifier).filter_by(kind=kind).all()

    def check_samples(self):
        """
        Return the result of runnign all enabled checkers against the samples
        belonging to this VirtualMachine.
        """
        result = {}
        result['checks'] = dict(
            (k, [checker(sample) for sample in self.get_samples(k)])
            for (k, checker) in ENABLED_CHECKERS.items()
        )
        result['id'] = self.identifier
        return result


class Notification(db.Model):
    __tablename__ = 'notifications'
    identifier = db.Column('id', db.String(36), primary_key=True)
    username = db.Column(db.String(64))
    last_sent = db.Column(db.DateTime)

    def __init__(self, username):
        self.identifier = uuid.uuid4().hex
        self.username = username

    def get_user_vms(self):
        return VirtualMachine.query.filter_by(username=self.username).all()
