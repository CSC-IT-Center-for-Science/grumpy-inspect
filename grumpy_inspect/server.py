"""
Server endpoint with ReST API.
"""
import datetime
from flask.ext.restful import marshal_with, fields
from flask.ext import restful
from grumpy_inspect.app import app
from grumpy_inspect.settings import BaseConfig
from grumpy_inspect.models import db, VirtualMachine, Notification
config = BaseConfig()


class VirtualMachineView(restful.Resource):
    def put(self, vm_id):
        vm = VirtualMachine.query.filter_by(identifier=vm_id).first_or_404()
        vm.user_confirmed_at = datetime.datetime.utcnow()
        db.session.commit()

vm_fields = {
    'identifier': fields.String,
    'username': fields.String,
    'util_report': fields.String
}

notification_fields = {
    'vms': fields.List(fields.Nested(vm_fields))
}


class NotificationView(restful.Resource):
    @marshal_with(notification_fields)
    def get(self, notification_id):
        notification = Notification.query.filter_by(identifier=notification_id).first()
        q = VirtualMachine.query
        q = q.filter(
            VirtualMachine.username == notification.username,
            VirtualMachine.user_notified_at > '1970-01-01',
            VirtualMachine.user_confirmed_at == None)
        return {'vms': q.all()}
api = restful.Api(app)
api.add_resource(VirtualMachineView, '/api/vms/<string:vm_id>')
api.add_resource(NotificationView, '/api/notifications/<string:notification_id>')

if __name__ == '__main__':
    app.run(debug=True)
