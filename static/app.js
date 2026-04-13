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
  document.getElementById("reviewForm").addEventListener("submit", submitReview);
  document.getElementById("revFilterRestaurant").addEventListener("change", loadReviews);
  document.getElementById("restSegmentFilter").addEventListener("change", renderRestaurantTable);
  document.getElementById("restDistrictFilter").addEventListener("change", renderRestaurantTable);

  document.getElementById("mfDate").valueAsDate = new Date();
  document.getElementById("revDate").valueAsDate = new Date();
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
      if (btn.dataset.tab === "reviews") loadReviews();
    });
  });
}

function populateAllSelects() {
  ["mfRestaurant","browseRestaurant","revRestaurant","revFilterRestaurant"].forEach(id => {
    const el = document.getElementById(id);
    restaurants.forEach(r => { el.innerHTML += `<option value="${r.id}">${r.name}</option>`; });
  });
  const districts = [...new Set(restaurants.map(r => r.district))].sort();
  const df = document.getElementById("restDistrictFilter");
  districts.forEach(d => { df.innerHTML += `<option value="${d}">${d}</option>`; });
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
    tbody.innerHTML = '<tr><td colspan="7" class="empty-cell">No price changes yet</td></tr>';
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
  msg.textContent = "Item added!";
  setTimeout(() => msg.textContent = "", 3000);
  document.getElementById("mfCategory").value = "";
  document.getElementById("mfName").value = "";
  document.getElementById("mfPrice").value = "";
  document.getElementById("mfDesc").value = "";
  loadMenuManagement();
  // Refresh browse if same restaurant
  const browseRid = document.getElementById("browseRestaurant").value;
  if (browseRid) browseMenu();
}

