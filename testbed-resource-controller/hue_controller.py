#from flask import Flask, jsonify, abort, make_response
#from base import BindAPI, ResourceAPI, authorization_required ,authentication_required, abort_json

from http import HTTPStatus
from flask import Flask, jsonify, make_response
from base import BindAPI, ResourceAPI, DescriptionAPI
from utils import authorization_required, register_api, add_property, add_action, abort_json, api_description, logger

from flask_cors import CORS
import redis
import requests
import json

@api_description( # mistake for api_description vs register_api
    description="hue resource api"
)
class hueAPI(ResourceAPI):
    
    def __init__(self):
        super().__init__()
    
        self.hue_urls = None

        with open('hue_url_set.json') as urls:
            self.hue_urls = json.load(urls)

    @authorization_required
    @add_property(
        name="resource",
        title="Show resource info",
        description="It shows status indicating on or off",
        properties={"status": {"type": "string"}},
        path="/resource",
        security="basic_sc"
    )
    def get(self):
        #url = 'http://143.248.49.87:88/api/XAI8Yvp26NTLSxP0uGurWuI091Qxj65C2VFjSsr2/lights'
        try: 
            #return self.status()
            return self.status_newV()
        except:
            #abort(400, description="abort in get()")
            abort_json(HTTPStatus.BAD_REQUEST, "abort in get()")
        #return res.text, 200
        #return status

    def status_newV(self):
        res = requests.get(self.hue_urls['status'])
        if res.status_code == 200:
            #res_dict = json.loads(res) # error
            content = res.content
            content.decode('utf-8')
            res_dict = json.loads(content)

            hueState = res_dict['2']
            state = hueState['state']
            if state['on'] == True:
                self.redis.set('status', "On")
                return make_response(jsonify({"status": self.redis.get('status')}), 200)
            else:
                self.redis.set('status', "Off")
                return make_response(jsonify({"status": self.redis.get('status')}), 200)
        else:
            abort_json(HTTPStatus.BAD_REQUEST, "abort in status()")

    def status(self): # not used -> deprecated
        try:
            res = requests.get(self.hue_urls['status'])
            text_res = res.text
        except:
            abort_json(HTTPStatus.BAD_REQUEST, "abort in status()")
        return make_response(jsonify(text_res), HTTPStatus.OK)

    @authorization_required
    def post(self, action):
        #url = 'http://143.248.49.87:88/api/XAI8Yvp26NTLSxP0uGurWuI091Qxj65C2VFjSsr2/lights/2/state'

        # I don't know exact reason but, when I don't call action by 'self', hueAPI can't recognize redis variable in superclass
        '''
        if action == "on":
            on_message_body = {"on": True, "sat": 254, "bri": 254, "hue": 10000}
            res = requests.put(url, data=json.dumps(on_message_body))
            if res.status_code == 200:
                return jsonify(res.text), 200
            else: abort(400, description="abort in post() for on")

        elif action == "off":
            off_message_body = {"on": False}
            res = requests.put(url, data=json.dumps(off_message_body))
            if res.status_code == 200:
                return jsonify(res.text), 200
            else: abort(400, description="abort in post() for off")

        else: abort(400, description="wrong action name")
        '''
        if action == "on":
            return self.on()

        elif action == "off":
            return self.off()

        else:
            #abort(400, description="Invalid action")
            abort_json(HTTPStatus.BAD_REQUEST, "Invalid action.")

    @logger
    @add_action(
        name="on",
        title="Turn on the hue",
        description="This mean turn on action",
        output={"status": {"type": "string"}},
        path="/resource/on",
        security="basic_sc"
    )
    def on(self):
        on_message_body = {"on": True, "sat": 254, "bri": 254, "hue": 10000}
        #res = requests.put('http://143.248.49.87:88/api/XAI8Yvp26NTLSxP0uGurWuI091Qxj65C2VFjSsr2/lights/2/state',data=json.dumps(on_message_body))
        
        res = requests.put(self.hue_urls['action'],data=json.dumps(on_message_body))

        self.redis.set('status', "On")
        if res.status_code == 200:
            #return make_response(jsonify(res.text), HTTPStatus.OK)
            return make_response(jsonify({"status": self.redis.get('status')}), 200)
        else:
            #abort(400, description="abort in post() for on")
            abort_json(HTTPStatus.BAD_REQUEST, "abort in post() about on func")

    @logger
    @add_action(
        name="off",
        title="turn off the hue",
        description="this mean turn off action",
        output={"status": "string"},
        path="/resource/off",
        security="basic_sc"
    )
    def off(self):
        off_message_body = {"on": False}
        #res = requests.put('http://143.248.49.87:88/api/XAI8Yvp26NTLSxP0uGurWuI091Qxj65C2VFjSsr2/lights/2/state',data=json.dumps(off_message_body))
        
        res = requests.put(self.hue_urls['action'],data=json.dumps(off_message_body))

        self.redis.set('status', "Off")
        if res.status_code == 200:
            #return make_response(jsonify(res.text), HTTPStatus.OK)
            return make_response(jsonify({"status": self.redis.get('status')}), 200)
        else:
            #abort(400, description="abort in post() for off")
            abort_json(HTTPStatus.BAD_REQUEST, "abort in post() about off func")

    @staticmethod
    def add_url_rule(_app):
        view = hueAPI.as_view('resource_api')
        # hue resource API View
        _app.add_url_rule('/resource', view_func=view, methods=['GET', ])
        _app.add_url_rule('/resource/<action>', view_func=view, methods=['POST', ])


# Run server
#if __name__ == "__main__":
app = Flask(__name__)
CORS(app)
BindAPI.add_url_rule(app)
DescriptionAPI.add_url_rule(app)
hueAPI.add_url_rule(app)

register_api()
    #app.run(host='0.0.0.0', port=5000)
