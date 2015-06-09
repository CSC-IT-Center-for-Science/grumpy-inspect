import datetime
import itertools
import json
import uuid

from flask.ext.sqlalchemy import SQLAlchemy

from grumpy_inspect import checkers

MAX_SAMPLES = 10

db = SQLAlchemy()

enabled_checkers = [
    checkers.always_idle,
    checkers.cpu_idle,
]


def load_column(column):
    try:
        value = json.loads(column)
    except:
        value = {}
    return value


class Sample(db.Model):
    __tablename__ = 'samples'
    id = db.Column(db.String(32), primary_key=True)
    measured_at = db.Column(db.DateTime)
    kind = db.Column(db.String(64))
    value = db.Column(db.PickleType)
    vm_id = db.Column(db.String, db.ForeignKey('vms.id'))

    def __init__(self, kind, value):
        self.id = uuid.uuid4().hex
        self.measured_at = datetime.datetime.utcnow()
        self.kind = kind
        self.value = value


class VirtualMachine(db.Model):
    __tablename__ = 'vms'
    id = db.Column(db.String(32), primary_key=True)
    user_notified_at = db.Column(db.DateTime)
    user_confirmed_at = db.Column(db.DateTime)
    samples = db.relationship("Sample")

    def add_sample(self, kind, value):
        sample = Sample(kind, value)
        sample.vm_id = self.id
        self.samples.append(sample)
        for sample in self.samples[:-MAX_SAMPLES]:
            sample.delete()

    def check_sample(self, sample):
        return any(f(sample) for f in enabled_checkers)

    def currently_idle(self):
        if len(self.samples) > 0:
            return self.check_sample(self.samples[-1])
        else:
            return False

    def idled_since(self):
        active_samples = list(itertools.takewhile(lambda x: self.check_sample(x), reversed(self.samples)))
        if active_samples:
            return active_samples[-1].measured_at
        return None
