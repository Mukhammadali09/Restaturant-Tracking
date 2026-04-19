const API = "";
const COLORS = ["#6c63ff","#fbbf24","#34d399","#f87171","#60a5fa","#a78bfa","#fb923c","#38bdf8","#e879f9","#4ade80","#f472b6","#facc15"];
const fmt = n => Number(n).toLocaleString("uz-UZ");

// ─── Auth ────────────────────────────────────────────────────────────────
const TOKEN_KEY = "rt_token";
const USER_KEY  = "rt_user";
function getToken() { return localStorage.getItem(TOKEN_KEY); }
function setAuth(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}
function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}
function currentUser() {
  try { return JSON.parse(localStorage.getItem(USER_KEY) || "null"); }
  catch { return null; }
}
function authHeaders(extra) {
  const h = extra || {};
  const t = getToken();
  if (t) h["Authorization"] = "Bearer " + t;
  return h;
}
async function handleAuthResponse(r) {
  if (r.status === 401) {
    clearAuth();
    showAuthScreen();
    throw new Error("unauthorized");
  }
  return r;
}

const fetchJSON = url => fetch(API + url, {headers: authHeaders()}).then(handleAuthResponse).then(r => r.json());
const postJSON = (url, body) => fetch(API + url, {method:"POST",headers:authHeaders({"Content-Type":"application/json"}),body:JSON.stringify(body)}).then(handleAuthResponse).then(r => r.json());
const putJSON = (url, body) => fetch(API + url, {method:"PUT",headers:authHeaders({"Content-Type":"application/json"}),body:JSON.stringify(body)}).then(handleAuthResponse).then(r => r.json());
const deleteJSON = url => fetch(API + url, {method:"DELETE", headers:authHeaders()}).then(handleAuthResponse).then(r => r.json());

let restaurants = [];
let charts = {};

function showAuthScreen() {
  document.getElementById("authScreen").classList.remove("hidden");
  document.getElementById("appShell").classList.add("hidden");
}
function showAppShell() {
  document.getElementById("authScreen").classList.add("hidden");
  document.getElementById("appShell").classList.remove("hidden");
  const u = currentUser();
  const nameEl = document.getElementById("userDisplayName");
  if (nameEl && u) nameEl.textContent = u.name + (u.company ? " — " + u.company : "");
}

async function submitLogin(e) {
  e.preventDefault();
  const email = document.getElementById("liEmail").value.trim();
  const password = document.getElementById("liPassword").value;
  const errEl = document.getElementById("authError");
  errEl.textContent = "";
  const r = await fetch(API + "/api/auth/login", {
    method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({email, password}),
  });
  const data = await r.json();
  if (!r.ok) { errEl.textContent = data.error || "Login failed"; return; }
  setAuth(data.token, data.user);
  await bootApp();
}

async function submitRegister(e) {
  e.preventDefault();
  const name = document.getElementById("riName").value.trim();
  const company = document.getElementById("riCompany").value.trim();
  const email = document.getElementById("riEmail").value.trim();
  const password = document.getElementById("riPassword").value;
  const errEl = document.getElementById("authError");
  errEl.textContent = "";
  const r = await fetch(API + "/api/auth/register", {
    method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({name, company, email, password}),
  });
  const data = await r.json();
  if (!r.ok) { errEl.textContent = data.error || "Registration failed"; return; }
  setAuth(data.token, data.user);
  await bootApp();
}

function switchAuthMode(mode) {
  document.getElementById("loginForm").classList.toggle("hidden", mode !== "login");
  document.getElementById("registerForm").classList.toggle("hidden", mode !== "register");
  document.getElementById("authError").textContent = "";
  document.querySelectorAll(".auth-switch button").forEach(b => b.classList.toggle("active", b.dataset.mode === mode));
}

function logout() {
  clearAuth();
  location.reload();
}

async function bootApp() {
  try {
    restaurants = await fetchJSON("/api/restaurants");
  } catch (e) { return; }  // handleAuthResponse already kicked us to login
  showAppShell();
  applyLanguage();
  setupTabs();
  populateAllSelects();
  loadMenuManagement();
  document.getElementById("mfDate").valueAsDate = new Date();
}

// ═══════════════════════════════════════════════════════════════════════════════
//  BOOTSTRAP
// ═══════════════════════════════════════════════════════════════════════════════
document.addEventListener("DOMContentLoaded", async () => {
  // Wire auth forms
  document.getElementById("loginForm").addEventListener("submit", submitLogin);
  document.getElementById("registerForm").addEventListener("submit", submitRegister);
  document.querySelectorAll(".auth-switch button").forEach(b => {
    b.addEventListener("click", () => switchAuthMode(b.dataset.mode));
  });
  document.getElementById("logoutBtn").addEventListener("click", logout);
  document.getElementById("profileBtn").addEventListener("click", openProfile);
  document.getElementById("profileForm").addEventListener("submit", saveProfile);
  document.getElementById("passwordForm").addEventListener("submit", changePassword);
  document.getElementById("engRunBtn").addEventListener("click", runMenuEngineering);
  document.getElementById("engExportBtn").addEventListener("click", exportCSV);

  // Event listeners for app features
  document.getElementById("menuForm").addEventListener("submit", submitMenuItem);
  document.getElementById("csvUploadBtn").addEventListener("click", uploadCSV);
  document.getElementById("browseRestaurant").addEventListener("change", browseMenu);
  document.getElementById("compRunBtn").addEventListener("click", runCompetitiveAnalysis);
  document.getElementById("pcCategory").addEventListener("change", loadPCDishes);
  document.getElementById("pcSearchBtn").addEventListener("click", runPriceCompare);
  document.getElementById("pcDish").addEventListener("change", runPriceCompare);
  document.getElementById("restSegmentFilter").addEventListener("change", renderRestaurantTable);
  document.getElementById("restDistrictFilter").addEventListener("change", renderRestaurantTable);
  document.getElementById("addRestaurantForm").addEventListener("submit", addRestaurant);
  document.getElementById("ocrUploadBtn").addEventListener("click", ocrUpload);

  // Check for existing session
  if (getToken()) {
    await bootApp();
  } else {
    showAuthScreen();
  }
});

