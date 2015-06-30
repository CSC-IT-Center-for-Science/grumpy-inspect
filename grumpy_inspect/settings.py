import functools
import os
import yaml

CONFIG_FILE = '/etc/grumpy_inspect/config.yaml'


def resolve_configuration_value(key, default=None, *args, **kwargs):
    pb_key = 'GI_' + key
    value = os.getenv(pb_key)
    if value:
        return value

    CONFIG = {}
    if os.path.isfile(CONFIG_FILE):
        CONFIG = yaml.load(open(CONFIG_FILE).read())
    if key in CONFIG:
        return CONFIG[key]
    elif default:
        return default
    elif not default:
        raise RuntimeError('configuration value for %s missing' % key)


def fields_to_properties(cls):
    for k, default in vars(cls).items():
        if not k.startswith('_'):
            resolvef = functools.partial(resolve_configuration_value, k, default)
            setattr(cls, k, property(resolvef))
    return cls


@fields_to_properties
class BaseConfig(object):
    DEBUG = True
    BASE_URL = 'https://localhost:8888'
    MESSAGE_QUEUE_URI = 'redis://www:6379/0'
    MAIL_SUPPRESS_SEND = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/grumpy.db'
    SQLALCHEMY_RECORD_QUERIES = True
    SENDER_EMAIL = 'grumpy@example.org'
    CHECK_SAMPLES_INTERVAL = 24 * 3600
    COLLECT_SAMPLES_INTERAL = 3600
    LOW_UTILIZATION_GRACE_PERIOD = 14 * 24 * 3600
    LDAP_HOST = 'ldaphost.example.org'
    LDAP_PORT = 636
    LDAP_USER = 'uid=username,ou=org,dc=example,dc=org'
    LDAP_PASSWORD = 'change_me'
    LDAP_SEARCH_BASE = 'ou=Users,dc=example,dc=org'
    # %s will be replaced with the searched username
    LDAP_SEARCH_FILTER = '(&(objectClass=Person)(UserName=%s))'
    LDAP_SEARCHED_ATTRIBUTE = 'mail'
    OS_USERNAME = "username"
    OS_PASSWORD = "change_me"
    OS_TENANT_NAME = "my-tenant"
    OS_TENANT_ID = "my-tenant"
    OS_AUTH_URL = "https://openstack.example.org:5000/v2.0"

    def __getitem__(self, item):
        return getattr(self, item)

    def get(self, key):
        return getattr(self, key)


class TestConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    MAIL_SUPPRESS_SEND = True
