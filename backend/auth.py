import hashlib
import secrets
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session
from config import SECRET_KEY, ENCRYPTION_KEY
from database import get_connection

SECRET_KEY_BYTES = SECRET_KEY.encode()
sessions = {}


def hash_password(password):
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return salt + ':' + pwd_hash.hex()


def verify_password(password, stored):
    salt, pwd_hash = stored.split(':')
    check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return check.hex() == pwd_hash


def create_session(user_id, username):
    token = secrets.token_urlsafe(32)
    sessions[token] = {
        'user_id': user_id,
        'username': username,
        'created': datetime.now(),
        'expires': datetime.now() + timedelta(hours=24)
    }
    return token


def destroy_session(token):
    if token and token in sessions:
        del sessions[token]


def validate_session(token):
    if not token:
        return None
    sess = sessions.get(token)
    if not sess:
        return None
    if datetime.now() > sess['expires']:
        del sessions[token]
        return None
    return sess


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            token = request.cookies.get('session_token', '')
        sess = validate_session(token)
        if not sess:
            return jsonify({'error': 'Unauthorized'}), 401
        request.current_user = sess
        return f(*args, **kwargs)
    return decorated


def create_user(username, password):
    conn = get_connection()
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        conn.close()
        return None, 'Username already exists'
    pwd_hash = hash_password(password)
    cursor = conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, pwd_hash))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id, None


def authenticate_user(username, password):
    conn = get_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if not user:
        return None
    if verify_password(password, user['password_hash']):
        return dict(user)
    return None


def encrypt_value(value):
    key = ENCRYPTION_KEY[:32].ljust(32, '0').encode()
    from cryptography.fernet import Fernet
    import base64
    fernet_key = base64.urlsafe_b64encode(key)
    f = Fernet(fernet_key)
    return f.encrypt(value.encode()).decode()


def decrypt_value(encrypted_value):
    key = ENCRYPTION_KEY[:32].ljust(32, '0').encode()
    from cryptography.fernet import Fernet
    import base64
    fernet_key = base64.urlsafe_b64encode(key)
    f = Fernet(fernet_key)
    return f.decrypt(encrypted_value.encode()).decode()


def save_setting(key, value):
    conn = get_connection()
    existing = conn.execute("SELECT id FROM settings WHERE key = ?", (key,)).fetchone()
    if existing:
        conn.execute("UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?", (value, key))
    else:
        conn.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def get_setting(key, default=None):
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row['value'] if row else default
