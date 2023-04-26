from flask_limiter import Limiter
from flask import Flask,app
import os
from flask_limiter.util import get_remote_address

def is_not_empty_string(s):
    return isinstance(s, str) and len(s.strip()) > 0

MAX_REQUEST_PER_HOUR = os.environ.get("MAX_REQUEST_PER_HOUR", "")

max_count = int(MAX_REQUEST_PER_HOUR) if (is_not_empty_string(MAX_REQUEST_PER_HOUR) and MAX_REQUEST_PER_HOUR.isnumeric()) else 0

limiter_ip_rule = Limiter(key_func=get_remote_address, default_limits=[f"{max_count} per hour"],storage_uri="redis://localhost:6379")