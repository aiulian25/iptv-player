from flask import Blueprint, request, jsonify
import os
from datetime import datetime
from models.playlist import get_session, Playlist, add_playlist, delete_playlist_by_id
from middleware.auth_middleware import login_required, password_change_required

playlist_bp = Blueprint("playlist", __name__)

@playlist_bp.route("", methods=["GET"])
@login_required
def get_playlists():
    """Get all playlists - REQUIRES AUTH"""
    session = get_session()
    try:
        playlists = session.query(Playlist).all()
        return jsonify([{
            "id": p.id,
            "name": p.name,
            "playlist_type": p.playlist_type,
            "source_url": p.source_url,
            "file_path": p.file_path,
            "channel_count": p.channel_count,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "last_updated": p.last_updated.isoformat() if p.last_updated else None,
        } for p in playlists])
    finally:
        session.close()

@playlist_bp.route("/<int:playlist_id>", methods=["GET"])
@login_required
def get_playlist(playlist_id: int):
    """Get single playlist - REQUIRES AUTH"""
    session = get_session()
    try:
        playlist = session.query(Playlist).get(playlist_id)
        if not playlist:
            return jsonify({"error": "Playlist not found"}), 404
        
        return jsonify({
            "id": playlist.id,
            "name": playlist.name,
            "playlist_type": playlist.playlist_type,
            "source_url": playlist.source_url,
            "file_path": playlist.file_path,
            "channel_count": playlist.channel_count,
            "created_at": playlist.created_at.isoformat() if playlist.created_at else None,
            "last_updated": playlist.last_updated.isoformat() if playlist.last_updated else None,
        })
    finally:
        session.close()

@playlist_bp.route("", methods=["POST"])
@login_required
@password_change_required
def create_playlist():
    """Create playlist - REQUIRES AUTH"""
    data = request.get_json()
    
    required_fields = ["name", "playlist_type", "source_type"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    try:
        playlist = add_playlist(
            name=data["name"],
            playlist_type=data["playlist_type"],
            source_type=data["source_type"],
            source_url=data.get("source_url"),
            file_path=data.get("file_path"),
            user_agent=data.get("user_agent"),
            xtream_username=data.get("xtream_username"),
            xtream_password=data.get("xtream_password"),
            stalker_mac=data.get("stalker_mac"),
            auto_update=data.get("auto_update", True)
        )
        
        return jsonify({
            "id": playlist.id,
            "name": playlist.name,
            "channel_count": playlist.channel_count,
            "message": "Playlist added successfully"
        }), 201
        
    except Exception as e:
        print(f"Error creating playlist: {e}")
        return jsonify({"error": str(e)}), 500

@playlist_bp.route("/<int:playlist_id>", methods=["DELETE"])
@login_required
@password_change_required
def delete_playlist(playlist_id: int):
    """Delete playlist - REQUIRES AUTH"""
    try:
        success = delete_playlist_by_id(playlist_id)
        if success:
            return jsonify({"message": "Playlist deleted"}), 200
        else:
            return jsonify({"error": "Playlist not found"}), 404
    except Exception as e:
        print(f"Error deleting playlist: {e}")
        return jsonify({"error": str(e)}), 500

@playlist_bp.route("/upload", methods=["POST"])
@login_required
@password_change_required
def upload_file():
    """Upload M3U file - REQUIRES AUTH"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.endswith(('.m3u', '.m3u8')):
        return jsonify({"error": "Only .m3u and .m3u8 files are allowed"}), 400
    
    try:
        upload_dir = "./data/playlists"
        os.makedirs(upload_dir, exist_ok=True)
        
        safe_filename = file.filename.replace(" ", "_")
        filepath = os.path.join(upload_dir, safe_filename)
        
        file.save(filepath)
        
        return jsonify({
            "message": "File uploaded successfully",
            "filepath": filepath,
            "filename": safe_filename
        }), 200
        
    except Exception as e:
        print(f"Error uploading file: {e}")
        return jsonify({"error": str(e)}), 500

@playlist_bp.route("/<int:playlist_id>/update", methods=["POST"])
@login_required
@password_change_required
def update_playlist(playlist_id: int):
    """Update/refresh playlist - REQUIRES AUTH"""
    from models.playlist import update_playlist_channels
    
    try:
        session = get_session()
        playlist = session.query(Playlist).get(playlist_id)
        session.close()
        
        if not playlist:
            return jsonify({"error": "Playlist not found"}), 404
        
        update_playlist_channels(playlist)
        
        return jsonify({
            "message": "Playlist updated successfully",
            "channel_count": playlist.channel_count
        }), 200
        
    except Exception as e:
        print(f"Error updating playlist: {e}")
        return jsonify({"error": str(e)}), 500

@playlist_bp.route("/store", methods=["POST"])
@login_required
@password_change_required
def store_m3u():
    """Store M3U file for later use"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.endswith(('.m3u', '.m3u8')):
        return jsonify({"error": "Only .m3u and .m3u8 files are allowed"}), 400
    
    try:
        storage_dir = "./data/m3u_storage"
        os.makedirs(storage_dir, exist_ok=True)
        
        safe_filename = file.filename.replace(" ", "_")
        filepath = os.path.join(storage_dir, safe_filename)
        
        file.save(filepath)
        
        return jsonify({
            "message": "M3U file stored successfully",
            "filepath": filepath,
            "filename": safe_filename
        }), 200
        
    except Exception as e:
        print(f"Error storing M3U file: {e}")
        return jsonify({"error": str(e)}), 500

@playlist_bp.route("/stored", methods=["GET"])
@login_required
def list_stored_m3u():
    """List stored M3U files"""
    try:
        storage_dir = "./data/m3u_storage"
        os.makedirs(storage_dir, exist_ok=True)
        
        files = []
        for filename in os.listdir(storage_dir):
            if filename.endswith(('.m3u', '.m3u8')):
                filepath = os.path.join(storage_dir, filename)
                stat = os.stat(filepath)
                files.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "size_mb": round(stat.st_size / 1024 / 1024, 2),
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
        
        files.sort(key=lambda x: x["created"], reverse=True)
        return jsonify(files), 200
        
    except Exception as e:
        print(f"Error listing stored M3U files: {e}")
        return jsonify({"error": str(e)}), 500

@playlist_bp.route("/stored/<filename>", methods=["DELETE"])
@login_required
@password_change_required
def delete_stored_m3u(filename):
    """Delete stored M3U file"""
    try:
        storage_dir = "./data/m3u_storage"
        filepath = os.path.join(storage_dir, filename)
        
        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404
        
        os.remove(filepath)
        return jsonify({"message": "File deleted successfully"}), 200
        
    except Exception as e:
        print(f"Error deleting stored M3U file: {e}")
        return jsonify({"error": str(e)}), 500

@playlist_bp.route("/stored/<filename>/download", methods=["GET"])
@login_required
def download_stored_m3u(filename):
    """Download stored M3U file"""
    from flask import send_file
    try:
        storage_dir = "./data/m3u_storage"
        filepath = os.path.join(storage_dir, filename)
        
        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        print(f"Error downloading stored M3U file: {e}")
        return jsonify({"error": str(e)}), 500
