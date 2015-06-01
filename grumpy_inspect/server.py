from flask import Flask
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

class Index(Resource):
    def get(self, token):
        return {'token': token}

api.add_resource(Index, '/api/<string:token>')

if __name__ == '__main__':
    app.run(debug=True)
