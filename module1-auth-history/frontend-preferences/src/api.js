// Small API helper. Change API_URL if your backend runs elsewhere.
export const API_URL = import.meta.env?.VITE_API_URL || "http://127.0.0.1:8000";

// Token is saved by the login page: localStorage.setItem("token", access_token)
const authHeaders = () => ({
  "Content-Type": "application/json",
  Authorization: `Bearer ${localStorage.getItem("token")}`,
});

async function handle(res) {
  if (res.status === 401) throw new Error("Session expired. Please log in again.");
  if (!res.ok) {
    let msg = "Something went wrong";
    try {
      const body = await res.json();
      msg = typeof body.detail === "string" ? body.detail : "Invalid selection";
    } catch {}
    throw new Error(msg);
  }
  return res.status === 204 ? null : res.json();
}

export const getPreferences = () =>
  fetch(`${API_URL}/preferences`, { headers: authHeaders() }).then(handle);

export const savePreferences = (data) =>
  fetch(`${API_URL}/preferences`, {
    method: "PUT",
    headers: authHeaders(),
    body: JSON.stringify(data),
  }).then(handle);

export const resetPreferences = () =>
  fetch(`${API_URL}/preferences`, { method: "DELETE", headers: authHeaders() }).then(handle);