function setupTabs() {
  document.querySelectorAll(".tab").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
      if (btn.dataset.tab === "menu-mgmt") loadMenuManagement();
      if (btn.dataset.tab === "competitive") loadCompetitiveTab();
      if (btn.dataset.tab === "price-compare") loadPriceCompareTab();
      if (btn.dataset.tab === "market") loadMarketAnalytics();
      if (btn.dataset.tab === "engineering") loadEngineeringTab();
      if (btn.dataset.tab === "restaurants") renderRestaurantTable();
    });
  });
}

function populateAllSelects() {
  ["mfRestaurant","browseRestaurant","ocrRestaurant","compBase"].forEach(id => {
    const el = document.getElementById(id);
    restaurants.forEach(r => { el.innerHTML += `<option value="${r.id}">${r.name}</option>`; });
  });
  const districts = [...new Set(restaurants.map(r => r.district))].sort();
  const df = document.getElementById("restDistrictFilter");
  districts.forEach(d => { df.innerHTML += `<option value="${d}">${d}</option>`; });
  const dl = document.getElementById("districtList");
  districts.forEach(d => { dl.innerHTML += `<option value="${d}">`; });
}

// ═══════════════════════════════════════════════════════════════════════════════
//  TAB 1: MENU MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════════
async function loadMenuManagement() {
  const [cov, cats, history] = await Promise.all([
    fetchJSON("/api/menu/coverage"),
    fetchJSON("/api/menu/categories"),
    fetchJSON("/api/price-history?limit=20"),
  ]);

  // Coverage cards
  document.getElementById("covTotal").textContent = cov.total_restaurants;
  document.getElementById("covWith").textContent = cov.restaurants_with_menu;
  document.getElementById("covWithout").textContent = cov.restaurants_without_menu;
  document.getElementById("covItems").textContent = fmt(cov.total_menu_items);

  // Category datalist
  const dl = document.getElementById("catList");
  dl.innerHTML = "";
  cats.forEach(c => { dl.innerHTML += `<option value="${c}">`; });

  // Price history
  const tbody = document.querySelector("#historyTable tbody");
  tbody.innerHTML = "";
  if (history.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-cell">${t("msg_no_changes")}</td></tr>`;
  } else {
    history.forEach(h => {
      const cls = h.new_price > h.old_price ? "diff-negative" : "diff-positive";
      const sign = h.change_pct > 0 ? "+" : "";
      tbody.innerHTML += `<tr>
        <td>${new Date(h.changed_at).toLocaleDateString()}</td>
        <td>${h.restaurant_name}</td><td>${h.dish_name}</td>
        <td>${fmt(h.old_price)}</td><td>${fmt(h.new_price)}</td>
        <td class="${cls}">${sign}${h.change_pct}%</td>
        <td>${h.changed_by || "—"}</td>
      </tr>`;
    });
  }
}

async function submitMenuItem(e) {
  e.preventDefault();
  await postJSON("/api/menu", {
    restaurant_id: +document.getElementById("mfRestaurant").value,
    category: document.getElementById("mfCategory").value,
    name: document.getElementById("mfName").value,
    price: +document.getElementById("mfPrice").value,
    description: document.getElementById("mfDesc").value,
    collected_by: document.getElementById("mfBy").value,
    collected_date: document.getElementById("mfDate").value || null,
  });
  const msg = document.getElementById("menuFormMsg");
  msg.textContent = t("msg_item_added");
  setTimeout(() => msg.textContent = "", 3000);
  document.getElementById("mfCategory").value = "";
  document.getElementById("mfName").value = "";
  document.getElementById("mfPrice").value = "";
  document.getElementById("mfDesc").value = "";
  loadMenuManagement();
  const browseRid = document.getElementById("browseRestaurant").value;
  if (browseRid) browseMenu();
}

async function uploadCSV() {
  const fileInput = document.getElementById("csvFile");
  const msg = document.getElementById("csvMsg");
  if (!fileInput.files.length) { msg.textContent = t("msg_select_csv"); return; }
  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  const res = await fetch(API + "/api/menu/csv", {method: "POST", body: formData, headers: authHeaders()});
  const data = await res.json();
  msg.textContent = t("msg_uploaded", data.added);
  if (data.skipped && data.skipped.length) {
    msg.textContent += " " + t("msg_skipped", data.skipped.join(", "));
  }
  fileInput.value = "";
  loadMenuManagement();
}

