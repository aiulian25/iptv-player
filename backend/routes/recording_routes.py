from flask import Blueprint, request, jsonify, send_file
import subprocess
import os
import json
from datetime import datetime
import threading
from middleware.auth_middleware import login_required, password_change_required

recording_bp = Blueprint("recording", __name__)

active_recordings = {}

RECORDINGS_DIR = "/app/data/recordings"
os.makedirs(RECORDINGS_DIR, exist_ok=True)

@recording_bp.route("/start", methods=["POST"])
@login_required
@password_change_required
def start_recording():
    """Start recording - REQUIRES AUTH"""
    data = request.get_json()
    stream_url = data.get("stream_url")
    channel_name = data.get("channel_name", "Unknown")
    duration = data.get("duration", 3600)
    
    if not stream_url:
        return jsonify({"error": "stream_url required"}), 400
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in channel_name if c.isalnum() or c in (' ', '-', '_')).strip()
    filename = f"{safe_name}_{timestamp}.mp4"
    output_path = os.path.join(RECORDINGS_DIR, filename)
    
    cmd = [
        "ffmpeg",
        "-i", stream_url,
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        "-t", str(duration),
        "-y",
        output_path
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        recording_id = f"{channel_name}_{timestamp}"
        active_recordings[recording_id] = {
            "process": process,
            "filename": filename,
            "output_path": output_path,
            "channel_name": channel_name,
            "started_at": datetime.now().isoformat(),
            "duration": duration,
            "status": "recording"
        }
        
        print(f"[RECORDING] Started: {channel_name} -> {filename}")
        
        return jsonify({
            "recording_id": recording_id,
            "filename": filename,
            "message": "Recording started",
            "duration": duration
        }), 200
        
    except Exception as e:
        print(f"[RECORDING] Error starting: {e}")
        return jsonify({"error": str(e)}), 500

@recording_bp.route("/stop/<recording_id>", methods=["POST"])
@login_required
@password_change_required
def stop_recording(recording_id):
    """Stop recording - REQUIRES AUTH"""
    if recording_id not in active_recordings:
        return jsonify({"error": "Recording not found"}), 404
    
    recording = active_recordings[recording_id]
    process = recording["process"]
    
    try:
        process.terminate()
        process.wait(timeout=5)
        
        recording["status"] = "stopped"
        print(f"[RECORDING] Stopped: {recording['channel_name']}")
        
        return jsonify({
            "message": "Recording stopped",
            "filename": recording["filename"]
        }), 200
        
    except subprocess.TimeoutExpired:
        process.kill()
        recording["status"] = "killed"
        return jsonify({"message": "Recording force stopped"}), 200
    except Exception as e:
        print(f"[RECORDING] Error stopping: {e}")
        return jsonify({"error": str(e)}), 500

@recording_bp.route("/list", methods=["GET"])
@login_required
@password_change_required
def list_recordings():
    """List recordings - REQUIRES AUTH"""
    try:
        files = []
        for filename in os.listdir(RECORDINGS_DIR):
            if filename.endswith('.mp4'):
                filepath = os.path.join(RECORDINGS_DIR, filename)
                stat = os.stat(filepath)
                files.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "size_mb": round(stat.st_size / 1024 / 1024, 2),
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
        
        files.sort(key=lambda x: x["created"], reverse=True)
        
        return jsonify({
            "recordings": files,
            "active": [
                {
                    "id": rid,
                    "channel": rec["channel_name"],
                    "filename": rec["filename"],
                    "started_at": rec["started_at"],
                    "status": rec["status"]
                }
                for rid, rec in active_recordings.items()
                if rec["status"] == "recording"
            ]
        }), 200
        
    except Exception as e:
        print(f"[RECORDING] Error listing: {e}")
        return jsonify({"error": str(e)}), 500

@recording_bp.route("/download/<filename>", methods=["GET"])
@login_required
@password_change_required
def download_recording(filename):
    """Download recording - REQUIRES AUTH"""
    filepath = os.path.join(RECORDINGS_DIR, filename)
    
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    
    return send_file(filepath, as_attachment=True, download_name=filename)

@recording_bp.route("/delete/<filename>", methods=["DELETE"])
@login_required
@password_change_required
def delete_recording(filename):
    """Delete recording - REQUIRES AUTH"""
    filepath = os.path.join(RECORDINGS_DIR, filename)
    
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    
    try:
        os.remove(filepath)
        print(f"[RECORDING] Deleted: {filename}")
        return jsonify({"message": "Recording deleted"}), 200
    except Exception as e:
        print(f"[RECORDING] Error deleting: {e}")
        return jsonify({"error": str(e)}), 500

@recording_bp.route("/status", methods=["GET"])
def recording_status():
    """Get recording status - PUBLIC (for monitoring)"""
    active = []
    
    for recording_id, rec in list(active_recordings.items()):
        process = rec["process"]
        
        if process.poll() is not None:
            rec["status"] = "completed"
        
        active.append({
            "id": recording_id,
            "channel": rec["channel_name"],
            "filename": rec["filename"],
            "status": rec["status"],
            "started_at": rec["started_at"],
            "duration": rec["duration"]
        })
    
    return jsonify({"active_recordings": active}), 200
