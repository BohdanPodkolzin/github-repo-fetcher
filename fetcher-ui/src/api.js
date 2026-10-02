// All calls use relative URLs (/api/...), so the same build works behind
// the Vite dev proxy, behind Nginx locally, and on EC2, with no host to configure.

async function request(path, options) {
  const res = await fetch(path, options);
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(body?.error || `Request failed (HTTP ${res.status})`);
  }
  return body;
}

export function fetchFromGithub(type, target) {
  return request("/api/fetch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ type, target }),
  });
}

export function getHistory({ page, perPage, status, type }) {
  const query = new URLSearchParams({ page, per_page: perPage });
  if (status) query.set("status", status);
  if (type) query.set("type", type);
  return request(`/api/history?${query}`);
}

export function getHistoryItem(id) {
  return request(`/api/history/${id}`);
}
