import os

# Flask 환경설정
FLASK_PORT = os.getenv("FLASK_PORT", 80)
FLASK_DEBUG = os.getenv("FLASK_DEBUG", 1)

# DB 정보
# DB_HOST = os.getenv("DB_HOST", "host.docker.internal")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "!root1234")
DB_DATABSE = os.getenv("DB_DATABSE", "flask-simple-board")