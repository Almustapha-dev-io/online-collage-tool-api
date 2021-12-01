from flask import jsonify
from os import getcwd, path, mkdir
from PIL import Image
from re import search


def hex_color_valid(color):
    return True if search(r"#(?:[0-9a-fA-F]{3}){1,2}$", color) else False


def is_number(n):
    try:
        n = float(n)
        return True
    except:
        return False


def get_response(msg, data=None, status=200):
    return jsonify(msg=msg, data=data), status


def create_dir(folder_name):
    base_dir = getcwd()
    existing_dir = path.join(base_dir, folder_name)
    if not path.isdir(existing_dir):
        mkdir(existing_dir)

    return existing_dir


def map_files_to_image(files, _dir):
    return [Image.open(path.join(_dir, f)) for f in files]