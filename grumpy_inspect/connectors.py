import asyncio
import random
import os
from novaclient.v2 import client
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from grumpy_inspect.settings import BaseConfig
from grumpy_inspect.models import Base, VirtualMachine

"""
Connectors to data sources producing usage data
"""

config = BaseConfig()
MAX_CONCURRENT_REQUESTS = 5


def create_database_session():
    engine = create_engine('sqlite:////tmp/grumpy.db')
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def get_openstack_nova_client():
    env = os.environ.copy()
    required = set(('OS_AUTH_URL', 'OS_USERNAME', 'OS_PASSWORD', 'OS_TENANT_NAME'))
    found = set(env.keys()).intersection(required)
    if len(found) != len(required):
        print("Some of following variables are not defined in your environment: %s" % ', '.join(required - found))
        print("Source OpenStack RC file before running this script (available under Access & Security tab)")
        print("e.g. source tenant_openrc.sh")

    os_username = env['OS_USERNAME']
    os_password = env['OS_PASSWORD']
    os_tenant_name = env['OS_TENANT_NAME']
    os_auth_url = env['OS_AUTH_URL']
    return client.Client(os_username, os_password, os_tenant_name, os_auth_url)


@asyncio.coroutine
def fetch_cpu_utilization(vm):
    with (yield from sem):
        wait_time = random.randint(1, 2)
        yield from asyncio.sleep(wait_time)
        print("cpu for %s processed, took %s secs" % (vm, wait_time))
        val = random.random()
        vm.add_sample('cpu_util', val)
        return val


def fetch_another_metric(vm):
    with (yield from sem):
        wait_time = random.randint(1, 2)
        yield from asyncio.sleep(wait_time)
        print("another metric for %s processed, took %s secs" % (vm, wait_time))
        val = random.random()
        vm.add_sample('another_metric', val)
    return val


collectors = (
    fetch_cpu_utilization,
)


@asyncio.coroutine
def collect_usage_for(vms):
    for f in collectors:
        coroutines = [f(vm) for vm in vms]
        results = yield from asyncio.gather(*coroutines)
        print(results)


def process_active_vms():
    nc = get_openstack_nova_client()
    servers = nc.servers.list()
    vms = []
    session = create_database_session()
    for server in servers:
        vm = session.query(VirtualMachine).filter(VirtualMachine.id == server.id).first()
        if not vm:
            vm = VirtualMachine(server.id)
        vms.append(vm)

if __name__ == '__main__':
    vms = []
    session = create_database_session()
    for i in range(10):
        vm = session.query(VirtualMachine).filter(VirtualMachine.id == i).first()
        if not vm:
            vm = VirtualMachine('%s' % i)
        vms.append(vm)
    sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(collect_usage_for(vms))

    for vm in vms:
        session.add(vm)
        for sample in vm.old_samples():
            print("Deleting")
            session.delete(sample)

        print(vm.id, vm.samples)
    session.commit()
    for vm in session.query(VirtualMachine).all():
        print([x.value for x in vm.samples])
