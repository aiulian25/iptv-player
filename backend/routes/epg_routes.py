from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from models.playlist import get_session, EPGSource
from parsers.xmltv_parser import XMLTVParser

epg_bp = Blueprint("epg", __name__)

# Simple in-memory cache per URL
_epg_cache = {}

@epg_bp.route("/sources", methods=["GET"])
def get_epg_sources():
    session = get_session()
    try:
        srcs = session.query(EPGSource).all()
        return jsonify([{
            "id": s.id,
            "name": s.name,
            "url": s.url,
            "auto_update": s.auto_update,
            "last_updated": s.last_updated.isoformat() if s.last_updated else None,
        } for s in srcs])
    finally:
        session.close()

@epg_bp.route("/sources", methods=["POST"])
def add_epg_source():
    data = request.get_json(force=True)
    session = get_session()
    try:
        s = EPGSource(
            name=data["name"],
            url=data["url"],
            auto_update=data.get("auto_update", True),
        )
        session.add(s)
        session.commit()
        return jsonify({"id": s.id, "name": s.name}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@epg_bp.route("/programmes", methods=["GET"])
def get_programmes():
    channel_id = request.args.get("channel_id")
    if not channel_id:
        return jsonify({"error": "channel_id required"}), 400

    parser = XMLTVParser()
    session = get_session()
    try:
        for source in session.query(EPGSource).all():
            try:
                if source.url not in _epg_cache:
                    _epg_cache[source.url] = XMLTVParser()
                    _epg_cache[source.url].parse_from_url(source.url)
                parser = _epg_cache[source.url]
            except Exception:
                continue

        now = datetime.utcnow()
        end = now + timedelta(days=7)
        progs = parser.get_programmes_by_channel(channel_id, now, end)
        return jsonify([{
            "channel": p["channel"],
            "start": p["start"].isoformat() if p["start"] else None,
            "stop": p["stop"].isoformat() if p["stop"] else None,
            "title": p["title"],
            "desc": p["desc"],
            "category": p["category"],
            "icon": p["icon"],
        } for p in progs])
    finally:
        session.close()

@epg_bp.route("/current", methods=["GET"])
def get_current():
    channel_id = request.args.get("channel_id")
    if not channel_id:
        return jsonify({"error": "channel_id required"}), 400

    parser = XMLTVParser()
    session = get_session()
    try:
        for source in session.query(EPGSource).all():
            try:
                if source.url not in _epg_cache:
                    _epg_cache[source.url] = XMLTVParser()
                    _epg_cache[source.url].parse_from_url(source.url)
                parser = _epg_cache[source.url]
            except Exception:
                continue

        p = parser.get_current_programme(channel_id)
        if not p:
            return jsonify(None)
        return jsonify({
            "channel": p["channel"],
            "start": p["start"].isoformat() if p["start"] else None,
            "stop": p["stop"].isoformat() if p["stop"] else None,
            "title": p["title"],
            "desc": p["desc"],
            "category": p["category"],
            "icon": p["icon"],
        })
    finally:
        session.close()
