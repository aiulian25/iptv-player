from flask import Blueprint, request, jsonify, session
from datetime import datetime
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.user import User

auth_bp = Blueprint("auth", __name__)

def get_user_session():
    db_path = os.environ.get("DATABASE_PATH", "./data/database.db")
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    return Session()

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    db_session = get_user_session()
    try:
        user = db_session.query(User).filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid username or password"}), 401
        
        user.last_login = datetime.utcnow()
        db_session.commit()
        
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin
        session['must_change_password'] = user.must_change_password
        
        return jsonify({
            "message": "Login successful",
            "user": user.to_dict()
        }), 200
        
    finally:
        db_session.close()

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200

@auth_bp.route("/change-password", methods=["POST"])
def change_password():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    data = request.get_json()
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    user_id = data.get("user_id", session['user_id'])
    
    if not current_password or not new_password:
        return jsonify({"error": "Current and new password required"}), 400
    
    if len(new_password) < 8:
        return jsonify({"error": "New password must be at least 8 characters"}), 400
    
    db_session = get_user_session()
    try:
        current_user = db_session.query(User).get(session['user_id'])
        
        # Check if admin changing another user's password
        if user_id != session['user_id']:
            if not session.get('is_admin'):
                return jsonify({"error": "Admin access required"}), 403
            target_user = db_session.query(User).get(user_id)
            if not target_user:
                return jsonify({"error": "User not found"}), 404
        else:
            target_user = current_user
        
        # Verify current user's password
        if not current_user.check_password(current_password):
            return jsonify({"error": "Current password is incorrect"}), 401
        
        target_user.set_password(new_password)
        target_user.must_change_password = False
        db_session.commit()
        
        if user_id == session['user_id']:
            session['must_change_password'] = False
        
        return jsonify({"message": "Password changed successfully"}), 200
        
    finally:
        db_session.close()

@auth_bp.route("/change-username", methods=["POST"])
def change_username():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    data = request.get_json()
    new_username = data.get("new_username")
    password = data.get("password")
    user_id = data.get("user_id", session['user_id'])
    
    if not new_username or not password:
        return jsonify({"error": "New username and password required"}), 400
    
    if len(new_username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400
    
    db_session = get_user_session()
    try:
        current_user = db_session.query(User).get(session['user_id'])
        
        # Verify current user's password
        if not current_user.check_password(password):
            return jsonify({"error": "Password is incorrect"}), 401
        
        # Check if admin changing another user's username
        if user_id != session['user_id']:
            if not session.get('is_admin'):
                return jsonify({"error": "Admin access required"}), 403
            target_user = db_session.query(User).get(user_id)
            if not target_user:
                return jsonify({"error": "User not found"}), 404
        else:
            target_user = current_user
        
        # Check if username already exists
        existing_user = db_session.query(User).filter_by(username=new_username).first()
        if existing_user and existing_user.id != target_user.id:
            return jsonify({"error": "Username already taken"}), 400
        
        target_user.username = new_username
        db_session.commit()
        
        if user_id == session['user_id']:
            session['username'] = new_username
        
        return jsonify({"message": "Username changed successfully", "username": new_username}), 200
        
    finally:
        db_session.close()

@auth_bp.route("/profile", methods=["GET"])
def get_profile():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    db_session = get_user_session()
    try:
        user = db_session.query(User).get(session['user_id'])
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify(user.to_dict()), 200
    finally:
        db_session.close()

@auth_bp.route("/users", methods=["GET"])
def list_users():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    if not session.get('is_admin'):
        return jsonify({"error": "Admin access required"}), 403
    
    db_session = get_user_session()
    try:
        users = db_session.query(User).all()
        return jsonify([user.to_dict() for user in users]), 200
    finally:
        db_session.close()

@auth_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    if not session.get('is_admin'):
        return jsonify({"error": "Admin access required"}), 403
    
    if user_id == session['user_id']:
        return jsonify({"error": "Cannot delete your own account"}), 400
    
    db_session = get_user_session()
    try:
        user = db_session.query(User).get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        db_session.delete(user)
        db_session.commit()
        
        return jsonify({"message": "User deleted successfully"}), 200
    finally:
        db_session.close()

@auth_bp.route("/register", methods=["POST"])
def register():
    if 'user_id' not in session:
        disable_signups = os.environ.get("DISABLE_SIGNUPS", "false").lower() == "true"
        if disable_signups:
            return jsonify({"error": "User registration is disabled"}), 403
    else:
        if not session.get('is_admin'):
            return jsonify({"error": "Admin access required"}), 403
    
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    is_admin = data.get("is_admin", False)
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400
    
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    
    db_session = get_user_session()
    try:
        existing_user = db_session.query(User).filter_by(username=username).first()
        if existing_user:
            return jsonify({"error": "Username already exists"}), 400
        
        user = User(username=username, is_admin=is_admin, must_change_password=False)
        user.set_password(password)
        db_session.add(user)
        db_session.commit()
        
        return jsonify({
            "message": "User created successfully",
            "user": user.to_dict()
        }), 201
        
    finally:
        db_session.close()

@auth_bp.route("/status", methods=["GET"])
def auth_status():
    if 'user_id' in session:
        return jsonify({
            "authenticated": True,
            "username": session.get('username'),
            "is_admin": session.get('is_admin'),
            "must_change_password": session.get('must_change_password')
        }), 200
    else:
        return jsonify({"authenticated": False}), 200
