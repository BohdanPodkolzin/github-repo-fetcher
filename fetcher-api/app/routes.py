from flask import Blueprint, current_app, jsonify, request # pyright: ignore[reportMissingImports]

from . import db, github

bp = Blueprint("api", __name__)


@bp.get("/db/health")
def health():
    if db.is_healthy():
        return jsonify(status="ok"), 200
    return jsonify(status="unavailable", detail="database unreachable"), 503


@bp.post("/api/fetch")
def fetch():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error="request body must be a JSON object"), 400

    req_type = body.get("type")
    target = body.get("target")
    try:
        github.validate(req_type, target)
    except github.ValidationError as exc:
        # Nothing was sent to GitHub, so nothing is recorded.
        return jsonify(error=str(exc)), 400

    token = current_app.config["APP_CONFIG"].github_token
    result = github.fetch(req_type, target, token)

    # Recorded whatever the outcome: success, 404, rate limit or timeout.
    try:
        row = db.insert_request(
            endpoint=req_type,
            params={"target": target},
            status_code=result["status_code"],
            duration_ms=result["duration_ms"],
            response=result["response"],
            error=result["error"],
        )
    except Exception:
        current_app.logger.exception("could not record request")
        return jsonify(error="could not record the request in the database"), 503

    return jsonify(row), 200
