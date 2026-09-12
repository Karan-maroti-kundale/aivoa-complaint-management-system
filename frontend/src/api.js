async function parseResponse(r, fallbackMessage) {
  const text = await r.text();
  let body = null;
  try {
    body = text ? JSON.parse(text) : null;
  } catch (_) {}
  if (!r.ok) {
    const detail =
      body?.detail ||
      (text &&
        text
          .replace(/<[^>]*>/g, " ")
          .replace(/\s+/g, " ")
          .trim()) ||
      fallbackMessage;
    throw new Error(detail);
  }
  if (!body)
    throw new Error("The server returned an empty or invalid JSON response.");
  return body;
}

export async function postJSON(url, body) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseResponse(r, "Request failed");
}
export async function upload(url, file) {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch(url, { method: "POST", body: fd });
  return parseResponse(r, "Upload failed");
}
export async function commit(id) {
  const r = await fetch(`/api/v1/complaints/${id}/commit`, { method: "POST" });
  return parseResponse(r, "Commit failed");
}
export async function audit(id) {
  const r = await fetch(`/api/v1/complaints/${id}/audit`);
  return parseResponse(r, "Audit lookup failed");
}
