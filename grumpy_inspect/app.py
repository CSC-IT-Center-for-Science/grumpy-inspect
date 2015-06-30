from flask import Flask

from flask.ext.mail import Mail

from grumpy_inspect.settings import BaseConfig


app = Flask(__name__)
app.config.from_object(BaseConfig())
mail = Mail()
mail.init_app(app)
