const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";
const TOKEN_KEY = "book_condenser_token";

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  let body;
  try {
    body = contentType.includes("application/json")
      ? await response.json()
      : await response.text();
  } catch {
    body = await response.text().catch(() => "");
  }

  if (!response.ok) {
    let message = "Something went wrong. Please try again.";
    if (typeof body === "object" && body !== null) {
      if (typeof body.detail === "string" && body.detail) {
        message = body.detail;
      } else if (body.detail && typeof body.detail === "object") {
        message = body.detail.message || JSON.stringify(body.detail);
      } else if (typeof body.message === "string" && body.message) {
        message = body.message;
      }
    } else if (typeof body === "string" && body.trim()) {
      try {
        const parsed = JSON.parse(body);
        message = parsed.detail || parsed.message || body;
      } catch {
        message = body;
      }
    }
    throw new Error(message);
  }

  return body;
}

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function storeToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export async function signup({ fullName, email, password }) {
  return parseResponse(await fetch(`${API_BASE_URL}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      full_name: fullName,
      email,
      password
    })
  }));
}

export async function login({ email, password }) {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);

  return parseResponse(await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form
  }));
}

export async function getProfile(token) {
  return parseResponse(await fetch(`${API_BASE_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` }
  }));
}

export async function requestPasswordReset(email) {
  return parseResponse(await fetch(`${API_BASE_URL}/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email })
  }));
}

export async function resetPassword({ accessToken, refreshToken, newPassword }) {
  return parseResponse(await fetch(`${API_BASE_URL}/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      access_token: accessToken,
      refresh_token: refreshToken,
      new_password: newPassword
    })
  }));
}

export async function uploadBook({ file, token, signal }) {
  const form = new FormData();
  form.append("file", file);

  return parseResponse(await fetch(`${API_BASE_URL}/auth/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
    signal
  }));
}
