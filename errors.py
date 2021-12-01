from app import app
from helpers import get_response


@app.errorhandler(500)
def internal_server_error(e):
    return get_response("Something failed on the server!", status=500)


@app.errorhandler(413)
def content_too_long(e):
    return get_response(f"Files too large! Max size {16}mb", status=413)