import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Neon/Heroku give postgres:// but SQLAlchemy needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Fall back to SQLite for local dev if no DATABASE_URL is set
if not DATABASE_URL:
    DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'restaurant_tracker.db')}"

SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-in-production")
JWT_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRY_HOURS", "168"))  # 7 days
