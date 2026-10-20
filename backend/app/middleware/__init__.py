"""Authentication & authorization helpers (JWT + role-based access control)."""

from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required, get_jwt

from app.extensions import db
from app.models.user import User


def _load_user(user_id):
    return db.session.get(User, int(user_id)) if user_id else None


def get_current_user():
    """Return the User object for the current JWT identity (or None)."""
    identity = get_jwt_identity()
    if identity is None:
        return None
    return _load_user(identity)


def require_role(*roles):
    """Decorator factory: enforce a valid JWT and one of the allowed roles.

    Usage:
        @jwt_required()
        @require_role("admin")
        def admin_only(): ...
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if user is None:
                return jsonify(success=False, message="Unauthorized"), 401
            if user.role not in roles:
                return jsonify(success=False, message="Forbidden: insufficient role"), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def get_current_role():
    claims = get_jwt()
    return claims.get("role")


__all__ = ["get_current_user", "require_role", "get_current_role"]
