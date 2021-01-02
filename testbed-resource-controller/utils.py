import os
import requests
import redis
import json

from http import HTTPStatus
from urllib.parse import urljoin
from functools import wraps
from flask import abort, request, jsonify, make_response


# TODO hard-coded and duplicated call. Better to globally call once
db = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


def abort_json(status_code, error_message):
    response = make_response(jsonify({
        "errorMessage": error_message
    }), status_code)
    abort(response)


def authentication_required(f):
    """
    authentication_required: a decorator to check authentication of requests
    :param f: original function to decorate
    :return: authentication function as a decorator
    """
    @wraps(f)
    def check_authentication(self, *args, **kwargs):
        # Every HTTP request should contain 'USER-ID' header
        user_id = request.headers.get('USER-ID')

        # Raise 401 Unauthorized error if user id is not set
        if user_id is None:
            abort_json(HTTPStatus.UNAUTHORIZED, "Authentication Failed.")

        # Finish the remaining process
        return f(self, *args, **kwargs)
    return check_authentication


def authorization_required(f):
    """
    authorization_required: a decorator to check authorization of requests according to bound status
    :param f: original function to decorate
    :return: authorization function as a decorator
    """
    @wraps(f)
    @authentication_required
    def check_authorization(self, *args, **kwargs):
        user_id = request.headers.get('USER-ID')

        # Raise 401 error if the resource is not bound
        if not self.redis.exists('user_id'):
            abort_json(HTTPStatus.UNAUTHORIZED, "Resource not bound.")

        # Raise 409 Conflict error if the resource is already bound to another user
        if self.redis.get('user_id') != user_id:
            abort_json(HTTPStatus.CONFLICT, "Resource bound to another user.")

        return f(self, *args, **kwargs)
    return check_authorization


def resource_required(resource_description):
    """
    resource_required: a decorator to indicate required resources for the action
    :param resource_description: url of required resource
    :return: resource binding function as a decorator
    """
    # TODO currently, allow single resource only: extend to multiple resources
    # TODO currently, directly specify url of the required resource: extend to use registry and discovery
    def decorator(f):
        @wraps(f)
        def bind_resource(self, *args, **kwargs):
            # TODO how to pass resource information to service?
            url = resource_description["url"]

            # Use the service's user id to control resources
            user_id = self.redis.get('user_id')
            headers = {'USER-ID': user_id}

            # Bind the resource
            bind_response = requests.post(url=urljoin(base=url, url='user/bind'),
                                          headers=headers)

            if bind_response.status_code == HTTPStatus.OK:
                # Binding successful

                resource = {
                    "name": resource_description["name"],
                    "url": resource_description["url"]
                }

                # Service action
                result = f(self, resource, *args, **kwargs)

                # Unbind the resource
                unbind_response = requests.post(url=urljoin(base=url, url='user/unbind'),
                                                headers=headers)

                return result
            else:
                # Binding failed
                # TODO error code
                abort_json(HTTPStatus.CONFLICT, "Resource bound to another user.")
        return bind_resource
    return decorator


def api_description(description): # for storing api description into redis(db) 
    """
    api_description: a decorator for decorating API to construct description and register automatically
    :param description: description of the API
    :return:
    """
    def decorator(cls):
        api_dict = {
            "@context": [
                "https://www.w3.org/2019/wot/td/v1",
                {"@language": "en"}
            ],
            "id": "webeng:{name}:{id}".format(name=os.environ.get('NAME').lower(),
                                              id=os.environ.get('ID')),
            "title": "WebEng-{name}".format(name=os.environ.get('NAME')),
            "url": os.environ.get('URL'),
            "description": description,
            "securityDefinitions": {
                "nosec_sc": {
                    "scheme": "nosec"
                },
                "basic_sc": {
                    "scheme": "basic",
                    "in": "header",
                    "name": "USER-ID"
                }
            },
            "security": "basic_sc"
        }
        db.set('description', json.dumps(api_dict))

        return cls
    return decorator


