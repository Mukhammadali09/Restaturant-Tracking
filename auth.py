"""Authentication helpers: JWT tokens and auth-required decorator."""

from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request

from models import User


def generate_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(
            hours=current_app.config.get("JWT_EXPIRY_HOURS", 168)
        ),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def decode_token(token):
    return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])


def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authentication required"}), 401
        token = auth_header[7:].strip()
        if not token:
            return jsonify({"error": "Authentication required"}), 401
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        user = User.query.get(payload.get("user_id"))
        if not user:
            return jsonify({"error": "User not found"}), 401

        g.user = user
        g.user_id = user.id
        return f(*args, **kwargs)

    return decorated
