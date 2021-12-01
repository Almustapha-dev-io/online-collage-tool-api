from app import app
from helpers import get_response


@app.errorhandler(500)
def internal_server_error(e):
    return get_response("Something failed on the server!", status=500)


@app.errorhandler(413)
def content_too_long(e):
    size_in_mb = app.config.get("MAX_CONTENT_LENGTH") / (1024 * 1024)
    return get_response(f"Files too large! Max size {size_in_mb}mb", status=413)