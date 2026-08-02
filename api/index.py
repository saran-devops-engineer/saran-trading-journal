import sys
import os

backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
sys.path.insert(0, backend_path)

os.environ.setdefault('DB_PATH', '/tmp/trades.db')
os.environ.setdefault('SECRET_KEY', 'vercel-production-secret-key')
os.environ.setdefault('ENCRYPTION_KEY', 'vercel-production-encryption-key!')

from app import app

app.static_folder = os.path.abspath(frontend_path)
app.root_path = os.path.abspath(backend_path)
