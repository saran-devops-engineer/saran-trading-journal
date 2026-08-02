import sys
import os

backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend')
sys.path.insert(0, backend_path)

os.environ['DB_PATH'] = '/tmp/trades.db'
os.environ.setdefault('SECRET_KEY', 'vercel-secret-key-change-me')
os.environ.setdefault('ENCRYPTION_KEY', 'vercel-encryption-key-change-me!')

from app import app

app.static_folder = os.path.abspath(frontend_path)
