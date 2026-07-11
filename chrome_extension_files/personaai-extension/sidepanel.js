// sidepanel.js
const els = {
  connStatus: document.getElementById("connStatus"),
  syncMeta: document.getElementById("syncMeta"),
  signedOutView: document.getElementById("signedOutView"),
  signedInView: document.getElementById("signedInView"),
  signInBtn: document.getElementById("signInBtn"),
  refreshBtn: document.getElementById("refreshBtn"),
  reconnectBanner: document.getElementById("reconnectBanner"),
  reconnectBtn: document.getElementById("reconnectBtn"),
  offlineBanner: document.getElementById("offlineBanner"),
  messageList: document.getElementById("messageList"),
  emptyState: document.getElementById("emptyState"),
  chatDock: document.getElementById("chatDock"),
  chatLog: document.getElementById("chatLog"),
  chatInput: document.getElementById("chatInput"),
  chatSendBtn: document.getElementById("chatSendBtn"),
  modelSelect: document.getElementById("modelSelect"),
  newChatBtn: document.getElementById("newChatBtn"),
  historyBtn: document.getElementById("historyBtn"),
  settingsBtn: document.getElementById("settingsBtn"),
  greetingText: document.getElementById("greetingText"),
  welcomeContainer: document.getElementById("welcomeContainer"),
};

const CACHE_KEY = "cachedInbox";
let currentMessages = [];

// Dynamic greeting based on time of day
function updateGreeting() {
  const hour = new Date().getHours();
  let greeting = "Good morning";
  if (hour >= 12 && hour < 17) greeting = "Good afternoon";
  else if (hour >= 17) greeting = "Good evening";
  if (els.greetingText) els.greetingText.textContent = greeting;
}

function setConnStatus(state) {
  els.connStatus.textContent = state;
  els.connStatus.className = "conn-status conn-" + state;
}

function formatSyncMeta(connector) {
  const lastSync = connector?.last_sync ? new Date(connector.last_sync).toLocaleString() : "never";
  const status = connector?.last_sync_status || "never";
  return `Last synced: ${lastSync} • Sync: ${status}`;
}

async function cacheInbox(messages) {
  await chrome.storage.local.set({ [CACHE_KEY]: messages });
}

async function loadCachedInbox() {
  const { [CACHE_KEY]: cached } = await chrome.storage.local.get(CACHE_KEY);
  return cached || [];
}

function renderMessages(messages) {
  currentMessages = messages;
  els.messageList.innerHTML = "";
  els.emptyState.classList.toggle("hidden", messages.length > 0);

  for (const msg of messages) {
    const li = document.createElement("li");
    li.className = "message-item" + (msg.unread || msg.metadata?.unread ? " unread" : "");
    li.innerHTML = `
      <div class="subject">${escapeHtml(msg.subject || "(no subject)")}</div>
      <div class="sender">${escapeHtml(msg.sender || msg.from || "")}</div>
      <div class="snippet">${escapeHtml(msg.metadata?.snippet || "")}</div>
      <div class="summary-box"></div>
    `;
    li.addEventListener("click", () => toggleSummary(li, msg));
    els.messageList.appendChild(li);
  }
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s ?? "";
  return div.innerHTML;
}

async function toggleSummary(li, msg) {
  const box = li.querySelector(".summary-box");
  const wasExpanded = li.classList.contains("expanded");
  li.classList.toggle("expanded");
  if (wasExpanded || box.dataset.loaded) return;

  box.innerHTML = `<div class="loading-state" style="color: #4c6ef5;">Summarizing…</div>`;
  box.style.display = "block";
  try {
    const res = await window.Persona.api(
      "getSummary",
      `Subject: "${msg.subject}". Body: ${msg.body || msg.metadata?.snippet || ""}`
    );
    
    const sum = res?.summary || res;
    if (!sum) {
      box.textContent = "No summary available.";
      return;
    }

    // Deconstruct structured fields
    const tldr = sum.tldr ? `<div class="sum-tldr"><strong>TLDR:</strong> ${escapeHtml(sum.tldr)}</div>` : "";
    const summary = sum.summary ? `<div class="sum-body">${escapeHtml(sum.summary)}</div>` : "";
    
    const buildList = (title, items) => {
      if (!items || items.length === 0) return "";
      return `
        <div class="sum-section">
          <span class="sum-section-title">${title}:</span>
          <ul>${items.map(item => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
        </div>
      `;
    };

    box.innerHTML = `
      <div class="structured-summary-card">
        ${tldr}
        ${summary}
        ${buildList("Action Items", sum.action_items)}
        ${buildList("Deadlines", sum.deadlines)}
        ${buildList("People Involved", sum.people)}
        ${buildList("Projects", sum.projects)}
        ${buildList("Meetings Scheduled", sum.meetings)}
        ${buildList("Risks Identified", sum.risks)}
        ${buildList("Follow-ups", sum.follow_ups)}
        ${buildList("Questions Asked", sum.questions)}
      </div>
    `;
    box.dataset.loaded = "true";
  } catch (e) {
    box.textContent = "Couldn't summarize this email right now.";
  }
}

