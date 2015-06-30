from flask.ext.script import Manager
from grumpy_inspect.server import app

manager = Manager(app)

if __name__ == '__main__':
    manager.run()
