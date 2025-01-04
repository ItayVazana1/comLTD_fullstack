from decouple import config

try:
    DATABASE_URL = config("DATABASE_URL")
    LOG_LEVEL = config("LOG_LEVEL", default="info")
except Exception as e:
    print(f"Error: {e}")
