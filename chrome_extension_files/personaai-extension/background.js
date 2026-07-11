// background.js
// Single source of truth for auth + API access. The side panel and content
// script never call the backend directly — they send a message here and
// this worker does the fetch (with 401-refresh-retry) and replies.

import * as api from "./lib/api.js";

chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});
});

async function launchGoogleOAuthFlow({ responseType, scopes }) {
  const manifest = chrome.runtime.getManifest();
  const clientId = manifest.oauth2.client_id;
  const redirectUri = chrome.identity.getRedirectURL();
  const nonce = crypto.randomUUID();

  const authUrl =
    "https://accounts.google.com/o/oauth2/v2/auth" +
    `?client_id=${encodeURIComponent(clientId)}` +
    `&response_type=${encodeURIComponent(responseType)}` +
    `&redirect_uri=${encodeURIComponent(redirectUri)}` +
    `&scope=${encodeURIComponent(scopes.join(" "))}` +
    `&nonce=${encodeURIComponent(nonce)}` +
    `&access_type=offline` +
    `&prompt=consent`;

  return chrome.identity.launchWebAuthFlow({
    url: authUrl,
    interactive: true,
  });
}

// ---- Google sign-in ----
// Uses launchWebAuthFlow with response_type=id_token so we get a real Google
// ID token to hand to POST /api/v1/auth/google, per the contract.
async function signInWithGoogle() {
  const redirectedTo = await launchGoogleOAuthFlow({
    responseType: "id_token",
    scopes: ["openid", "email", "profile"],
  });

  const fragment = new URL(redirectedTo).hash.substring(1);
  const params = new URLSearchParams(fragment);
  const idToken = params.get("id_token");
  if (!idToken) throw new Error("no_id_token_returned");

  return api.loginWithGoogle(idToken);
}

async function connectGmail() {
  const postAuthRedirectUri = chrome.identity.getRedirectURL("gmail-oauth");
  const authResponse = await api.getGmailAuthUrl(postAuthRedirectUri);
  const authorizationUrl = authResponse?.json?.data?.authorization_url || authResponse?.data?.authorization_url;
  if (!authorizationUrl) {
    throw new Error("no_authorization_url_returned");
  }

  const redirectedTo = await chrome.identity.launchWebAuthFlow({
    url: authorizationUrl,
    interactive: true,
  });

  if (!redirectedTo) {
    throw new Error("gmail_oauth_cancelled");
  }

  const connectorState = await waitForGmailConnectorConnected();
  return { redirectedTo, authorizationUrl, connectorState };
}

async function waitForGmailConnectorConnected() {
  const deadline = Date.now() + 120000;
  let lastState = "unknown";

  while (Date.now() < deadline) {
    const connectors = await api.listConnectors();
    console.log("[PersonaAI] Gmail connector poll:", connectors);
    const payload = connectors?.json?.data || connectors?.data || connectors?.json || connectors;
    const activeConnectors = payload?.active || payload || [];
    const gmail = activeConnectors.find((c) => c.platform === "gmail");
    lastState = gmail?.state || gmail?.status || "unknown";
    if (lastState === "connected") {
      return lastState;
    }
    if (lastState === "authorizing" || lastState === "syncing" || lastState === "reconnect_required") {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      continue;
    }
    if (lastState === "error" || lastState === "failed") {
      throw new Error(`gmail_connection_failed:${lastState}`);
    }
    await new Promise((resolve) => setTimeout(resolve, 2000));
  }

  throw new Error(`gmail_connection_timed_out:${lastState}`);
}

async function runBackgroundSync() {
  const result = await api.triggerSync("gmail");
  const syncResult = result?.json?.data || result?.data || result;
  await notifySyncResult(syncResult);
  return syncResult;
}

// ---- Message router ----
// All callers (sidepanel.js, content.js) use:
//   chrome.runtime.sendMessage({ type: "API_CALL", method: "getMessages", args: [...] })
// or { type: "SIGN_IN" } / { type: "SIGN_OUT" } / { type: "GET_AUTH_STATE" }

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  handleMessage(message).then(sendResponse).catch((err) =>
    sendResponse({ ok: false, error: err.message })
  );
  return true; // keep the message channel open for async response
});

async function handleMessage(message) {
  switch (message.type) {
    case "SIGN_IN": {
      const data = await signInWithGoogle();
      return { ok: true, data };
    }
    case "CONNECT_GMAIL": {
      const data = await connectGmail();
      return { ok: true, data };
    }
    case "SIGN_OUT": {
      await api.logout();
      return { ok: true };
    }
    case "GET_AUTH_STATE": {
      const { accessToken } = await api.getTokens();
      return { ok: true, signedIn: Boolean(accessToken) };
    }
    case "TRIGGER_BACKGROUND_SYNC": {
      const data = await runBackgroundSync();
      return { ok: true, data };
    }
    case "API_CALL": {
      const { method, args = [] } = message;
      if (typeof api[method] !== "function") {
        throw new Error(`unknown_api_method:${method}`);
      }
      const result = await api[method](...args);
      return { ok: result.ok, status: result.status, data: result.json };
    }
    default:
      throw new Error(`unknown_message_type:${message.type}`);
  }
}

// ---- Background polling (optional, conservative) ----
// Honors extension context's sync_interval_minutes instead of hardcoding one.
chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name !== "persona-sync") return;
  const { accessToken } = await api.getTokens();
  if (!accessToken) return;

  const connectors = await api.listConnectors();
  const gmail = connectors.json?.data?.find?.((c) => c.platform === "gmail");
  if (gmail?.state === "connected") {
    await runBackgroundSync();
  }
});

async function scheduleSync() {
  let minutes = 15;
  try {
    const ctx = await api.getExtensionContext();
    if (ctx.ok && ctx.json?.data?.sync_interval_minutes) {
      minutes = ctx.json.data.sync_interval_minutes;
    }
  } catch (_) {
    // fall back to default
  }
  chrome.alarms.create("persona-sync", { periodInMinutes: minutes });
}

chrome.runtime.onStartup.addListener(scheduleSync);
chrome.runtime.onInstalled.addListener(scheduleSync);

async function notifySyncResult(syncResult) {
  const messagesImported = syncResult?.messages_imported || 0;
  if (messagesImported > 0 && chrome.notifications?.create) {
    await chrome.notifications.create(`persona-sync-${Date.now()}`, {
      type: "basic",
      iconUrl: "icons/icon128.png",
      title: "PersonaAI Gmail sync complete",
      message: `${messagesImported} new email${messagesImported === 1 ? "" : "s"} synced.`,
    });
  }

  chrome.runtime.sendMessage({
    type: "PERSONA_SYNC_COMPLETED",
    data: syncResult,
  }).catch(() => {});
}

chrome.notifications?.onClicked?.addListener(async () => {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  const tabId = tabs[0]?.id;
  if (tabId !== undefined) {
    chrome.sidePanel.open({ tabId }).catch(() => {});
  }
});
