"""Tashkent High-End Restaurant Review Tracker — Flask application."""

from datetime import date, datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, request
from flask_cors import CORS

import config
from analytics import compute_daily_stats
from models import DailyStat, Restaurant, Review, db
from seed import seed_database


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="")
    app.config.from_object(config)
    CORS(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_database()

        # Compute stats for the last 30 days on first run
        today = date.today()
        for offset in range(30):
            compute_daily_stats(today - timedelta(days=offset))

    # --- Scheduled daily analytics -------------------------------------------
    scheduler = BackgroundScheduler(daemon=True)

    def scheduled_analytics():
        with app.app_context():
            compute_daily_stats()

    scheduler.add_job(scheduled_analytics, "cron", hour=0, minute=5)
    scheduler.start()

    # --- Routes --------------------------------------------------------------

    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    # -- Restaurants --

    @app.route("/api/restaurants")
    def list_restaurants():
        restaurants = Restaurant.query.order_by(Restaurant.name).all()
        return jsonify([r.to_dict() for r in restaurants])

    @app.route("/api/restaurants/<int:rid>")
    def get_restaurant(rid):
        r = Restaurant.query.get_or_404(rid)
        return jsonify(r.to_dict())

    @app.route("/api/restaurants", methods=["POST"])
    def add_restaurant():
        data = request.get_json()
        r = Restaurant(
            name=data["name"],
            cuisine=data["cuisine"],
            address=data["address"],
            district=data.get("district", "Tashkent"),
            phone=data.get("phone"),
        )
        db.session.add(r)
        db.session.commit()
        return jsonify(r.to_dict()), 201

    # -- Reviews --

    @app.route("/api/reviews")
    def list_reviews():
        restaurant_id = request.args.get("restaurant_id", type=int)
        limit = request.args.get("limit", 50, type=int)
        q = Review.query.order_by(Review.created_at.desc())
        if restaurant_id:
            q = q.filter_by(restaurant_id=restaurant_id)
        reviews = q.limit(limit).all()
        return jsonify([r.to_dict() for r in reviews])

    @app.route("/api/reviews", methods=["POST"])
    def add_review():
        data = request.get_json()
        review = Review(
            restaurant_id=data["restaurant_id"],
            reviewer_name=data["reviewer_name"],
            rating=int(data["rating"]),
            bill_amount=float(data["bill_amount"]),
            comment=data.get("comment", ""),
            visit_date=date.fromisoformat(data["visit_date"]),
        )
        db.session.add(review)
        db.session.commit()

        # Re-compute stats for that day
        compute_daily_stats(review.visit_date)

        return jsonify(review.to_dict()), 201

    # -- Daily Stats / Analytics --

    @app.route("/api/stats/daily")
    def daily_stats():
        restaurant_id = request.args.get("restaurant_id", type=int)
        days = request.args.get("days", 30, type=int)
        start = date.today() - timedelta(days=days)

        q = DailyStat.query.filter(DailyStat.date >= start).order_by(DailyStat.date.desc())
        if restaurant_id:
            q = q.filter_by(restaurant_id=restaurant_id)
        stats = q.all()
        return jsonify([s.to_dict() for s in stats])

    @app.route("/api/stats/summary")
    def summary_stats():
        """Overall summary across all restaurants."""
        days = request.args.get("days", 30, type=int)
        start = date.today() - timedelta(days=days)

        stats = DailyStat.query.filter(DailyStat.date >= start).all()

        if not stats:
            return jsonify({"total_reviews": 0, "avg_bill": 0, "avg_rating": 0})

        total_reviews = sum(s.review_count for s in stats)
        weighted_bill = sum(s.avg_bill * s.review_count for s in stats)
        weighted_rating = sum(s.avg_rating * s.review_count for s in stats)

        return jsonify({
            "total_reviews": total_reviews,
            "avg_bill": round(weighted_bill / total_reviews, 2) if total_reviews else 0,
            "avg_rating": round(weighted_rating / total_reviews, 2) if total_reviews else 0,
            "restaurants_tracked": len({s.restaurant_id for s in stats}),
            "period_days": days,
        })

    @app.route("/api/stats/recompute", methods=["POST"])
    def recompute():
        """Manually trigger analytics recomputation."""
        days = request.json.get("days", 1) if request.json else 1
        today = date.today()
        count = 0
        for offset in range(days):
            count += compute_daily_stats(today - timedelta(days=offset))
        return jsonify({"recomputed_restaurants": count, "days": days})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
