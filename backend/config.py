import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'fallback-encryption-key-change-me')
DB_PATH = os.getenv('DB_PATH', 'data/trades.db')
