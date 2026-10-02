import { useEffect, useState } from "react";

import { getHistory, getHistoryItem } from "../api.js";
import { REQUEST_TYPES, typeLabel } from "../requestTypes.js";
import StatusBadge from "../StatusBadge.jsx";

const PER_PAGE = 10;

const STATUS_FILTERS = [
  { value: "", label: "Any status" },
  { value: "200", label: "200 OK" },
  { value: "404", label: "404 Not Found" },
  { value: "403", label: "403 Forbidden" },
  { value: "429", label: "429 Too Many Requests" },
  { value: "none", label: "No answer (timeout)" },
];

export default function HistoryPage() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");
  const [type, setType] = useState("");
  const [data, setData] = useState(null); // {items, total, page, per_page}
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null); // full row, including response
  const [selectedError, setSelectedError] = useState(null);

  // Reload the list whenever the page or a filter changes.
  useEffect(() => {
    let stale = false; // ignore a slow answer if a newer request was started
    setError(null);
    getHistory({ page, perPage: PER_PAGE, status, type })
      .then((body) => !stale && setData(body))
      .catch((err) => !stale && setError(err.message));
    return () => {
      stale = true;
    };
  }, [page, status, type]);

  function changeFilter(setter) {
    return (event) => {
      setter(event.target.value);
      setPage(1);
      setSelected(null);
    };
  }

  async function openRow(id) {
    setSelectedError(null);
    try {
      setSelected(await getHistoryItem(id));
    } catch (err) {
      setSelected(null);
      setSelectedError(err.message);
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PER_PAGE)) : 1;

  return (
    <>
      <h1>History</h1>
      <div className="form">
        <label>
          Request type
          <select value={type} onChange={changeFilter(setType)}>
            <option value="">Any type</option>
            {REQUEST_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Status
          <select value={status} onChange={changeFilter(setStatus)}>
            {STATUS_FILTERS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error && <p className="error">{error}</p>}
      {!data && !error && <p>Loading…</p>}

      {data && data.items.length === 0 && <p>No requests match.</p>}

      {data && data.items.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Request type</th>
                <th>Params</th>
                <th>Status</th>
                <th className="num">Duration</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((row) => (
                <tr
                  key={row.id}
                  className={selected?.id === row.id ? "active" : ""}
                  onClick={() => openRow(row.id)}
                  onKeyDown={(e) => e.key === "Enter" && openRow(row.id)}
                  tabIndex={0}
                  title="Show full response"
                >
                  <td>{new Date(row.created_at).toLocaleString()}</td>
                  <td>{typeLabel(row.endpoint)}</td>
                  <td>
                    <code>{row.params.target ?? JSON.stringify(row.params)}</code>
                  </td>
                  <td>
                    <StatusBadge status={row.status_code} />
                  </td>
                  <td className="num">{row.duration_ms} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data && (
        <div className="pager">
          <button onClick={() => setPage(page - 1)} disabled={page <= 1}>
            Previous
          </button>
          <span>
            Page {page} of {totalPages} ({data.total} requests)
          </span>
          <button onClick={() => setPage(page + 1)} disabled={page >= totalPages}>
            Next
          </button>
        </div>
      )}

      {selectedError && <p className="error">{selectedError}</p>}

      {selected && (
        <section className="panel">
          <div className="meta">
            <strong>Request #{selected.id}</strong>
            <StatusBadge status={selected.status_code} />
            <span>{selected.duration_ms} ms</span>
            <button className="link" onClick={() => setSelected(null)}>
              Close
            </button>
          </div>
          {selected.error && <p className="error">GitHub: {selected.error}</p>}
          <pre className="json">
            {selected.response === null
              ? "No response body was stored."
              : JSON.stringify(selected.response, null, 2)}
          </pre>
        </section>
      )}
    </>
  );
}
