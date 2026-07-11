// lib/api.js
// Thin client for the PersonaAI backend, matching CHROME_EXTENSION_API_CONTRACT.md.
// Used by background.js (source of truth) and re-used via message passing from
// the side panel / content script so token refresh logic lives in ONE place.

const DEFAULT_BASE_URL = "http://localhost:8000";

export async function getBaseUrl() {
  const { baseUrl } = await chrome.storage.local.get("baseUrl");
  return baseUrl || DEFAULT_BASE_URL;
}

export async function getTokens() {
  const { accessToken, refreshToken } = await chrome.storage.local.get([
    "accessToken",
    "refreshToken",
  ]);
  return { accessToken, refreshToken };
}

export async function setTokens({ accessToken, refreshToken }) {
  await chrome.storage.local.set({ accessToken, refreshToken });
}

export async function clearTokens() {
  await chrome.storage.local.remove(["accessToken", "refreshToken"]);
}

function newRequestId() {
  return crypto.randomUUID();
}

// Low-level fetch wrapper. Does NOT handle 401 refresh — see apiFetch() below.
async function rawFetch(path, { method = "GET", body, headers = {}, auth = true } = {}) {
  const baseUrl = await getBaseUrl();
  const finalHeaders = {
    "X-Request-ID": newRequestId(),
    ...headers,
  };

  if (body !== undefined) {
    finalHeaders["Content-Type"] = "application/json";
  }

  if (auth) {
    const { accessToken } = await getTokens();
    if (accessToken) {
      finalHeaders["Authorization"] = `Bearer ${accessToken}`;
    }
  }

  const res = await fetch(`${baseUrl}${path}`, {
    method,
    headers: finalHeaders,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  let json = null;
  try {
    json = await res.json();
  } catch (_) {
    // non-JSON response, leave json null
  }

  return { status: res.status, ok: res.ok, json };
}

let refreshInFlight = null;

async function refreshTokens() {
  // Coalesce concurrent refreshes — only one refresh call in flight at a time.
  if (refreshInFlight) return refreshInFlight;

  refreshInFlight = (async () => {
    const { refreshToken } = await getTokens();
    if (!refreshToken) {
      throw new Error("no_refresh_token");
    }

    const { ok, json } = await rawFetch("/api/v1/auth/refresh", {
      method: "POST",
      auth: false,
      body: { refresh_token: refreshToken },
    });

    if (!ok || !json?.success) {
      await clearTokens();
      throw new Error("refresh_failed");
    }

    const { access_token, refresh_token } = json.data;
    await setTokens({ accessToken: access_token, refreshToken: refresh_token });
    return access_token;
  })();

  try {
    return await refreshInFlight;
  } finally {
    refreshInFlight = null;
  }
}

// Main entry point: handles the 401 -> refresh -> retry-once flow from
// section 2.5 of the contract. Returns the parsed envelope (success/data/error).
export async function apiFetch(path, options = {}) {
  let result = await rawFetch(path, options);

  if (result.status === 401 && options.auth !== false) {
    try {
      await refreshTokens();
    } catch (e) {
      return { status: 401, ok: false, json: { success: false, error: "session_expired" } };
    }
    result = await rawFetch(path, options);
  }

  return result;
}

// --- Auth ---

export async function loginWithGoogle(idToken) {
  const { ok, json } = await rawFetch("/api/v1/auth/google", {
    method: "POST",
    auth: false,
    body: { id_token: idToken },
  });
  if (!ok || !json?.success) {
    throw new Error(json?.message || "login_failed");
  }
  const { access_token, refresh_token } = json.data;
  await setTokens({ accessToken: access_token, refreshToken: refresh_token });
  return json.data;
}

export async function getGmailAuthUrl(postAuthRedirectUri) {
  const params = new URLSearchParams({ post_auth_redirect_uri: postAuthRedirectUri });
  return apiFetch(`/api/v1/connectors/gmail/auth-url?${params.toString()}`);
}

export async function logout() {
  const { refreshToken } = await getTokens();
  if (refreshToken) {
    await rawFetch("/api/v1/auth/logout", {
      method: "POST",
      auth: false,
      body: { refresh_token: refreshToken },
    });
  }
  await clearTokens();
}

// --- Profile ---
export const getMe = () => apiFetch("/api/v1/users/me");

// --- Connectors ---
export const listConnectors = () => apiFetch("/api/v1/connectors");
export const connectorHealth = (platform) => apiFetch(`/api/v1/connectors/${platform}/health`);
export const triggerSync = (platform) =>
  apiFetch(`/api/v1/connectors/${platform}/sync`, { method: "POST" });
export const getMessages = (platform, refresh = false) =>
  apiFetch(`/api/v1/connectors/${platform}/messages${refresh ? "?refresh=true" : ""}`);
export const disconnectPlatform = (platform) =>
  apiFetch(`/api/v1/connectors/${platform}/disconnect`, { method: "POST" });

// --- Communications ---
export const searchCommunications = (query, platform = "gmail", limit = 25) =>
  apiFetch(
    `/api/v1/communications/search?platform=${platform}&query=${encodeURIComponent(query)}&limit=${limit}`
  );
export const recentCommunications = (platform = "gmail", limit = 20) =>
  apiFetch(`/api/v1/communications/recent?platform=${platform}&limit=${limit}`);
export const getCommunication = (id) => apiFetch(`/api/v1/communications/${id}`);

// --- Extension-specific ---
export const getExtensionContext = () => apiFetch("/api/v1/extension/context");
export const sendChatMessage = (message) =>
  apiFetch("/api/v1/extension/chat", { method: "POST", body: { message } });
export const getSummary = (thread) =>
  apiFetch("/api/v1/brain/chat", { method: "POST", body: { thread, mode: "summarize", source: "gmail" } });

