/* ============================================================
   CloudDrive — frontend logic (vanilla JS, no framework).

   The key thing to notice for your viva:
   uploads/downloads use PRE-SIGNED URLs. The browser sends file
   bytes straight to storage (S3 in prod / our blob endpoint in
   local mode) — never through the JSON API. That's the scaling trick.
   ============================================================ */

const API = ""; // same origin (served by FastAPI)
let token = localStorage.getItem("cd_token") || null;
let authMode = "login";
let shareFileId = null;
let currentView = "mine"; // "mine" or "shared"

// ---------- helpers ----------
function api(path, opts = {}) {
  opts.headers = opts.headers || {};
  if (token) opts.headers["Authorization"] = "Bearer " + token;
  return fetch(API + path, opts);
}

function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.remove("hidden");
  clearTimeout(window._toastT);
  window._toastT = setTimeout(() => t.classList.add("hidden"), 2600);
}

function fmtSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
  if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + " MB";
  return (bytes / 1073741824).toFixed(2) + " GB";
}

function iconFor(name) {
  const ext = (name.split(".").pop() || "").toLowerCase();
  const map = {
    pdf: "📕", doc: "📘", docx: "📘", xls: "📗", xlsx: "📗",
    png: "🖼️", jpg: "🖼️", jpeg: "🖼️", gif: "🖼️", svg: "🖼️",
    mp4: "🎬", mov: "🎬", mp3: "🎵", wav: "🎵",
    zip: "🗜️", rar: "🗜️", txt: "📄", md: "📄",
    js: "📜", py: "🐍", html: "🌐", css: "🎨", json: "🔧",
  };
  return map[ext] || "📄";
}

// ---------- auth ----------
function switchTab(mode) {
  authMode = mode;
  document.getElementById("tab-login").classList.toggle("active", mode === "login");
  document.getElementById("tab-signup").classList.toggle("active", mode === "signup");
  document.getElementById("auth-btn").textContent = mode === "login" ? "Log in" : "Sign up";
  document.getElementById("auth-error").textContent = "";
}

async function submitAuth(e) {
  e.preventDefault();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const errEl = document.getElementById("auth-error");
  errEl.textContent = "";

  try {
    let res;
    if (authMode === "signup") {
      res = await fetch(API + "/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
    } else {
      const form = new URLSearchParams({ username: email, password });
      res = await fetch(API + "/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form,
      });
    }
    if (!res.ok) {
      const d = await res.json().catch(() => ({}));
      throw new Error(d.detail || "Authentication failed");
    }
    const data = await res.json();
    token = data.access_token;
    localStorage.setItem("cd_token", token);
    await enterApp();
  } catch (err) {
    errEl.textContent = err.message;
  }
  return false;
}

function logout() {
  token = null;
  localStorage.removeItem("cd_token");
  document.getElementById("app-screen").classList.add("hidden");
  document.getElementById("auth-screen").classList.remove("hidden");
}

async function enterApp() {
  const res = await api("/api/auth/me");
  if (!res.ok) return logout();
  const user = await res.json();

  document.getElementById("auth-screen").classList.add("hidden");
  document.getElementById("app-screen").classList.remove("hidden");
  document.getElementById("user-email").textContent = user.email;

  const health = await (await fetch(API + "/api/health")).json();
  document.getElementById("storage-badge").textContent = "storage: " + health.storage;

  updateQuota(user);
  loadFiles();
}

function updateQuota(user) {
  const usedMB = user.storage_used / 1048576;
  const totalMB = user.storage_quota / 1048576;
  const pct = totalMB ? Math.min(100, (usedMB / totalMB) * 100) : 0;
  document.getElementById("quota-fill").style.width = pct + "%";
  document.getElementById("quota-text").textContent =
    usedMB.toFixed(1) + " / " + totalMB.toFixed(0) + " MB";
}

async function refreshQuota() {
  const res = await api("/api/auth/me");
  if (res.ok) updateQuota(await res.json());
}