async function uploadCSV() {
  const fileInput = document.getElementById("csvFile");
  const msg = document.getElementById("csvMsg");
  if (!fileInput.files.length) { msg.textContent = "Select a CSV file first"; return; }
  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  const res = await fetch(API + "/api/menu/csv", {method: "POST", body: formData});
  const data = await res.json();
  msg.textContent = `Uploaded: ${data.added} items added.`;
  if (data.skipped && data.skipped.length) {
    msg.textContent += ` Skipped: ${data.skipped.join(", ")}`;
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
    area.innerHTML = '<p class="hint">No menu items entered for this restaurant yet. Add items above or upload a CSV.</p>';
    return;
  }

  // Group by category
  const cats = {};
  items.forEach(m => { (cats[m.category] = cats[m.category] || []).push(m); });

  let html = '<div class="table-scroll"><table><thead><tr><th>Category</th><th>Dish</th><th>Price (UZS)</th><th>Collected</th><th>By</th><th>Actions</th></tr></thead><tbody>';
  for (const [cat, list] of Object.entries(cats)) {
    list.forEach(m => {
      html += `<tr data-id="${m.id}">
        <td>${m.category}</td>
        <td><strong>${m.name}</strong><br><small class="muted">${m.description || ""}</small></td>
        <td><input type="number" class="inline-price" value="${m.price}" data-id="${m.id}" min="0" style="width:110px" /></td>
        <td>${m.collected_date || "—"}</td>
        <td>${m.collected_by || "—"}</td>
        <td>
          <button class="btn-sm btn-save" onclick="savePrice(${m.id}, this)">Save</button>
          <button class="btn-sm btn-del" onclick="deleteItem(${m.id})">Del</button>
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
  btn.textContent = "Saved!";
  setTimeout(() => { btn.textContent = "Save"; }, 1500);
  loadMenuManagement();
}

async function deleteItem(id) {
  await deleteJSON(`/api/menu/${id}`);
  browseMenu();
  loadMenuManagement();
}

// ═══════════════════════════════════════════════════════════════════════════════
//  TAB 2: PRICE COMPARISON
// ═══════════════════════════════════════════════════════════════════════════════
async function loadPriceCompareTab() {
  const categories = await fetchJSON("/api/menu/categories");
  const catSel = document.getElementById("pcCategory");
  catSel.innerHTML = '<option value="">All</option>';
  categories.forEach(c => { catSel.innerHTML += `<option value="${c}">${c}</option>`; });
  await loadPCDishes();
}

async function loadPCDishes() {
  const cat = document.getElementById("pcCategory").value;
  const url = cat ? `/api/menu/items?category=${encodeURIComponent(cat)}` : "/api/menu/items";
  const items = await fetchJSON(url);
  const sel = document.getElementById("pcDish");
  sel.innerHTML = '<option value="">— Select a dish —</option>';
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

  // Summary
  document.getElementById("pcSummary").style.display = "grid";
  document.getElementById("pcCoverage").textContent = `${data.restaurants_with_data} / ${data.total_restaurants} (${data.coverage_pct}%)`;
  document.getElementById("pcAvg").textContent = fmt(data.avg_price) + " UZS";
  document.getElementById("pcMin").textContent = fmt(data.min_price) + " UZS";
  document.getElementById("pcMax").textContent = fmt(data.max_price) + " UZS";

  // Segment cards
  const segDiv = document.getElementById("pcSegments");
  segDiv.innerHTML = "";
  segDiv.style.display = "grid";
  for (const [seg, avg] of Object.entries(data.segment_averages)) {
    segDiv.innerHTML += `<div class="card"><span class="card-label">${seg} Avg</span><span class="card-value">${fmt(avg)} UZS</span></div>`;
  }

  // Chart
  document.getElementById("pcChartSection").style.display = "grid";
  document.getElementById("pcChartTitle").textContent = `${dish} — Price by Restaurant`;
  const labels = data.results.map(r => r.restaurant_name);
  const prices = data.results.map(r => r.price);
  const colors = data.results.map(r => {
    if (r.restaurant_segment === "Luxury") return "#f87171";
    if (r.restaurant_segment === "Premium") return "#6c63ff";
    return "#34d399";
  });
  renderChart("priceCompareChart", "bar", labels, [{label:"Price (UZS)", data:prices, backgroundColor:colors, borderWidth:0}], {y:{beginAtZero:true}});

  // Table
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
      [{label:"Avg Menu Price",data:segsWithData.map(s => s.avg_menu_price),backgroundColor:["#34d399","#6c63ff","#f87171"]}],
      {y:{beginAtZero:true}});
    renderChart("districtChart", "doughnut",
      districts.map(d => d.district),
      [{data:districts.map(d => d.restaurant_count),backgroundColor:COLORS}],{},false,true);
  }

  // Ranking
  const rtbody = document.querySelector("#rankingTable tbody");
  rtbody.innerHTML = "";
  ranking.forEach((r, i) => {
    rtbody.innerHTML += `<tr>
      <td>${i+1}</td><td><strong>${r.name}</strong></td><td>${r.cuisine}</td>
      <td>${r.price_segment}</td><td>${r.district}</td>
      <td>${r.menu_items > 0 ? r.menu_items : '<span class="muted">none</span>'}</td>
      <td>${r.avg_menu_price > 0 ? fmt(r.avg_menu_price) : '<span class="muted">—</span>'}</td>
    </tr>`;
  });

  // Tables
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
    </tr>`;
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
//  TAB 5: REVIEWS
// ═══════════════════════════════════════════════════════════════════════════════
async function loadReviews() {
  const rid = document.getElementById("revFilterRestaurant").value;
  const url = rid ? `/api/reviews?limit=30&restaurant_id=${rid}` : "/api/reviews?limit=30";
  const reviews = await fetchJSON(url);
  const container = document.getElementById("reviewsList");
  container.innerHTML = "";
  if (!reviews.length) { container.innerHTML = '<p class="hint">No reviews yet. Submit one above.</p>'; return; }
  reviews.forEach(r => {
    container.innerHTML += `
      <div class="review-card">
        <div class="rc-header"><span class="rc-name">${r.reviewer_name}</span><span class="rc-rating">${"★".repeat(r.rating)}${"☆".repeat(5-r.rating)}</span></div>
        <div class="rc-meta">${r.restaurant_name} &middot; ${r.visit_date} &middot; ${fmt(r.bill_amount)} UZS</div>
        <div class="rc-comment">${r.comment}</div>
      </div>`;
  });
}

async function submitReview(e) {
  e.preventDefault();
  await postJSON("/api/reviews", {
    restaurant_id: +document.getElementById("revRestaurant").value,
    reviewer_name: document.getElementById("revName").value,
    rating: +document.getElementById("revRating").value,
    bill_amount: +document.getElementById("revBill").value,
    visit_date: document.getElementById("revDate").value,
    comment: document.getElementById("revComment").value,
  });
  document.getElementById("reviewFormMsg").textContent = "Review submitted!";
  document.getElementById("reviewForm").reset();
  document.getElementById("revDate").valueAsDate = new Date();
  loadReviews();
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
