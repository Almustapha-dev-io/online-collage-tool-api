import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "asupersecretsecret")
    ENV = os.environ.get("FLASK_ENV", "development")
    DEBUG = True if os.environ.get("FLASK_ENV", "development") == "development" else False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    PORT = os.environ.get("PORT", 5000) 
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")