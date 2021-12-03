import os
from uuid import uuid4
from celery.result import AsyncResult
from flask import jsonify, request, send_from_directory
from concurrent.futures import ThreadPoolExecutor, as_completed

from app import app
from tasks import process_tasks, celery_app
from helpers import get_response, hex_color_valid, is_number


def file_allowed(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[0].lower() not in app.config.get("ALLOWED_TYPES")

    
@app.route("/")
def index():
    return get_response("Application running...")


@app.route("/", methods=["POST"])
def receive_images():
    if "files" not in request.files:
        return get_response("No files attached!", status=400)

    attached_files = request.files.getlist("files")
    if not attached_files[0]:
        return get_response("No files attached!", status=400)

    max_images = app.config.get("MAX_IMAGES")
    if len(attached_files) > max_images:
        return get_response(f"Attached images must not be more than {max_images}", status=400)


    for attached_file in attached_files:
        if not file_allowed(attached_file.filename):
            return get_response(f"{attached_file.filename} is not allowed!", status=400)

    form = request.form
    orientation = form.get("orientation", None)
    border = form.get("border", None)
    border_color = form.get("border_color", None)

    if not orientation or orientation not in app.config.get("ALLOWED_ORIENTATIONS"):
        return get_response("Invalid orientation!", status=400)

    if not border or not is_number(border) or float(border) < 0:
        return get_response("Invalid border", status=400)

    if not border_color or not hex_color_valid(border_color):
        return get_response("Invalid border color", status=400)

    files = []
    def save_file(img_file):
        filename = f"{uuid4()}.png"
        img_file.save(os.path.join(app.config.get("TMP_IMG_DIR"), filename))
        files.append(filename)
        return f"{filename} saved"

    with ThreadPoolExecutor() as executor:
        results = [executor.submit(save_file, img_file) for img_file in attached_files]
        for f in as_completed(results):
            print(f.result())

    task = process_tasks.delay(files, int(border), border_color, orientation)
    return get_response("Task received and queued!", data=task.id, status=200)
    


@app.route("/<string:id>")
def get_combined_image(id):
    task_result = AsyncResult(id, app=celery_app)
    task_status = task_result.status

    msg = "Task still in progress!"
    data = None
    status = 200

    if task_status == "SUCCESS":
        msg = "Collage has been generated"
        data = task_result.get() + ".png"

    elif task_status == "FAILURE":
        msg = "Task failed. Please retry!"
        status = 422

    return get_response(msg, data=data, status=status)


@app.route("/download/<path:name>")
def download_file(name):
    return send_from_directory(
        app.config['RESULTS_DIR'], name, as_attachment=True
    )