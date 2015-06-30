"""
Connectors to fetch meterings from data sources
"""
import asyncio
import logging
import random
from novaclient.v2 import client
from grumpy_inspect.settings import BaseConfig
from grumpy_inspect.models import db, VirtualMachine

MAX_CONCURRENT_REQUESTS = 5
sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
config = BaseConfig()


def get_openstack_nova_client():
    """Return nova client object used to communicate with OpenStack API"""
    return client.Client(config.OS_USERNAME, config.OS_PASSWORD, config.OS_TENANT_NAME, config.OS_AUTH_URL)


@asyncio.coroutine
def fetch_cpu_utilization(vm):
    """
    Produces dummy data
    """
    with (yield from sem):
        wait_time = random.randint(1, 2)
        yield from asyncio.sleep(wait_time)
        logging.debug("cpu for %s processed, took %s secs" % (vm, wait_time))
        val = random.random()
        vm.add_sample('cpu_util', val)
        return val


collectors = (
    fetch_cpu_utilization,
)


@asyncio.coroutine
def collect_usage_for(vms):
    """
    Run metering functions asynchronously for each VirtualMachine in vms.
    """
    for f in collectors:
        coroutines = [f(vm) for vm in vms]
        result = yield from asyncio.gather(*coroutines)
        return result


@asyncio.coroutine
def process_active_vms(config):
    """
    Retrieve list of active virtual machines from OpenStack and call for
    metering functions for each virtual machine.
    """
    nc = get_openstack_nova_client()
    servers = nc.servers.list()
    vms = []
    for server in servers:
        vm = VirtualMachine.query.filter_by(identifier=server.id).first()
        if not vm:
            vm = VirtualMachine(server.id, server.user_id)
            db.session.add(vm)
        vms.append(vm)
    yield from collect_usage_for(vms)
    db.session.commit()

    # Purge old samples from DB
    for vm in vms:
        for old_sample in vm.old_samples():
            db.session.delete(old_sample)

    # Purge old VMs
    vms_in_db = set(vm.identifier for vm in VirtualMachine.query.all())
    active_vms = set(server.id for server in servers)
    terminated_vms = vms_in_db - active_vms
    for vm in vms:
        if vm.identifier in terminated_vms:
            for sample in vm.samples:
                db.session.delete(sample)

    db.session.commit()

    for old_sample in vm.old_samples():
        db.session.delete(old_sample)

    db.session.commit()


def process_connectors():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(process_active_vms(config))


def main():
    process_connectors()
    for vm in VirtualMachine.query.all():
        print(vm.identifier, [x.value for x in vm.samples])


if __name__ == '__main__':
    main()
