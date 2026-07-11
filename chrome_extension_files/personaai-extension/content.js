// content.js
// Runs inside mail.google.com. Two jobs:
//   1. Floating orb — ambient "X need attention" badge, click to open a mini digest.
//   2. Auto-summarize — when a thread is opened, inject a summary card above it,
//      no click required.
//
// Gmail's DOM is unstable and undocumented, so all selectors here are
// best-effort and wrapped defensively. If Gmail changes markup, this script
// should fail quietly rather than break the inbox.

const SUMMARY_CACHE = new Map(); // threadKey -> summary text, avoids re-summarizing

// ---------- Floating orb ----------

function buildOrb() {
  if (document.getElementById("persona-launcher-stack")) return;

  const stack = document.createElement("div");
  stack.id = "persona-launcher-stack";

  // 1. Settings sub-button
  const settingsBtn = document.createElement("div");
  settingsBtn.className = "persona-sub-btn";
  settingsBtn.title = "Settings";
  settingsBtn.innerHTML = "⚙️";
  settingsBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    chrome.runtime.sendMessage({ type: "OPEN_OPTIONS" }).catch(() => {});
  });
  stack.appendChild(settingsBtn);

  // 2. Web launcher sub-button
  const webBtn = document.createElement("div");
  webBtn.className = "persona-sub-btn";
  webBtn.title = "Open Web App";
  webBtn.innerHTML = "🌐";
  webBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    chrome.runtime.sendMessage({ type: "OPEN_URL", url: "http://localhost:3000" }).catch(() => {});
  });
  stack.appendChild(webBtn);

  // 3. Main Orb launcher
  const orb = document.createElement("div");
  orb.id = "persona-orb";
  orb.innerHTML = `P<span class="badge"></span><span class="persona-shortcut-label">Ctrl + M</span>`;
  stack.appendChild(orb);

  document.body.appendChild(stack);

  const panel = document.createElement("div");
  panel.id = "persona-orb-panel";
  panel.innerHTML = `
    <div class="panel-header">PersonaAI digest</div>
    <div class="panel-body">Loading…</div>
  `;
  document.body.appendChild(panel);

  orb.addEventListener("click", async () => {
    panel.classList.toggle("open");
    if (panel.classList.contains("open")) {
      await refreshDigest(panel);
    }
  });

  return { orb, panel };
}

async function refreshDigest(panel) {
  const body = panel.querySelector(".panel-body");
  body.textContent = "Checking your inbox…";
  try {
    const result = await window.Persona.api("getMessages", "gmail", false);
    const messages = result?.messages || result || [];
    const unread = messages.filter((m) => m.unread || m.metadata?.unread).length;

    setBadge(unread);

    if (!messages.length) {
      body.textContent = "Nothing new right now.";
      return;
    }

    const reply = await window.Persona.api(
      "sendChatMessage",
      `Give me a one or two sentence digest of what's important across these ${messages.length} recent emails, focused on anything that needs a reply.`
    );
    body.textContent = reply?.reply || "No digest available.";
  } catch (e) {
    console.error("[PersonaAI] refreshDigest failed:", e);
    body.textContent = "Sign in to PersonaAI to see your digest.";
  }
}

function setBadge(count) {
  const badge = document.querySelector("#persona-orb .badge");
  if (!badge) return;
  if (count > 0) {
    badge.textContent = count > 9 ? "9+" : String(count);
    badge.classList.add("show");
  } else {
    badge.classList.remove("show");
  }
}

async function pollBadgeQuietly() {
  try {
    const { signedIn } = await window.Persona.authState();
    if (!signedIn) return;
    const result = await window.Persona.api("getMessages", "gmail", false);
    const messages = result?.messages || result || [];
    setBadge(messages.filter((m) => m.unread || m.metadata?.unread).length);
  } catch (e) {
    console.error("[PersonaAI] pollBadgeQuietly failed:", e);
  }
}

// ---------- Auto-summarize on open ----------

function getOpenThreadSubjectAndBody() {
  // Gmail's reading pane subject is typically an h2 with class containing "hP".
  const subjectEl = document.querySelector("h2.hP");
  const bodyEls = document.querySelectorAll("div.a3s");
  if (!subjectEl || !bodyEls.length) return null;

  const subject = subjectEl.textContent.trim();
  const body = Array.from(bodyEls)
    .map((el) => el.innerText)
    .join("\n")
    .slice(0, 4000); // keep payload reasonable

  return { subject, body };
}

function getThreadKey(subject) {
  // Good enough heuristic key; Gmail thread IDs aren't reliably exposed in DOM.
  return subject;
}

function injectSummaryCard(text) {
  document.getElementById("persona-inline-summary")?.remove();

  const anchor = document.querySelector("h2.hP");
  if (!anchor) return;

  const card = document.createElement("div");
  card.id = "persona-inline-summary";
  card.innerHTML = `<div class="label">PersonaAI summary</div><div class="text"></div>`;
  card.querySelector(".text").textContent = text;

  anchor.insertAdjacentElement("afterend", card);
}

async function handleThreadOpen() {
  const info = getOpenThreadSubjectAndBody();
  if (!info || !info.subject) return;

  const key = getThreadKey(info.subject);
  if (SUMMARY_CACHE.has(key)) {
    injectSummaryCard(SUMMARY_CACHE.get(key));
    return;
  }

  // Skip very short emails — not worth an AI call or the user's attention.
  if (info.body.split(/\s+/).length < 40) return;

  injectSummaryCard("Summarizing…");
  try {
    const { signedIn } = await window.Persona.authState();
    if (!signedIn) {
      console.warn("[PersonaAI] Not signed in, skipping auto-summary");
      return;
    }

    const res = await window.Persona.api(
      "getSummary",
      `Subject: "${info.subject}". Body: ${info.body}`
    );
    const sum = res?.summary || res;
    const text = sum?.summary || sum || "No summary available.";
    SUMMARY_CACHE.set(key, text);
    injectSummaryCard(text);
  } catch (e) {
    console.error("[PersonaAI] Auto-summarization failed:", e);
    injectSummaryCard("Couldn't summarize this email right now.");
  }
}

// Gmail is a SPA — watch for DOM mutations and URL changes instead of page loads.
let lastUrl = location.href;
const observer = new MutationObserver(() => {
  if (location.href !== lastUrl) {
    lastUrl = location.href;
    onRouteChange();
  }
});
observer.observe(document.body, { childList: true, subtree: true });

let debounceHandle;
function onRouteChange() {
  clearTimeout(debounceHandle);
  // Gmail renders the thread pane slightly after the URL changes.
  debounceHandle = setTimeout(handleThreadOpen, 600);
}

function init() {
  buildOrb();
  pollBadgeQuietly();
  setInterval(pollBadgeQuietly, 5 * 60 * 1000); // conservative, matches contract's polling guidance
  onRouteChange(); // handle case where a thread is already open on script load
}

chrome.runtime.onMessage.addListener((message) => {
  if (message?.type === "PERSONA_SYNC_COMPLETED") {
    pollBadgeQuietly();
    onRouteChange();
  }
});

if (document.readyState === "complete") init();
else window.addEventListener("load", init);
