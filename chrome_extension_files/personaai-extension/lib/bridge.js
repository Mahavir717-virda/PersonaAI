// lib/bridge.js
// Plain script (no ES module) so it can be loaded by both the side panel
// and the content script. Wraps chrome.runtime.sendMessage into promises.

function callBackground(message) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(message, (response) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
        return;
      }
      if (!response || response.ok === false) {
        reject(new Error(response?.error || "request_failed"));
        return;
      }
      resolve(response);
    });
  });
}

const Persona = {
  signIn: () => callBackground({ type: "SIGN_IN" }),
  signOut: () => callBackground({ type: "SIGN_OUT" }),
  connectGmail: () => callBackground({ type: "CONNECT_GMAIL" }),
  authState: () => callBackground({ type: "GET_AUTH_STATE" }),

  api: (method, ...args) =>
    callBackground({ type: "API_CALL", method, args }).then((r) => r.data?.data ?? r.data),

  // Raw call when you need status/envelope details too.
  apiRaw: (method, ...args) => callBackground({ type: "API_CALL", method, args }),
};

// Expose globally for non-module scripts.
if (typeof window !== "undefined") window.Persona = Persona;
if (typeof globalThis !== "undefined") globalThis.Persona = Persona;
