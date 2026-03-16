const API = "";
const COLORS = ["#6c63ff","#fbbf24","#34d399","#f87171","#60a5fa","#a78bfa","#fb923c","#38bdf8","#e879f9","#4ade80","#f472b6","#facc15"];

// ── Helpers ──────────────────────────────────────────────────────────────────
const fmt = n => Number(n).toLocaleString("uz-UZ");
const fetchJSON = url => fetch(API + url).then(r => r.json());
const postJSON = (url, body) => fetch(API + url, {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}).then(r => r.json());

// ── State ────────────────────────────────────────────────────────────────────
let restaurants = [];
let charts = {};

// ── Bootstrap ────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
  restaurants = await fetchJSON("/api/restaurants");
  setupTabs();
  populateAllSelects();
  loadPriceCompareDropdowns();

  // Event listeners
  document.getElementById("dashRestaurant").addEventListener("change", loadDashboard);
  document.getElementById("recomputeBtn").addEventListener("click", async () => {
    await postJSON("/api/stats/recompute", {days: 30});
    loadDashboard();
  });
  document.getElementById("pcCategory").addEventListener("change", loadPriceCompareDishes);
  document.getElementById("pcSearchBtn").addEventListener("click", runPriceCompare);
  document.getElementById("pcDish").addEventListener("change", runPriceCompare);
  document.getElementById("reviewForm").addEventListener("submit", submitReview);
  document.getElementById("menuForm").addEventListener("submit", submitMenuItem);
  document.getElementById("revFilterRestaurant").addEventListener("change", loadReviews);
  document.getElementById("revDate").valueAsDate = new Date();
  document.getElementById("restSegmentFilter").addEventListener("change", renderRestaurantTable);
  document.getElementById("restDistrictFilter").addEventListener("change", renderRestaurantTable);
});

// ═══════════════════════════════════════════════════════════════════════════════
//  TABS
// ═══════════════════════════════════════════════════════════════════════════════
function setupTabs() {
  document.querySelectorAll(".tab").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("tab-" + btn.dataset.tab).classList.add("active");

      // Lazy-load tab data
      if (btn.dataset.tab === "dashboard") loadDashboard();
      if (btn.dataset.tab === "market") loadMarketAnalytics();
      if (btn.dataset.tab === "restaurants") renderRestaurantTable();
      if (btn.dataset.tab === "reviews") loadReviews();
    });
  });
}

function populateAllSelects() {
  const selectors = ["dashRestaurant", "revRestaurant", "mfRestaurant", "revFilterRestaurant"];
  selectors.forEach(id => {
    const el = document.getElementById(id);
    restaurants.forEach(r => {
      el.innerHTML += `<option value="${r.id}">${r.name}</option>`;
    });
  });
  // District filter
  const districts = [...new Set(restaurants.map(r => r.district))].sort();
  const df = document.getElementById("restDistrictFilter");
  districts.forEach(d => { df.innerHTML += `<option value="${d}">${d}</option>`; });
}

