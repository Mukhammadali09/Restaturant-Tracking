"""Tashkent High-End Restaurant Market Tracker — Flask application."""

import csv
import io
from datetime import date, datetime, timezone

from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import func

import config
from models import MenuItem, PriceHistory, Restaurant, db
from ocr import parse_menu_image
from seed import seed_database


def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="")
    app.config.from_object(config)
    CORS(app)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_database()

    # ═══════════════════════════════════════════════════════════════════════════
    #  STATIC
    # ═══════════════════════════════════════════════════════════════════════════

    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    # ═══════════════════════════════════════════════════════════════════════════
    #  RESTAURANTS
    # ═══════════════════════════════════════════════════════════════════════════

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
            name=data["name"], cuisine=data["cuisine"], address=data["address"],
            district=data.get("district", "Tashkent"), phone=data.get("phone"),
            price_segment=data.get("price_segment", "Premium"),
            avg_bill_min=data.get("avg_bill_min", 0),
            avg_bill_max=data.get("avg_bill_max", 0),
        )
        db.session.add(r)
        db.session.commit()
        return jsonify(r.to_dict()), 201

    @app.route("/api/restaurants/<int:rid>", methods=["DELETE"])
    def delete_restaurant(rid):
        r = Restaurant.query.get_or_404(rid)
        db.session.delete(r)
        db.session.commit()
        return jsonify({"deleted": rid})

    # ═══════════════════════════════════════════════════════════════════════════
    #  MENU MANAGEMENT (core of the tool)
    # ═══════════════════════════════════════════════════════════════════════════

    @app.route("/api/menu")
    def list_menu():
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
        rows = db.session.query(MenuItem.category).distinct().order_by(MenuItem.category).all()
        return jsonify([r[0] for r in rows])

    @app.route("/api/menu/items")
    def menu_item_names():
        category = request.args.get("category")
        q = db.session.query(MenuItem.name).distinct().order_by(MenuItem.name)
        if category:
            q = q.filter(MenuItem.category == category)
        return jsonify([r[0] for r in q.all()])

    @app.route("/api/menu", methods=["POST"])
    def add_menu_item():
        data = request.get_json()
        collected = data.get("collected_date")
        mi = MenuItem(
            restaurant_id=data["restaurant_id"],
            category=data["category"],
            name=data["name"],
            name_normalized=data["name"].lower().strip(),
            price=int(data["price"]),
            description=data.get("description", ""),
            collected_by=data.get("collected_by", ""),
            collected_date=date.fromisoformat(collected) if collected else date.today(),
        )
        db.session.add(mi)
        db.session.commit()
        return jsonify(mi.to_dict()), 201

    @app.route("/api/menu/<int:mid>", methods=["PUT"])
    def update_menu_item(mid):
        """Update a menu item's price. Logs the change to price_history."""
        mi = MenuItem.query.get_or_404(mid)
        data = request.get_json()
        new_price = int(data["price"])
        changed_by = data.get("collected_by", "")

        if new_price != mi.price:
            history = PriceHistory(
                menu_item_id=mi.id,
                old_price=mi.price,
                new_price=new_price,
                changed_by=changed_by,
            )
            db.session.add(history)
            mi.price = new_price

        if "category" in data:
            mi.category = data["category"]
        if "name" in data:
            mi.name = data["name"]
            mi.name_normalized = data["name"].lower().strip()
        if "description" in data:
            mi.description = data["description"]
        if "collected_by" in data:
            mi.collected_by = data["collected_by"]
        collected = data.get("collected_date")
        if collected:
            mi.collected_date = date.fromisoformat(collected)
        mi.updated_at = datetime.now(timezone.utc)

        db.session.commit()
        return jsonify(mi.to_dict())

    @app.route("/api/menu/<int:mid>", methods=["DELETE"])
    def delete_menu_item(mid):
        mi = MenuItem.query.get_or_404(mid)
        db.session.delete(mi)
        db.session.commit()
        return jsonify({"deleted": mid})

    @app.route("/api/menu/restaurant/<int:rid>", methods=["DELETE"])
    def delete_all_menu_items(rid):
        """Delete ALL menu items for a restaurant."""
        count = MenuItem.query.filter_by(restaurant_id=rid).delete()
        db.session.commit()
        return jsonify({"deleted": count, "restaurant_id": rid})

    @app.route("/api/menu/bulk", methods=["POST"])
    def bulk_add_menu():
        """Add multiple menu items at once. Expects JSON array of items."""
        items = request.get_json()
        if not isinstance(items, list):
            return jsonify({"error": "Expected a JSON array"}), 400
        added = 0
        for data in items:
            collected = data.get("collected_date")
            mi = MenuItem(
                restaurant_id=data["restaurant_id"],
                category=data.get("category", "Uncategorized"),
                name=data["name"],
                name_normalized=data["name"].lower().strip(),
                price=int(data["price"]),
                description=data.get("description", ""),
                collected_by=data.get("collected_by", ""),
                collected_date=date.fromisoformat(collected) if collected else date.today(),
            )
            db.session.add(mi)
            added += 1
        db.session.commit()
        return jsonify({"added": added})

    @app.route("/api/menu/csv", methods=["POST"])
    def csv_upload_menu():
        """
        Upload menu data via CSV. Expected columns:
        restaurant_name, category, dish_name, price, description, collected_by
        """
        if "file" not in request.files:
            raw = request.get_data(as_text=True)
            if not raw:
                return jsonify({"error": "No CSV data provided"}), 400
            reader = csv.DictReader(io.StringIO(raw))
        else:
            f = request.files["file"]
            reader = csv.DictReader(io.TextIOWrapper(f.stream, encoding="utf-8-sig"))

        # Build name→id lookup
        rest_map = {r.name.lower(): r.id for r in Restaurant.query.all()}

        added = 0
        skipped = []
        for row in reader:
            rname = row.get("restaurant_name", "").strip()
            rid = rest_map.get(rname.lower())
            if not rid:
                skipped.append(rname)
                continue
            price_str = row.get("price", "0").replace(",", "").replace(" ", "").strip()
            try:
                price = int(float(price_str))
            except ValueError:
                skipped.append(f"{rname}: bad price '{row.get('price')}'")
                continue
            collected = row.get("collected_date", "").strip()
            mi = MenuItem(
                restaurant_id=rid,
                category=row.get("category", "Uncategorized").strip(),
                name=row.get("dish_name", "").strip(),
                name_normalized=row.get("dish_name", "").strip().lower(),
                price=price,
                description=row.get("description", "").strip(),
                collected_by=row.get("collected_by", "").strip(),
                collected_date=date.fromisoformat(collected) if collected else date.today(),
            )
            db.session.add(mi)
            added += 1
        db.session.commit()
        return jsonify({"added": added, "skipped": skipped})

    # ═══════════════════════════════════════════════════════════════════════════
    #  OCR MENU UPLOAD
    # ═══════════════════════════════════════════════════════════════════════════

    @app.route("/api/menu/ocr", methods=["POST"])
    def ocr_menu_upload():
        """Upload one or more menu photos/PDFs.

        All files are sent in a SINGLE Claude Vision API call (saves credits).
        Falls back to OCR.space if Anthropic key is not configured.
        Auto-saves items to the restaurant when restaurant_id is provided.
        """
        uploaded = request.files.getlist("file")
        if not uploaded or not uploaded[0].filename:
            return jsonify({"error": "No file uploaded"}), 400

        ocr_lang = request.form.get("language", "rus")
        restaurant_id = request.form.get("restaurant_id", type=int)
        collected_by = request.form.get("collected_by", "OCR Upload")

        # Collect all files into a list for batch processing
        files_list = []
        for f in uploaded:
            if f.filename:
                files_list.append((
                    f.read(),
                    f.content_type or "application/octet-stream",
                    f.filename,
                ))

        if not files_list:
            return jsonify({"error": "No valid files"}), 400

        try:
            raw_text, items, method, claude_err = parse_menu_image(
                files_list, language=ocr_lang,
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            return jsonify({"error": f"Menu parsing failed: {str(e)}"}), 500

        # Auto-save items to the restaurant
        saved = 0
        if restaurant_id and items:
            for item in items:
                mi = MenuItem(
                    restaurant_id=restaurant_id,
                    category=item.get("category", "Uncategorized"),
                    name=item["name"],
                    name_normalized=item["name"].lower().strip(),
                    price=int(item["price"]),
                    collected_by=collected_by,
                    collected_date=date.today(),
                )
                db.session.add(mi)
                saved += 1
            db.session.commit()

        return jsonify({
            "raw_text": raw_text,
            "parsed_items": items,
            "saved": saved,
            "method": method,
            "claude_error": claude_err,
        })

    # ═══════════════════════════════════════════════════════════════════════════
    #  PRICE COMPARISON
    # ═══════════════════════════════════════════════════════════════════════════

    @app.route("/api/menu/compare")
    def compare_prices():
        dish = request.args.get("dish", "").strip()
        category = request.args.get("category", "").strip()
        if not dish:
            return jsonify({"error": "Provide ?dish= parameter"}), 400

        q = MenuItem.query.filter(MenuItem.name_normalized == dish.lower())
        if category:
            q = q.filter(MenuItem.category == category)
        items = q.order_by(MenuItem.price).all()

        if not items:
            q = MenuItem.query.filter(MenuItem.name_normalized.contains(dish.lower()))
            if category:
                q = q.filter(MenuItem.category == category)
            items = q.order_by(MenuItem.price).all()

        total_restaurants = Restaurant.query.count()
        prices = [m.price for m in items]
        avg_price = round(sum(prices) / len(prices)) if prices else 0

        by_segment = {}
        for m in items:
            seg = m.restaurant.price_segment if m.restaurant else "Unknown"
            by_segment.setdefault(seg, []).append(m.price)
        segment_avgs = {seg: round(sum(ps) / len(ps)) for seg, ps in by_segment.items()}

        return jsonify({
            "dish": dish,
            "restaurants_with_data": len(items),
            "total_restaurants": total_restaurants,
            "coverage_pct": round(len(items) / total_restaurants * 100) if total_restaurants else 0,
            "avg_price": avg_price,
            "min_price": min(prices) if prices else 0,
            "max_price": max(prices) if prices else 0,
            "segment_averages": segment_avgs,
            "results": [m.to_dict() for m in items],
        })

    @app.route("/api/menu/coverage")
    def menu_coverage():
        """How many restaurants have menu data entered."""
        total = Restaurant.query.count()
        with_menu = db.session.query(func.count(func.distinct(MenuItem.restaurant_id))).scalar()
        items_count = MenuItem.query.count()
        return jsonify({
            "total_restaurants": total,
            "restaurants_with_menu": with_menu,
            "restaurants_without_menu": total - with_menu,
            "coverage_pct": round(with_menu / total * 100) if total else 0,
            "total_menu_items": items_count,
        })

    # ═══════════════════════════════════════════════════════════════════════════
    #  PRICE HISTORY
    # ═══════════════════════════════════════════════════════════════════════════

    @app.route("/api/price-history")
    def price_history():
        limit = request.args.get("limit", 50, type=int)
        dish = request.args.get("dish", "").strip()
        q = PriceHistory.query.order_by(PriceHistory.changed_at.desc())
        if dish:
            q = q.join(MenuItem).filter(MenuItem.name_normalized == dish.lower())
        return jsonify([h.to_dict() for h in q.limit(limit).all()])

    # ═══════════════════════════════════════════════════════════════════════════
    #  MARKET ANALYTICS
    # ═══════════════════════════════════════════════════════════════════════════

    @app.route("/api/analytics/segments")
    def analytics_segments():
        """Menu-price-based segment analysis."""
        results = (
            db.session.query(
                Restaurant.price_segment,
                func.count(func.distinct(Restaurant.id)),
                func.avg(MenuItem.price),
                func.count(MenuItem.id),
            )
            .outerjoin(MenuItem, MenuItem.restaurant_id == Restaurant.id)
            .group_by(Restaurant.price_segment)
            .all()
        )
        return jsonify([{
            "segment": r[0],
            "restaurant_count": r[1],
            "avg_menu_price": round(r[2] or 0, 2),
            "menu_items_entered": r[3],
        } for r in results])

    @app.route("/api/analytics/cuisines")
    def analytics_cuisines():
        results = (
            db.session.query(
                Restaurant.cuisine,
                func.count(func.distinct(Restaurant.id)),
                func.avg(MenuItem.price),
                func.count(MenuItem.id),
            )
            .outerjoin(MenuItem, MenuItem.restaurant_id == Restaurant.id)
            .group_by(Restaurant.cuisine)
            .order_by(func.avg(MenuItem.price).desc())
            .all()
        )
        return jsonify([{
            "cuisine": r[0],
            "restaurant_count": r[1],
            "avg_menu_price": round(r[2] or 0, 2),
            "menu_items_entered": r[3],
        } for r in results])

    @app.route("/api/analytics/districts")
    def analytics_districts():
        results = (
            db.session.query(
                Restaurant.district,
                func.count(func.distinct(Restaurant.id)),
                func.avg(MenuItem.price),
                func.count(MenuItem.id),
            )
            .outerjoin(MenuItem, MenuItem.restaurant_id == Restaurant.id)
            .group_by(Restaurant.district)
            .order_by(func.count(func.distinct(Restaurant.id)).desc())
            .all()
        )
        return jsonify([{
            "district": r[0],
            "restaurant_count": r[1],
            "avg_menu_price": round(r[2] or 0, 2),
            "menu_items_entered": r[3],
        } for r in results])

    @app.route("/api/analytics/ranking")
    def analytics_ranking():
        """Rank restaurants by avg menu price and data completeness."""
        results = (
            db.session.query(
                Restaurant.id,
                Restaurant.name,
                Restaurant.cuisine,
                Restaurant.price_segment,
                Restaurant.district,
                func.count(MenuItem.id),
                func.avg(MenuItem.price),
            )
            .outerjoin(MenuItem, MenuItem.restaurant_id == Restaurant.id)
            .group_by(Restaurant.id)
            .order_by(func.count(MenuItem.id).desc())
            .all()
        )
        return jsonify([{
            "id": r[0], "name": r[1], "cuisine": r[2],
            "price_segment": r[3], "district": r[4],
            "menu_items": r[5],
            "avg_menu_price": round(r[6] or 0, 2),
        } for r in results])

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
