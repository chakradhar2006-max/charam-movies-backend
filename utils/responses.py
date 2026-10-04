from flask import jsonify


def ok(data=None, message="Success", status=200):
    body = {"success": True, "message": message}
    if data is not None:
        body["data"] = data
    return jsonify(body), status


def err(message="Something went wrong", status=400, data=None):
    body = {"success": False, "message": message}
    if data is not None:
        body["data"] = data
    return jsonify(body), status