def get_description():
    """
    get_description: get the description stored in redis server
    :return:
    """
    description = db.get("description")
    if description:
        api_dict = json.loads(description)
        properties_dict = json.loads(db.get('properties'))
        actions_dict = json.loads(db.get('actions'))

        api_dict['properties'] = properties_dict
        api_dict['actions'] = actions_dict

        return api_dict
    return None

# here -> parameter typeerror
def register_api():
#def register_api(description):
    """
    register_api: register the description of APIs stored in redis server
    :return:
    """
    api_dict = get_description()

    if api_dict:
        # TODO scheme
        data = {
            "raw_description": json.dumps(api_dict)
        }

        # TODO url hard-coded
        requests.post(url='http://143.248.47.96:8000/api/services/', data=data)


def add_property(name, title, description, properties, path, security="basic_sc"):
    """
    add_property: a decorator that add a property for API, based on WoT things format
    :param name: name of the property
    :param title: title of the property
    :param description: human-readable short description of the property
    :param properties: sub-properties of the property
    :param path: url to get the information of the property
    :param security: authorization level of the property
    :return: None
    """
    def decorator(f):
        new_property_dict = {
            name: {
                "title": title,
                "type": "object",
                "description": description,
                "properties": properties,
                "required": list(properties.keys()),
                "forms": [{
                    "href": os.environ.get('URL') + path,
                    "htv:methodName": "GET",  # Assume every property is GET
                    "security": security
                }]
            }
        }
        f.__property = new_property_dict

        properties_dict = db.get('properties')
        if properties_dict:
            properties_dict = json.loads(properties_dict)
        else:
            properties_dict = {}

        properties_dict.update(new_property_dict)
        db.set('properties', json.dumps(properties_dict))

        return f
    return decorator


def add_action(name, title, description, output, path, security="basic_sc", input=None):
    """
    add_action: a decorator that add an action for API, based on WoT things format
    :param name: name of the action
    :param title: title of the action
    :param description: human-readable short description of the action
    :param output: a dictionary for the output properties of the action
    :param path: url to get the information of the action
    :param security: authorization level of the action
    :param input: a dictionary for the input properties of the action
    :return: None
    """
    def decorator(f):
        new_action_dict = {
            name: {
                "title": title,
                "type": "object",
                "description": description,
                "output": {
                    "type": "object",
                    "properties": output
                },
                "required": [list(output.keys())],
                "forms": [{
                    "href": os.environ.get('URL') + path,
                    "htv:methodName": "POST",  # Assume every action is POST
                    "security": security
                }]
            }
        }
        
        if input is not None:
            new_action_dict[name]["input"] = {
                "type": "object",
                "properties": input
            }

        f.__action = new_action_dict

        actions_dict = db.get('actions')
        if actions_dict:
            actions_dict = json.loads(actions_dict)
        else:
            actions_dict = {}

        actions_dict.update(new_action_dict)
        db.set('actions', json.dumps(actions_dict))

        return f
    return decorator


def logger(f):
    """
    logger: a decorator to enable logging to a method
    :param f: original function to decorate
    :return: function with logger attached
    """
    @wraps(f)
    def log(self, *args, **kwargs):

        # TODO currently, simple rest API is provided to collect raw data
        url = "http://143.248.47.96:8000/api/data/"

        # Get user ID
        user_id = request.headers.get('USER-ID')

        # Generate request ID
        import random
        import string
        request_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

        # Action
        result = f(self, *args, **kwargs)

        data = {
            "type": type(self).__name__,
            "id": request_id,
            "user_id": str(user_id),
            "bounded_user_id": str(self.redis.get('user_id')),
            "request_ip": str(request.remote_addr),
            "function_name": f.__name__,
            "function_argument": {
                "args": str(args),
                "kwargs": str(kwargs)
            },
            "function_result": str(result)
        }

        requests.post(url=url, data=data)

        return result
    return log
