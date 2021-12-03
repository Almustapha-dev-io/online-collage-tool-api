from flask import Flask
from flask_cors import CORS
from config import Config
import os


app = Flask(__name__)
app.config.from_object(Config)
CORS(app)


from routes import *
from errors import *


if __name__ == "__main__":
    app.run(port=app.config.get("PORT"))