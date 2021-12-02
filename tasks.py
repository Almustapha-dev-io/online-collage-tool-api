from os import path, environ
from uuid import uuid4
from PIL import Image
from celery import Celery, result
from helpers import create_dir, map_files_to_image

temp_image_dir = create_dir("images")
results_dir = create_dir("resized")


BROKER_URL = environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
BACKEND_URL = environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
BASE_SIZE = 640

celery_app = Celery("tasks", broker=BROKER_URL, backend=BACKEND_URL)


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



@celery_app.task
def resize_images(files, orientation):
    new_filenames = []
    for filename in files:
        img = Image.open(path.join(temp_image_dir, filename))

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
        img.save(path.join(temp_image_dir, filename), "png")
        new_filenames.append(filename)

    return new_filenames


@celery_app.task
def combine_images(files, file_id, border, border_color, orientation):
    if orientation == "vertical":
        new_image = vertical_combine(files, border, border_color)

    else:
        new_image = horizontal_combine(files, border, border_color)

    new_image.save(path.join(results_dir, f"{file_id}.png"), "png")


@celery_app.task
def process_tasks(files, border, border_color, orientation):
    resize_results = resize_images.delay(files=files, orientation=orientation)
    file_id = uuid4()
    combine_images.delay(
        files=resize_results.get(),
        file_id=file_id,
        border=border,
        border_color=border_color,
        orientation=orientation
    )

    return file_id
