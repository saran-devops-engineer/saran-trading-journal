import sys
import os

backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

os.environ.setdefault('DB_PATH', '/tmp/trades.db')
os.environ.setdefault('SECRET_KEY', 'vercel-production-secret-key')
os.environ.setdefault('ENCRYPTION_KEY', 'vercel-production-encryption-key!')

from app import app