// ═══════════════════════════════════════════════════════════════════════════════
//  TAB 1: DASHBOARD
// ═══════════════════════════════════════════════════════════════════════════════
async function loadDashboard() {
  const rid = document.getElementById("dashRestaurant").value;
  const [summary, stats, ranking] = await Promise.all([
    fetchJSON("/api/stats/summary?days=30"),
    fetchJSON(rid ? `/api/stats/daily?days=30&restaurant_id=${rid}` : "/api/stats/daily?days=30"),
    fetchJSON("/api/analytics/ranking?days=30"),
  ]);

  // Summary cards
  document.getElementById("totalReviews").textContent = fmt(summary.total_reviews);
  document.getElementById("avgBill").textContent = fmt(summary.avg_bill);
  document.getElementById("avgRating").textContent = (summary.avg_rating || 0).toFixed(1);
  document.getElementById("restaurantCount").textContent = summary.restaurants_tracked || 0;

  // Charts
  const byDate = {};
  stats.forEach(s => {
    if (!byDate[s.date]) byDate[s.date] = {bills:[], ratings:[], counts:[]};
    byDate[s.date].bills.push(s.avg_bill * s.review_count);
    byDate[s.date].ratings.push(s.avg_rating * s.review_count);
    byDate[s.date].counts.push(s.review_count);
  });
  const dates = Object.keys(byDate).sort();
  const avgBills = dates.map(d => { const t=byDate[d].bills.reduce((a,b)=>a+b,0); const c=byDate[d].counts.reduce((a,b)=>a+b,0); return c?Math.round(t/c):0; });
  const avgRatings = dates.map(d => { const t=byDate[d].ratings.reduce((a,b)=>a+b,0); const c=byDate[d].counts.reduce((a,b)=>a+b,0); return c?+(t/c).toFixed(2):0; });

  renderChart("billChart", "line", dates, [{label:"Avg Bill (UZS)",data:avgBills,borderColor:"#6c63ff",backgroundColor:"rgba(108,99,255,.1)",fill:true,tension:.3}], {});
  renderChart("ratingChart", "bar", dates, [{label:"Avg Rating",data:avgRatings,backgroundColor:"rgba(251,191,36,.6)",borderColor:"#fbbf24",borderWidth:1}], {y:{min:0,max:5}});

  // Ranking table
  const tbody = document.querySelector("#rankingTable tbody");
  tbody.innerHTML = "";
  ranking.forEach((r, i) => {
    tbody.innerHTML += `<tr>
      <td>${i+1}</td><td><strong>${r.name}</strong></td><td>${r.cuisine}</td>
      <td><span class="segment-badge seg-${r.price_segment.toLowerCase().replace(/\s/g,'')}">${r.price_segment}</span></td>
      <td>${r.district}</td><td>${fmt(r.total_reviews)}</td>
      <td>${fmt(r.avg_bill)}</td><td>${r.avg_rating.toFixed(1)}</td>
    </tr>`;
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
//  TAB 2: PRICE COMPARISON
// ═══════════════════════════════════════════════════════════════════════════════
async function loadPriceCompareDropdowns() {
  const categories = await fetchJSON("/api/menu/categories");
  const catSel = document.getElementById("pcCategory");
  categories.forEach(c => { catSel.innerHTML += `<option value="${c}">${c}</option>`; });
  await loadPriceCompareDishes();
}

async function loadPriceCompareDishes() {
  const cat = document.getElementById("pcCategory").value;
  const url = cat ? `/api/menu/items?category=${encodeURIComponent(cat)}` : "/api/menu/items";
  const items = await fetchJSON(url);
  const sel = document.getElementById("pcDish");
  sel.innerHTML = '<option value="">— Select a dish —</option>';
  items.forEach(name => { sel.innerHTML += `<option value="${name}">${name}</option>`; });
}

async function runPriceCompare() {
  const dish = document.getElementById("pcDish").value;
  const cat = document.getElementById("pcCategory").value;
  if (!dish) return;

  let url = `/api/menu/compare?dish=${encodeURIComponent(dish)}`;
  if (cat) url += `&category=${encodeURIComponent(cat)}`;
  const data = await fetchJSON(url);

  if (!data.results || !data.results.length) {
    document.getElementById("pcSummary").style.display = "none";
    document.getElementById("pcChartSection").style.display = "none";
    document.getElementById("pcTableSection").style.display = "none";
    return;
  }

  // Summary cards
  document.getElementById("pcSummary").style.display = "grid";
  document.getElementById("pcCount").textContent = data.total_restaurants;
  document.getElementById("pcAvg").textContent = fmt(data.avg_price) + " UZS";
  document.getElementById("pcMin").textContent = fmt(data.min_price) + " UZS";
  document.getElementById("pcMax").textContent = fmt(data.max_price) + " UZS";

  // Segment averages
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

  renderChart("priceCompareChart", "bar", labels, [{
    label: "Price (UZS)", data: prices, backgroundColor: colors, borderWidth: 0,
  }], {y:{beginAtZero:true}}, true);

  // Table
  document.getElementById("pcTableSection").style.display = "block";
  const tbody = document.querySelector("#pcTable tbody");
  tbody.innerHTML = "";
  data.results.forEach(r => {
    const diff = r.price - data.avg_price;
    const pct = data.avg_price ? ((diff / data.avg_price) * 100).toFixed(1) : 0;
    const cls = diff > 0 ? "diff-negative" : "diff-positive";
    const sign = diff > 0 ? "+" : "";
    tbody.innerHTML += `<tr>
      <td><strong>${r.restaurant_name}</strong></td>
      <td>${r.restaurant_segment}</td>
      <td>${fmt(r.price)}</td>
      <td class="${cls}">${sign}${fmt(diff)} (${sign}${pct}%)</td>
      <td>${r.description || "—"}</td>
    </tr>`;
  });
}

// ═══════════════════════════════════════════════════════════════════════════════
//  TAB 3: MARKET ANALYTICS
// ═══════════════════════════════════════════════════════════════════════════════
async function loadMarketAnalytics() {
  const [segments, cuisines, districts] = await Promise.all([
    fetchJSON("/api/analytics/segments"),
    fetchJSON("/api/analytics/cuisines"),
    fetchJSON("/api/analytics/districts"),
  ]);

  // Segment charts
  renderChart("segmentBillChart", "bar",
    segments.map(s=>s.segment),
    [{label:"Avg Bill",data:segments.map(s=>s.avg_bill),backgroundColor:["#34d399","#6c63ff","#f87171"]}],
    {y:{beginAtZero:true}});
  renderChart("segmentRatingChart", "bar",
    segments.map(s=>s.segment),
    [{label:"Avg Rating",data:segments.map(s=>s.avg_rating),backgroundColor:["#34d399","#6c63ff","#f87171"]}],
    {y:{min:0,max:5}});

  // District chart
  renderChart("districtChart", "doughnut",
    districts.map(d=>d.district),
    [{data:districts.map(d=>d.restaurant_count),backgroundColor:COLORS}], {}, false, true);

  // Cuisine chart (top 12)
  const topCuisines = cuisines.slice(0, 12);
  renderChart("cuisineChart", "horizontalBar",
    topCuisines.map(c=>c.cuisine),
    [{label:"Avg Bill",data:topCuisines.map(c=>c.avg_bill),backgroundColor:COLORS.slice(0,12)}],
    {x:{beginAtZero:true}});

  // Tables
  fillTable("#segmentTable tbody", segments, ["segment","restaurant_count","avg_bill","avg_rating"]);
  fillTable("#districtTable tbody", districts, ["district","restaurant_count","avg_bill","avg_rating"]);
  fillTable("#cuisineTable tbody", cuisines, ["cuisine","restaurant_count","avg_bill","avg_rating"]);
}

function fillTable(sel, data, keys) {
  const tbody = document.querySelector(sel);
  tbody.innerHTML = "";
  data.forEach(row => {
    tbody.innerHTML += "<tr>" + keys.map(k => {
      let v = row[k];
      if (typeof v === "number" && k.includes("bill")) v = fmt(v);
      if (typeof v === "number" && k.includes("rating")) v = v.toFixed(1);
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
  reviews.forEach(r => {
    container.innerHTML += `
      <div class="review-card">
        <div class="rc-header">
          <span class="rc-name">${r.reviewer_name}</span>
          <span class="rc-rating">${"★".repeat(r.rating)}${"☆".repeat(5-r.rating)}</span>
        </div>
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
  document.getElementById("reviewFormMsg").textContent = "Review submitted! Stats updated.";
  document.getElementById("reviewForm").reset();
  document.getElementById("revDate").valueAsDate = new Date();
  loadReviews();
  loadDashboard();
}

async function submitMenuItem(e) {
  e.preventDefault();
  await postJSON("/api/menu", {
    restaurant_id: +document.getElementById("mfRestaurant").value,
    category: document.getElementById("mfCategory").value,
    name: document.getElementById("mfName").value,
    price: +document.getElementById("mfPrice").value,
    description: document.getElementById("mfDesc").value,
  });
  document.getElementById("menuFormMsg").textContent = "Menu item added!";
  document.getElementById("menuForm").reset();
  loadPriceCompareDishes();
}

// ═══════════════════════════════════════════════════════════════════════════════
//  CHART HELPER
// ═══════════════════════════════════════════════════════════════════════════════
function renderChart(canvasId, type, labels, datasets, scaleOpts, horizontal, isPie) {
  if (charts[canvasId]) charts[canvasId].destroy();

  let realType = type;
  let indexAxis;
  if (type === "horizontalBar") { realType = "bar"; indexAxis = "y"; }

  const opts = {
    responsive: true,
    indexAxis: indexAxis || "x",
    scales: isPie ? {} : {},
    plugins: { legend: { labels: { color: "#e4e4e7", font:{size:11} } } },
  };

  if (!isPie) {
    opts.scales = {
      x: { ticks:{color:"#9ca3af",font:{size:10}}, grid:{color:"#2a2d3a"}, ...((scaleOpts||{}).x||{}) },
      y: { ticks:{color:"#9ca3af",font:{size:10}}, grid:{color:"#2a2d3a"}, ...((scaleOpts||{}).y||{}) },
    };
  }

  charts[canvasId] = new Chart(document.getElementById(canvasId), {
    type: realType, data: { labels, datasets }, options: opts,
  });
}