// ---------- files ----------
async function loadFiles() {
  const res = await api("/api/files");
  const files = res.ok ? await res.json() : [];
  const grid = document.getElementById("file-grid");
  const empty = document.getElementById("empty-state");
  grid.innerHTML = "";

  empty.classList.toggle("hidden", files.length > 0);
  if (files.length === 0) {
    empty.querySelector("p").textContent =
      "No files yet — upload your first file to get started ☁️";
  }

  for (const f of files) {
    const card = document.createElement("div");
    card.className = "file-card";
    card.innerHTML = `
      <div class="file-icon">${iconFor(f.name)}</div>
      <div class="file-name">${escapeHtml(f.name)}</div>
      <div class="file-meta">${fmtSize(f.size)}</div>
      <div class="file-actions">
        <button onclick="download(${f.id})" title="Download">⬇️</button>
        <button onclick="openShare(${f.id}, '${escapeHtml(f.name)}')" title="Share">🔗</button>
        <button class="del" onclick="removeFile(${f.id})" title="Delete">🗑️</button>
      </div>`;
    grid.appendChild(card);
  }
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// ---------- view switching (My Files vs Shared with me) ----------
function switchView(view) {
  currentView = view;
  document.getElementById("view-mine").classList.toggle("active", view === "mine");
  document.getElementById("view-shared").classList.toggle("active", view === "shared");
  // Upload + drag-drop only make sense for your own files.
  const showUpload = view === "mine";
  document.querySelector(".toolbar-actions").style.display = showUpload ? "" : "none";
  document.getElementById("dropzone").style.display = showUpload ? "" : "none";
  if (view === "mine") loadFiles();
  else loadSharedWithMe();
}

async function loadSharedWithMe() {
  const res = await api("/api/shared-with-me");
  const files = res.ok ? await res.json() : [];
  const grid = document.getElementById("file-grid");
  const empty = document.getElementById("empty-state");
  grid.innerHTML = "";
  empty.classList.toggle("hidden", files.length > 0);
  if (files.length === 0) {
    empty.querySelector("p").textContent = "Nothing shared with you yet 🤝";
  }

  for (const f of files) {
    const card = document.createElement("div");
    card.className = "file-card";
    card.innerHTML = `
      <div class="file-icon">${iconFor(f.name)}</div>
      <div class="file-name">${escapeHtml(f.name)}</div>
      <div class="file-meta">${fmtSize(f.size)} · shared</div>
      <div class="file-actions">
        <button onclick="sharedDownload(${f.id})" title="Download">⬇️ Download</button>
      </div>`;
    grid.appendChild(card);
  }
}

async function sharedDownload(id) {
  const res = await api(`/api/files/${id}/shared-download`);
  if (!res.ok) return toast("Download failed");
  const { download_url } = await res.json();
  window.open(download_url, "_blank");
}

// THE PRE-SIGNED UPLOAD FLOW (3 steps)
async function uploadOne(file) {
  // Step 1: ask the API for an upload ticket (pre-signed URL)
  const initRes = await api("/api/files/init", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: file.name,
      size: file.size,
      content_type: file.type || "application/octet-stream",
    }),
  });
  if (!initRes.ok) {
    const d = await initRes.json().catch(() => ({}));
    throw new Error(d.detail || "Upload init failed");
  }
  const ticket = await initRes.json();

  // Step 2: PUT the bytes straight to storage using the pre-signed URL
  await putWithProgress(ticket.upload_url, file);

  // Step 3: tell the API the bytes landed
  await api(`/api/files/${ticket.file_id}/complete`, { method: "POST" });
}

function putWithProgress(url, file) {
  return new Promise((resolve, reject) => {
    const row = addProgressRow(file.name);
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", url);
    if (file.type) xhr.setRequestHeader("Content-Type", file.type);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) row.style.width = (e.loaded / e.total) * 100 + "%";
    };
    xhr.onload = () => (xhr.status < 300 ? resolve() : reject(new Error("PUT failed")));
    xhr.onerror = () => reject(new Error("Network error"));
    xhr.send(file);
  });
}

function addProgressRow(name) {
  const wrap = document.getElementById("upload-progress");
  wrap.classList.remove("hidden");
  const item = document.createElement("div");
  item.className = "up-item";
  item.innerHTML = `<div class="up-name"><span>${escapeHtml(name)}</span><span>uploading…</span></div>
    <div class="up-track"><div class="up-fill"></div></div>`;
  wrap.appendChild(item);
  return item.querySelector(".up-fill");
}

async function handleUpload(files) {
  if (!files.length) return;
  for (const file of files) {
    try {
      await uploadOne(file);
    } catch (err) {
      toast("⚠️ " + err.message);
    }
  }
  document.getElementById("upload-progress").innerHTML = "";
  document.getElementById("upload-progress").classList.add("hidden");
  document.getElementById("file-input").value = "";
  toast("✅ Upload complete");
  loadFiles();
  refreshQuota();
}

async function download(id) {
  const res = await api(`/api/files/${id}/download`);
  if (!res.ok) return toast("Download failed");
  const { download_url } = await res.json();
  window.open(download_url, "_blank");
}

async function removeFile(id) {
  if (!confirm("Delete this file permanently?")) return;
  const res = await api(`/api/files/${id}`, { method: "DELETE" });
  if (res.ok) {
    toast("🗑️ Deleted");
    loadFiles();
    refreshQuota();
  }
}

// ---------- sharing ----------
function openShare(id, name) {
  shareFileId = id;
  document.getElementById("share-file-name").textContent = name;
  document.getElementById("share-msg").textContent = "";
  document.getElementById("public-link-box").classList.add("hidden");
  document.getElementById("share-email").value = "";
  document.getElementById("share-expiry").value = "";
  document.getElementById("share-modal").classList.remove("hidden");
}
function closeShare() {
  document.getElementById("share-modal").classList.add("hidden");
}

async function shareWithUser() {
  const email = document.getElementById("share-email").value.trim();
  if (!email) return;
  const res = await api("/api/shares", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id: shareFileId, email }),
  });
  const msg = document.getElementById("share-msg");
  if (res.ok) {
    msg.style.color = "var(--success)";
    msg.textContent = "✅ Shared with " + email;
  } else {
    const d = await res.json().catch(() => ({}));
    msg.style.color = "var(--danger)";
    msg.textContent = d.detail || "Could not share";
  }
}

async function makePublicLink() {
  const hours = document.getElementById("share-expiry").value;
  const body = { file_id: shareFileId, public: true };
  if (hours) body.expires_in_hours = parseInt(hours, 10);
  const res = await api("/api/shares", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (res.ok) {
    const data = await res.json();
    document.getElementById("public-link").value = data.public_url;
    document.getElementById("public-link-box").classList.remove("hidden");
  } else {
    toast("Could not create link");
  }
}

function copyLink() {
  const input = document.getElementById("public-link");
  input.select();
  navigator.clipboard.writeText(input.value);
  toast("🔗 Link copied");
}

// ---------- drag & drop ----------
const dz = document.getElementById("dropzone");
if (dz) {
  ["dragover", "dragenter"].forEach((ev) =>
    dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("drag"); }));
  ["dragleave", "drop"].forEach((ev) =>
    dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove("drag"); }));
  dz.addEventListener("drop", (e) => handleUpload(e.dataTransfer.files));
}

// ---------- boot ----------
if (token) enterApp().catch(logout);
