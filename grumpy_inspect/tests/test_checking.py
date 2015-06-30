import uuid

from grumpy_inspect.tests.base import BaseTestCase
from grumpy_inspect.models import db, VirtualMachine


class TestCase(BaseTestCase):
    def setUp(self):
        db.create_all()
        vm1 = VirtualMachine(uuid.uuid4().hex, 'username_abc')
        vm1.add_sample('cpu_util', 0.01)
        vm1.add_sample('cpu_util', 0.011)
        vm1.add_sample('cpu_util', 0.008)
        vm1.add_sample('some_meter', 0.5)
        vm1.add_sample('some_meter', 0.99)
        vm1.add_sample('some_meter', 0.80)
        self.known_idle_vm_id = vm1.identifier

        vm2 = VirtualMachine(uuid.uuid4().hex, 'username_abc')
        vm2.add_sample('cpu_util', 0.99)
        vm2.add_sample('cpu_util', 0.92)
        vm2.add_sample('cpu_util', 0.8)
        self.known_busy_vm_id = vm2.identifier

        db.session.add(vm1)
        db.session.add(vm2)
        db.session.commit()

    def test_cpu_low_utilization_triggers(self):
        vm = VirtualMachine.query.filter_by(identifier=self.known_idle_vm_id).first()
        report = vm.check_samples()
        assert all(report['cpu_util'])
        assert report['id'] == self.known_idle_vm_id

    def test_cpu_high_utilization_nop(self):
        vm = VirtualMachine.query.filter_by(identifier=self.known_busy_vm_id).first()
        report = vm.check_samples()
        assert not all(report['cpu_util'])
