class BaseConfig(object):
    MESSAGE_QUEUE_URI = 'redis://www:6379/0'
    SQLALCHEMY_DATABASE_URI = '/tmp/grumpy.db'

    def __getitem__(self, item):
        return getattr(self, item)
