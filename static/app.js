const API = "";

// ── Helpers ──────────────────────────────────────────────────────────────────
function fmt(n) {
  return Number(n).toLocaleString("uz-UZ");
}

async function fetchJSON(url) {
  const res = await fetch(API + url);
  return res.json();
}

async function postJSON(url, body) {
  const res = await fetch(API + url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

// ── State ────────────────────────────────────────────────────────────────────
let restaurants = [];
let billChart = null;
let ratingChart = null;

// ── Bootstrap ────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
  restaurants = await fetchJSON("/api/restaurants");
  populateSelects();
  await Promise.all([loadSummary(), loadStats(), loadReviews()]);

  document.getElementById("restaurantSelect").addEventListener("change", () => {
    loadStats();
    loadReviews();
  });

  document.getElementById("recomputeBtn").addEventListener("click", async () => {
    await postJSON("/api/stats/recompute", { days: 30 });
    await Promise.all([loadSummary(), loadStats()]);
  });

  document.getElementById("reviewForm").addEventListener("submit", submitReview);

  // Set default date to today
  document.getElementById("revDate").valueAsDate = new Date();
});

function populateSelects() {
  const sel = document.getElementById("restaurantSelect");
  const revSel = document.getElementById("revRestaurant");
  restaurants.forEach((r) => {
    sel.innerHTML += `<option value="${r.id}">${r.name}</option>`;
    revSel.innerHTML += `<option value="${r.id}">${r.name}</option>`;
  });
}

// ── Summary ──────────────────────────────────────────────────────────────────
async function loadSummary() {
  const s = await fetchJSON("/api/stats/summary?days=30");
  document.getElementById("totalReviews").textContent = fmt(s.total_reviews);
  document.getElementById("avgBill").textContent = fmt(s.avg_bill);
  document.getElementById("avgRating").textContent = (s.avg_rating || 0).toFixed(1);
  document.getElementById("restaurantCount").textContent = s.restaurants_tracked || 0;
}

// ── Daily stats table + charts ───────────────────────────────────────────────
async function loadStats() {
  const rid = document.getElementById("restaurantSelect").value;
  const url = rid ? `/api/stats/daily?days=30&restaurant_id=${rid}` : "/api/stats/daily?days=30";
  const stats = await fetchJSON(url);

  // Table
  const tbody = document.querySelector("#statsTable tbody");
  tbody.innerHTML = "";
  stats.forEach((s) => {
    tbody.innerHTML += `<tr>
      <td>${s.date}</td>
      <td>${s.restaurant_name}</td>
      <td>${s.review_count}</td>
      <td>${fmt(s.avg_bill)}</td>
      <td>${fmt(s.min_bill)}</td>
      <td>${fmt(s.max_bill)}</td>
      <td>${s.avg_rating.toFixed(1)}</td>
    </tr>`;
  });

  // Aggregate per date for charts
  const byDate = {};
  stats.forEach((s) => {
    if (!byDate[s.date]) byDate[s.date] = { bills: [], ratings: [], counts: [] };
    byDate[s.date].bills.push(s.avg_bill * s.review_count);
    byDate[s.date].ratings.push(s.avg_rating * s.review_count);
    byDate[s.date].counts.push(s.review_count);
  });

  const dates = Object.keys(byDate).sort();
  const avgBills = dates.map((d) => {
    const total = byDate[d].bills.reduce((a, b) => a + b, 0);
    const count = byDate[d].counts.reduce((a, b) => a + b, 0);
    return count ? Math.round(total / count) : 0;
  });
  const avgRatings = dates.map((d) => {
    const total = byDate[d].ratings.reduce((a, b) => a + b, 0);
    const count = byDate[d].counts.reduce((a, b) => a + b, 0);
    return count ? +(total / count).toFixed(2) : 0;
  });

  renderBillChart(dates, avgBills);
  renderRatingChart(dates, avgRatings);
}

function renderBillChart(labels, data) {
  if (billChart) billChart.destroy();
  billChart = new Chart(document.getElementById("billChart"), {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Avg Bill (UZS)",
          data,
          borderColor: "#6c63ff",
          backgroundColor: "rgba(108,99,255,0.1)",
          fill: true,
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        x: { ticks: { color: "#9ca3af" }, grid: { color: "#2a2d3a" } },
        y: { ticks: { color: "#9ca3af" }, grid: { color: "#2a2d3a" } },
      },
      plugins: { legend: { labels: { color: "#e4e4e7" } } },
    },
  });
}

function renderRatingChart(labels, data) {
  if (ratingChart) ratingChart.destroy();
  ratingChart = new Chart(document.getElementById("ratingChart"), {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Avg Rating",
          data,
          backgroundColor: "rgba(251,191,36,0.6)",
          borderColor: "#fbbf24",
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        x: { ticks: { color: "#9ca3af" }, grid: { color: "#2a2d3a" } },
        y: { min: 0, max: 5, ticks: { color: "#9ca3af" }, grid: { color: "#2a2d3a" } },
      },
      plugins: { legend: { labels: { color: "#e4e4e7" } } },
    },
  });
}

// ── Reviews ──────────────────────────────────────────────────────────────────
async function loadReviews() {
  const rid = document.getElementById("restaurantSelect").value;
  const url = rid ? `/api/reviews?limit=20&restaurant_id=${rid}` : "/api/reviews?limit=20";
  const reviews = await fetchJSON(url);

  const container = document.getElementById("reviewsList");
  container.innerHTML = "";
  reviews.forEach((r) => {
    container.innerHTML += `
      <div class="review-card">
        <div class="rc-header">
          <span class="rc-name">${r.reviewer_name}</span>
          <span class="rc-rating">${"★".repeat(r.rating)}${"☆".repeat(5 - r.rating)}</span>
        </div>
        <div class="rc-meta">${r.restaurant_name} &middot; ${r.visit_date} &middot; ${fmt(r.bill_amount)} UZS</div>
        <div class="rc-comment">${r.comment}</div>
      </div>`;
  });
}

// ── Submit review ────────────────────────────────────────────────────────────
async function submitReview(e) {
  e.preventDefault();
  const body = {
    restaurant_id: +document.getElementById("revRestaurant").value,
    reviewer_name: document.getElementById("revName").value,
    rating: +document.getElementById("revRating").value,
    bill_amount: +document.getElementById("revBill").value,
    visit_date: document.getElementById("revDate").value,
    comment: document.getElementById("revComment").value,
  };
  await postJSON("/api/reviews", body);
  document.getElementById("formMsg").textContent = "Review submitted! Stats updated.";
  document.getElementById("reviewForm").reset();
  document.getElementById("revDate").valueAsDate = new Date();
  await Promise.all([loadSummary(), loadStats(), loadReviews()]);
}
