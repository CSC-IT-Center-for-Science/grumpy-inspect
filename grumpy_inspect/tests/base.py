from flask.ext.testing import TestCase

from grumpy_inspect.server import app
from grumpy_inspect.models import db
from grumpy_inspect.settings import TestConfig


class BaseTestCase(TestCase):
    def create_app(self):
        app.dynamic_config = TestConfig()
        app.config.from_object(app.dynamic_config)
        app.config['TESTING'] = True
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
