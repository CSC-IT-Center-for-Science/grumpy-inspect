import datetime
import itertools
import json
import uuid
from sqlalchemy import Column, String, DateTime, PickleType, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from grumpy_inspect import checkers

MAX_SAMPLES = 10

Base = declarative_base()

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


class Sample(Base):
    __tablename__ = 'samples'
    id = Column(String(32), primary_key=True)
    measured_at = Column(DateTime)
    kind = Column(String(64))
    value = Column(PickleType)
    vm_id = Column(String, ForeignKey('vms.id'))

    def __init__(self, kind, value):
        self.id = uuid.uuid4().hex
        self.measured_at = datetime.datetime.utcnow()
        self.kind = kind
        self.value = value


class VirtualMachine(Base):
    __tablename__ = 'vms'
    id = Column(String(32), primary_key=True)
    user_notified_at = Column(DateTime)
    user_confirmed_at = Column(DateTime)
    samples = relationship("Sample")

    def __init__(self, id):
        self.id = id

    def add_sample(self, kind, value):
        sample = Sample(kind, value)
        sample.vm_id = self.id
        self.samples.append(sample)

    def old_samples(self):
        return self.samples[:-MAX_SAMPLES]

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