async function refreshConnectorAndInbox(forceRefresh) {
  try {
    const connectors = await window.Persona.api("listConnectors");
    const activeConnectors = connectors?.active || [];
    const gmail = activeConnectors.find((c) => c.platform === "gmail");
    const state = gmail?.state || gmail?.status || "unknown";
    setConnStatus(state);
    els.syncMeta.textContent = gmail ? formatSyncMeta(gmail) : "No Gmail connector found";

    const needsReconnect = ["error", "expired", "reconnect_required"].includes(state);
    els.reconnectBanner.classList.toggle("hidden", !needsReconnect);

    if (state === "connected" || state === "syncing") {
      const result = await window.Persona.api("getMessages", "gmail", forceRefresh);
      const messages = result?.messages || result || [];
      renderMessages(messages);
      cacheInbox(messages);
      els.offlineBanner.classList.add("hidden");
    }
  } catch (e) {
    setConnStatus("error");
    els.syncMeta.textContent = "Sync unavailable";
    const cached = await loadCachedInbox();
    if (cached.length) {
      renderMessages(cached);
      els.offlineBanner.classList.remove("hidden");
    }
  }
}

els.refreshBtn.addEventListener("click", () => refreshConnectorAndInbox(true));
els.reconnectBtn.addEventListener("click", async () => {
  await window.Persona.connectGmail();
  refreshConnectorAndInbox(true);
});

els.signInBtn.addEventListener("click", async () => {
  try {
    await window.Persona.signIn();
    await showSignedIn();
  } catch (e) {
    alert("Sign-in failed: " + e.message);
  }
});

function appendChat(role, text) {
  const div = document.createElement("div");
  div.className = "chat-msg " + role;
  div.textContent = text;
  els.chatLog.appendChild(div);
  els.chatLog.scrollTop = els.chatLog.scrollHeight;
}

async function sendChat(textOverride) {
  const text = textOverride || els.chatInput.value.trim();
  if (!text) return;
  
  // Hide the greeting / suggestion prompts upon first interaction
  if (els.welcomeContainer) {
    els.welcomeContainer.classList.add("hidden");
  }

  appendChat("user", text);
  if (!textOverride) els.chatInput.value = "";
  
  try {
    const selectedModel = els.modelSelect ? els.modelSelect.value : "llama-3.1-8b-instant";
    console.log(`[PersonaAI] Querying with model: ${selectedModel}`);
    
    const result = await window.Persona.api("sendChatMessage", text);
    appendChat("ai", result?.reply || "(no reply)");
  } catch (e) {
    appendChat("ai", "Something went wrong reaching the assistant.");
  }
}

els.chatSendBtn.addEventListener("click", () => sendChat());
els.chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendChat();
  }
});

// Setup suggestion chips
document.querySelectorAll(".suggestion-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    const prompt = chip.getAttribute("data-prompt");
    sendChat(prompt);
  });
});

// Topbar Control Handlers
if (els.newChatBtn) {
  els.newChatBtn.addEventListener("click", () => {
    els.chatLog.innerHTML = "";
    if (els.welcomeContainer) {
      els.welcomeContainer.classList.remove("hidden");
    }
  });
}

if (els.historyBtn) {
  els.historyBtn.addEventListener("click", () => {
    alert("Chat History feature coming soon in version 1.1!");
  });
}

if (els.settingsBtn) {
  els.settingsBtn.addEventListener("click", () => {
    chrome.runtime.openOptionsPage();
  });
}

async function showSignedIn() {
  els.signedOutView.classList.add("hidden");
  els.signedInView.classList.remove("hidden");
  els.chatDock.classList.remove("hidden");
  await refreshConnectorAndInbox(false);
}

async function init() {
  updateGreeting();
  if (!navigator.onLine) {
    els.offlineBanner.classList.remove("hidden");
  }
  window.addEventListener("online", () => {
    els.offlineBanner.classList.add("hidden");
    refreshConnectorAndInbox(false);
  });
  window.addEventListener("offline", () => els.offlineBanner.classList.remove("hidden"));

  const { signedIn } = await window.Persona.authState();
  if (signedIn) {
    await showSignedIn();
  } else {
    els.signedOutView.classList.remove("hidden");
    setConnStatus("unknown");
    els.syncMeta.textContent = "Sync state unavailable";
  }
}

chrome.runtime.onMessage.addListener((message) => {
  if (message?.type === "PERSONA_SYNC_COMPLETED") {
    refreshConnectorAndInbox(false);
  }
});

init();
