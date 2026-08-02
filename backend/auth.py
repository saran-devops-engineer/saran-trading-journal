import hashlib
import secrets
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session
from config import SECRET_KEY, ENCRYPTION_KEY
from database import get_connection, sql, last_id

app = None


def init_auth(flask_app):
    global app
    app = flask_app
    flask_app.secret_key = SECRET_KEY
    flask_app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    flask_app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)


def hash_password(password):
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return salt + ':' + pwd_hash.hex()


def verify_password(password, stored):
    salt, pwd_hash = stored.split(':')
    check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return check.hex() == pwd_hash


def create_session(user_id, username):
    session.permanent = True
    session['user_id'] = user_id
    session['username'] = username
    session['logged_in'] = True
    return 'ok'


def destroy_session():
    session.clear()


def validate_session():
    if session.get('logged_in'):
        return {
            'user_id': session.get('user_id'),
            'username': session.get('username')
        }
    return None


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        sess = validate_session()
        if not sess:
            return jsonify({'error': 'Unauthorized'}), 401
        request.current_user = sess
        return f(*args, **kwargs)
    return decorated


def create_user(username, password):
    conn = get_connection()
    existing = conn.execute(sql("SELECT id FROM users WHERE username = ?"), (username,)).fetchone()
    if existing:
        conn.close()
        return None, 'Username already exists'
    pwd_hash = hash_password(password)
    cursor = conn.execute(sql("INSERT INTO users (username, password_hash) VALUES (?, ?)"), (username, pwd_hash))
    user_id = last_id(cursor)
    conn.commit()
    conn.close()
    return user_id, None


def authenticate_user(username, password):
    conn = get_connection()
    user = conn.execute(sql("SELECT * FROM users WHERE username = ?"), (username,)).fetchone()
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
    existing = conn.execute(sql("SELECT id FROM settings WHERE key = ?"), (key,)).fetchone()
    if existing:
        conn.execute(sql("UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?"), (value, key))
    else:
        conn.execute(sql("INSERT INTO settings (key, value) VALUES (?, ?)"), (key, value))
    conn.commit()
    conn.close()


def get_setting(key, default=None):
    conn = get_connection()
    row = conn.execute(sql("SELECT value FROM settings WHERE key = ?"), (key,)).fetchone()
    conn.close()
    return row['value'] if row else default
