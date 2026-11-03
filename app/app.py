import os
import socket
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, jsonify
import redis

app = Flask(__name__)

# Configuration
APP_VERSION = os.getenv("APP_VERSION", "v1.0")
APP_TITLE = os.getenv("APP_TITLE", "Cloud Counter - Docker & Swarm Demo")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

def get_redis_client():
    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            socket_connect_timeout=1.5,
            socket_timeout=1.5,
            decode_responses=True
        )
        r.ping()
        return r
    except Exception:
        return None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col items-center justify-start p-6">
    <div class="max-w-3xl w-full space-y-6">
        
        <!-- Header Card -->
        <div class="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-xl relative overflow-hidden">
            <div class="absolute top-0 right-0 p-4">
                <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold {{ 'bg-blue-600 text-white' if version == 'v1.0' else 'bg-emerald-600 text-white' }}">
                    <i class="fa-solid fa-code-commit mr-1.5"></i> Release {{ version }}
                </span>
            </div>
            <div class="flex items-center space-x-4">
                <div class="p-3 bg-blue-500/20 text-blue-400 rounded-lg">
                    <i class="fa-solid fa-cubes text-3xl"></i>
                </div>
                <div>
                    <h1 class="text-2xl font-bold text-white tracking-tight">{{ title }}</h1>
                    <p class="text-sm text-slate-400">Docker &bull; Swarm Mesh &bull; Docker Hub &bull; AWS EC2</p>
                </div>
            </div>
        </div>

        <!-- System Stats Grid -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <!-- Hit Counter -->
            <div class="bg-slate-800 border border-slate-700 rounded-xl p-5 shadow">
                <div class="flex items-center justify-between text-slate-400 text-xs font-medium uppercase tracking-wider mb-2">
                    <span>Total Visits</span>
                    <i class="fa-solid fa-chart-line text-blue-400"></i>
                </div>
                <div class="text-3xl font-extrabold text-blue-400">
                    {{ visits }}
                </div>
                <p class="text-xs text-slate-500 mt-1">Incremented on each page load</p>
            </div>

            <!-- Container Hostname -->
            <div class="bg-slate-800 border border-slate-700 rounded-xl p-5 shadow">
                <div class="flex items-center justify-between text-slate-400 text-xs font-medium uppercase tracking-wider mb-2">
                    <span>Container ID</span>
                    <i class="fa-solid fa-server text-purple-400"></i>
                </div>
                <div class="text-xl font-mono font-bold text-purple-300 truncate" title="{{ hostname }}">
                    {{ hostname }}
                </div>
                <p class="text-xs text-slate-500 mt-1">Changes across Swarm replicas</p>
            </div>

            <!-- Redis Status -->
            <div class="bg-slate-800 border border-slate-700 rounded-xl p-5 shadow">
                <div class="flex items-center justify-between text-slate-400 text-xs font-medium uppercase tracking-wider mb-2">
                    <span>Database Status</span>
                    <i class="fa-solid fa-database text-emerald-400"></i>
                </div>
                <div>
                    {% if redis_connected %}
                    <span class="inline-flex items-center text-sm font-semibold text-emerald-400">
                        <span class="w-2.5 h-2.5 bg-emerald-500 rounded-full mr-2 animate-pulse"></span>
                        Connected (Redis)
                    </span>
                    <p class="text-xs text-slate-500 mt-1">{{ redis_host }}:{{ redis_port }}</p>
                    {% else %}
                    <span class="inline-flex items-center text-sm font-semibold text-amber-400">
                        <span class="w-2.5 h-2.5 bg-amber-500 rounded-full mr-2"></span>
                        Standalone Mode
                    </span>
                    <p class="text-xs text-slate-500 mt-1">No backing DB attached</p>
                    {% endif %}
                </div>
            </div>
        </div>

        <!-- Persistence Test Section -->
        <div class="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-xl space-y-4">
            <div class="flex items-center justify-between">
                <div>
                    <h2 class="text-lg font-semibold text-white flex items-center">
                        <i class="fa-solid fa-hard-drive mr-2 text-blue-400"></i> Data Persistence Test
                    </h2>
                    <p class="text-xs text-slate-400">Submit data below to verify persistence across container restarts and Docker named volumes.</p>
                </div>
                <span class="text-xs text-slate-400 bg-slate-700/50 px-2.5 py-1 rounded-md border border-slate-600">
                    Volume: <code class="text-blue-300 font-mono">redis_data</code>
                </span>
            </div>

            <form action="/add" method="POST" class="flex gap-2">
                <input type="text" name="item" required placeholder="Enter test text (e.g. Homework Test Data #1)..." 
                       class="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500">
                <button type="submit" class="bg-blue-600 hover:bg-blue-500 text-white font-medium px-5 py-2 rounded-lg text-sm transition flex items-center shadow">
                    <i class="fa-solid fa-plus mr-1.5"></i> Save
                </button>
            </form>

            <div class="border-t border-slate-700/70 pt-4">
                <h3 class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Persisted Items ({{ notes|length }})</h3>
                {% if notes %}
                <ul class="divide-y divide-slate-700/50 bg-slate-900/50 rounded-lg border border-slate-700/70 overflow-hidden">
                    {% for note in notes %}
                    <li class="px-4 py-2.5 text-sm flex items-center justify-between hover:bg-slate-800/50 transition">
                        <span class="text-slate-200 font-medium">{{ note }}</span>
                        <span class="text-xs text-slate-500"><i class="fa-regular fa-clock mr-1"></i>Stored in Redis</span>
                    </li>
                    {% endfor %}
                </ul>
                {% else %}
                <p class="text-xs text-slate-500 italic py-2">No custom items stored yet. Type something above and click "Save" to test persistence!</p>
                {% endif %}
            </div>
        </div>

        <!-- Footer -->
        <div class="text-center text-xs text-slate-500 space-y-1">
            <p>Docker &bull; Docker Compose &bull; Docker Swarm &bull; AWS EC2 Deployment</p>
            <p>Maintainer: <span class="text-slate-400 font-semibold">lihengkh</span></p>
        </div>

    </div>
</body>
</html>
"""

# In-memory fallback if Redis is not connected (e.g., standalone EC2 demo)
FALLBACK_VISITS = 0
FALLBACK_NOTES = ["Standalone mode default note"]

@app.route("/", methods=["GET"])
def index():
    global FALLBACK_VISITS
    hostname = socket.gethostname()
    r = get_redis_client()
    
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

    return render_template_string(
        HTML_TEMPLATE,
        title=APP_TITLE,
        version=APP_VERSION,
        hostname=hostname,
        visits=visits,
        notes=notes,
        redis_connected=redis_connected,
        redis_host=REDIS_HOST,
        redis_port=REDIS_PORT
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

@app.route("/health", methods=["GET"])
def health():
    r = get_redis_client()
    return jsonify({
        "status": "healthy",
        "app_version": APP_VERSION,
        "hostname": socket.gethostname(),
        "redis_connected": r is not None
    }), 200

@app.route("/api/info", methods=["GET"])
def api_info():
    global FALLBACK_VISITS
    r = get_redis_client()
    hostname = socket.gethostname()
    if r:
        try:
            visits = int(r.get("page_views") or 0)
            notes = r.lrange("user_notes", 0, -1)
            redis_connected = True
        except Exception:
            visits = FALLBACK_VISITS
            notes = FALLBACK_NOTES
            redis_connected = False
    else:
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
        "redis_host": REDIS_HOST
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

