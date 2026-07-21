const API_BASE_URL = "https://trata-backend-service.internal.net/api/v1";

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

let profile = {
  name: "",
  role: "",
  organization: "",
  team: "",
  email: "",
  device: "",
  apiKey: ""
};

const GOOGLE_CLIENT_ID = "667539636431-im6uicpgbjpon632vpp2osjc8pg6t1lg.apps.googleusercontent.com";
const LOCAL_USERNAME = "trata.admin";
const LOCAL_PASSWORD = "trata@2026";

const state = {
  route: "home",
  dark: localStorage.getItem("trataTheme") !== "light",
  loggedIn: false,
  backendVerified: false,
  keyVisible: false,
  suspicious: false,
  selected: { packets: 0, logs: 0, files: 0 },
  graphResize: null,
  proxy: []
};

let packets = [];
let logs = [];
let files = [];
let graphData = { nodes: [], edges: [] };

async function apiFetch(endpoint, options = {}) {
  try {
    const headers = {
      "Content-Type": "application/json",
      "X-API-Key": profile.apiKey,
      ...options.headers
    };
    const response = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

async function fetchTelemetryData() {
  if (!state.backendVerified) return;
  const data = await apiFetch("/telemetry/stream");
  if (data) {
    packets = data.packets || [];
    logs = data.logs || [];
    files = data.files || [];
    state.proxy = data.proxy || [];
    state.suspicious = data.suspicious || false;
  }
}

async function fetchGraphTopology() {
  if (!state.backendVerified) return;
  const data = await apiFetch("/topology/graph");
  if (data && data.csv) {
    graphData = parseGraphCsv(data.csv);
  }
}

async function fetchEngineMetrics() {
  if (!state.backendVerified) return;
  const metrics = await apiFetch("/ai/engine-metrics");
  if (metrics) {
    $("#heroScore").textContent = metrics.detectionAccuracy;
    $("#graphCatchRate").textContent = metrics.graphDetectionAccuracy;
    $("#embeddingSync").textContent = metrics.embeddingsLastUpdated;
    $("#monitoredAssets").textContent = metrics.monthlyUserIncrement;
  }
}

function parseGraphCsv(csvText) {
  const lines = csvText.trim().split("\n");
  const nodesMap = new Map();
  const edges = [];

  lines.forEach((line) => {
    const [type, source, target, weight, status] = line.split(",").map(s => s?.trim());
    if (type === "NODE") {
      nodesMap.set(source, { label: source, cluster: target || "core", important: true });
    } else if (type === "EDGE") {
      edges.push({ source, target, weight: parseFloat(weight) || 0.5, alert: status === "ALERT" });
    }
  });

  return {
    nodes: Array.from(nodesMap.values()),
    edges
  };
}

async function fetchUserProfile() {
  if (!state.backendVerified) return;
  const data = await apiFetch("/profile/details");
  if (data) {
    profile = { ...profile, ...data };
  }
}

function floorToTen(date) {
  const copy = new Date(date);
  copy.setSeconds(0, 0);
  copy.setMinutes(Math.floor(copy.getMinutes() / 10) * 10);
  return copy;
}

function pad(value) {
  return String(value).padStart(2, "0");
}

function displayTime(date) {
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function readableRealtimeTime(date) {
  return `${pad(date.getDate())}-${pad(date.getMonth() + 1)}-${String(date.getFullYear()).slice(2)} ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

const endTime = floorToTen(new Date());
const timeline = Array.from({ length: 7 }, (_, index) => new Date(endTime.getTime() - (6 - index) * 10 * 60 * 1000));
const nextSuspiciousTime = new Date(endTime.getTime() + 10 * 60 * 1000);

function badge(value) {
  return `<span class="badge ${value === "Suspicious" || value === "Blocked" ? "alert" : value === "Suggested" ? "suggested" : ""}">${value}</span>`;
}

function routeTo(route) {
  const cleanRoute = (route || "home").split("?")[0];

  if (!state.backendVerified && cleanRoute !== "home" && cleanRoute !== "profile") {
    history.replaceState(null, "", `#home`);
    state.route = "home";
  } else {
    state.route = $(`[data-page="${cleanRoute}"]`) ? cleanRoute : "home";
    history.replaceState(null, "", `#${state.route}`);
  }

  $$(".page").forEach((page) => page.classList.toggle("active", page.dataset.page === state.route));
  $$(".nav a, .brand, .profile-card").forEach((link) => link.classList.toggle("active", link.dataset.route === state.route));
  window.scrollTo(0, 0);
  if (state.route === "behaviour" && state.graphResize) {
    requestAnimationFrame(state.graphResize);
  }
}

function renderTraffic() {
  if (!packets.length) return;

  const max = Math.max(...packets.map((item) => item.packets || 0));
  const min = Math.min(...packets.map((item) => item.packets || 0));
  const range = Math.max(1, max - min);
  const leftBound = 8;
  const rightBound = 92;

  const points = packets.map((item, index) => {
    const x = packets.length === 1 ? 50 : leftBound + (index / (packets.length - 1)) * (rightBound - leftBound);
    const y = 18 + ((max - item.packets) / range) * 60;
    return { ...item, x, y };
  });

  const polylinePoints = points.map((p) => `${p.x},${p.y}`).join(" ");
  const areaPoints = `${points[0].x},88 ${polylinePoints} ${points[points.length - 1].x},88`;
  const normalPoints = state.suspicious ? points.slice(0, -1) : points;
  const normalPolyline = normalPoints.map((p) => `${p.x},${p.y}`).join(" ");
  const attackPoints = state.suspicious ? points.slice(-2) : [];
  const attackPolyline = attackPoints.map((p) => `${p.x},${p.y}`).join(" ");

  $("#trafficChart").innerHTML = `
    <svg class="traffic-path" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true" style="position:absolute; inset:0; width:100%; height:100%; overflow:visible;">
      <defs>
        <linearGradient id="trafficAreaGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="${state.suspicious ? "#FF6B6B" : "#68E1FD"}" stop-opacity="0.3"></stop>
          <stop offset="100%" stop-color="${state.suspicious ? "#FF6B6B" : "#68E1FD"}" stop-opacity="0"></stop>
        </linearGradient>
      </defs>
      <polygon points="${areaPoints}" fill="url(#trafficAreaGradient)"></polygon>
      <polyline points="${normalPolyline}" fill="none" stroke="#68E1FD" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"></polyline>
      ${state.suspicious ? `<polyline points="${attackPolyline}" fill="none" stroke="#FF6B6B" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"></polyline>` : ""}
    </svg>
    ${points.map((point) => `
      <button class="traffic-point ${point.verdict === "Suspicious" ? "alert" : ""}" style="left:${point.x}%; top:${point.y}%; transform:translate(-50%, -50%); ${point.verdict === "Suspicious" ? "animation:pulse 1.15s infinite; box-shadow:0 0 0 6px rgba(255,107,107,0.25), 0 0 14px rgba(255,107,107,0.5);" : ""}" aria-label="${point.timestamp}">
        <span class="tooltip"><b>${point.timestamp}</b><br>${point.packets} packets<br>${point.event}</span>
      </button>
      <span class="traffic-label" style="left:${point.x}%; transform:translateX(-50%); bottom:10px;">${point.timestamp}</span>
    `).join("")}
  `;
}

function renderRealtime() {
  const items = packets.map(p => `traffic_capture_${p.timestamp}.pcap`)
    .concat(logs.map(l => `security_log_${l.timestamp}.log`))
    .concat(files.map(f => f.location.split("/").pop()));

  $("#realtimeData").innerHTML = items.map((item, index) => `
    <div class="data-item ${state.suspicious && index < 3 ? "alert" : ""}">
      <b>${item}</b><span>${index < 3 && state.suspicious ? "new" : ""}</span>
    </div>
  `).join("");
}

function renderTable(kind, rows, bodyId, headId, query = "") {
  const columns = kind === "files"
    ? ["Timestamp", "Verdict", "Event", "Packets", "File location"]
    : ["Timestamp", "Verdict", "Event", "Packets"];
  const filtered = rows.filter((row) => Object.values(row).join(" ").toLowerCase().includes(query.toLowerCase()));
  $(`#${headId}`).innerHTML = `<tr>${columns.map((column) => `<th>${column}</th>`).join("")}</tr>`;
  $(`#${bodyId}`).innerHTML = filtered.map((row, index) => `
    <tr data-kind="${kind}" data-index="${rows.indexOf(row)}" class="${rows.indexOf(row) === state.selected[kind] ? "selected" : ""}">
      <td>${row.timestamp}</td>
      <td>${badge(row.verdict)}</td>
      <td>${row.event}</td>
      <td>${row.packets}</td>
      ${kind === "files" ? `<td>${row.location}</td>` : ""}
    </tr>
  `).join("");
}

function renderDetail(kind, rows, targetId) {
  const row = rows[state.selected[kind]];
  if (!row) return;
  const fields = kind === "packets" ? [
    ["Timestamp", row.timestamp], ["Duration", row.duration], ["Source IP", row.sourceIp], ["Source port", row.sourcePort],
    ["Protocol", row.protocol], ["Attack type", row.attackType], ["Packets transferred", row.transferred]
  ] : kind === "logs" ? [
    ["Process ID", row.processId], ["Process generated timestamp", row.generatedTimestamp], ["Process generated by", row.generatedBy],
    ["Command run", row.command], ["YARA identified attack", row.yara], ["Sigma identified attack", row.sigma]
  ] : [
    ["Parent process", row.parentProcess], ["Size", row.size], ["YARA identified attack", row.yara],
    ["Location", row.location], ["Is executable", row.executable], ["Is running", row.running]
  ];
  $(`#${targetId}`).classList.add("open");
  $(`#${targetId}`).innerHTML = `
    <div class="detail-grid">${fields.map(([label, value]) => `<div class="detail-row"><span>${label}</span><b>${value}</b></div>`).join("")}</div>
    <aside class="intel-box">
      <div class="intel-row"><span>Threat intel</span><b>${row.intel}</b></div>
      <div class="intel-row"><span>MITRE ATT&CK ID</span><b>${row.mitre}</b></div>
      <div class="intel-row"><span>CVE Context ID</span><b>${row.cve}</b></div>
      <div class="intel-row"><span>Certificate ID</span><b>${row.cert}</b></div>
    </aside>
  `;
}

function hideDetail(targetId) {
  const target = $(`#${targetId}`);
  target.classList.remove("open");
  target.innerHTML = "";
}

function renderProxy() {
  $("#proxyCount").textContent = state.proxy.filter((item) => item.status === "Blocked").length;
  $("#proxyList").innerHTML = state.proxy.map((item, index) => `
    <article class="panel proxy-row">
      <header><b>${item.ip}</b>${badge(item.suggested ? "Suggested" : item.status === "Blocked" ? "Blocked" : "Normal")}</header>
      <small>${item.domain || item.ip} | ${item.description || item.reason} | number of attacks : ${item.attacks ?? 0} | timestamp : ${item.timestamp || "20/07/26 00:00"}${item.suggested ? " | suggested from recent suspicious activity" : ""}</small>
      <div class="proxy-actions">
        <button class="text-button" data-proxy="${index}" data-status="Allowed">Allow</button>
        <button class="text-button" data-proxy="${index}" data-status="Blocked">Block</button>
      </div>
    </article>
  `).join("");
}

function renderProfile() {
  if (!state.backendVerified) {
    $("#profileInitials").textContent = "NA";
    $("#profileNameMini").textContent = "Not Connected";
    $("#profileRoleMini").textContent = "Locked";
    $("#oauthState").textContent = "Sign in required";
    $("#oauthPanel").style.display = "grid";
    $("#profileData").innerHTML = "";
    return;
  }

  $("#profileInitials").textContent = profile.name ? profile.name.split(" ").map((part) => part[0]).join("") : "OP";
  $("#profileNameMini").textContent = profile.name || "Operator";
  $("#profileRoleMini").textContent = profile.role || "Security Analyst";
  $("#oauthState").textContent = "Connected";
  $("#oauthPanel").style.display = "none";
  const maskedKey = state.keyVisible ? profile.apiKey : "••••••••••••••••••••••••";
  $("#profileData").innerHTML = [
    ["Name", profile.name], ["Organization", profile.organization], ["Team", profile.team], ["Role", profile.role],
    ["Email", profile.email], ["Device", profile.device]
  ].map(([label, value]) => `<div class="profile-row"><span>${label}</span><b>${value}</b></div>`).join("") + `
    <div class="collector-box">
      <div class="collector-row"><span>Collector pairing key</span><code id="collectorKey">${maskedKey}</code></div>
      <button id="toggleCollectorKey" class="text-button">${state.keyVisible ? "Hide" : "Show"}</button>
      <button id="generateCollectorKey" class="text-button">Generate key</button>
      <button id="copyCollectorKey" class="primary-action">Copy key</button>
    </div>
  `;
}

async function answer(message) {
  const res = await apiFetch("/rag/query", {
    method: "POST",
    body: JSON.stringify({ query: message })
  });
  return res?.answer || "No response received from RAG engine.";
}

function addChat(text, user = false) {
  const item = document.createElement("div");
  item.className = `message ${user ? "user" : ""}`;
  item.textContent = text;
  $("#chatLog").appendChild(item);
  $("#chatLog").scrollTop = $("#chatLog").scrollHeight;
}

async function triggerSuspicious() {
  if (state.suspicious || !state.backendVerified) return;
  state.suspicious = true;
  
  const attackPayload = await apiFetch("/telemetry/attack-trigger", { method: "POST" });
  if (attackPayload?.packet) packets.push(attackPayload.packet);
  if (attackPayload?.log) logs.push(attackPayload.log);
  if (attackPayload?.file) files.push(attackPayload.file);
  if (attackPayload?.proxy) state.proxy.unshift(attackPayload.proxy);

  const statusRes = await apiFetch("/telemetry/status-message");
  $("#graphState").textContent = statusRes?.message || "Suspicious payload ingress detected via backend CNN model";
  renderAll();
  addChat(statusRes?.chatNotice || "Suspicious payload signature detected from remote inference pipeline.");
}

function renderAll() {
  if (!state.backendVerified) return;
  renderTraffic();
  renderRealtime();
  renderTable("packets", packets, "packetBody", "packetHead", $("#packetSearch")?.value || "");
  renderTable("logs", logs, "logBody", "logHead", $("#logSearch")?.value || "");
  renderTable("files", files, "fileBody", "fileHead", $("#fileSearch")?.value || "");
  renderProxy();
  renderProfile();
  updateCountdown();
}

function updateCountdown() {
  if (!state.backendVerified) return;
  const remaining = Math.max(0, nextSuspiciousTime.getTime() - Date.now());
  const minutes = Math.floor(remaining / 60000);
  const seconds = Math.floor((remaining % 60000) / 1000);
  $("#nextWindow").textContent = `${pad(minutes)}:${pad(seconds)}`;
  if (remaining <= 0) triggerSuspicious();
}

function bindEvents() {
  $$(".nav a, .brand, .profile-card").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      const targetRoute = link.dataset.route;
      if (!state.backendVerified && targetRoute !== "home" && targetRoute !== "profile") {
        routeTo("home");
        return;
      }
      routeTo(targetRoute);
    });
  });
  $("#themeToggle").addEventListener("click", () => {
    state.dark = !state.dark;
    document.body.classList.toggle("dark", state.dark);
    localStorage.setItem("trataTheme", state.dark ? "dark" : "light");
    $("#themeToggle").textContent = state.dark ? "Light mode" : "Dark mode";
  });
  [["packetSearch", "packets", packets, "packetBody", "packetHead"], ["logSearch", "logs", logs, "logBody", "logHead"], ["fileSearch", "files", files, "fileBody", "fileHead"]].forEach(([input, kind, rows, body, head]) => {
    $(`#${input}`).addEventListener("input", () => {
      renderTable(kind, rows, body, head, $(`#${input}`).value);
      if (kind === "packets") hideDetail("packetDetail");
      if (kind === "logs") hideDetail("logDetail");
      if (kind === "files") hideDetail("fileDetail");
    });
  });
  ["packetBody", "logBody", "fileBody"].forEach((bodyId) => {
    $(`#${bodyId}`).addEventListener("click", (event) => {
      const row = event.target.closest("[data-kind]");
      if (!row) return;
      const kind = row.dataset.kind;
      state.selected[kind] = Number(row.dataset.index);
      renderAll();
      if (kind === "packets") renderDetail("packets", packets, "packetDetail");
      if (kind === "logs") renderDetail("logs", logs, "logDetail");
      if (kind === "files") renderDetail("files", files, "fileDetail");
    });
  });
  $("#addProxyButton").addEventListener("click", () => $("#proxyForm").classList.toggle("open"));
  $("#proxyForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const ip = $("#proxyIp").value.trim();
    if (!ip) return;
    await apiFetch("/proxy/block", { method: "POST", body: JSON.stringify({ ip, reason: $("#proxyReason").value }) });
    state.proxy.unshift({ ip, status: "Blocked", reason: $("#proxyReason").value || "Manual operator block", suggested: false });
    $("#proxyIp").value = "";
    $("#proxyReason").value = "";
    renderProxy();
  });
  $("#proxyList").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-proxy]");
    if (!button) return;
    const idx = Number(button.dataset.proxy);
    const newStatus = button.dataset.status;
    state.proxy[idx].status = newStatus;
    await apiFetch(`/proxy/${state.proxy[idx].ip}/status`, { method: "PUT", body: JSON.stringify({ status: newStatus }) });
    renderProxy();
  });

  ["googleLogin", "homeGoogleLogin"].forEach((id) => {
    const btn = $(`#${id}`);
    if (btn) {
      btn.addEventListener("click", async () => {
        await apiFetch("/auth/initiate", { method: "POST" });
        sessionStorage.setItem("trataSessionActive", "true");
        $("#detailsModal").style.display = "grid";
      });
    }
  });

  $("#detailsForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    profile.name = $("#inputName").value.trim();
    profile.email = $("#inputEmail").value.trim();
    profile.organization = $("#inputOrg").value.trim();
    profile.role = $("#inputRole").value.trim();

    await apiFetch("/profile/register", { method: "POST", body: JSON.stringify(profile) });

    $("#detailsModal").style.display = "none";
    $("#apiKeyModal").style.display = "grid";
  });

  let tempGeneratedKey = "";
  $("#triggerGenKey").addEventListener("click", async () => {
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    let randomKey = "";
    for (let i = 0; i < 12; i++) {
      randomKey += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    tempGeneratedKey = randomKey;

    await apiFetch("/auth/generate-key", { method: "POST", body: JSON.stringify({ apiKey: tempGeneratedKey }) });

    $("#generatedApiKeyDisplay").textContent = tempGeneratedKey;
    $("#copyGenKey").style.display = "inline-flex";
    $("#finishApiKey").removeAttribute("disabled");
  });

  $("#copyGenKey").addEventListener("click", async () => {
    await navigator.clipboard.writeText(tempGeneratedKey);
    $("#copyGenKey").textContent = "Copied!";
    setTimeout(() => { $("#copyGenKey").textContent = "Copy key"; }, 1200);
  });

  $("#finishApiKey").addEventListener("click", async () => {
    profile.apiKey = tempGeneratedKey;
    state.loggedIn = true;
    localStorage.setItem("trataOAuth", "connected");
    $("#apiKeyModal").style.display = "none";

    await apiFetch("/auth/verify-session", { method: "POST", body: JSON.stringify({ apiKey: tempGeneratedKey }) });

    const connLoader = $("#connectionLoader");
    if (connLoader) {
      connLoader.style.opacity = "1";
      connLoader.style.visibility = "visible";
    }

    // Waiting window stays active indefinitely as requested
  });

  $("#manualLogin").addEventListener("click", async (event) => {
    event.preventDefault();
    const username = $("#manualUsername").value.trim();
    const password = $("#manualPassword").value;
    await apiFetch("/auth/manual", { method: "POST", body: JSON.stringify({ username, password }) });
    if (username !== LOCAL_USERNAME || password !== LOCAL_PASSWORD) return;
    completeLogin();
  });

  function completeLogin() {
    sessionStorage.setItem("trataSessionActive", "true");
    localStorage.setItem("trataOAuth", "connected");
    state.loggedIn = true;
    state.backendVerified = true;
    fetchUserProfile().then(() => renderProfile());
    history.replaceState(null, "", `#profile`);
  }

  $("#profileData").addEventListener("click", async (event) => {
    if (event.target.id === "toggleCollectorKey") {
      state.keyVisible = !state.keyVisible;
      renderProfile();
    }
    if (event.target.id === "generateCollectorKey") {
      const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
      let randomKey = "";
      for (let i = 0; i < 12; i++) {
        randomKey += chars.charAt(Math.floor(Math.random() * chars.length));
      }
      profile.apiKey = randomKey;
      await apiFetch("/auth/generate-key", { method: "POST", body: JSON.stringify({ apiKey: profile.apiKey }) });
      state.keyVisible = false;
      renderProfile();
    }
    if (event.target.id === "copyCollectorKey") {
      await navigator.clipboard.writeText(profile.apiKey);
      event.target.textContent = "Copied";
      setTimeout(() => {
        const button = $("#copyCollectorKey");
        if (button) button.textContent = "Copy key";
      }, 900);
    }
  });

  $("#chatToggle").addEventListener("click", () => $("#chatWidget").classList.toggle("open"));
  $("#chatForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const text = $("#chatInput").value.trim();
    if (!text) return;
    addChat(text, true);
    $("#chatInput").value = "";
    const reply = await answer(text);
    setTimeout(() => addChat(reply), 250);
  });
  addEventListener("hashchange", () => routeTo(location.hash.replace("#", "") || "home"));
}

