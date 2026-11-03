import os
import time
import socket
import platform
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify
import redis

app = Flask(__name__)

# Start time for container uptime calculation
START_TIME = time.time()

# Configuration from Environment
APP_VERSION = os.getenv("APP_VERSION", "v1.0")
APP_TITLE = os.getenv("APP_TITLE", "Cloud Counter - DevOps & Cloud Computing Demo")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

def get_redis_client():
    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            socket_connect_timeout=1.2,
            socket_timeout=1.2,
            decode_responses=True
        )
        r.ping()
        return r
    except Exception:
        return None

# Fallback store if Redis is absent (e.g. standalone AWS EC2 demo container)
FALLBACK_VISITS = 0
FALLBACK_NOTES = ["Welcome to Cloud Counter Demo! (Standalone Mode)"]

def format_uptime(seconds):
    mins, secs = divmod(int(seconds), 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours}h {mins}m {secs}s"
    elif mins > 0:
        return f"{mins}m {secs}s"
    else:
        return f"{secs}s"

@app.route("/", methods=["GET"])
def index():
    global FALLBACK_VISITS
    hostname = socket.gethostname()
    r = get_redis_client()
    uptime_str = format_uptime(time.time() - START_TIME)
    
    if r:
        try:
            visits = r.incr("page_views")
            notes = r.lrange("user_notes", 0, -1)
            redis_connected = True
        except Exception:
            FALLBACK_VISITS += 1
            visits = FALLBACK_VISITS
            notes = FALLBACK_NOTES
            redis_connected = False
    else:
        FALLBACK_VISITS += 1
        visits = FALLBACK_VISITS
        notes = FALLBACK_NOTES
        redis_connected = False

    return render_template(
        "index.html",
        title=APP_TITLE,
        version=APP_VERSION,
        hostname=hostname,
        visits=visits,
        notes=notes,
        redis_connected=redis_connected,
        redis_host=REDIS_HOST,
        redis_port=REDIS_PORT,
        uptime_str=uptime_str,
        py_version=platform.python_version()
    )

@app.route("/add", methods=["POST"])
def add_note():
    item = request.form.get("item", "").strip()
    if item:
        r = get_redis_client()
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"{item} (at {timestamp})"
        if r:
            try:
                r.rpush("user_notes", entry)
            except Exception:
                FALLBACK_NOTES.append(entry)
        else:
            FALLBACK_NOTES.append(entry)
    return redirect(url_for("index"))

@app.route("/clear", methods=["POST"])
def clear_notes():
    r = get_redis_client()
    if r:
        try:
            r.delete("user_notes")
        except Exception:
            pass
    FALLBACK_NOTES.clear()
    return redirect(url_for("index"))

@app.route("/health", methods=["GET"])
def health():
    r = get_redis_client()
    return jsonify({
        "status": "healthy",
        "app_version": APP_VERSION,
        "hostname": socket.gethostname(),
        "redis_connected": r is not None,
        "uptime_seconds": int(time.time() - START_TIME)
    }), 200

@app.route("/api/info", methods=["GET"])
def api_info():
    global FALLBACK_VISITS
    r = get_redis_client()
    hostname = socket.gethostname()
    if r:
        try:
            visits = int(r.incr("page_views"))
            notes = r.lrange("user_notes", 0, -1)
            redis_connected = True
        except Exception:
            FALLBACK_VISITS += 1
            visits = FALLBACK_VISITS
            notes = FALLBACK_NOTES
            redis_connected = False
    else:
        FALLBACK_VISITS += 1
        visits = FALLBACK_VISITS
        notes = FALLBACK_NOTES
        redis_connected = False

    return jsonify({
        "app_title": APP_TITLE,
        "version": APP_VERSION,
        "hostname": hostname,
        "visits": visits,
        "notes": notes,
        "redis_connected": redis_connected,
        "redis_host": REDIS_HOST,
        "uptime": format_uptime(time.time() - START_TIME),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
