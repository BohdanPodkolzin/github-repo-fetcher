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


MAX_PER_PAGE = 100
MAX_BIGINT = 2**63 - 1  # largest id Postgres can store


@bp.get("/api/history")
def history():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
    except ValueError:
        return jsonify(error="page and per_page must be integers"), 400
    if page < 1 or not 1 <= per_page <= MAX_PER_PAGE:
        return jsonify(error=f"page must be >= 1 and per_page between 1 and {MAX_PER_PAGE}"), 400
    if (page - 1) * per_page > MAX_BIGINT:
        return jsonify(error="page is too large"), 400

    # status=404 filters by GitHub status; status=none finds requests that never got an answer.
    status = request.args.get("status")
    status_is_null = status == "none"
    if status is not None and not status_is_null:
        try:
            status = int(status)
        except ValueError:
            return jsonify(error="status must be an integer or 'none'"), 400
        if not 100 <= status <= 599:
            return jsonify(error="status must be an HTTP status code (100-599)"), 400

    req_type = request.args.get("type")
    if req_type is not None and req_type not in github.ENDPOINTS:
        return jsonify(error="type must be one of: " + ", ".join(github.ENDPOINTS)), 400

    try:
        items, total = db.list_requests(
            page=page,
            per_page=per_page,
            status=None if status_is_null else status,
            status_is_null=status_is_null,
            req_type=req_type,
        )
    except Exception:
        current_app.logger.exception("could not read history")
        return jsonify(error="database unavailable"), 503

    return jsonify(items=items, total=total, page=page, per_page=per_page), 200


@bp.get("/api/history/<int:request_id>")
def history_item(request_id):
    if request_id > MAX_BIGINT:
        return jsonify(error="not found"), 404
    try:
        row = db.get_request(request_id)
    except Exception:
        current_app.logger.exception("could not read history item")
        return jsonify(error="database unavailable"), 503
    if row is None:
        return jsonify(error="not found"), 404
    return jsonify(row), 200
