from flask import Flask, request, jsonify, abort
from functools import wraps
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)

API_TOKEN = os.environ.get("API_TOKEN", "")

# DB init
def init_db():
    conn = sqlite3.connect('eggfarm.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coop_id TEXT,
            temperature REAL,
            humidity REAL,
            timestamp TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS feed_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coop_id TEXT,
            feed_weight REAL,
            timestamp TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coop_id TEXT,
            eggs_collected INTEGER,
            feed_given_g REAL,
            dewormed INTEGER,
            date TEXT
        )
    ''')

    conn.commit()
    conn.close()

@app.route('/')
def index():
    return "Egg Farm API is running ✅"

def require_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', None)
        if not auth or not auth.startswith("Bearer "):
            abort(401, description="Missing or invalid Authorization header")

        token = auth.split(" ")[1]
        if token != API_TOKEN:
            abort(403, description="Invalid token")

        return f(*args, **kwargs)
    return decorated

@app.route('/sensor-data', methods=['POST'])
@require_token
def sensor_data():
    data = request.get_json()
    required = ['coop_id', 'temperature', 'humidity']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing fields'}), 400

    conn = sqlite3.connect('eggfarm.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO sensor_data (coop_id, temperature, humidity, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (data['coop_id'], data['temperature'], data['humidity'], datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'}), 200

@app.route('/feed-weight', methods=['POST'])
@require_token
def feed_weight():
    data = request.get_json()
    if not all(k in data for k in ('coop_id', 'feed_weight')):
        return jsonify({'error': 'Missing fields'}), 400

    conn = sqlite3.connect('eggfarm.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO feed_data (coop_id, feed_weight, timestamp)
        VALUES (?, ?, ?)
    ''', (data['coop_id'], data['feed_weight'], datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'}), 200

@app.route('/daily-log', methods=['POST'])
@require_token
def daily_log():
    data = request.get_json()
    required = ['coop_id', 'eggs_collected', 'feed_given_g', 'dewormed']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing fields'}), 400

    conn = sqlite3.connect('eggfarm.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO daily_logs (coop_id, eggs_collected, feed_given_g, dewormed, date)
        VALUES (?, ?, ?, ?, ?)
    ''', (data['coop_id'], data['eggs_collected'], data['feed_given_g'], int(data['dewormed']),
          datetime.utcnow().date().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({'status': 'Log saved'}), 200

@app.route('/eggs-today/<coop_id>')
@require_token
def eggs_today(coop_id):
    conn = sqlite3.connect('eggfarm.db')
    c = conn.cursor()
    today = datetime.utcnow().date().isoformat()
    c.execute('SELECT eggs_collected FROM daily_logs WHERE coop_id=? AND date=?', (coop_id, today))
    row = c.fetchone()
    conn.close()
    return jsonify({'eggs_collected': row[0] if row else 0})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)