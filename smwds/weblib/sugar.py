from flask import json
from werkzeug.wrappers import Response


class ApiResult(object):

    def __init__(self, value, status=200):
        self.value = value
        self.status = status

    def to_response(self):
        return Response(json.dumps(self.value),
                        status=self.status,
                        mimetype='application/json')


class ApiException(Exception):

    def __init__(self, message, status=400):
        self.message = message
        self.status = status

    def to_result(self):
        return ApiResult({'message': self.message, 'r': 1},
                         status=self.status)


@json_api.errorhandler(ApiException)
def api_error_handler(error):
    return error.to_result()


@json_api.errorhandler(403)
@json_api.errorhandler(404)
@json_api.errorhandler(500)
def error_handler(error):
    if hasattr(error, 'name'):
        msg = error.name
        code = error.code
    else:
        msg = error.message
        code = 500
    return ApiResult({'message': msg}, status=code)


def success(res=None, status_code=200):
    res = res or {}

    dct = {
        'r': 1
    }

    if res and isinstance(res, dict):
        dct.update(res)

    return ApiResult(dct, status_code)


def failure(message, status_code):
    dct = {
        'r': 0,
        'status': status_code,
        'message': message
    }
    return dct


def updated(res=None):
    return success(res=res, status_code=204)


def bad_request(message, res=None):
    return failure(message, 400)
