# PersonaAI Chrome Extension

Built directly against `CHROME_EXTENSION_API_CONTRACT.md`. No backend logic is
guessed at — every endpoint, header, and error code matches that doc.

## What's here

- **`background.js`** — the only place that calls the backend. Owns the
  Google sign-in flow, access/refresh token storage, and the 401 → refresh →
  retry-once logic from section 2.5. Also schedules background sync using
  `sync_interval_minutes` from `/api/v1/extension/context` instead of a
  hardcoded interval.
- **`lib/api.js`** — typed wrapper around every endpoint in section 5 of the
  contract (auth, users, connectors, communications, extension).
- **`lib/bridge.js`** — lets the side panel and content script call the
  backend by messaging `background.js`, so token logic never has to be
  duplicated in two places.
- **`sidepanel.html/js/css`** — main UI. Inbox list, search (debounced,
  hits `/communications/search`), manual refresh (`?refresh=true`),
  reconnect banner driven by `ConnectorState`, offline banner with cached
  inbox fallback, and a chat dock that calls `/extension/chat`.
- **`content.js`** — runs on `mail.google.com`. Two pieces:
  1. **Floating orb** (bottom-right) — ambient unread-count badge, click to
     get a short AI digest of what needs attention.
  2. **Auto-summarize on open** — when a thread is opened, a summary card is
     injected above it automatically, no button click. Skips very short
     emails and caches per-thread so reopening doesn't refire the AI call.
- **`options.html/js`** — set the backend base URL (defaults to
  `http://localhost:8000`, matches the contract's dev base path). Point this
  at your deployed backend when you ship.

## What you need to fill in

1. **`manifest.json` → `oauth2.client_id`** — a real Google OAuth client ID
   (Web application type, with the extension's redirect URI — visible via
   `chrome.identity.getRedirectURL()` — registered in Google Cloud Console).
2. **`host_permissions`** — add your production backend's origin once it's
   not `localhost:8000` anymore (Chrome requires explicit host permissions
   for `fetch` to work without prompting).
3. **Icons** — `icons/icon16.png`, `48`, `128` are placeholders; swap for
   real artwork.
4. **Gmail DOM selectors in `content.js`** (`h2.hP`, `div.a3s`) — these are
   Gmail's current reading-pane classes. Gmail changes markup periodically;
   if the inline summary card stops appearing, these are the first thing to
   check.

## Load it locally

1. `chrome://extensions` → enable Developer Mode.
2. "Load unpacked" → select this folder.
3. Click the extension icon to open the side panel, or visit `chrome://extensions`
   → Details → Extension options to set your backend URL first if it's not
   on `localhost:8000`.
4. Open Gmail — the floating orb should appear bottom-right.

## Design decisions worth knowing about

- **No `localStorage`** — everything uses `chrome.storage.local`, which is
  the correct API for extensions (your contract's "extension storage"
  language maps directly to this).
- **Single source of truth for tokens** — only `background.js` reads/writes
  tokens. The side panel and content script never touch them directly, which
  avoids race conditions between two refresh attempts firing at once
  (handled by `refreshInFlight` coalescing in `lib/api.js`).
- **Conservative polling** — background alarm and orb polling both use
  `refresh=false` per section 7.3's guidance; only an explicit user action
  (side panel refresh button, manual reconnect) sends `refresh=true`.
- **Cost control on auto-summarize** — emails under ~40 words are skipped
  entirely, and summaries are cached per-thread in memory so navigating
  away and back doesn't re-trigger `/extension/chat`.
