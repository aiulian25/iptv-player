from flask import Flask, jsonify, send_from_directory, session
from flask_cors import CORS
from flask_session import Session
from apscheduler.schedulers.background import BackgroundScheduler
import os

from routes.playlist_routes import playlist_bp
from routes.channel_routes import channel_bp
from routes.epg_routes import epg_bp
from routes.stream_routes import stream_bp
from routes.recording_routes import recording_bp
from routes.auth_routes import auth_bp

app = Flask(__name__, static_folder="../frontend")

# Session configuration
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", os.urandom(24).hex())
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './data/sessions'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 7  # 7 days

os.makedirs('./data/sessions', exist_ok=True)
Session(app)

CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": "*",
        "supports_credentials": True
    }
})

app.config["DATABASE_PATH"] = os.environ.get("DATABASE_PATH", "./data/database.db")
app.config["DATA_DIR"] = "./data"
app.config["PLAYLISTS_DIR"] = "./data/playlists"
app.config["EPG_DIR"] = "./data/epg"

os.makedirs(app.config["DATA_DIR"], exist_ok=True)
os.makedirs(app.config["PLAYLISTS_DIR"], exist_ok=True)
os.makedirs(app.config["EPG_DIR"], exist_ok=True)

from models.playlist import init_db, update_all_playlists
init_db(app.config["DATABASE_PATH"])

# Register blueprints
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(playlist_bp, url_prefix="/api/playlists")
app.register_blueprint(channel_bp, url_prefix="/api/channels")
app.register_blueprint(epg_bp, url_prefix="/api/epg")
app.register_blueprint(stream_bp, url_prefix="/api/stream")
app.register_blueprint(recording_bp, url_prefix="/api/recordings")

scheduler = BackgroundScheduler(daemon=True)
if os.environ.get("AUTO_UPDATE_PLAYLISTS", "true").lower() == "true":
    scheduler.add_job(
        func=lambda: update_all_playlists(app.config),
        trigger="cron",
        hour=6,
        minute=0,
        id="auto_update_playlists",
        replace_existing=True,
    )
    scheduler.start()

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route("/api/health")
def health_check():
    return jsonify({"status": "healthy", "version": "1.0.0"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting IPTV Player on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
