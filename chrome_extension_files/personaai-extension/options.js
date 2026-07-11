const input = document.getElementById("baseUrl");
const status = document.getElementById("status");

chrome.storage.local.get("baseUrl", ({ baseUrl }) => {
  input.value = baseUrl || "http://localhost:8000";
});

document.getElementById("saveBtn").addEventListener("click", async () => {
  await chrome.storage.local.set({ baseUrl: input.value.trim() });
  status.textContent = "Saved";
  setTimeout(() => (status.textContent = ""), 1500);
});
