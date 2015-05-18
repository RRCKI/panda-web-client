from flask_restful import Resource
from flask_restful import fields, marshal_with
from app import app, db, lm, api

class IsAliveResource(Resource):
    def get(self):
        return {'status': 'true'}

job_fields = {
    'task':   fields.String,
    'uri':    fields.Url('todo_ep')
}

class JobsResource(Resource):
    def get(self):
        return

    def post(self):
        return


api.add_resource(IsAliveResource, '/m/isAlive')