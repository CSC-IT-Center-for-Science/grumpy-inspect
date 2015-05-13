import os
import itertools
import logging
from novaclient.v2 import client

logging.captureWarnings(True)


def get_openstack_nova_client():
    env = os.environ.copy()
    required = set(('OS_AUTH_URL', 'OS_USERNAME', 'OS_PASSWORD', 'OS_TENANT_NAME'))
    found = set(env.keys()).intersection(required)
    if len(found) != len(required):
        print "Some of following variables are not defined in your environment: %s" % ', '.join(required - found)
        print "Source OpenStack RC file before running this script (available under Access & Security tab)"
        print "e.g. source tenant_openrc.sh"
        return

    os_username = env['OS_USERNAME']
    os_password = env['OS_PASSWORD']
    os_tenant_name = env['OS_TENANT_NAME']
    os_auth_url = env['OS_AUTH_URL']
    return client.Client(os_username, os_password, os_tenant_name, os_auth_url)


def main():
    cli = get_openstack_nova_client()
    if not cli:
        return
    servers = cli.servers.list()

    cold_instances = [s for s in servers if s.status != 'ACTIVE']
    if cold_instances:
        print
        print "! Following instances are reserving resources but not in the running state."
        print "? Terminate these instances if they are not needed."
        print "? Otherwise consider snapshotting an instance into a volume if you plan to use it later at some point."
        for instance in cold_instances:
            print "\t- %s (%s, in state %s)" % (instance.name, instance.id, instance.status)


    def unsafe(x):
        for rule in x.rules:
            if rule['ip_range'].get('cidr', '').endswith("/0"):
                return True


    def format_rules(rules):
        return ', '.join(["%s: %s %s-%s" % (rule['ip_protocol'], rule['ip_range'].get('cidr', '???'), rule['from_port'], rule['to_port']) for rule in rules])

    security_groups = cli.security_groups.list()
    groups_open_to_world = [sg for sg in security_groups if unsafe(sg)]

    if groups_open_to_world:
        print
        print "! Following security groups include rules allowing inbound connections from everywhere"
        print "? If not necessary, consider restricting access to certain subnets only"
        for group in groups_open_to_world:
            print "\t- %s (%s)" % (group.name, format_rules(group.rules))

    security_groups_available = set([sg.name for sg in security_groups])
    security_groups_used = set(itertools.chain.from_iterable([[g['name'] for g in s.security_groups] for s in servers]))

    unused_security_groups = security_groups_available.difference(security_groups_used)
    if unused_security_groups:
        print
        print "! Following security groups are defined but not associated with any instance"
        print "? Consider removing these security groups if they are not longer need"
        for sg in unused_security_groups:
            print "\t-", sg


if __name__ == '__main__':
    main()
