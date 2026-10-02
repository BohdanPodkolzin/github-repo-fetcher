import { useState } from "react";

import { fetchFromGithub } from "../api.js";
import { REQUEST_TYPES } from "../requestTypes.js";
import StatusBadge from "../StatusBadge.jsx";

export default function FetchPage() {
  const [type, setType] = useState("repo");
  const [target, setTarget] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  // The user profile request needs a username, every other request needs owner/repo.
  const isUser = type === "user";

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await fetchFromGithub(type, target.trim()));
    } catch (err) {
      // Validation errors (HTTP 400) and an unreachable backend both land here.
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <h1>Fetch from GitHub</h1>
      <form className="form" onSubmit={handleSubmit}>
        <label>
          What to fetch
          <select value={type} onChange={(e) => setType(e.target.value)}>
            {REQUEST_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </label>
        <label className="grow">
          {isUser ? "Username" : "Repository (owner/repo)"}
          <input
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder={isUser ? "torvalds" : "facebook/react"}
            autoComplete="off"
            spellCheck="false"
            required
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "Fetching…" : "Fetch"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {result && (
        <section className="panel">
          <div className="meta">
            <StatusBadge status={result.status_code} />
            <span>{result.duration_ms} ms</span>
            <span>saved as history #{result.id}</span>
          </div>
          {result.error && <p className="error">GitHub: {result.error}</p>}
          {result.response !== null && (
            <pre className="json">{JSON.stringify(result.response, null, 2)}</pre>
          )}
        </section>
      )}
    </>
  );
}