async function browseMenu() {
  const rid = document.getElementById("browseRestaurant").value;
  const area = document.getElementById("browseMenuArea");
  if (!rid) { area.innerHTML = ""; return; }

  const items = await fetchJSON(`/api/menu?restaurant_id=${rid}`);
  if (!items.length) {
    area.innerHTML = `<p class="hint">${t("msg_no_menu")}</p>`;
    return;
  }

  const cats = {};
  items.forEach(m => { (cats[m.category] = cats[m.category] || []).push(m); });

  let html = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem">
    <span class="hint">${items.length} ${t("th_items").toLowerCase()}</span>
    <div style="display:flex;gap:.4rem">
      <button class="btn-sm btn-save" onclick="saveAllPrices(${rid})">${t("btn_save_all")}</button>
      <button class="btn-sm btn-del" onclick="clearRestaurantMenu(${rid})">${t("btn_clear_all")}</button>
    </div>
  </div>`;
  html += `<div class="table-scroll"><table><thead><tr><th>${t("lbl_category")}</th><th>${t("th_dish")}</th><th>${t("lbl_price")}</th><th>${t("th_collected")}</th><th>${t("th_by")}</th><th>${t("th_actions")}</th></tr></thead><tbody>`;
  for (const [cat, list] of Object.entries(cats)) {
    list.forEach(m => {
      html += `<tr data-id="${m.id}">
        <td>${m.category}</td>
        <td><strong>${m.name}</strong><br><small class="muted">${m.description || ""}</small></td>
        <td><input type="number" class="inline-price" value="${m.price}" data-id="${m.id}" min="0" style="width:110px" /></td>
        <td>${m.collected_date || "—"}</td>
        <td>${m.collected_by || "—"}</td>
        <td>
          <button class="btn-sm btn-save" onclick="savePrice(${m.id}, this)">${t("btn_save")}</button>
          <button class="btn-sm btn-del" onclick="deleteItem(${m.id})">${t("btn_del")}</button>
        </td>
      </tr>`;
    });
  }
  html += '</tbody></table></div>';
  area.innerHTML = html;
}

async function savePrice(id, btn) {
  const input = document.querySelector(`input.inline-price[data-id="${id}"]`);
  const newPrice = +input.value;
  const by = document.getElementById("mfBy").value || "";
  await putJSON(`/api/menu/${id}`, {price: newPrice, collected_by: by, collected_date: new Date().toISOString().split("T")[0]});
  btn.textContent = t("btn_saved");
  setTimeout(() => { btn.textContent = t("btn_save"); }, 1500);
  loadMenuManagement();
}

async function saveAllPrices(rid) {
  const inputs = document.querySelectorAll("input.inline-price");
  const by = document.getElementById("mfBy").value || "";
  const today = new Date().toISOString().split("T")[0];
  const promises = [];
  inputs.forEach(input => {
    const id = input.dataset.id;
    promises.push(putJSON(`/api/menu/${id}`, {price: +input.value, collected_by: by, collected_date: today}));
  });
  await Promise.all(promises);
  loadMenuManagement();
  browseMenu();
}

async function deleteItem(id) {
  await deleteJSON(`/api/menu/${id}`);
  browseMenu();
  loadMenuManagement();
}

// ═══════════════════════════════════════════════════════════════════════════════
//  OCR MENU UPLOAD — auto-saves to restaurant, shows in browse table
// ═══════════════════════════════════════════════════════════════════════════════
async function ocrUpload() {
  const fileInput = document.getElementById("ocrFile");
  const status = document.getElementById("ocrStatus");
  const rid = document.getElementById("ocrRestaurant").value;
  const by = document.getElementById("ocrBy").value || "OCR Upload";
  const lang = document.getElementById("ocrLang").value;
  const files = fileInput.files;

  if (!files.length) { status.textContent = t("msg_select_photo"); status.style.color = "var(--red)"; return; }
  if (files.length > 10) { status.textContent = t("msg_max_files"); status.style.color = "var(--red)"; return; }

  // Send each file one at a time — server handles image conversion via Pillow
  let totalSaved = 0;
  let lastMethod = "";
  let lastClaudeError = "";
  let allRawText = "";
  let errors = [];

  for (let i = 0; i < files.length; i++) {
    status.textContent = t("msg_scanning") + ` (${i + 1}/${files.length})`;
    status.style.color = "var(--gold)";

    const formData = new FormData();
    formData.append("file", files[i]);
    formData.append("language", lang);
    formData.append("restaurant_id", rid);
    formData.append("collected_by", by);

    try {
      const res = await fetch(API + "/api/menu/ocr", {method: "POST", body: formData, headers: authHeaders()});
      if (!res.ok) {
        let errMsg = `HTTP ${res.status}`;
        try { const d = await res.json(); errMsg = d.error || errMsg; } catch {}
        errors.push(`${files[i].name}: ${errMsg}`);
        continue;
      }
      const data = await res.json();
      if (data.error) { errors.push(`${files[i].name}: ${data.error}`); continue; }

      totalSaved += data.saved || 0;
      lastMethod = data.method || lastMethod;
      if (data.claude_error) lastClaudeError = data.claude_error;
      if (data.raw_text) allRawText += (allRawText ? "\n\n" : "") + data.raw_text;
    } catch (e) {
      errors.push(`${files[i].name}: ${e.message}`);
    }
  }

  // Show raw text for debugging
  if (allRawText) {
    document.getElementById("ocrRawText").textContent = allRawText;
    document.getElementById("ocrRawDetails").style.display = "block";
  }

  if (totalSaved === 0 && errors.length) {
    status.textContent = errors.join("; ");
    status.style.color = "var(--red)";
    return;
  }

  // Build success message
  const restName = document.querySelector(`#ocrRestaurant option[value="${rid}"]`)?.textContent || "";
  const methodLabel = lastMethod === "claude_vision" ? "AI Vision" : "OCR";
  let msg = t("msg_ocr_saved", totalSaved, restName) + ` [${methodLabel}]`;
  if (lastClaudeError && lastMethod !== "claude_vision") {
    msg += ` | Claude Vision error: ${lastClaudeError}`;
  }
  if (errors.length) msg += ` | ${errors.length} failed`;
  status.textContent = msg;
  status.style.color = lastMethod === "claude_vision" ? "var(--green)" : "var(--gold)";

  // Clear file input
  fileInput.value = "";

  // Auto-select restaurant in browse and show the menu table
  const browseSelect = document.getElementById("browseRestaurant");
  browseSelect.value = rid;
  await browseMenu();

  // Scroll to the browse area so user sees the added items
  document.getElementById("browseMenuArea").scrollIntoView({behavior: "smooth", block: "start"});

  // Refresh coverage stats
  loadMenuManagement();
}

async function clearRestaurantMenu(rid) {
  const restName = document.querySelector(`#browseRestaurant option[value="${rid}"]`)?.textContent || "";
  if (!confirm(t("msg_confirm_clear", restName))) return;
  await deleteJSON(`/api/menu/restaurant/${rid}`);
  browseMenu();
  loadMenuManagement();
}

