import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "asupersecretsecret")
    ENV = os.environ.get("FLASK_ENV", "development")
    DEBUG = True if os.environ.get("FLASK_ENV", "development") == "development" else False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    PORT = os.environ.get("PORT", 5000) 