import hmac
from functools import wraps
from flask import request, current_app, abort


def check_netbox_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        x_hook_signature = request.headers.get('X-Hook-Signature', None)
        content_length = int(request.headers.get('Content-Length', 0))

        if content_length > 1_000_000:
            # To prevent memory allocation attacks
            abort(400, "Content too long")

        if x_hook_signature:
            # Check signature
            raw_input = request.data
            input_hmac = hmac.new(key=current_app.config.NETBOX_SECRET.encode(), msg=raw_input, digestmod="sha512")
            if not hmac.compare_digest(input_hmac.hexdigest(), x_hook_signature):
                abort(400, "Invalid message signature")
        else:
            abort(400, "No message signature to check")
        return f(*args, **kwargs)

    return decorated
