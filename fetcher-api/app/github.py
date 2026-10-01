"""Everything that knows about the GitHub REST API. No Flask or database code here."""

import re
import time

import requests

API_ROOT = "https://api.github.com"
TIMEOUT_SECONDS = 10
PER_PAGE = 10  # keep stored responses small

# request type -> (path template, query parameters)
ENDPOINTS = {
    "repo": ("/repos/{target}", {}),
    "commits": ("/repos/{target}/commits", {"per_page": PER_PAGE}),
    "issues": ("/repos/{target}/issues", {"state": "open", "per_page": PER_PAGE}),
    "releases": ("/repos/{target}/releases", {"per_page": PER_PAGE}),
    "contributors": ("/repos/{target}/contributors", {"per_page": PER_PAGE}),
    "languages": ("/repos/{target}/languages", {}),
    "user": ("/users/{target}", {}),
}

# GitHub names: letters, digits and hyphens for owners; repos also allow "." and "_".
# Strict patterns mean user input can never alter the URL path (no "/", "..", "?").
_OWNER = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})"
_USER_RE = re.compile(_OWNER)
_REPO_RE = re.compile(_OWNER + r"/(?!\.{1,2}$)[A-Za-z0-9._-]{1,100}")


class ValidationError(ValueError):
    pass


def validate(req_type, target):
    if req_type not in ENDPOINTS:
        allowed = ", ".join(ENDPOINTS)
        raise ValidationError(f"type must be one of: {allowed}")
    if not isinstance(target, str):
        raise ValidationError("target must be a string")
    if req_type == "user":
        if not _USER_RE.fullmatch(target):
            raise ValidationError("target must be a GitHub username, e.g. torvalds")
    elif not _REPO_RE.fullmatch(target):
        raise ValidationError("target must look like owner/repo, e.g. facebook/react")


def fetch(req_type, target, token):
    """Call GitHub and describe the outcome. Never raises: every outcome is a result."""
    path, query = ENDPOINTS[req_type]
    url = API_ROOT + path.format(target=target)
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "github-repo-fetcher",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    result = {"status_code": None, "response": None, "error": None}
    started = time.perf_counter()
    try:
        resp = requests.get(url, params=query, headers=headers, timeout=TIMEOUT_SECONDS)
    except requests.Timeout:
        result["error"] = "timeout"
    except requests.RequestException as exc:
        # Only the exception type: the full message can contain request details.
        result["error"] = f"network error: {type(exc).__name__}"
    else:
        result["status_code"] = resp.status_code
        try:
            result["response"] = resp.json()
        except ValueError:
            pass  # empty or non-JSON body
        if not resp.ok:
            result["error"] = _describe_error(resp, result["response"])
    result["duration_ms"] = round((time.perf_counter() - started) * 1000)
    return result


def _describe_error(resp, body):
    # GitHub answers 403 or 429 when rate limited; the header tells it apart from a real 403.
    if resp.status_code in (403, 429) and resp.headers.get("X-RateLimit-Remaining") == "0":
        return "rate limit exceeded"
    if isinstance(body, dict) and body.get("message"):
        return body["message"]
    return f"HTTP {resp.status_code}"
