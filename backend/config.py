import os

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "!root1234")
DB_DATABSE = os.getenv("DB_DATABSE", "flask-simple-board")