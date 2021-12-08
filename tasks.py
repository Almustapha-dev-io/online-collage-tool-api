import os
from datetime import datetime
from time import time
from PIL import Image
from uuid import uuid4
from celery import Celery, result, schedules, chain
from concurrent.futures import ThreadPoolExecutor
from helpers import create_dir, map_files_to_image

temp_image_dir = create_dir("images")
results_dir = create_dir("resized")


BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
BACKEND_URL = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
BASE_SIZE = 640

celery_app = Celery("tasks", broker=BROKER_URL, backend=BACKEND_URL)
celery_app.conf.beat_schedule = {
    "remove-stale-files-every-sunday": {
        "task": "tasks.delete_old_images",
        "schedule": schedules.crontab(day_of_week=0)
    }
}
celery_app.conf.timezone = 'UTC'

def vertical_combine(files, border, border_color):
    files = map_files_to_image(files, temp_image_dir)
    total_files = len(files)
    total_height = 0

    for img_file in files:
        total_height += img_file.size[1]

    height = total_height + ((1 + total_files) * border)
    width = BASE_SIZE + (2 * border)

    combined_img = Image.new("RGBA", (width, height), border_color)
    prev_img_height = 0

    for i, img in enumerate(files):
        top_offset = prev_img_height + ((i + 1) * border)
        combined_img.paste(img, (border, top_offset))
        prev_img_height += img.size[1]

    return combined_img


def horizontal_combine(files, border, border_color):
    files = map_files_to_image(files, temp_image_dir)
    total_files = len(files)
    total_width = 0

    for img_file in files:
        total_width += img_file.size[0]

    width = total_width + ((1 + total_files) * border)
    height = BASE_SIZE + (2 * border)

    combined_img = Image.new("RGBA", (width, height), border_color)
    prev_img_width = 0

    for i, img in enumerate(files):
        left_offset = prev_img_width + ((i + 1) * border)
        combined_img.paste(img, (left_offset, border))
        prev_img_width += img.size[0]

    return combined_img


def resize_image(filename, orientation):
    try:
        print(f"Resizing {filename}...")
        img = Image.open(os.path.join(temp_image_dir, filename))

        if orientation == "vertical":
            width = BASE_SIZE
            width_percent = width / float(img.size[0])
            height = int(float(img.size[1]) * float(width_percent))

        else:
            height = BASE_SIZE
            height_percent = height / float(img.size[1])
            width = int(float(img.size[0]) * float(height_percent))

        img = img.resize((width, height), Image.ANTIALIAS)
        filename = filename.rsplit(".", 1)[0] + ".png"
        img.save(os.path.join(temp_image_dir, filename), "png")

        return filename

    except Exception as e:
        print(e)
        return None


def delete_img(filename):
    try:
        print(f"Deleting {filename}...")
        file_path = os.path.join(temp_image_dir, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return f"Deleted {filename}!"

    except Exception as e:
        print(e)    
        return None


@celery_app.task
def delete_temp_images(files):
    with ThreadPoolExecutor() as executor:
        results = executor.map(delete_img, files)
        for result in results:
            print(f"{result} resized!")


@celery_app.task
def resize_images(files, orientation):
    files = [(file_name, orientation) for file_name in files]
    new_filenames = []
    
    with ThreadPoolExecutor() as executor:
        results = executor.map(resize_image, *zip(*files))
        for result in results:
            print(result)
            if result:
                new_filenames.append(result)

    return new_filenames


@celery_app.task
def combine_images(files, file_id, border, border_color, orientation):
    if orientation == "vertical":
        new_image = vertical_combine(files, border, border_color)

    else:
        new_image = horizontal_combine(files, border, border_color)

    delete_temp_images.delay(files)
    new_image.save(os.path.join(results_dir, f"{file_id}.png"), "png")


@celery_app.task
def process_tasks(files, border, border_color, orientation):
    file_id = uuid4()
    res = resize_images.apply_async(
        (files, orientation),
        link=combine_images.s(
            file_id,
            border,
            border_color,
            orientation
        )
    )

    return file_id


@celery_app.task
def delete_old_images():
    cur_date = datetime.fromtimestamp(time())
    for filename in os.listdir(results_dir):
        file_path = os.path.join(results_dir, filename)
        if os.path.exists(file_path):
            created_date = datetime.fromtimestamp(os.path.getctime(file_path))
            date_diff = cur_date - created_date

            # Remove files that are up to 2 weeks old
            if (date_diff.days >= 14):
                os.remove(file_path)
