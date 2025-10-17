from flask import Blueprint, request, jsonify, Response
import requests
from urllib.parse import urlparse, urljoin
import re
from sqlalchemy import or_
from models.playlist import get_session, Channel
from middleware.auth_middleware import login_required, password_change_required

channel_bp = Blueprint("channel", __name__)

@channel_bp.route("", methods=["GET"])
@login_required
def get_channels():
    """Get channels - REQUIRES AUTH"""
    session = get_session()
    try:
        playlist_id = request.args.get("playlist_id")
        group = request.args.get("group")
        search = request.args.get("search")
        favorites = request.args.get("favorites")

        query = session.query(Channel)
        if playlist_id:
            query = query.filter(Channel.playlist_id == int(playlist_id))
        if group:
            query = query.filter(Channel.group_title == group)
        if search:
            like = f"%{search}%"
            query = query.filter(or_(Channel.name.like(like), Channel.tvg_name.like(like)))
        if favorites and favorites.lower() == "true":
            query = query.filter(Channel.is_favorite == True)

        rows = query.all()
        return jsonify([{
            "id": c.id,
            "playlist_id": c.playlist_id,
            "name": c.name,
            "group_title": c.group_title,
            "tvg_id": c.tvg_id,
            "tvg_name": c.tvg_name,
            "tvg_logo": c.tvg_logo,
            "stream_url": c.stream_url,
            "catchup": c.catchup,
            "catchup_source": c.catchup_source,
            "catchup_days": c.catchup_days,
            "is_favorite": c.is_favorite,
            "channel_number": c.channel_number,
        } for c in rows])
    finally:
        session.close()

@channel_bp.route("/groups", methods=["GET"])
@login_required
def get_groups():
    """Get channel groups - REQUIRES AUTH"""
    session = get_session()
    try:
        playlist_id = request.args.get("playlist_id")
        query = session.query(Channel.group_title).distinct()
        if playlist_id:
            query = query.filter(Channel.playlist_id == int(playlist_id))
        groups = [g[0] for g in query.all() if g[0]]
        return jsonify(groups)
    finally:
        session.close()

@channel_bp.route("/<int:channel_id>/favorite", methods=["POST"])
@login_required
def toggle_favorite(channel_id: int):
    """Toggle favorite - REQUIRES AUTH"""
    session = get_session()
    try:
        ch = session.query(Channel).get(channel_id)
        if not ch:
            return jsonify({"error": "Channel not found"}), 404
        ch.is_favorite = not ch.is_favorite
        session.commit()
        return jsonify({"id": ch.id, "is_favorite": ch.is_favorite})
    finally:
        session.close()

@channel_bp.route("/<int:channel_id>", methods=["GET"])
@login_required
def get_channel(channel_id: int):
    """Get single channel - REQUIRES AUTH"""
    session = get_session()
    try:
        ch = session.query(Channel).get(channel_id)
        if not ch:
            return jsonify({"error": "Channel not found"}), 404
        return jsonify({
            "id": ch.id,
            "name": ch.name,
            "stream_url": ch.stream_url,
        })
    finally:
        session.close()

@channel_bp.route("/<int:channel_id>", methods=["DELETE"])
@login_required
@password_change_required
def delete_channel(channel_id: int):
    """Delete channel - REQUIRES AUTH"""
    session = get_session()
    try:
        ch = session.query(Channel).get(channel_id)
        if not ch:
            return jsonify({"error": "Channel not found"}), 404
        
        session.delete(ch)
        session.commit()
        print(f"Deleted channel: {ch.name} (ID: {channel_id})")
        return jsonify({"message": "Channel deleted", "id": channel_id})
    except Exception as e:
        session.rollback()
        print(f"Error deleting channel: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@channel_bp.route("/bulk-delete", methods=["POST"])
@login_required
@password_change_required
def bulk_delete_channels():
    """Bulk delete channels - REQUIRES AUTH"""
    data = request.get_json()
    channel_ids = data.get("channel_ids", [])
    
    if not channel_ids:
        return jsonify({"error": "No channel IDs provided"}), 400
    
    session = get_session()
    try:
        deleted_count = session.query(Channel).filter(Channel.id.in_(channel_ids)).delete(synchronize_session=False)
        session.commit()
        print(f"Bulk deleted {deleted_count} channels")
        return jsonify({"message": f"Deleted {deleted_count} channels", "count": deleted_count})
    except Exception as e:
        session.rollback()
        print(f"Error bulk deleting channels: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()
