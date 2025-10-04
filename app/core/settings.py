import os


class Settings:
    PG_USER = os.environ.get("PG_USER")
    PG_PASSWORD = os.environ.get("PG_PASSWORD")
    PG_HOST = os.environ.get("PG_HOST")
    PG_PORT = int(os.environ.get("PG_PORT", 5432))
    PG_DATABASE = os.environ.get("PG_DATABASE")


settings = Settings()
