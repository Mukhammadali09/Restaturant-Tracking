"""Tashkent High-End Restaurant Market Tracker — Flask application."""

from datetime import date, datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import func

import config
from analytics import compute_daily_stats
from models import DailyStat, MenuItem, Restaurant, Review, db
from seed import seed_database


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="")
    app.config.from_object(config)
    CORS(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_database()

    # --- Scheduled daily analytics -------------------------------------------
    scheduler = BackgroundScheduler(daemon=True)

    def scheduled_analytics():
        with app.app_context():
            compute_daily_stats()

    scheduler.add_job(scheduled_analytics, "cron", hour=0, minute=5)
    scheduler.start()

    # ═══════════════════════════════════════════════════════════════════════════
    #  ROUTES
    # ═══════════════════════════════════════════════════════════════════════════

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
            price_segment=data.get("price_segment", "Premium"),
            avg_bill_min=data.get("avg_bill_min", 0),
            avg_bill_max=data.get("avg_bill_max", 0),
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
        days = request.json.get("days", 1) if request.json else 1
        today = date.today()
        count = 0
        for offset in range(days):
            count += compute_daily_stats(today - timedelta(days=offset))
        return jsonify({"recomputed_restaurants": count, "days": days})

    # ═══════════════════════════════════════════════════════════════════════════
    #  MENU ITEMS & PRICE COMPARISON
    # ═══════════════════════════════════════════════════════════════════════════

    @app.route("/api/menu")
    def list_menu():
        """List menu items, optionally filtered by restaurant."""
        restaurant_id = request.args.get("restaurant_id", type=int)
        category = request.args.get("category")
        q = MenuItem.query.order_by(MenuItem.category, MenuItem.name)
        if restaurant_id:
            q = q.filter_by(restaurant_id=restaurant_id)
        if category:
            q = q.filter_by(category=category)
        return jsonify([m.to_dict() for m in q.all()])

    @app.route("/api/menu/categories")
    def menu_categories():
        """Get all distinct menu categories."""
        rows = db.session.query(MenuItem.category).distinct().order_by(MenuItem.category).all()
        return jsonify([r[0] for r in rows])

    @app.route("/api/menu/items")
    def menu_item_names():
        """Get distinct dish names (for autocomplete / search)."""
        category = request.args.get("category")
        q = db.session.query(MenuItem.name).distinct().order_by(MenuItem.name)
        if category:
            q = q.filter(MenuItem.category == category)
        return jsonify([r[0] for r in q.all()])

    @app.route("/api/menu", methods=["POST"])
    def add_menu_item():
        data = request.get_json()
        mi = MenuItem(
            restaurant_id=data["restaurant_id"],
            category=data["category"],
            name=data["name"],
            name_normalized=data["name"].lower().strip(),
            price=int(data["price"]),
            description=data.get("description", ""),
        )
        db.session.add(mi)
        db.session.commit()
        return jsonify(mi.to_dict()), 201

    @app.route("/api/menu/compare")
    def compare_prices():
        """
        Core price comparison tool.
        ?dish=Caesar Salad  → returns that dish's price at every restaurant that has it,
                              sorted by price, with segment info and market stats.
        ?category=Salads    → optional extra filter
        """
        dish = request.args.get("dish", "").strip()
        category = request.args.get("category", "").strip()

        if not dish:
            return jsonify({"error": "Provide ?dish= parameter"}), 400

        q = MenuItem.query.filter(MenuItem.name_normalized == dish.lower())
        if category:
            q = q.filter(MenuItem.category == category)

        items = q.order_by(MenuItem.price).all()

        if not items:
            # Fuzzy: try partial match
            q = MenuItem.query.filter(MenuItem.name_normalized.contains(dish.lower()))
            if category:
                q = q.filter(MenuItem.category == category)
            items = q.order_by(MenuItem.price).all()

        prices = [m.price for m in items]
        avg_price = round(sum(prices) / len(prices)) if prices else 0
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0

        # Group by segment
        by_segment = {}
        for m in items:
            seg = m.restaurant.price_segment if m.restaurant else "Unknown"
            by_segment.setdefault(seg, []).append(m.price)

        segment_avgs = {
            seg: round(sum(ps) / len(ps))
            for seg, ps in by_segment.items()
        }

        return jsonify({
            "dish": dish,
            "total_restaurants": len(items),
            "avg_price": avg_price,
            "min_price": min_price,
            "max_price": max_price,
            "segment_averages": segment_avgs,
            "results": [m.to_dict() for m in items],
        })

    # ═══════════════════════════════════════════════════════════════════════════
    #  MARKET ANALYTICS
    # ═══════════════════════════════════════════════════════════════════════════

    @app.route("/api/analytics/segments")
    def analytics_segments():
        """Breakdown by price segment: count, avg bill, avg rating."""
        days = request.args.get("days", 30, type=int)
        start = date.today() - timedelta(days=days)

        results = (
            db.session.query(
                Restaurant.price_segment,
                func.count(func.distinct(Restaurant.id)),
                func.avg(DailyStat.avg_bill),
                func.avg(DailyStat.avg_rating),
            )
            .join(DailyStat, DailyStat.restaurant_id == Restaurant.id)
            .filter(DailyStat.date >= start)
            .group_by(Restaurant.price_segment)
            .all()
        )

        return jsonify([
            {
                "segment": r[0],
                "restaurant_count": r[1],
                "avg_bill": round(r[2] or 0, 2),
                "avg_rating": round(r[3] or 0, 2),
            }
            for r in results
        ])

    @app.route("/api/analytics/cuisines")
    def analytics_cuisines():
        """Breakdown by cuisine type."""
        days = request.args.get("days", 30, type=int)
        start = date.today() - timedelta(days=days)

        results = (
            db.session.query(
                Restaurant.cuisine,
                func.count(func.distinct(Restaurant.id)),
                func.avg(DailyStat.avg_bill),
                func.avg(DailyStat.avg_rating),
            )
            .join(DailyStat, DailyStat.restaurant_id == Restaurant.id)
            .filter(DailyStat.date >= start)
            .group_by(Restaurant.cuisine)
            .order_by(func.avg(DailyStat.avg_bill).desc())
            .all()
        )

        return jsonify([
            {
                "cuisine": r[0],
                "restaurant_count": r[1],
                "avg_bill": round(r[2] or 0, 2),
                "avg_rating": round(r[3] or 0, 2),
            }
            for r in results
        ])

    @app.route("/api/analytics/districts")
    def analytics_districts():
        """Breakdown by district."""
        days = request.args.get("days", 30, type=int)
        start = date.today() - timedelta(days=days)

        results = (
            db.session.query(
                Restaurant.district,
                func.count(func.distinct(Restaurant.id)),
                func.avg(DailyStat.avg_bill),
                func.avg(DailyStat.avg_rating),
            )
            .join(DailyStat, DailyStat.restaurant_id == Restaurant.id)
            .filter(DailyStat.date >= start)
            .group_by(Restaurant.district)
            .order_by(func.count(func.distinct(Restaurant.id)).desc())
            .all()
        )

        return jsonify([
            {
                "district": r[0],
                "restaurant_count": r[1],
                "avg_bill": round(r[2] or 0, 2),
                "avg_rating": round(r[3] or 0, 2),
            }
            for r in results
        ])

    @app.route("/api/analytics/ranking")
    def analytics_ranking():
        """Restaurant ranking by avg rating and avg bill over period."""
        days = request.args.get("days", 30, type=int)
        start = date.today() - timedelta(days=days)

        results = (
            db.session.query(
                Restaurant.id,
                Restaurant.name,
                Restaurant.cuisine,
                Restaurant.price_segment,
                Restaurant.district,
                func.sum(DailyStat.review_count),
                func.avg(DailyStat.avg_bill),
                func.avg(DailyStat.avg_rating),
            )
            .join(DailyStat, DailyStat.restaurant_id == Restaurant.id)
            .filter(DailyStat.date >= start)
            .group_by(Restaurant.id)
            .order_by(func.avg(DailyStat.avg_rating).desc())
            .all()
        )

        return jsonify([
            {
                "id": r[0],
                "name": r[1],
                "cuisine": r[2],
                "price_segment": r[3],
                "district": r[4],
                "total_reviews": r[5],
                "avg_bill": round(r[6] or 0, 2),
                "avg_rating": round(r[7] or 0, 2),
            }
            for r in results
        ])

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
