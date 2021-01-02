from http import HTTPStatus
from flask import Flask, make_response, jsonify
from base import BindAPI, DescriptionAPI, ResourceAPI
from utils import authorization_required, api_description, add_property, add_action, logger, register_api
from flask_cors import CORS


@api_description(
    description="Dummy resource api"
)
class DummyResourceAPI(ResourceAPI):
    @add_property(
        name="resource",
        title="Show resource status",
        description="Example of property method",
        properties={"status": {"type": "string"}},
        path="/resource",
        security="basic_sc"
    )
    def get(self):
        pass

    @authorization_required
    def post(self, action):
        if action == "example":
            return self.example()

    @logger
    @add_action(
        name="example",
        title="Example method of action",
        description="Example method of action",
        output={"status": {"type": "string"}},
        path="/resource/example",
        security="basic_sc"
    )
    def example(self):
        return make_response(jsonify({
            "result": "success"
        }), HTTPStatus.OK)

    @staticmethod
    def add_url_rule(_app):
        # TODO may can be automated by using decorators
        view = DummyResourceAPI.as_view('resource_api')
        # Dummy resource API View
        _app.add_url_rule('/resource', view_func=view, methods=['GET', ])
        _app.add_url_rule('/resource/<action>', view_func=view, methods=['POST', ])


# Run server
app = Flask(__name__)
CORS(app)
BindAPI.add_url_rule(app)
DescriptionAPI.add_url_rule(app)
DummyResourceAPI.add_url_rule(app)
register_api()

# app.run(host='0.0.0.0', port=8000)
