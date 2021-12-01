import os

class Config:
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    PORT = os.environ.get("PORT", 5000) 