function escHtml(s) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// ═══════════════════════════════════════════════════════════════════════════════
//  TAB 2: COMPETITIVE ANALYSIS
// ═══════════════════════════════════════════════════════════════════════════════
async function loadCompetitiveTab() {
  // Populate base restaurant selector
  const baseSel = document.getElementById("compBase");
  baseSel.innerHTML = "";
  restaurants.forEach(r => {
    baseSel.innerHTML += `<option value="${r.id}">${r.name}</option>`;
  });

  // Category filter
  const categories = await fetchJSON("/api/menu/categories");
  const catSel = document.getElementById("compCatFilter");
  catSel.innerHTML = `<option value="">${t("opt_all")}</option>`;
  categories.forEach(c => { catSel.innerHTML += `<option value="${c}">${c}</option>`; });

  // Populate competitor checkboxes
  updateCompetitorPicker();
  baseSel.addEventListener("change", updateCompetitorPicker);
}

function updateCompetitorPicker() {
  const baseId = +document.getElementById("compBase").value;
  const picker = document.getElementById("compCompetitors");
  picker.innerHTML = "";
  restaurants.forEach(r => {
    if (r.id === baseId) return;
    picker.innerHTML += `<label><input type="checkbox" name="comp" value="${r.id}" /><span>${r.name}</span></label>`;
  });
}

function getSelectedCompetitors() {
  return Array.from(document.querySelectorAll('#compCompetitors input[type="checkbox"]:checked'))
    .map(cb => cb.value);
}