function startHeroCanvas() {
  const canvas = $("#heroGraph");
  const ctx = canvas.getContext("2d");
  const points = Array.from({ length: 28 }, () => ({ x: Math.random(), y: Math.random(), vx: (Math.random() - 0.5) * 0.0006, vy: (Math.random() - 0.5) * 0.0006 }));
  function size() {
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
  }
  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = getComputedStyle(document.body).getPropertyValue("--bg");
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    points.forEach((point, index) => {
      point.x += point.vx;
      point.y += point.vy;
      if (point.x < 0 || point.x > 1) point.vx *= -1;
      if (point.y < 0 || point.y > 1) point.vy *= -1;
      points.slice(index + 1).forEach((other) => {
        const x = point.x * canvas.width;
        const y = point.y * canvas.height;
        const ox = other.x * canvas.width;
        const oy = other.y * canvas.height;
        const distance = Math.hypot(x - ox, y - oy);
        if (distance < 180) {
          ctx.globalAlpha = 0.16;
          ctx.strokeStyle = "#DCEAF7";
          ctx.beginPath();
          ctx.moveTo(x, y);
          ctx.lineTo(ox, oy);
          ctx.stroke();
        }
      });
      ctx.globalAlpha = 0.65;
      ctx.fillStyle = index % 8 === 0 ? "#58D68D" : "#68E1FD";
      ctx.beginPath();
      ctx.arc(point.x * canvas.width, point.y * canvas.height, 2.6, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.globalAlpha = 1;
    requestAnimationFrame(draw);
  }
  size();
  addEventListener("resize", size);
  draw();
}

function startBehaviourGraph() {
  const canvas = $("#behaviourGraph");
  const ctx = canvas.getContext("2d");
  
  function size() {
    const box = canvas.getBoundingClientRect();
    const width = Math.max(720, box.width || canvas.parentElement.clientWidth || 900);
    const height = Math.max(520, box.height || canvas.parentElement.clientHeight || 560);
    const ratio = Math.min(devicePixelRatio || 1, 2);
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  }

  function draw() {
    const width = canvas.width / Math.min(devicePixelRatio || 1, 2);
    const height = canvas.height / Math.min(devicePixelRatio || 1, 2);
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = getComputedStyle(document.body).getPropertyValue("--chart-bg").trim() || "#03060B";
    ctx.fillRect(0, 0, width, height);

    if (graphData.nodes.length === 0) return;

    const nodePositions = new Map();
    graphData.nodes.forEach((node, i) => {
      const angle = (i / graphData.nodes.length) * Math.PI * 2;
      const radius = Math.min(width, height) * 0.35;
      const x = width / 2 + Math.cos(angle) * radius;
      const y = height / 2 + Math.sin(angle) * radius;
      nodePositions.set(node.label, { x, y });
    });

    graphData.edges.forEach((edge) => {
      const from = nodePositions.get(edge.source);
      const to = nodePositions.get(edge.target);
      if (!from || !to) return;
      ctx.strokeStyle = edge.alert ? "#FF5F6D" : "#58D68D";
      ctx.globalAlpha = edge.alert ? 0.9 : 0.3;
      ctx.lineWidth = edge.alert ? 2.5 : 1;
      ctx.beginPath();
      ctx.moveTo(from.x, from.y);
      ctx.lineTo(to.x, to.y);
      ctx.stroke();
    });

    nodePositions.forEach((pos, label) => {
      ctx.globalAlpha = 1;
      ctx.fillStyle = "#68E1FD";
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, 5, 0, Math.PI * 2);
      ctx.fill();

      ctx.font = "600 11px Inter, sans-serif";
      ctx.fillStyle = "#F4F9FF";
      ctx.fillText(label, pos.x + 8, pos.y + 4);
    });

    requestAnimationFrame(draw);
  }

  size();
  state.graphResize = size;
  addEventListener("resize", size);
  draw();
}

async function init() {
  document.body.classList.toggle("dark", state.dark);
  $("#themeToggle").textContent = state.dark ? "Light mode" : "Dark mode";
  routeTo(location.hash.replace("#", "") || "home");
  
  renderProfile();
  bindEvents();
  
  addChat("Authentication required to initialize system state from backend and vector stores.");
  startHeroCanvas();
  startBehaviourGraph();
  requestAnimationFrame(() => $("#loader").classList.add("hidden"));
}

init();