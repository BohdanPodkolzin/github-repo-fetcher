// status is GitHub's HTTP status, or null when GitHub never answered (timeout, network error).
export default function StatusBadge({ status }) {
  if (status === null || status === undefined) {
    return <span className="badge badge-fail">no answer</span>;
  }
  const ok = status >= 200 && status < 300;
  return <span className={`badge ${ok ? "badge-ok" : "badge-fail"}`}>{status}</span>;
}
