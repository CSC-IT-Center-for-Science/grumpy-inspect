class BaseConfig(object):
    MESSAGE_QUEUE_URI = 'redis://www:6379/0'

    def __getitem__(self, item):
        return getattr(self, item)
