from flask import Blueprint, jsonify

from . import db

bp = Blueprint("api", __name__)


@bp.get("/db/health")
def health():
    if db.is_healthy():
        return jsonify(status="ok"), 200
    return jsonify(status="unavailable", detail="database unreachable"), 503
