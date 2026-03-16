# Tashkent High-End Restaurant Review Tracker

A web portal that tracks reviews for high-end restaurants in Tashkent, automatically analyzing average bill amounts with daily statistical updates.

## Features

- **Dashboard** with summary cards (total reviews, avg bill, avg rating, restaurant count)
- **Interactive charts** — 30-day average bill trend and rating trend (Chart.js)
- **Daily auto-analytics** — scheduled job at 00:05 computes per-restaurant stats (avg/min/max bill, avg rating)
- **Real-time updates** — submitting a review instantly recomputes that day's stats
- **Filter by restaurant** — view stats and reviews per restaurant or across all
- **Manual recompute** button to refresh analytics on demand
- **Pre-seeded** with 10 popular Tashkent restaurants and 30 days of sample reviews

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000 in your browser.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/restaurants` | List all restaurants |
| POST | `/api/restaurants` | Add a restaurant |
| GET | `/api/reviews?restaurant_id=&limit=` | List reviews |
| POST | `/api/reviews` | Submit a review (triggers stat recompute) |
| GET | `/api/stats/daily?days=30&restaurant_id=` | Daily stats |
| GET | `/api/stats/summary?days=30` | Aggregate summary |
| POST | `/api/stats/recompute` | Manually trigger analytics |

## Tech Stack

- **Backend**: Flask + SQLAlchemy + SQLite
- **Frontend**: Vanilla HTML/CSS/JS + Chart.js
- **Scheduler**: APScheduler (daily cron job)
