import os
from functools import wraps
from flask import request, jsonify

def is_not_empty_string(s):
    return isinstance(s, str) and len(s.strip()) > 0

def auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        AUTH_SECRET_KEY = os.environ.get("AUTH_SECRET_KEY", "")
        if is_not_empty_string(AUTH_SECRET_KEY):
            try:
                authorization = request.headers.get("Authorization")
                if not authorization or authorization.replace("Bearer ", "").strip() != AUTH_SECRET_KEY.strip():
                    raise ValueError("Error: 无访问权限 | No access rights")
                return  f(*args, **kwargs)
            except ValueError as e:
                return jsonify(status="Unauthorized", message=str(e), data=None)
        else:
            return f(*args, **kwargs)

    return decorated_function