async function runCompetitiveAnalysis() {
  const baseId = document.getElementById("compBase").value;
  const compIds = getSelectedCompetitors();
  const catFilter = document.getElementById("compCatFilter").value;

  if (!compIds.length) {
    document.getElementById("compResults").style.display = "none";
    document.getElementById("compEmpty").style.display = "block";
    return;
  }

  let url = `/api/menu/compare-restaurants?base_id=${baseId}&competitor_ids=${compIds.join(",")}`;
  if (catFilter) url += `&category=${encodeURIComponent(catFilter)}`;

  const data = await fetchJSON(url);

  document.getElementById("compEmpty").style.display = "none";
  document.getElementById("compResults").style.display = "block";

  // Summary cards
  document.getElementById("compYourAvg").textContent = fmt(data.summary.base_avg_price) + " UZS";
  document.getElementById("compMarketAvg").textContent = fmt(data.summary.competitors_avg_price) + " UZS";

  const diff = data.summary.diff_pct;
  const posEl = document.getElementById("compPosition");
  if (diff > 5) {
    posEl.textContent = `+${diff}%`;
    posEl.className = "card-value red";
  } else if (diff < -5) {
    posEl.textContent = `${diff}%`;
    posEl.className = "card-value green";
  } else {
    posEl.textContent = `${diff > 0 ? "+" : ""}${diff}%`;
    posEl.className = "card-value";
  }
  document.getElementById("compCommonCount").textContent = data.common_dishes.length;

  // Competitor overview table
  const oTbody = document.querySelector("#compOverviewTable tbody");
  oTbody.innerHTML = "";
  data.competitors.forEach(c => {
    const cls = c.diff_pct > 0 ? "price-higher" : c.diff_pct < 0 ? "price-lower" : "price-same";
    const sign = c.diff_pct > 0 ? "+" : "";
    oTbody.innerHTML += `<tr>
      <td><strong>${c.name}</strong></td>
      <td>${c.cuisine}</td>
      <td>${c.segment}</td>
      <td>${c.item_count}</td>
      <td>${fmt(c.avg_price)} UZS</td>
      <td>${c.common_dishes}</td>
      <td class="${cls}">${sign}${c.diff_pct}%</td>
    </tr>`;
  });

  // Category comparison chart
  const cats = data.by_category.filter(c => c.base_avg > 0 || c.competitors_avg > 0);
  if (cats.length > 0) {
    renderChart("compCategoryChart", "bar",
      cats.map(c => c.category),
      [
        {label: data.base.name, data: cats.map(c => c.base_avg), backgroundColor: "#6c63ff", borderWidth: 0},
        {label: t("comp_competitors_label"), data: cats.map(c => c.competitors_avg), backgroundColor: "#fbbf2480", borderColor: "#fbbf24", borderWidth: 1},
      ],
      {y: {beginAtZero: true}});
  }

  // Category breakdown table
  const catTbody = document.querySelector("#compCatTable tbody");
  catTbody.innerHTML = "";
  data.by_category.forEach(c => {
    const cls = c.diff_pct > 0 ? "price-higher" : c.diff_pct < 0 ? "price-lower" : "price-same";
    const sign = c.diff_pct > 0 ? "+" : "";
    catTbody.innerHTML += `<tr>
      <td><strong>${c.category}</strong></td>
      <td>${c.base_avg > 0 ? fmt(c.base_avg) : '<span class="muted">—</span>'}</td>
      <td>${c.competitors_avg > 0 ? fmt(c.competitors_avg) : '<span class="muted">—</span>'}</td>
      <td class="${cls}">${c.base_avg > 0 && c.competitors_avg > 0 ? sign + c.diff_pct + "%" : '<span class="muted">—</span>'}</td>
      <td>${c.base_count}</td>
      <td>${c.competitors_count}</td>
    </tr>`;
  });

  // Common dishes table — with fuzzy match details
  const dTbody = document.querySelector("#compDishTable tbody");
  dTbody.innerHTML = "";
  if (data.common_dishes.length === 0) {
    dTbody.innerHTML = `<tr><td colspan="5" class="empty-cell">${t("comp_no_common")}</td></tr>`;
  } else {
    data.common_dishes.forEach(d => {
      const cls = d.diff_pct > 0 ? "price-higher" : d.diff_pct < 0 ? "price-lower" : "price-same";
      const sign = d.diff_pct > 0 ? "+" : "";
      // Build competitor detail with matched names
      const compDetail = d.competitor_prices.map(p => {
        const nameNote = p.matched_name && p.matched_name !== d.name
          ? ` <span class="muted" style="font-size:.72rem">(${p.matched_name})</span>` : "";
        const simBadge = p.similarity < 100
          ? ` <span class="muted" style="font-size:.68rem">${p.similarity}%</span>` : "";
        return `${p.name}: ${fmt(p.price)}${nameNote}${simBadge}`;
      }).join("<br>");
      // Show matched competitor names below avg
      const matchedNames = d.competitor_prices
        .filter(p => p.matched_name && p.matched_name !== d.name)
        .map(p => `<span class="muted" style="font-size:.7rem">${p.name}: "${p.matched_name}"</span>`)
        .join(", ");
      const matchNote = matchedNames ? `<br>${matchedNames}` : "";
      dTbody.innerHTML += `<tr>
        <td><strong>${d.name}</strong></td>
        <td>${d.category}</td>
        <td>${fmt(d.base_price)}</td>
        <td><span title="${d.competitor_prices.map(p => p.name + ': ' + fmt(p.price)).join(', ')}">${fmt(d.competitors_avg)}</span>${matchNote}</td>
        <td class="${cls}">${sign}${d.diff_pct}%</td>
      </tr>`;
    });
  }

  // Dish price comparison chart (top 15 by biggest difference)
  const topDishes = data.common_dishes.slice(0, 15);
  if (topDishes.length > 0) {
    renderChart("compDishChart", "bar",
      topDishes.map(d => d.name.length > 25 ? d.name.substring(0, 22) + "..." : d.name),
      [
        {label: data.base.name, data: topDishes.map(d => d.base_price), backgroundColor: "#6c63ff", borderWidth: 0},
        {label: t("comp_competitors_label"), data: topDishes.map(d => d.competitors_avg), backgroundColor: "#fbbf2480", borderColor: "#fbbf24", borderWidth: 1},
      ],
      {y: {beginAtZero: true}});
  }

  // Missing dishes table
  const mTbody = document.querySelector("#compMissingTable tbody");
  mTbody.innerHTML = "";
  if (data.missing_from_base.length === 0) {
    mTbody.innerHTML = `<tr><td colspan="4" class="empty-cell">${t("comp_no_gaps")}</td></tr>`;
  } else {
    data.missing_from_base.forEach(d => {
      mTbody.innerHTML += `<tr>
        <td>${d.name}</td>
        <td>${d.category}</td>
        <td>${d.available_at.join(", ")}</td>
        <td>${fmt(d.avg_price)} UZS</td>
      </tr>`;
    });
  }

  // Unique dishes table
  const uTbody = document.querySelector("#compUniqueTable tbody");
  uTbody.innerHTML = "";
  if (data.unique_to_base.length === 0) {
    uTbody.innerHTML = `<tr><td colspan="3" class="empty-cell">${t("comp_no_unique")}</td></tr>`;
  } else {
    data.unique_to_base.forEach(d => {
      uTbody.innerHTML += `<tr>
        <td>${d.name}</td>
        <td>${d.category}</td>
        <td>${fmt(d.price)} UZS</td>
      </tr>`;
    });
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
//  TAB 3: PRICE COMPARISON (single dish lookup)
// ═══════════════════════════════════════════════════════════════════════════════
async function loadPriceCompareTab() {
  const categories = await fetchJSON("/api/menu/categories");
  const catSel = document.getElementById("pcCategory");
  catSel.innerHTML = `<option value="">${t("opt_all")}</option>`;
  categories.forEach(c => { catSel.innerHTML += `<option value="${c}">${c}</option>`; });
  await loadPCDishes();
}

async function loadPCDishes() {
  const cat = document.getElementById("pcCategory").value;
  const url = cat ? `/api/menu/items?category=${encodeURIComponent(cat)}` : "/api/menu/items";
  const items = await fetchJSON(url);
  const sel = document.getElementById("pcDish");
  sel.innerHTML = `<option value="">${t("opt_select_dish")}</option>`;
  items.forEach(name => { sel.innerHTML += `<option value="${name}">${name}</option>`; });
}

async function runPriceCompare() {
  const dish = document.getElementById("pcDish").value;
  if (!dish) return;
  const cat = document.getElementById("pcCategory").value;
  let url = `/api/menu/compare?dish=${encodeURIComponent(dish)}`;
  if (cat) url += `&category=${encodeURIComponent(cat)}`;
  const data = await fetchJSON(url);

  const empty = document.getElementById("pcEmpty");
  if (!data.results || !data.results.length) {
    document.getElementById("pcSummary").style.display = "none";
    document.getElementById("pcSegments").style.display = "none";
    document.getElementById("pcChartSection").style.display = "none";
    document.getElementById("pcTableSection").style.display = "none";
    empty.style.display = "block";
    return;
  }
  empty.style.display = "none";

  document.getElementById("pcSummary").style.display = "grid";
  document.getElementById("pcCoverage").textContent = `${data.restaurants_with_data} / ${data.total_restaurants} (${data.coverage_pct}%)`;
  document.getElementById("pcAvg").textContent = fmt(data.avg_price) + " UZS";
  document.getElementById("pcMin").textContent = fmt(data.min_price) + " UZS";
  document.getElementById("pcMax").textContent = fmt(data.max_price) + " UZS";

  const segDiv = document.getElementById("pcSegments");
  segDiv.innerHTML = "";
  segDiv.style.display = "grid";
  for (const [seg, avg] of Object.entries(data.segment_averages)) {
    segDiv.innerHTML += `<div class="card"><span class="card-label">${seg} ${t("avg_suffix")}</span><span class="card-value">${fmt(avg)} UZS</span></div>`;
  }

  document.getElementById("pcChartSection").style.display = "grid";
  document.getElementById("pcChartTitle").textContent = t("pc_chart_title", dish);
  const labels = data.results.map(r => r.restaurant_name);
  const prices = data.results.map(r => r.price);
  const colors = data.results.map(r => {
    if (r.restaurant_segment === "Luxury") return "#f87171";
    if (r.restaurant_segment === "Premium") return "#6c63ff";
    return "#34d399";
  });
  renderChart("priceCompareChart", "bar", labels, [{label:t("chart_price_label"), data:prices, backgroundColor:colors, borderWidth:0}], {y:{beginAtZero:true}});

  document.getElementById("pcTableSection").style.display = "block";
  const tbody = document.querySelector("#pcTable tbody");
  tbody.innerHTML = "";
  data.results.forEach(r => {
    const diff = r.price - data.avg_price;
    const pct = data.avg_price ? ((diff / data.avg_price)*100).toFixed(1) : 0;
    const cls = diff > 0 ? "diff-negative" : "diff-positive";
    const sign = diff > 0 ? "+" : "";
    tbody.innerHTML += `<tr>
      <td><strong>${r.restaurant_name}</strong></td>
      <td>${r.restaurant_segment}</td>
      <td>${fmt(r.price)}</td>
      <td class="${cls}">${sign}${fmt(diff)} (${sign}${pct}%)</td>
      <td>${r.collected_date || "—"}</td>
      <td>${r.collected_by || "—"}</td>
    </tr>`;
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
//  TAB 4: MARKET ANALYTICS
// ═══════════════════════════════════════════════════════════════════════════════
async function loadMarketAnalytics() {
  const [segments, districts, ranking, catCoverage] = await Promise.all([
    fetchJSON("/api/analytics/segments"),
    fetchJSON("/api/analytics/districts"),
    fetchJSON("/api/analytics/ranking"),
    fetchJSON("/api/analytics/category-coverage"),
  ]);

  const hasData = segments.some(s => s.menu_items_entered > 0);
  document.getElementById("marketEmpty").style.display = hasData ? "none" : "block";
  document.getElementById("marketCharts").style.display = hasData ? "grid" : "none";
  document.getElementById("marketLandscape").style.display = hasData ? "grid" : "none";

  if (hasData) {
    const segsWithData = segments.filter(s => s.avg_menu_price > 0);
    renderChart("segmentChart", "bar",
      segsWithData.map(s => s.segment),
      [{label:t("chart_avg_label"),data:segsWithData.map(s => s.avg_menu_price),backgroundColor:["#34d399","#6c63ff","#f87171"]}],
      {y:{beginAtZero:true}});
    renderChart("districtChart", "doughnut",
      districts.map(d => d.district),
      [{data:districts.map(d => d.restaurant_count),backgroundColor:COLORS}],{},false,true);

    // Competitive Landscape scatter chart
    const restsWithData = ranking.filter(r => r.menu_items > 0);
    if (restsWithData.length > 0) {
      const segColors = {"Luxury":"#f87171","Premium":"#6c63ff","Upper Casual":"#34d399"};
      const scatterData = restsWithData.map(r => ({
        x: r.menu_items,
        y: r.avg_menu_price,
        label: r.name,
      }));
      const scatterColors = restsWithData.map(r => segColors[r.price_segment] || "#60a5fa");

      if (charts["landscapeChart"]) charts["landscapeChart"].destroy();
      charts["landscapeChart"] = new Chart(document.getElementById("landscapeChart"), {
        type: "bubble",
        data: {
          datasets: [{
            label: t("market_landscape_label"),
            data: scatterData.map((d, i) => ({x: d.x, y: d.y, r: 8})),
            backgroundColor: scatterColors.map(c => c + "99"),
            borderColor: scatterColors,
            borderWidth: 2,
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: {display: false},
            tooltip: {
              callbacks: {
                label: ctx => {
                  const d = scatterData[ctx.dataIndex];
                  return `${d.label}: ${d.x} items, avg ${fmt(d.y)} UZS`;
                }
              }
            }
          },
          scales: {
            x: {title: {display: true, text: t("market_x_items"), color: "#9ca3af"}, ticks: {color: "#9ca3af"}, grid: {color: "#2a2d3a"}},
            y: {title: {display: true, text: t("market_y_price"), color: "#9ca3af"}, ticks: {color: "#9ca3af"}, grid: {color: "#2a2d3a"}, beginAtZero: true},
          }
        }
      });
    }
  }

  const rtbody = document.querySelector("#rankingTable tbody");
  rtbody.innerHTML = "";
  ranking.forEach((r, i) => {
    rtbody.innerHTML += `<tr>
      <td>${i+1}</td><td><strong>${r.name}</strong></td><td>${r.cuisine}</td>
      <td>${r.price_segment}</td><td>${r.district}</td>
      <td>${r.menu_items > 0 ? r.menu_items : `<span class="muted">${t("lbl_none")}</span>`}</td>
      <td>${r.avg_menu_price > 0 ? fmt(r.avg_menu_price) : '<span class="muted">—</span>'}</td>
    </tr>`;
  });

  fillTable("#segmentTable tbody", segments, ["segment","restaurant_count","avg_menu_price","menu_items_entered"]);
  fillTable("#districtTable tbody", districts, ["district","restaurant_count","avg_menu_price","menu_items_entered"]);

  // Category Coverage Heatmap
  if (catCoverage.restaurants.length > 0 && catCoverage.categories.length > 0) {
    document.getElementById("categoryCoverageSection").style.display = "block";
    renderCategoryCoverage(catCoverage);
  } else {
    document.getElementById("categoryCoverageSection").style.display = "none";
  }
}

function renderCategoryCoverage(data) {
  const cats = data.categories;
  const rests = data.restaurants;

  // Find max count for color scaling
  let maxCount = 1;
  rests.forEach(r => {
    Object.values(r.categories).forEach(c => {
      if (c.count > maxCount) maxCount = c.count;
    });
  });

  let html = '<table><thead><tr><th data-i18n="lbl_restaurant">' + t("lbl_restaurant") + '</th>';
  cats.forEach(cat => {
    const shortCat = cat.length > 12 ? cat.substring(0, 10) + "…" : cat;
    html += `<th style="writing-mode:vertical-lr;transform:rotate(180deg);font-size:.65rem;padding:.3rem;max-width:30px" title="${cat}">${shortCat}</th>`;
  });
  html += '</tr></thead><tbody>';

  rests.forEach(r => {
    html += `<tr><td style="white-space:nowrap;font-size:.78rem"><strong>${r.name}</strong></td>`;
    cats.forEach(cat => {
      const c = r.categories[cat];
      if (c) {
        const intensity = Math.min(c.count / maxCount, 1);
        const alpha = (0.15 + intensity * 0.85).toFixed(2);
        html += `<td style="text-align:center;background:rgba(108,99,255,${alpha});font-size:.72rem;padding:.2rem" title="${cat}: ${c.count} items, avg ${fmt(c.avg_price)} UZS">${c.count}</td>`;
      } else {
        html += `<td style="text-align:center;color:var(--text-muted);font-size:.68rem;padding:.2rem">—</td>`;
      }
    });
    html += '</tr>';
  });
  html += '</tbody></table>';

  document.getElementById("categoryCoverageArea").innerHTML = html;
}

function fillTable(sel, data, keys) {
  const tbody = document.querySelector(sel);
  tbody.innerHTML = "";
  data.forEach(row => {
    tbody.innerHTML += "<tr>" + keys.map(k => {
      let v = row[k];
      if (typeof v === "number" && k.includes("price")) v = v > 0 ? fmt(v) : '<span class="muted">—</span>';
      return `<td>${v}</td>`;
    }).join("") + "</tr>";
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
//  TAB 4: RESTAURANTS
// ═══════════════════════════════════════════════════════════════════════════════
function renderRestaurantTable() {
  const seg = document.getElementById("restSegmentFilter").value;
  const dist = document.getElementById("restDistrictFilter").value;
  let filtered = restaurants;
  if (seg) filtered = filtered.filter(r => r.price_segment === seg);
  if (dist) filtered = filtered.filter(r => r.district === dist);
  const tbody = document.querySelector("#restTable tbody");
  tbody.innerHTML = "";
  filtered.forEach(r => {
    tbody.innerHTML += `<tr>
      <td><strong>${r.name}</strong></td><td>${r.cuisine}</td><td>${r.district}</td>
      <td>${r.price_segment}</td><td>${fmt(r.avg_bill_min)} – ${fmt(r.avg_bill_max)}</td>
      <td>${r.phone || "—"}</td><td>${r.address}</td>
      <td><button class="btn-sm btn-del" onclick="deleteRestaurant(${r.id},'${escHtml(r.name)}')">${t("btn_remove")}</button></td>
    </tr>`;
  });
}

async function addRestaurant(e) {
  e.preventDefault();
  const data = {
    name: document.getElementById("arName").value,
    cuisine: document.getElementById("arCuisine").value,
    address: document.getElementById("arAddress").value,
    district: document.getElementById("arDistrict").value,
    phone: document.getElementById("arPhone").value,
    price_segment: document.getElementById("arSegment").value,
    avg_bill_min: +document.getElementById("arBillMin").value || 0,
    avg_bill_max: +document.getElementById("arBillMax").value || 0,
  };
  const r = await postJSON("/api/restaurants", data);
  restaurants.push(r);

  ["mfRestaurant","browseRestaurant","ocrRestaurant","compBase"].forEach(id => {
    document.getElementById(id).innerHTML += `<option value="${r.id}">${r.name}</option>`;
  });

  const msg = document.getElementById("addRestMsg");
  msg.textContent = t("msg_rest_added", r.name);
  setTimeout(() => msg.textContent = "", 3000);
  document.getElementById("addRestaurantForm").reset();
  renderRestaurantTable();
}

async function deleteRestaurant(id, name) {
  if (!confirm(t("msg_confirm_del", name))) return;
  await deleteJSON(`/api/restaurants/${id}`);
  restaurants = restaurants.filter(r => r.id !== id);

  ["mfRestaurant","browseRestaurant","ocrRestaurant","compBase"].forEach(sid => {
    const opt = document.querySelector(`#${sid} option[value="${id}"]`);
    if (opt) opt.remove();
  });

  renderRestaurantTable();
  loadMenuManagement();
}

// ═══════════════════════════════════════════════════════════════════════════════
//  PROFILE
// ═══════════════════════════════════════════════════════════════════════════════
function openProfile() {
  const u = currentUser();
  if (!u) return;
  document.getElementById("pfName").value = u.name || "";
  document.getElementById("pfCompany").value = u.company || "";
  document.getElementById("pfEmail").value = u.email || "";
  document.getElementById("pfRole").value = (u.role || "manager").charAt(0).toUpperCase() + (u.role || "manager").slice(1);
  const avatar = document.getElementById("profileAvatar");
  const initials = u.name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);
  avatar.innerHTML = u.photo_url
    ? `<img src="${u.photo_url}" class="avatar-img" />`
    : `<div class="avatar-initials">${initials}</div>`;
  document.getElementById("profileMsg").textContent = "";
  document.getElementById("profileModal").classList.remove("hidden");
}

async function saveProfile(e) {
  e.preventDefault();
  const data = {
    name: document.getElementById("pfName").value.trim(),
    company: document.getElementById("pfCompany").value.trim(),
  };
  const r = await putJSON("/api/auth/profile", data);
  if (r.error) { document.getElementById("profileMsg").textContent = r.error; return; }
  setAuth(getToken(), r);
  document.getElementById("userDisplayName").textContent = r.name + (r.company ? " — " + r.company : "");
  document.getElementById("profileMsg").style.color = "var(--green)";
  document.getElementById("profileMsg").textContent = "Profile updated!";
  setTimeout(() => { document.getElementById("profileMsg").textContent = ""; document.getElementById("profileMsg").style.color = ""; }, 2000);
}

async function changePassword(e) {
  e.preventDefault();
  const data = {
    current_password: document.getElementById("pwCurrent").value,
    new_password: document.getElementById("pwNew").value,
  };
  const r = await putJSON("/api/auth/password", data);
  const msg = document.getElementById("profileMsg");
  if (r.error) { msg.style.color = "var(--red)"; msg.textContent = r.error; return; }
  msg.style.color = "var(--green)";
  msg.textContent = "Password updated!";
  document.getElementById("passwordForm").reset();
  setTimeout(() => { msg.textContent = ""; msg.style.color = ""; }, 2000);
}

// ═══════════════════════════════════════════════════════════════════════════════
//  MENU ENGINEERING
// ═══════════════════════════════════════════════════════════════════════════════
function loadEngineeringTab() {
  const sel = document.getElementById("engRestaurant");
  if (!sel.options.length) {
    restaurants.forEach(r => { sel.innerHTML += `<option value="${r.id}">${r.name}</option>`; });
  }
}

async function runMenuEngineering() {
  const rid = document.getElementById("engRestaurant").value;
  if (!rid) return;

  const data = await fetchJSON(`/api/analytics/menu-engineering?restaurant_id=${rid}`);
  const recData = await fetchJSON(`/api/analytics/price-recommendations?restaurant_id=${rid}`);

  // Summary cards
  const s = data.summary;
  document.getElementById("engSummary").style.display = "";
  document.getElementById("engStars").textContent = s.stars;
  document.getElementById("engPlowhorses").textContent = s.plowhorses;
  document.getElementById("engPuzzles").textContent = s.puzzles;
  document.getElementById("engDogs").textContent = s.dogs;

  // Matrix table
  const quadrantEmoji = { star: "★", plowhorse: "⚙", puzzle: "?", dog: "✕" };
  const quadrantClass = { star: "green", plowhorse: "gold", puzzle: "blue", dog: "red" };
  const quadrantLabel = { star: "Star", plowhorse: "Plowhorse", puzzle: "Puzzle", dog: "Dog" };

  let html = `<table class="data-table"><thead><tr>
    <th>Dish</th><th>Category</th><th>Price</th><th>Market Avg</th><th>vs Market</th>
    <th>Popularity</th><th>Classification</th><th>Found At</th>
  </tr></thead><tbody>`;

  const sorted = [...data.items].sort((a, b) => {
    const order = { star: 0, plowhorse: 1, puzzle: 2, dog: 3 };
    return (order[a.quadrant] || 0) - (order[b.quadrant] || 0);
  });

  for (const item of sorted) {
    const diff = item.price_vs_market;
    const diffClass = diff > 0 ? "green" : diff < 0 ? "red" : "";
    html += `<tr>
      <td>${item.name}</td>
      <td>${item.category}</td>
      <td>${fmt(item.price)}</td>
      <td>${fmt(item.market_avg)}</td>
      <td class="${diffClass}">${diff > 0 ? "+" : ""}${diff}%</td>
      <td>${item.popularity} restaurants</td>
      <td><span class="${quadrantClass[item.quadrant]}">${quadrantEmoji[item.quadrant]} ${quadrantLabel[item.quadrant]}</span></td>
      <td class="small-text">${(item.matched_restaurants || []).join(", ") || "—"}</td>
    </tr>`;
  }
  html += "</tbody></table>";
  document.getElementById("engResults").innerHTML = html;

  // Price recommendations
  if (recData.recommendations && recData.recommendations.length) {
    let recHtml = `<div class="card-row" style="margin-bottom:1rem">
      <div class="card"><span class="card-label">Items Analyzed</span><span class="card-value">${recData.summary.total_items_analyzed}</span></div>
      <div class="card"><span class="card-label">Price Raises</span><span class="card-value green">${recData.summary.raise_count}</span></div>
      <div class="card"><span class="card-label">Price Lowers</span><span class="card-value red">${recData.summary.lower_count}</span></div>
      <div class="card"><span class="card-label">Revenue Opportunity</span><span class="card-value gold">${fmt(recData.summary.total_revenue_opportunity)} UZS/item</span></div>
    </div>`;

    recHtml += `<table class="data-table"><thead><tr>
      <th>Dish</th><th>Current</th><th>Market Avg</th><th>Diff</th>
      <th>Suggested</th><th>Action</th><th>Reason</th>
    </tr></thead><tbody>`;

    for (const r of recData.recommendations) {
      const actionClass = r.action === "raise" ? "green" : r.action === "lower" ? "red" : "gold";
      recHtml += `<tr>
        <td>${r.dish}</td>
        <td>${fmt(r.current_price)}</td>
        <td>${fmt(r.market_avg)}</td>
        <td class="${r.diff_pct < 0 ? "red" : "green"}">${r.diff_pct > 0 ? "+" : ""}${r.diff_pct}%</td>
        <td><strong>${fmt(r.suggested_price)}</strong></td>
        <td class="${actionClass}">${r.action.toUpperCase()}</td>
        <td class="small-text">${r.reason}</td>
      </tr>`;
    }
    recHtml += "</tbody></table>";
    document.getElementById("priceRecResults").innerHTML = recHtml;
  } else {
    document.getElementById("priceRecResults").innerHTML = '<p class="hint">No pricing recommendations — your prices are well-aligned with the market.</p>';
  }
}

function exportCSV() {
  const rid = document.getElementById("engRestaurant").value;
  const url = rid ? `/api/export/menu-data?restaurant_id=${rid}` : "/api/export/menu-data";
  const a = document.createElement("a");
  a.href = url;
  a.download = "menu_data.csv";
  // Add auth header via fetch
  fetch(url, { headers: authHeaders() })
    .then(r => r.blob())
    .then(blob => {
      a.href = URL.createObjectURL(blob);
      a.click();
    });
}

// ═══════════════════════════════════════════════════════════════════════════════
//  CHART HELPER
// ═══════════════════════════════════════════════════════════════════════════════
function renderChart(canvasId, type, labels, datasets, scaleOpts, horizontal, isPie) {
  if (charts[canvasId]) charts[canvasId].destroy();
  let realType = type, indexAxis;
  if (type === "horizontalBar") { realType = "bar"; indexAxis = "y"; }
  const opts = {
    responsive: true, indexAxis: indexAxis || "x",
    plugins: { legend: { labels: { color: "#e4e4e7", font:{size:11} } } },
  };
  if (!isPie) {
    opts.scales = {
      x: { ticks:{color:"#9ca3af",font:{size:10}}, grid:{color:"#2a2d3a"}, ...((scaleOpts||{}).x||{}) },
      y: { ticks:{color:"#9ca3af",font:{size:10}}, grid:{color:"#2a2d3a"}, ...((scaleOpts||{}).y||{}) },
    };
  }
  charts[canvasId] = new Chart(document.getElementById(canvasId), { type:realType, data:{labels,datasets}, options:opts });
}
