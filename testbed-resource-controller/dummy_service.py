from http import HTTPStatus
from flask import Flask, jsonify, make_response
from base import BindAPI, ServiceAPI
from utils import abort_json, authorization_required, resource_required


class DummyServiceAPI(ServiceAPI):
    @authorization_required
    def get(self):
        pass

    @authorization_required
    def post(self, action):
        print(action)
        if action == "fake":
            return self.fake()
        else:
            return abort_json(HTTPStatus.BAD_REQUEST, "Invalid action.")

    @resource_required({
        "name": "dummy",
        "url": "http://localhost:8001"
    })
    def fake(self, resource=None):
        # Decorator will bind the resource automatically, and store the information to the argument 'resource'
        response = make_response(jsonify({
            "name": resource["name"],
            "url": resource["url"]
        }), HTTPStatus.OK)
        return response

    @staticmethod
    def add_url_rule(_app):
        view = DummyServiceAPI.as_view('service_api')
        # Dummy resource API View
        _app.add_url_rule('/service', view_func=view, methods=['GET', ])
        _app.add_url_rule('/service/<action>', view_func=view, methods=['POST', ])


# Run server
app = Flask(__name__)
BindAPI.add_url_rule(app)
DummyServiceAPI.add_url_rule(app)

# app.run(host='0.0.0.0', port=8000)
