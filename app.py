from flask import Flask
from config import Config


app = Flask(__name__)
app.config.from_object(Config)


from routes import *
from errors import *


if __name__ == "__main__":
    app.run(port=app.config.get("PORT"))