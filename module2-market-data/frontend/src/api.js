export const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8001";
export const AUTH_API_URL = import.meta.env.VITE_AUTH_API_URL || "http://127.0.0.1:8000";

async function get(path, params = {}) {
  const url = new URL(API_URL + path);
  Object.entries(params).forEach(([k, v]) => v && url.searchParams.set(k, v));
  let res;
  try {
    res = await fetch(url);
  } catch {
    throw new Error("Cannot reach the market data server. Is the backend running on " + API_URL + "?");
  }
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") msg = body.detail;
    } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export const searchCompanies = (q, market) => get("/api/search", { q, market });
export const getOverview = (symbol, period, market) =>
  get(`/api/stocks/${encodeURIComponent(symbol)}/overview`, { period, market });

// Optional: read the user's saved preferences from Module 1 (needs login token).
export async function getSavedPreferences() {
  const token = localStorage.getItem("token");
  if (!token) return null;
  try {
    const res = await fetch(`${AUTH_API_URL}/preferences`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return res.ok ? await res.json() : null;
  } catch {
    return null;
  }
}
