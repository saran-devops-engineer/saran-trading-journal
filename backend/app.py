import csv
import io
import urllib.request
import json as _json
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
from database import get_connection, init_db, row_to_dict, rows_to_list
from symbols import search_symbols, get_option_chain, get_all_symbols, get_option_expiries
from fees import calculate_fees
from auth import (init_auth, create_user, authenticate_user, create_session, destroy_session, require_auth, validate_session,
                  save_setting, get_setting, encrypt_value, decrypt_value)

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app, supports_credentials=True, origins=['http://localhost:5000', 'http://127.0.0.1:5000', 'http://192.168.1.39:5000'])
init_auth(app)


def renew_dhan_token():
    encrypted = get_setting('dhan_access_token')
    client_id = get_setting('dhan_client_id')
    if not encrypted or not client_id:
        return
    try:
        token = decrypt_value(encrypted)
    except Exception:
        return
    url = 'https://api.dhan.co/v2/RenewToken'
    req = urllib.request.Request(url, method='POST', headers={
        'access-token': token,
        'dhanClientId': client_id,
        'Content-Type': 'application/json'
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = _json.loads(resp.read())
            new_token = data.get('accessToken') or data.get('token') or data.get('access_token')
            if new_token:
                save_setting('dhan_access_token', encrypt_value(new_token))
                save_setting('dhan_token_renewed_at', datetime.now().isoformat())
                print(f'[Auto-Renew] Dhan token renewed at {datetime.now()}')
            else:
                print(f'[Auto-Renew] Renewed but no token in response: {data}')
    except Exception as e:
        print(f'[Auto-Renew] Failed: {e}')


try:
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(renew_dhan_token, 'interval', hours=23, id='dhan_renew')
    scheduler.start()
    print('[Auto-Renew] Scheduler started - token will renew every 23 hours')
except Exception as e:
    print(f'[Auto-Renew] Scheduler failed to start: {e}')


@app.before_request
def auto_renew_on_startup():
    if not getattr(app, '_token_renewed_on_startup', False):
        app._token_renewed_on_startup = True
        try:
            renew_dhan_token()
        except Exception:
            pass


@app.before_request
def ensure_db():
    init_db()


@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    user_id, error = create_user(username, password)
    if error:
        return jsonify({'error': error}), 400
    create_session(user_id, username)
    return jsonify({'message': 'User created', 'username': username}), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    user = authenticate_user(username, password)
    if not user:
        return jsonify({'error': 'Invalid username or password'}), 401
    create_session(user['id'], user['username'])
    return jsonify({'message': 'Logged in', 'username': user['username']})


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    destroy_session()
    return jsonify({'message': 'Logged out'})


@app.route('/api/auth/me', methods=['GET'])
def get_me():
    sess = validate_session()
    if not sess:
        return jsonify({'error': 'Not logged in'}), 401
    return jsonify({'username': sess['username']})


@app.route('/api/settings', methods=['GET'])
@require_auth
def get_settings():
    dhan_token = get_setting('dhan_access_token')
    dhan_client_id = get_setting('dhan_client_id')
    has_token = bool(dhan_token)
    renewed_at = get_setting('dhan_token_renewed_at') or ''
    return jsonify({
        'dhan_client_id': dhan_client_id or '',
        'has_dhan_token': has_token,
        'dhan_token_renewed_at': renewed_at
    })


@app.route('/api/settings', methods=['POST'])
@require_auth
def save_settings():
    data = request.get_json()
    if 'dhan_client_id' in data:
        save_setting('dhan_client_id', data['dhan_client_id'])
    if 'dhan_access_token' in data and data['dhan_access_token']:
        encrypted = encrypt_value(data['dhan_access_token'])
        save_setting('dhan_access_token', encrypted)
    return jsonify({'message': 'Settings saved'})


@app.route('/api/settings/dhan-token', methods=['GET'])
@require_auth
def get_dhan_token():
    encrypted = get_setting('dhan_access_token')
    if not encrypted:
        return jsonify({'token': '', 'expires': ''})
    try:
        token = decrypt_value(encrypted)
        return jsonify({'token': token[:8] + '...' + token[-4:] if len(token) > 12 else '***', 'expires': ''})
    except:
        return jsonify({'token': '', 'expires': ''})


@app.route('/api/settings/test-dhan', methods=['POST'])
@require_auth
def test_dhan_connection():
    encrypted = get_setting('dhan_access_token')
    client_id = get_setting('dhan_client_id')
    if not encrypted or not client_id:
        return jsonify({'ok': False, 'error': 'Save Client ID and Access Token first'}), 400
    try:
        token = decrypt_value(encrypted)
    except Exception:
        return jsonify({'ok': False, 'error': 'Failed to decrypt token'}), 500

    import urllib.request
    import json as _json
    today = __import__('datetime').date.today().strftime('%Y-%m-%d')
    url = f'https://api.dhan.co/v2/trades/{today}/{today}/0'
    req = urllib.request.Request(url, headers={
        'access-token': token,
        'dhanClientId': client_id,
        'Content-Type': 'application/json'
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = _json.loads(resp.read())
            return jsonify({'ok': True, 'message': 'Connected to Dhan API', 'data': data})
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        return jsonify({'ok': False, 'error': f'HTTP {e.code}: {body[:200]}'}), 400
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/settings/renew-dhan', methods=['POST'])
@require_auth
def renew_dhan_now():
    encrypted = get_setting('dhan_access_token')
    client_id = get_setting('dhan_client_id')
    if not encrypted or not client_id:
        return jsonify({'ok': False, 'error': 'Save Client ID and Access Token first'}), 400
    try:
        token = decrypt_value(encrypted)
    except Exception:
        return jsonify({'ok': False, 'error': 'Failed to decrypt token'}), 500
    url = 'https://api.dhan.co/v2/RenewToken'
    req = urllib.request.Request(url, method='POST', headers={
        'access-token': token,
        'dhanClientId': client_id,
        'Content-Type': 'application/json'
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = _json.loads(resp.read())
            new_token = data.get('accessToken') or data.get('token') or data.get('access_token')
            if new_token:
                save_setting('dhan_access_token', encrypt_value(new_token))
                save_setting('dhan_token_renewed_at', datetime.now().isoformat())
                return jsonify({'ok': True, 'message': 'Token renewed'})
            return jsonify({'ok': False, 'error': f'No token in response: {data}'}), 500
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        return jsonify({'ok': False, 'error': f'HTTP {e.code}: {body[:200]}'}), 400
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)


@app.route('/api/trades', methods=['GET'])
@require_auth
def list_trades():
    conn = get_connection()
    query = "SELECT * FROM trades WHERE 1=1"
    params = []

    status = request.args.get('status')
    if status:
        query += " AND status = ?"
        params.append(status)

    symbol = request.args.get('symbol')
    if symbol:
        query += " AND UPPER(symbol) = UPPER(?)"
        params.append(symbol)

    asset_type = request.args.get('type')
    if asset_type:
        query += " AND asset_type = ?"
        params.append(asset_type)

    query += " ORDER BY date DESC, id DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify(rows_to_list(rows))


@app.route('/api/trades', methods=['POST'])
@require_auth
def create_trade():
    data = request.get_json()
    required = ['date', 'symbol', 'asset_type', 'side', 'entry_price', 'quantity']
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    entry = float(data['entry_price'])
    exit_price = data.get('exit_price')
    exit_price = float(exit_price) if exit_price else None
    quantity = float(data['quantity'])
    fees = float(data.get('fees', 0))
    side = data['side']

    pnl = None
    status = 'open'
    if exit_price is not None:
        status = 'closed'
        if side == 'long':
            pnl = (exit_price - entry) * quantity - fees
        else:
            pnl = (entry - exit_price) * quantity - fees

    conn = get_connection()
    cursor = conn.execute("""
        INSERT INTO trades (date, symbol, asset_type, side, entry_price, exit_price,
                           quantity, fees, pnl, strategy, tags, notes, status,
                           entry_mood, hold_mood, takeaway, entry_time, exit_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['date'], data['symbol'].upper(), data['asset_type'], side,
        entry, exit_price, quantity, fees, pnl,
        data.get('strategy', ''), data.get('tags', ''), data.get('notes', ''),
        status,
        data.get('entry_mood', ''), data.get('hold_mood', ''), data.get('takeaway', ''),
        data.get('entry_time', ''), data.get('exit_time', '')
    ))
    conn.commit()
    trade = conn.execute("SELECT * FROM trades WHERE id = ?", (cursor.lastrowid,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(trade)), 201


@app.route('/api/trades/<int:trade_id>', methods=['GET'])
@require_auth
def get_trade(trade_id):
    conn = get_connection()
    trade = conn.execute("SELECT * FROM trades WHERE id = ?", (trade_id,)).fetchone()
    conn.close()
    if not trade:
        return jsonify({"error": "Trade not found"}), 404
    return jsonify(row_to_dict(trade))


@app.route('/api/trades/<int:trade_id>', methods=['PUT'])
@require_auth
def update_trade(trade_id):
    data = request.get_json()
    conn = get_connection()
    trade = conn.execute("SELECT * FROM trades WHERE id = ?", (trade_id,)).fetchone()
    if not trade:
        conn.close()
        return jsonify({"error": "Trade not found"}), 404

    trade = dict(trade)
    for key in ['date', 'symbol', 'asset_type', 'side', 'entry_price', 'exit_price',
                'quantity', 'fees', 'strategy', 'tags', 'notes',
                'entry_mood', 'hold_mood', 'takeaway', 'entry_time', 'exit_time']:
        if key in data:
            trade[key] = data[key]

    if trade['symbol']:
        trade['symbol'] = trade['symbol'].upper()

    entry = float(trade['entry_price'])
    exit_price = trade['exit_price']
    exit_price = float(exit_price) if exit_price else None
    quantity = float(trade['quantity'])
    fees = float(trade.get('fees', 0))
    side = trade['side']

    pnl = None
    status = 'open'
    if exit_price is not None:
        status = 'closed'
        if side == 'long':
            pnl = (exit_price - entry) * quantity - fees
        else:
            pnl = (entry - exit_price) * quantity - fees

    conn.execute("""
        UPDATE trades SET date=?, symbol=?, asset_type=?, side=?, entry_price=?,
               exit_price=?, quantity=?, fees=?, pnl=?, strategy=?, tags=?, notes=?, status=?,
               entry_mood=?, hold_mood=?, takeaway=?, entry_time=?, exit_time=?,
               updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (
        trade['date'], trade['symbol'], trade['asset_type'], side,
        entry, exit_price, quantity, fees, pnl,
        trade.get('strategy', ''), trade.get('tags', ''), trade.get('notes', ''),
        status,
        trade.get('entry_mood', ''), trade.get('hold_mood', ''), trade.get('takeaway', ''),
        trade.get('entry_time', ''), trade.get('exit_time', ''),
        trade_id
    ))
    conn.commit()
    updated = conn.execute("SELECT * FROM trades WHERE id = ?", (trade_id,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(updated))


@app.route('/api/trades/<int:trade_id>', methods=['DELETE'])
@require_auth
def delete_trade(trade_id):
    conn = get_connection()
    trade = conn.execute("SELECT * FROM trades WHERE id = ?", (trade_id,)).fetchone()
    if not trade:
        conn.close()
        return jsonify({"error": "Trade not found"}), 404
    conn.execute("DELETE FROM trades WHERE id = ?", (trade_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Trade deleted"})


def calculate_mood_stats(trades):
    mood_data = {}
    for t in trades:
        mood = t.get('entry_mood', '')
        if not mood:
            continue
        if mood not in mood_data:
            mood_data[mood] = {'total': 0, 'wins': 0, 'total_pnl': 0}
        mood_data[mood]['total'] += 1
        if t['pnl'] and t['pnl'] > 0:
            mood_data[mood]['wins'] += 1
        if t['pnl']:
            mood_data[mood]['total_pnl'] += t['pnl']

    result = {}
    for mood, data in mood_data.items():
        result[mood] = {
            'total': data['total'],
            'win_rate': round(data['wins'] / data['total'] * 100, 1) if data['total'] > 0 else 0,
            'avg_pnl': round(data['total_pnl'] / data['total'], 2) if data['total'] > 0 else 0
        }
    return result


@app.route('/api/stats', methods=['GET'])
@require_auth
def get_stats():
    conn = get_connection()
    trades = rows_to_list(conn.execute("SELECT * FROM trades WHERE status='closed' ORDER BY date").fetchall())
    conn.close()

    if not trades:
        return jsonify({
            "total_trades": 0, "win_rate": 0, "profit_factor": 0,
            "total_pnl": 0, "avg_win": 0, "avg_loss": 0,
            "largest_win": 0, "largest_loss": 0, "max_drawdown": 0,
            "winning_trades": 0, "losing_trades": 0, "risk_reward": 0
        })

    wins = [t for t in trades if t['pnl'] and t['pnl'] > 0]
    losses = [t for t in trades if t['pnl'] and t['pnl'] < 0]
    total_pnl = sum(t['pnl'] for t in trades if t['pnl'])

    gross_profit = sum(t['pnl'] for t in wins) if wins else 0
    gross_loss = abs(sum(t['pnl'] for t in losses)) if losses else 0

    win_rate = (len(wins) / len(trades) * 100) if trades else 0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (9999.99 if gross_profit > 0 else 0)

    avg_win = (gross_profit / len(wins)) if wins else 0
    avg_loss = (-gross_loss / len(losses)) if losses else 0

    risk_reward = (abs(avg_win / avg_loss)) if avg_loss != 0 else (9999.99 if avg_win > 0 else 0)

    equity = 0
    peak = 0
    max_dd = 0
    equity_curve = []
    for t in trades:
        equity += t['pnl'] if t['pnl'] else 0
        equity_curve.append(equity)
        peak = max(peak, equity)
        dd = peak - equity
        max_dd = max(max_dd, dd)

    return jsonify({
        "total_trades": len(trades),
        "win_rate": round(win_rate, 1),
        "profit_factor": round(profit_factor, 2),
        "total_pnl": round(total_pnl, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "largest_win": round(max((t['pnl'] for t in trades if t['pnl']), default=0), 2),
        "largest_loss": round(min((t['pnl'] for t in trades if t['pnl']), default=0), 2),
        "max_drawdown": round(max_dd, 2),
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "risk_reward": round(risk_reward, 2),
        "mood_stats": calculate_mood_stats(trades),
        "equity_curve": equity_curve,
        "trade_dates": [t['date'] for t in trades]
    })


@app.route('/api/analytics', methods=['GET'])
@require_auth
def get_analytics():
    conn = get_connection()
    trades = rows_to_list(conn.execute("SELECT * FROM trades WHERE status='closed' ORDER BY date").fetchall())
    conn.close()

    if not trades:
        return jsonify({
            "time_day": {}, "hold_time": {}, "strategy": {},
            "expectancy": 0, "behavioral": {}
        })

    time_day = analyze_time_day(trades)
    hold_time = analyze_hold_time(trades)
    strategy = analyze_strategy(trades)
    expectancy = calculate_expectancy(trades)
    behavioral = analyze_behavior(trades)

    return jsonify({
        "time_day": time_day,
        "hold_time": hold_time,
        "strategy": strategy,
        "expectancy": expectancy,
        "behavioral": behavioral
    })


def analyze_time_day(trades):
    day_stats = {}
    for t in trades:
        try:
            d = datetime.strptime(t['date'], '%Y-%m-%d')
            day_name = d.strftime('%A')
        except:
            continue
        if day_name not in day_stats:
            day_stats[day_name] = {'total': 0, 'wins': 0, 'total_pnl': 0}
        day_stats[day_name]['total'] += 1
        if t['pnl'] and t['pnl'] > 0:
            day_stats[day_name]['wins'] += 1
        if t['pnl']:
            day_stats[day_name]['total_pnl'] += t['pnl']

    result = {}
    for day, data in day_stats.items():
        result[day] = {
            'total': data['total'],
            'win_rate': round(data['wins'] / data['total'] * 100, 1) if data['total'] > 0 else 0,
            'avg_pnl': round(data['total_pnl'] / data['total'], 2) if data['total'] > 0 else 0,
            'total_pnl': round(data['total_pnl'], 2)
        }

    hour_stats = {}
    for t in trades:
        entry_time = t.get('entry_time', '')
        if not entry_time:
            continue
        try:
            hour = int(entry_time.split(':')[0])
        except:
            continue
        if hour not in hour_stats:
            hour_stats[hour] = {'total': 0, 'wins': 0, 'total_pnl': 0}
        hour_stats[hour]['total'] += 1
        if t['pnl'] and t['pnl'] > 0:
            hour_stats[hour]['wins'] += 1
        if t['pnl']:
            hour_stats[hour]['total_pnl'] += t['pnl']

    hourly = {}
    for hour, data in hour_stats.items():
        hourly[hour] = {
            'total': data['total'],
            'win_rate': round(data['wins'] / data['total'] * 100, 1) if data['total'] > 0 else 0,
            'avg_pnl': round(data['total_pnl'] / data['total'], 2) if data['total'] > 0 else 0
        }

    return {'by_day': result, 'by_hour': hourly}


def analyze_hold_time(trades):
    winners_hold = []
    losers_hold = []

    for t in trades:
        entry_time = t.get('entry_time', '')
        exit_time = t.get('exit_time', '')
        if not entry_time or not exit_time:
            continue
        try:
            entry_dt = datetime.strptime(t['date'] + ' ' + entry_time, '%Y-%m-%d %H:%M')
            exit_dt = datetime.strptime(t['date'] + ' ' + exit_time, '%Y-%m-%d %H:%M')
            hours = (exit_dt - entry_dt).total_seconds() / 3600
            if hours < 0:
                hours += 24
            if t['pnl'] and t['pnl'] > 0:
                winners_hold.append(hours)
            elif t['pnl'] and t['pnl'] < 0:
                losers_hold.append(hours)
        except:
            continue

    avg_winner_hold = round(sum(winners_hold) / len(winners_hold), 2) if winners_hold else 0
    avg_loser_hold = round(sum(losers_hold) / len(losers_hold), 2) if losers_hold else 0

    return {
        'avg_winner_hold_hours': avg_winner_hold,
        'avg_loser_hold_hours': avg_loser_hold,
        'winners_sample': len(winners_hold),
        'losers_sample': len(losers_hold)
    }


def analyze_strategy(trades):
    strat_stats = {}
    for t in trades:
        strat = t.get('strategy', '').strip()
        if not strat:
            strat = 'Untagged'
        if strat not in strat_stats:
            strat_stats[strat] = {'total': 0, 'wins': 0, 'total_pnl': 0, 'gross_profit': 0, 'gross_loss': 0}
        strat_stats[strat]['total'] += 1
        if t['pnl'] and t['pnl'] > 0:
            strat_stats[strat]['wins'] += 1
            strat_stats[strat]['gross_profit'] += t['pnl']
        elif t['pnl'] and t['pnl'] < 0:
            strat_stats[strat]['gross_loss'] += abs(t['pnl'])
        if t['pnl']:
            strat_stats[strat]['total_pnl'] += t['pnl']

    result = {}
    for strat, data in strat_stats.items():
        avg_win = data['gross_profit'] / data['wins'] if data['wins'] > 0 else 0
        avg_loss = data['gross_loss'] / (data['total'] - data['wins']) if (data['total'] - data['wins']) > 0 else 0
        result[strat] = {
            'total': data['total'],
            'win_rate': round(data['wins'] / data['total'] * 100, 1) if data['total'] > 0 else 0,
            'total_pnl': round(data['total_pnl'], 2),
            'avg_pnl': round(data['total_pnl'] / data['total'], 2) if data['total'] > 0 else 0,
            'profit_factor': round(data['gross_profit'] / data['gross_loss'], 2) if data['gross_loss'] > 0 else (9999.99 if data['gross_profit'] > 0 else 0),
            'risk_reward': round(avg_win / avg_loss, 2) if avg_loss > 0 else (9999.99 if avg_win > 0 else 0)
        }
    return result


def calculate_expectancy(trades):
    if not trades:
        return 0
    wins = [t for t in trades if t['pnl'] and t['pnl'] > 0]
    losses = [t for t in trades if t['pnl'] and t['pnl'] < 0]
    win_rate = len(wins) / len(trades)
    loss_rate = len(losses) / len(trades)
    avg_win = sum(t['pnl'] for t in wins) / len(wins) if wins else 0
    avg_loss = sum(abs(t['pnl']) for t in losses) / len(losses) if losses else 0
    expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)
    return round(expectancy, 2)


def analyze_behavior(trades):
    consecutive_losses = 0
    max_consecutive_losses = 0
    revenge_trades = 0
    overtrade_days = 0
    trades_per_day = {}

    for t in trades:
        day = t['date']
        trades_per_day[day] = trades_per_day.get(day, 0) + 1

        if t['pnl'] and t['pnl'] < 0:
            consecutive_losses += 1
            max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
        else:
            consecutive_losses = 0

    for day, count in trades_per_day.items():
        if count > 5:
            overtrade_days += 1

    day_trades = {}
    for t in trades:
        day = t['date']
        if day not in day_trades:
            day_trades[day] = []
        day_trades[day].append(t)

    for day, day_trade_list in day_trades.items():
        for i in range(1, len(day_trade_list)):
            prev = day_trade_list[i - 1]
            curr = day_trade_list[i]
            if prev['pnl'] and prev['pnl'] < 0 and curr['pnl'] is None:
                revenge_trades += 1

    return {
        'max_consecutive_losses': max_consecutive_losses,
        'revenge_trades': revenge_trades,
        'overtrade_days': overtrade_days,
        'avg_trades_per_day': round(sum(trades_per_day.values()) / len(trades_per_day), 1) if trades_per_day else 0
    }


@app.route('/api/benchmark', methods=['GET'])
@require_auth
def get_benchmark():
    conn = get_connection()
    trades = rows_to_list(conn.execute("SELECT * FROM trades WHERE status='closed' ORDER BY date").fetchall())
    conn.close()

    if not trades:
        return jsonify({"benchmark_returns": [], "your_returns": [], "dates": [], "alpha": 0, "benchmark_total": 0})

    total_investment = sum(t['entry_price'] * t['quantity'] for t in trades if t['entry_price'] and t['quantity'])
    if total_investment == 0:
        total_investment = 1

    annual_market_return = 0.12
    daily_market_return = annual_market_return / 252

    equity = 0
    your_returns = []
    benchmark_returns = []
    dates = []
    day_count = 0

    for t in trades:
        pnl = t['pnl'] if t['pnl'] else 0
        equity += pnl
        your_pct = (equity / total_investment) * 100
        bench_pct = daily_market_return * day_count * 100
        your_returns.append(round(your_pct, 2))
        benchmark_returns.append(round(bench_pct, 2))
        dates.append(t['date'])
        day_count += 1

    your_total = your_returns[-1] if your_returns else 0
    bench_total = benchmark_returns[-1] if benchmark_returns else 0
    alpha = round(your_total - bench_total, 2)

    return jsonify({
        "your_returns": your_returns,
        "benchmark_returns": benchmark_returns,
        "dates": dates,
        "alpha": alpha,
        "benchmark_total": round(bench_total, 2),
        "your_total": round(your_total, 2)
    })


@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    conn = get_connection()
    trades = rows_to_list(conn.execute("SELECT * FROM trades ORDER BY date DESC").fetchall())
    conn.close()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'id', 'date', 'symbol', 'asset_type', 'side', 'entry_price',
        'exit_price', 'quantity', 'fees', 'pnl', 'strategy', 'tags',
        'notes', 'status', 'entry_mood', 'hold_mood', 'takeaway',
        'created_at', 'updated_at'
    ])
    writer.writeheader()
    for t in trades:
        writer.writerow(t)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment; filename=trades_export.csv"}
    )


@app.route('/api/import/csv', methods=['POST'])
@require_auth
def import_csv_preview():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({"error": "File must be a .csv"}), 400

    try:
        content = file.read().decode('utf-8-sig')
    except UnicodeDecodeError:
        return jsonify({"error": "File encoding not supported. Use UTF-8."}), 400

    reader = csv.DictReader(io.StringIO(content))
    column_map = {
        'date': ['date', 'trade date', 'trade_date', 'datetime'],
        'symbol': ['symbol', 'stock', 'instrument', 'scrip', 'name'],
        'asset_type': ['asset_type', 'asset type', 'type', 'instrument type'],
        'side': ['side', 'direction', 'trade_type', 'trade type', 'action'],
        'entry_price': ['entry_price', 'entry price', 'entry', 'buy_price', 'buy price', 'avg price'],
        'exit_price': ['exit_price', 'exit price', 'exit', 'sell_price', 'sell price', 'close price'],
        'quantity': ['quantity', 'qty', 'lots', 'lot_size', 'lot size', 'units'],
        'fees': ['fees', 'fee', 'charges', 'brokerage', 'total charges'],
        'strategy': ['strategy', 'system'],
        'tags': ['tags', 'tag', 'labels'],
        'notes': ['notes', 'note', 'remarks', 'comment'],
    }

    def find_column(field, headers):
        headers_lower = [h.strip().lower() for h in headers]
        for alias in column_map.get(field, [field]):
            if alias in headers_lower:
                return headers[headers_lower.index(alias)]
        return None

    headers = reader.fieldnames or []
    mapped = {}
    for field in column_map:
        col = find_column(field, headers)
        if col:
            mapped[field] = col

    required = ['date', 'symbol', 'asset_type', 'side', 'entry_price', 'quantity']
    missing = [f for f in required if f not in mapped]
    if missing:
        return jsonify({"error": f"Missing required columns: {', '.join(missing)}"}), 400

    preview = []
    errors = []
    for i, row in enumerate(reader, start=2):
        try:
            date_val = row[mapped['date']].strip()
            symbol = row[mapped['symbol']].strip().upper()
            asset_type = row[mapped['asset_type']].strip().lower()
            side = row[mapped['side']].strip().lower()
            entry_price = float(row[mapped['entry_price']].strip().replace(',', ''))
            quantity = float(row[mapped['quantity']].strip().replace(',', ''))

            if asset_type not in ('stock', 'option', 'future'):
                asset_type = 'stock'
            if side in ('buy', 'b', 'long'):
                side = 'long'
            elif side in ('sell', 's', 'short'):
                side = 'short'
            else:
                side = 'long'

            exit_price = None
            if mapped.get('exit_price'):
                exit_val = row.get(mapped['exit_price'], '').strip().replace(',', '')
                if exit_val:
                    exit_price = float(exit_val)

            fees = 0
            if mapped.get('fees'):
                fees_val = row.get(mapped['fees'], '').strip().replace(',', '')
                if fees_val:
                    fees = float(fees_val)

            pnl = None
            status = 'open'
            if exit_price is not None:
                status = 'closed'
                if side == 'long':
                    pnl = (exit_price - entry_price) * quantity - fees
                else:
                    pnl = (entry_price - exit_price) * quantity - fees

            trade = {
                'date': date_val,
                'symbol': symbol,
                'asset_type': asset_type,
                'side': side,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'quantity': quantity,
                'fees': fees,
                'pnl': round(pnl, 2) if pnl is not None else None,
                'strategy': row.get(mapped.get('strategy', ''), '').strip() if mapped.get('strategy') else '',
                'tags': row.get(mapped.get('tags', ''), '').strip() if mapped.get('tags') else '',
                'notes': row.get(mapped.get('notes', ''), '').strip() if mapped.get('notes') else '',
                'status': status,
            }
            preview.append(trade)
        except (ValueError, KeyError) as e:
            errors.append(f"Row {i}: {str(e)}")

    return jsonify({"preview": preview, "errors": errors, "total_rows": len(preview)})


@app.route('/api/import/confirm', methods=['POST'])
@require_auth
def import_csv_confirm():
    data = request.get_json()
    trades = data.get('trades', [])
    if not trades:
        return jsonify({"error": "No trades to import"}), 400

    conn = get_connection()
    imported = 0
    for t in trades:
        try:
            conn.execute("""
                INSERT INTO trades (date, symbol, asset_type, side, entry_price, exit_price,
                                   quantity, fees, pnl, strategy, tags, notes, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t['date'], t['symbol'], t['asset_type'], t['side'],
                t['entry_price'], t.get('exit_price'), t['quantity'],
                t.get('fees', 0), t.get('pnl'),
                t.get('strategy', ''), t.get('tags', ''), t.get('notes', ''),
                t.get('status', 'open')
            ))
            imported += 1
        except Exception:
            pass
    conn.commit()
    conn.close()
    return jsonify({"imported": imported})


@app.route('/api/symbols/search', methods=['GET'])
def api_search_symbols():
    query = request.args.get('q', '')
    if not query or len(query) < 1:
        return jsonify(get_all_symbols()[:30])
    results = search_symbols(query)
    return jsonify(results)


@app.route('/api/symbols/all', methods=['GET'])
def api_all_symbols():
    return jsonify(get_all_symbols())


@app.route('/api/options/chain', methods=['GET'])
def api_option_chain():
    symbol = request.args.get('symbol', '')
    if not symbol:
        return jsonify({"error": "Symbol required"}), 400

    chain = get_option_chain(symbol)
    if not chain:
        return jsonify({"error": "Option chain not available for this symbol"}), 404

    return jsonify(chain)


@app.route('/api/options/expiries', methods=['GET'])
def api_option_expiries():
    return jsonify(get_option_expiries())


@app.route('/api/fees/calculate', methods=['POST'])
def api_calculate_fees():
    data = request.get_json()
    trade_type = data.get('asset_type', 'stock')
    side = data.get('side', 'long')
    entry_price = data.get('entry_price', 0)
    exit_price = data.get('exit_price')
    quantity = data.get('quantity', 0)
    exchange = data.get('exchange', 'NSE')

    fees = calculate_fees(trade_type, side, entry_price, exit_price, quantity, exchange)
    return jsonify(fees)


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
