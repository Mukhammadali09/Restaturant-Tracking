const API = "";
const COLORS = ["#6c63ff","#fbbf24","#34d399","#f87171","#60a5fa","#a78bfa","#fb923c","#38bdf8","#e879f9","#4ade80","#f472b6","#facc15"];
const fmt = n => Number(n).toLocaleString("uz-UZ");
const fetchJSON = url => fetch(API + url).then(r => r.json());
const postJSON = (url, body) => fetch(API + url, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}).then(r => r.json());
const putJSON = (url, body) => fetch(API + url, {method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}).then(r => r.json());
const deleteJSON = url => fetch(API + url, {method:"DELETE"}).then(r => r.json());

let restaurants = [];
let charts = {};

// ═══════════════════════════════════════════════════════════════════════════════
//  BOOTSTRAP
// ═══════════════════════════════════════════════════════════════════════════════
document.addEventListener("DOMContentLoaded", async () => {
  restaurants = await fetchJSON("/api/restaurants");
  applyLanguage();
  setupTabs();
  populateAllSelects();

  // Default tab: Menu Management
  loadMenuManagement();

  // Event listeners
  document.getElementById("menuForm").addEventListener("submit", submitMenuItem);
  document.getElementById("csvUploadBtn").addEventListener("click", uploadCSV);
  document.getElementById("browseRestaurant").addEventListener("change", browseMenu);
  document.getElementById("pcCategory").addEventListener("change", loadPCDishes);
  document.getElementById("pcSearchBtn").addEventListener("click", runPriceCompare);
  document.getElementById("pcDish").addEventListener("change", runPriceCompare);
  document.getElementById("restSegmentFilter").addEventListener("change", renderRestaurantTable);
  document.getElementById("restDistrictFilter").addEventListener("change", renderRestaurantTable);
  document.getElementById("addRestaurantForm").addEventListener("submit", addRestaurant);
  document.getElementById("ocrUploadBtn").addEventListener("click", ocrUpload);

  document.getElementById("mfDate").valueAsDate = new Date();
});

function setupTabs() {
  document.querySelectorAll(".tab").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
      if (btn.dataset.tab === "menu-mgmt") loadMenuManagement();
      if (btn.dataset.tab === "price-compare") loadPriceCompareTab();
      if (btn.dataset.tab === "market") loadMarketAnalytics();
      if (btn.dataset.tab === "restaurants") renderRestaurantTable();
    });
  });
}

function populateAllSelects() {
  ["mfRestaurant","browseRestaurant","ocrRestaurant"].forEach(id => {
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
  const res = await fetch(API + "/api/menu/csv", {method: "POST", body: formData});
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

  status.textContent = t("msg_scanning") + (files.length > 1 ? ` (1/${files.length})` : "");
  status.style.color = "var(--gold)";

  let totalSaved = 0;
  let allRawText = "";
  let errors = [];
  let lastMethod = "";
  let lastClaudeError = "";

  for (let i = 0; i < files.length; i++) {
    if (files.length > 1) {
      status.textContent = t("msg_scanning") + ` (${i + 1}/${files.length})`;
    }
    const formData = new FormData();
    formData.append("file", files[i]);
    formData.append("language", lang);
    formData.append("restaurant_id", rid);
    formData.append("collected_by", by);

    try {
      const res = await fetch(API + "/api/menu/ocr", {method: "POST", body: formData});
      const data = await res.json();

      if (data.error) {
        errors.push(`${files[i].name}: ${data.error}`);
        continue;
      }

      totalSaved += data.saved || 0;
      allRawText += (allRawText ? "\n\n--- " + files[i].name + " ---\n\n" : "") + (data.raw_text || "");
      lastMethod = data.method || "unknown";
      if (data.claude_error) lastClaudeError = data.claude_error;
    } catch (e) {
      errors.push(`${files[i].name}: ${e.message}`);
    }
  }

  if (errors.length && totalSaved === 0) {
    status.textContent = errors.join("; ");
    status.style.color = "var(--red)";
    return;
  }

  // Show raw text for debugging
  if (allRawText) {
    document.getElementById("ocrRawText").textContent = allRawText;
    document.getElementById("ocrRawDetails").style.display = "block";
  }

  // Build success message with method indicator
  const restName = document.querySelector(`#ocrRestaurant option[value="${rid}"]`)?.textContent || "";
  const methodLabel = lastMethod === "claude_vision" ? "AI Vision" : "OCR";
  let msg = t("msg_ocr_saved", totalSaved, restName) + ` [${methodLabel}]`;
  if (lastClaudeError && lastMethod !== "claude_vision") {
    msg += ` | Claude Vision error: ${lastClaudeError}`;
  }
  if (errors.length) msg += " | " + errors.join("; ");
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
//  TAB 2: PRICE COMPARISON
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
//  TAB 3: MARKET ANALYTICS
// ═══════════════════════════════════════════════════════════════════════════════
async function loadMarketAnalytics() {
  const [segments, districts, ranking] = await Promise.all([
    fetchJSON("/api/analytics/segments"),
    fetchJSON("/api/analytics/districts"),
    fetchJSON("/api/analytics/ranking"),
  ]);

  const hasData = segments.some(s => s.menu_items_entered > 0);
  document.getElementById("marketEmpty").style.display = hasData ? "none" : "block";
  document.getElementById("marketCharts").style.display = hasData ? "grid" : "none";

  if (hasData) {
    const segsWithData = segments.filter(s => s.avg_menu_price > 0);
    renderChart("segmentChart", "bar",
      segsWithData.map(s => s.segment),
      [{label:t("chart_avg_label"),data:segsWithData.map(s => s.avg_menu_price),backgroundColor:["#34d399","#6c63ff","#f87171"]}],
      {y:{beginAtZero:true}});
    renderChart("districtChart", "doughnut",
      districts.map(d => d.district),
      [{data:districts.map(d => d.restaurant_count),backgroundColor:COLORS}],{},false,true);
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

  ["mfRestaurant","browseRestaurant","ocrRestaurant"].forEach(id => {
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

  ["mfRestaurant","browseRestaurant","ocrRestaurant"].forEach(sid => {
    const opt = document.querySelector(`#${sid} option[value="${id}"]`);
    if (opt) opt.remove();
  });

  renderRestaurantTable();
  loadMenuManagement();
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
