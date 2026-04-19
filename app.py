"""Tashkent High-End Restaurant Market Tracker — Flask application."""

import csv
import io
import re
from datetime import date, datetime, timezone
from difflib import SequenceMatcher

from flask import Flask, g, jsonify, request
from flask_cors import CORS
from sqlalchemy import func

import config
from auth import auth_required, generate_token
from models import MenuItem, PriceHistory, Restaurant, User, db
from ocr import parse_menu_image
from seed import seed_database


# ═══════════════════════════════════════════════════════════════════════════════
#  FUZZY DISH MATCHING
# ═══════════════════════════════════════════════════════════════════════════════

# Patterns to strip from dish names before comparison
_RE_PARENS = re.compile(r"\([^)]*\)")
_RE_VOLUME = re.compile(
    r"\b\d+(\.\d+)?\s*(ml|l|g|kg|oz|cl|mg|гр|мл|л)\b", re.IGNORECASE
)
_RE_TRAILING_NUM = re.compile(r"\s+\d+\s*$")
_RE_WHITESPACE = re.compile(r"\s+")

# Modifiers/descriptors to ignore when comparing dish names.
# These words describe preparation or style but not the actual dish.
_MODIFIERS = frozenset({
    # English
    "classic", "traditional", "fresh", "homemade", "house", "signature",
    "special", "original", "authentic", "our", "new", "seasonal", "premium",
    "deluxe", "supreme", "grilled", "baked", "fried", "roasted", "steamed",
    "braised", "sauteed", "sautéed", "crispy", "tender", "warm", "cold",
    "chilled", "hot", "mini", "large", "small", "big", "style", "with",
    "and", "the", "a", "an", "in", "on", "of", "for", "from", "by",
    "al", "alla", "au", "aux", "con", "e", "di", "del", "la", "le",
    "italian", "french", "asian", "russian", "uzbek", "georgian", "turkish",
    "japanese", "chinese", "thai", "indian", "american", "european",
    "mediterranean", "modern", "chef", "chefs",
    # Russian
    "классический", "традиционный", "свежий", "домашний", "наш",
    "фирменный", "особый", "оригинальный", "авторский", "жареный",
    "запечённый", "запеченный", "тёплый", "теплый", "холодный", "мини",
    "большой", "маленький", "нежный", "хрустящий", "острый",
    "по", "с", "и", "в", "на", "из", "от", "для", "со", "под",
})


def _core_name(name):
    """Extract the core dish name by stripping volumes, sizes, parenthetical info."""
    s = name.lower().strip()
    s = _RE_PARENS.sub("", s)
    s = _RE_VOLUME.sub("", s)
    s = _RE_TRAILING_NUM.sub("", s)
    s = _RE_WHITESPACE.sub(" ", s).strip()
    return s


def _food_tokens(name):
    """Extract food-relevant tokens by stripping modifiers.

    "Classic Italian burrata" → {"burrata"}
    "Salad burrata with tomatoes" → {"salad", "burrata", "tomatoes"}
    "Grilled chicken" → {"chicken"}
    "Grilled salmon" → {"salmon"}
    """
    core = _core_name(name)
    tokens = core.split()
    food = {t for t in tokens if t not in _MODIFIERS and len(t) >= 3}
    return food if food else set(tokens)


def _dish_similarity(name1, name2):
    """Compute similarity between two dish names. Returns 0.0-1.0.

    Uses a three-layer strategy:
    1. Exact core match → 1.0
    2. Full token containment → 0.80–1.0
    3. Food-token matching (strips modifiers) + classic metrics.
       This catches "Classic Italian burrata" ≈ "Salad burrata with tomatoes"
       while still rejecting "Grilled chicken" ≠ "Grilled salmon".
    """
    c1 = _core_name(name1)
    c2 = _core_name(name2)

    if c1 == c2:
        return 1.0
    if not c1 or not c2:
        return 0.0

    tokens1 = set(c1.split())
    tokens2 = set(c2.split())

    smaller = tokens1 if len(tokens1) <= len(tokens2) else tokens2
    larger = tokens1 if len(tokens1) > len(tokens2) else tokens2
    containment = len(smaller & larger) / len(smaller) if smaller else 0.0

    union = tokens1 | tokens2
    jaccard = len(tokens1 & tokens2) / len(union) if union else 0.0

    if containment >= 1.0:
        return 0.80 + 0.20 * jaccard

    seq_sim = SequenceMatcher(None, c1, c2).ratio()

    # --- Food-token boost ---
    # Strip modifiers and compare what's left (the actual food words).
    food1 = _food_tokens(name1)
    food2 = _food_tokens(name2)
    food_overlap = food1 & food2

    if food_overlap and food1 and food2:
        food_score = len(food_overlap) / min(len(food1), len(food2))
        if food_score >= 0.5:
            base = (containment + jaccard + seq_sim) / 3.0
            return max(base, 0.55 + 0.35 * food_score)

    return (containment + jaccard + seq_sim) / 3.0


# Similarity threshold: >= this value counts as "same dish"
_MATCH_THRESHOLD = 0.55
# Same-category bonus: if two dishes share a category, we relax the threshold
_SAME_CAT_BONUS = 0.12


def _find_matches(base_items, comp_items):
    """Find fuzzy matches between base and competitor menu items.

    Returns:
      matched: list of (base_item, [(comp_item, similarity), ...])
      unmatched_base: list of base items with no match
      unmatched_comp: list of comp items with no match
    """
    # Pre-compute core names
    base_cores = [(m, _core_name(m.name)) for m in base_items]
    comp_cores = [(m, _core_name(m.name)) for m in comp_items]

    # Build similarity matrix: for each base item, find best comp matches
    # Group comp items by their best matching base item
    matched = {}          # base_item.id -> (base_item, [(comp_item, sim)])
    used_comp = set()     # comp item ids already matched

    # Score all pairs, then greedily assign
    pairs = []
    for b_item, b_core in base_cores:
        for c_item, c_core in comp_cores:
            sim = _dish_similarity(b_item.name, c_item.name)
            # Category bonus
            threshold = _MATCH_THRESHOLD
            if b_item.category == c_item.category:
                threshold -= _SAME_CAT_BONUS
            if sim >= threshold:
                pairs.append((sim, b_item, c_item))

    # Sort by similarity descending — greedily assign each comp item to
    # its best base match (a comp item can only match one base dish,
    # but multiple comp items from different restaurants can match the same base)
    pairs.sort(key=lambda x: x[0], reverse=True)

    # Track which (comp_id) is used per base_id to avoid duplicates within
    # the same restaurant, but allow same dish from different restaurants
    used_comp_per_base = {}  # base_id -> set of comp restaurant_ids we've matched

    for sim, b_item, c_item in pairs:
        bid = b_item.id
        if bid not in matched:
            matched[bid] = (b_item, [])
            used_comp_per_base[bid] = {}

        # Allow one match per competitor restaurant per base dish
        crid = c_item.restaurant_id
        if crid in used_comp_per_base[bid]:
            continue

        matched[bid][1].append((c_item, sim))
        used_comp_per_base[bid][crid] = True
        used_comp.add(c_item.id)

    # Split into matched (with at least one comp match) and unmatched
    matched_list = []
    unmatched_base = []
    for b_item, b_core in base_cores:
        if b_item.id in matched and matched[b_item.id][1]:
            matched_list.append(matched[b_item.id])
        else:
            unmatched_base.append(b_item)

    unmatched_comp = [m for m, _ in comp_cores if m.id not in used_comp]

    return matched_list, unmatched_base, unmatched_comp


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
    #  AUTH
    # ═══════════════════════════════════════════════════════════════════════════

    @app.route("/api/auth/register", methods=["POST"])
    def register():
        data = request.get_json() or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        name = (data.get("name") or "").strip()
        company = (data.get("company") or "").strip()

        if not email or "@" not in email:
            return jsonify({"error": "Valid email required"}), 400
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        if not name:
            return jsonify({"error": "Name required"}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 409

        user = User(email=email, name=name, company=company)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        token = generate_token(user.id)
        return jsonify({"token": token, "user": user.to_dict()}), 201

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        data = request.get_json() or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid email or password"}), 401
        token = generate_token(user.id)
        return jsonify({"token": token, "user": user.to_dict()})

    @app.route("/api/auth/me")
    @auth_required
    def me():
        return jsonify(g.user.to_dict())

    # ═══════════════════════════════════════════════════════════════════════════
    #  RESTAURANTS
    # ═══════════════════════════════════════════════════════════════════════════

    def _all_restaurants():
        return Restaurant.query

    def _get_restaurant_or_404(rid):
        return Restaurant.query.get_or_404(rid)

    def _get_menu_item_or_404(mid):
        return MenuItem.query.get_or_404(mid)

    @app.route("/api/restaurants")
    @auth_required
    def list_restaurants():
        restaurants = _all_restaurants().order_by(Restaurant.name).all()
        return jsonify([r.to_dict() for r in restaurants])

    @app.route("/api/restaurants/<int:rid>")
    @auth_required
    def get_restaurant(rid):
        r = _get_restaurant_or_404(rid)
        return jsonify(r.to_dict())

    @app.route("/api/restaurants", methods=["POST"])
    @auth_required
    def add_restaurant():
        data = request.get_json()
        r = Restaurant(
            user_id=g.user_id,  # audit: who added it
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
    @auth_required
    def delete_restaurant(rid):
        r = _get_restaurant_or_404(rid)
        db.session.delete(r)
        db.session.commit()
        return jsonify({"deleted": rid})

    # ═══════════════════════════════════════════════════════════════════════════
    #  MENU MANAGEMENT (core of the tool)
    # ═══════════════════════════════════════════════════════════════════════════

    @app.route("/api/menu")
    @auth_required
    def list_menu():
        restaurant_id = request.args.get("restaurant_id", type=int)
        category = request.args.get("category")
        q = MenuItem.query.order_by(MenuItem.category, MenuItem.name)
        if restaurant_id:
            q = q.filter(MenuItem.restaurant_id == restaurant_id)
        if category:
            q = q.filter(MenuItem.category == category)
        return jsonify([m.to_dict() for m in q.all()])

    @app.route("/api/menu/categories")
    @auth_required
    def menu_categories():
        rows = db.session.query(MenuItem.category).distinct().order_by(MenuItem.category).all()
        return jsonify([r[0] for r in rows])

    @app.route("/api/menu/items")
    @auth_required
    def menu_item_names():
        category = request.args.get("category")
        q = db.session.query(MenuItem.name).distinct().order_by(MenuItem.name)
        if category:
            q = q.filter(MenuItem.category == category)
        return jsonify([r[0] for r in q.all()])

    @app.route("/api/menu", methods=["POST"])
    @auth_required
    def add_menu_item():
        data = request.get_json()
        _get_restaurant_or_404(int(data["restaurant_id"]))
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
    @auth_required
    def update_menu_item(mid):
        """Update a menu item's price. Logs the change to price_history."""
        mi = _get_menu_item_or_404(mid)
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
    @auth_required
    def delete_menu_item(mid):
        mi = _get_menu_item_or_404(mid)
        db.session.delete(mi)
        db.session.commit()
        return jsonify({"deleted": mid})

    @app.route("/api/menu/restaurant/<int:rid>", methods=["DELETE"])
    @auth_required
    def delete_all_menu_items(rid):
        """Delete ALL menu items for a restaurant."""
        _get_restaurant_or_404(rid)
        count = MenuItem.query.filter_by(restaurant_id=rid).delete()
        db.session.commit()
        return jsonify({"deleted": count, "restaurant_id": rid})

    @app.route("/api/menu/bulk", methods=["POST"])
    @auth_required
    def bulk_add_menu():
        """Add multiple menu items at once. Expects JSON array of items."""
        items = request.get_json()
        if not isinstance(items, list):
            return jsonify({"error": "Expected a JSON array"}), 400
        added = 0
        for data in items:
            rid = int(data["restaurant_id"])
            collected = data.get("collected_date")
            mi = MenuItem(
                restaurant_id=rid,
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
    @auth_required
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

        # Build name→id lookup — scoped to this user's restaurants only
        rest_map = {r.name.lower(): r.id for r in _all_restaurants().all()}

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
    @auth_required
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

        # Verify the restaurant belongs to the current user
        if restaurant_id:
            _get_restaurant_or_404(restaurant_id)

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
    @auth_required
    def compare_prices():
        dish = request.args.get("dish", "").strip()
        category = request.args.get("category", "").strip()
        if not dish:
            return jsonify({"error": "Provide ?dish= parameter"}), 400

        # Try exact match first
        q = MenuItem.query.filter(MenuItem.name_normalized == dish.lower())
        if category:
            q = q.filter(MenuItem.category == category)
        items = q.order_by(MenuItem.price).all()

        # Fall back to contains match
        if not items:
            q = MenuItem.query.filter(MenuItem.name_normalized.contains(dish.lower()))
            if category:
                q = q.filter(MenuItem.category == category)
            items = q.order_by(MenuItem.price).all()

        # Fall back to fuzzy match across all items
        if not items:
            all_q = MenuItem.query
            if category:
                all_q = all_q.filter(MenuItem.category == category)
            all_items = all_q.all()
            for m in all_items:
                if _dish_similarity(dish, m.name) >= _MATCH_THRESHOLD:
                    items.append(m)
            items.sort(key=lambda m: m.price)

        total_restaurants = _all_restaurants().count()
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

    # ═══════════════════════════════════════════════════════════════════════════
    #  COMPETITIVE COMPARISON — the core marketing tool
    # ═══════════════════════════════════════════════════════════════════════════

    @app.route("/api/menu/compare-restaurants")
    @auth_required
    def compare_restaurants():
        """Compare a base restaurant against selected competitors.

        Query params:
          base_id: int — your restaurant
          competitor_ids: comma-separated ints — competitors to compare against
          category: optional — filter to a specific category
        """
        base_id = request.args.get("base_id", type=int)
        comp_str = request.args.get("competitor_ids", "")
        cat_filter = request.args.get("category", "").strip()

        if not base_id:
            return jsonify({"error": "Provide ?base_id= parameter"}), 400
        if not comp_str:
            return jsonify({"error": "Provide ?competitor_ids= parameter"}), 400

        comp_ids = [int(x) for x in comp_str.split(",") if x.strip().isdigit()]
        if not comp_ids:
            return jsonify({"error": "No valid competitor IDs"}), 400

        base_rest = _get_restaurant_or_404(base_id)
        comp_rests = Restaurant.query.filter(Restaurant.id.in_(comp_ids)).all()
        comp_map = {r.id: r for r in comp_rests}

        # Load menu items (scoped to user via restaurant ownership)
        base_q = MenuItem.query.filter_by(restaurant_id=base_id)
        comp_q = MenuItem.query.filter(MenuItem.restaurant_id.in_(comp_ids))
        if cat_filter:
            base_q = base_q.filter_by(category=cat_filter)
            comp_q = comp_q.filter(MenuItem.category == cat_filter)
        base_items = base_q.all()
        comp_items = comp_q.all()

        # --- Summary ---
        base_prices = [m.price for m in base_items]
        comp_prices = [m.price for m in comp_items]
        base_avg = round(sum(base_prices) / len(base_prices)) if base_prices else 0
        comp_avg = round(sum(comp_prices) / len(comp_prices)) if comp_prices else 0

        if comp_avg > 0 and base_avg > 0:
            diff_pct = round((base_avg - comp_avg) / comp_avg * 100, 1)
        else:
            diff_pct = 0

        # --- By category ---
        base_by_cat = {}
        for m in base_items:
            base_by_cat.setdefault(m.category, []).append(m)
        comp_by_cat = {}
        for m in comp_items:
            comp_by_cat.setdefault(m.category, []).append(m)

        all_cats = sorted(set(list(base_by_cat.keys()) + list(comp_by_cat.keys())))
        by_category = []
        for cat in all_cats:
            b_items = base_by_cat.get(cat, [])
            c_items = comp_by_cat.get(cat, [])
            b_avg = round(sum(m.price for m in b_items) / len(b_items)) if b_items else 0
            c_avg = round(sum(m.price for m in c_items) / len(c_items)) if c_items else 0

            # Per-competitor breakdown
            per_comp = {}
            for m in c_items:
                per_comp.setdefault(m.restaurant_id, []).append(m.price)
            comp_details = []
            for cid, prices in per_comp.items():
                r = comp_map.get(cid)
                comp_details.append({
                    "id": cid,
                    "name": r.name if r else "Unknown",
                    "avg": round(sum(prices) / len(prices)),
                    "count": len(prices),
                })

            cat_diff = round((b_avg - c_avg) / c_avg * 100, 1) if c_avg > 0 and b_avg > 0 else 0
            by_category.append({
                "category": cat,
                "base_avg": b_avg,
                "base_count": len(b_items),
                "competitors_avg": c_avg,
                "competitors_count": len(c_items),
                "competitor_details": comp_details,
                "diff_pct": cat_diff,
            })

        # --- Fuzzy-matched common dishes ---
        matched, unmatched_base, unmatched_comp = _find_matches(
            base_items, comp_items,
        )

        common_dishes = []
        matched_comp_ids = set()  # track which comp items were matched
        for base_m, comp_matches in matched:
            c_prices = [m.price for m, _sim in comp_matches]
            c_avg = round(sum(c_prices) / len(c_prices))
            diff = round((base_m.price - c_avg) / c_avg * 100, 1) if c_avg > 0 else 0
            # Build competitor details with match info
            comp_details = []
            for m, sim in comp_matches:
                matched_comp_ids.add(m.id)
                detail = {
                    "id": m.restaurant_id,
                    "name": m.restaurant.name if m.restaurant else "Unknown",
                    "price": m.price,
                    "matched_name": m.name,
                    "similarity": round(sim * 100),
                }
                comp_details.append(detail)
            common_dishes.append({
                "name": base_m.name,
                "category": base_m.category,
                "base_price": base_m.price,
                "competitor_prices": comp_details,
                "competitors_avg": c_avg,
                "diff_pct": diff,
            })
        common_dishes.sort(key=lambda x: abs(x["diff_pct"]), reverse=True)

        # --- Dishes unique to base (your competitive advantages) ---
        unique_to_base = [{
            "name": m.name, "category": m.category, "price": m.price,
        } for m in unmatched_base]

        # --- Dishes missing from base (competitor offerings you lack) ---
        # Group unmatched competitor items by core name
        missing_groups = {}
        for m in unmatched_comp:
            core = _core_name(m.name)
            if core not in missing_groups:
                missing_groups[core] = {
                    "name": m.name,
                    "category": m.category,
                    "items": [],
                }
            missing_groups[core]["items"].append(m)

        missing_list = []
        for core, group in missing_groups.items():
            items = group["items"]
            prices = [m.price for m in items]
            missing_list.append({
                "name": group["name"],
                "category": group["category"],
                "available_at": list(set(
                    m.restaurant.name for m in items if m.restaurant
                )),
                "avg_price": round(sum(prices) / len(prices)),
                "count": len(set(m.restaurant_id for m in items)),
            })
        missing_list.sort(key=lambda x: x["count"], reverse=True)

        # --- Per-competitor summary (with fuzzy match counts) ---
        # Count how many matched items came from each competitor
        comp_match_counts = {}
        for _base_m, comp_matches in matched:
            for m, _sim in comp_matches:
                comp_match_counts[m.restaurant_id] = (
                    comp_match_counts.get(m.restaurant_id, 0) + 1
                )

        comp_summaries = []
        for cid in comp_ids:
            r = comp_map.get(cid)
            if not r:
                continue
            r_items = [m for m in comp_items if m.restaurant_id == cid]
            r_prices = [m.price for m in r_items]
            r_avg = round(sum(r_prices) / len(r_prices)) if r_prices else 0
            comp_summaries.append({
                "id": cid,
                "name": r.name,
                "cuisine": r.cuisine,
                "segment": r.price_segment,
                "item_count": len(r_items),
                "avg_price": r_avg,
                "common_dishes": comp_match_counts.get(cid, 0),
                "diff_pct": round((base_avg - r_avg) / r_avg * 100, 1) if r_avg > 0 and base_avg > 0 else 0,
            })

        return jsonify({
            "base": {
                "id": base_rest.id,
                "name": base_rest.name,
                "cuisine": base_rest.cuisine,
                "segment": base_rest.price_segment,
                "item_count": len(base_items),
                "avg_price": base_avg,
            },
            "competitors": comp_summaries,
            "summary": {
                "base_avg_price": base_avg,
                "base_item_count": len(base_items),
                "competitors_avg_price": comp_avg,
                "competitors_item_count": len(comp_items),
                "diff_pct": diff_pct,
            },
            "by_category": by_category,
            "common_dishes": common_dishes,
            "unique_to_base": unique_to_base,
            "missing_from_base": missing_list,
        })

    @app.route("/api/menu/coverage")
    @auth_required
    def menu_coverage():
        """How many restaurants have menu data entered."""
        total = _all_restaurants().count()
        with_menu = (
            MenuItem.query
            .with_entities(func.count(func.distinct(MenuItem.restaurant_id)))
            .scalar()
        ) or 0
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
    @auth_required
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
    @auth_required
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
    @auth_required
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
    @auth_required
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
    @auth_required
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

    @app.route("/api/analytics/category-coverage")
    @auth_required
    def analytics_category_coverage():
        """Which categories each restaurant covers — for heatmap view."""
        results = (
            db.session.query(
                Restaurant.id,
                Restaurant.name,
                MenuItem.category,
                func.count(MenuItem.id),
                func.avg(MenuItem.price),
            )
            .join(MenuItem, MenuItem.restaurant_id == Restaurant.id)

            .group_by(Restaurant.id, MenuItem.category)
            .order_by(Restaurant.name, MenuItem.category)
            .all()
        )
        # Group by restaurant
        by_rest = {}
        all_cats = set()
        for r in results:
            rid, rname, cat, count, avg_price = r
            by_rest.setdefault(rid, {"id": rid, "name": rname, "categories": {}})
            by_rest[rid]["categories"][cat] = {
                "count": count,
                "avg_price": round(avg_price or 0),
            }
            all_cats.add(cat)
        return jsonify({
            "restaurants": list(by_rest.values()),
            "categories": sorted(all_cats),
        })

    # ═══════════════════════════════════════════════════════════════════════════
    #  USER PROFILE
    # ═══════════════════════════════════════════════════════════════════════════

    @app.route("/api/auth/profile", methods=["PUT"])
    @auth_required
    def update_profile():
        data = request.get_json() or {}
        if "name" in data:
            g.user.name = data["name"].strip()
        if "company" in data:
            g.user.company = data["company"].strip()
        if "photo_url" in data:
            photo = data["photo_url"]
            if len(photo) > 500_000:
                return jsonify({"error": "Photo too large (max 500KB)"}), 400
            g.user.photo_url = photo
        db.session.commit()
        return jsonify(g.user.to_dict())

    @app.route("/api/auth/password", methods=["PUT"])
    @auth_required
    def change_password():
        data = request.get_json() or {}
        current = data.get("current_password", "")
        new_pw = data.get("new_password", "")
        if not g.user.check_password(current):
            return jsonify({"error": "Current password is incorrect"}), 400
        if len(new_pw) < 6:
            return jsonify({"error": "New password must be at least 6 characters"}), 400
        g.user.set_password(new_pw)
        db.session.commit()
        return jsonify({"message": "Password updated"})

    # ═══════════════════════════════════════════════════════════════════════════
    #  MENU ENGINEERING MATRIX
    # ═══════════════════════════════════════════════════════════════════════════

    @app.route("/api/analytics/menu-engineering")
    @auth_required
    def menu_engineering():
        """Menu engineering matrix (Stars / Plowhorses / Puzzles / Dogs).

        For a given restaurant, classifies each dish based on:
        - Popularity: how many other restaurants carry a similar dish
        - Profitability: price vs market average for that dish

        Query params:
          restaurant_id: int — the restaurant to analyze
        """
        rid = request.args.get("restaurant_id", type=int)
        if not rid:
            return jsonify({"error": "Provide ?restaurant_id="}), 400
        rest = Restaurant.query.get_or_404(rid)
        my_items = MenuItem.query.filter_by(restaurant_id=rid).all()
        if not my_items:
            return jsonify({"restaurant": rest.name, "items": [], "summary": {}})

        all_items = MenuItem.query.filter(MenuItem.restaurant_id != rid).all()

        results = []
        for mi in my_items:
            matches = [m for m in all_items if _dish_similarity(mi.name, m.name) >= _MATCH_THRESHOLD]
            market_prices = [m.price for m in matches]
            market_avg = round(sum(market_prices) / len(market_prices)) if market_prices else mi.price
            popularity = len(set(m.restaurant_id for m in matches))
            price_vs_market = round((mi.price - market_avg) / market_avg * 100, 1) if market_avg else 0

            margin_pct = None
            if mi.food_cost and mi.price:
                margin_pct = round((mi.price - mi.food_cost) / mi.price * 100, 1)

            results.append({
                "id": mi.id,
                "name": mi.name,
                "category": mi.category,
                "price": mi.price,
                "food_cost": mi.food_cost,
                "margin_pct": margin_pct,
                "market_avg": market_avg,
                "price_vs_market": price_vs_market,
                "popularity": popularity,
                "matched_restaurants": list(set(m.restaurant.name for m in matches if m.restaurant))[:5],
            })

        # Classify: median splits
        pops = [r["popularity"] for r in results]
        med_pop = sorted(pops)[len(pops) // 2] if pops else 0
        margins = [r["price_vs_market"] for r in results]
        med_margin = sorted(margins)[len(margins) // 2] if margins else 0

        stars, plowhorses, puzzles, dogs = [], [], [], []
        for r in results:
            hi_pop = r["popularity"] >= med_pop
            hi_profit = r["price_vs_market"] >= med_margin
            if hi_pop and hi_profit:
                r["quadrant"] = "star"
                stars.append(r)
            elif hi_pop and not hi_profit:
                r["quadrant"] = "plowhorse"
                plowhorses.append(r)
            elif not hi_pop and hi_profit:
                r["quadrant"] = "puzzle"
                puzzles.append(r)
            else:
                r["quadrant"] = "dog"
                dogs.append(r)

        return jsonify({
            "restaurant": rest.name,
            "items": results,
            "summary": {
                "stars": len(stars),
                "plowhorses": len(plowhorses),
                "puzzles": len(puzzles),
                "dogs": len(dogs),
                "total": len(results),
                "avg_price": round(sum(r["price"] for r in results) / len(results)) if results else 0,
                "avg_market": round(sum(r["market_avg"] for r in results) / len(results)) if results else 0,
            },
        })

    # ═══════════════════════════════════════════════════════════════════════════
    #  PRICE RECOMMENDATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    @app.route("/api/analytics/price-recommendations")
    @auth_required
    def price_recommendations():
        """Smart pricing suggestions for a restaurant.

        Identifies items priced significantly below or above market and
        suggests adjustments with estimated revenue impact.
        """
        rid = request.args.get("restaurant_id", type=int)
        if not rid:
            return jsonify({"error": "Provide ?restaurant_id="}), 400
        rest = Restaurant.query.get_or_404(rid)
        my_items = MenuItem.query.filter_by(restaurant_id=rid).all()
        all_items = MenuItem.query.filter(MenuItem.restaurant_id != rid).all()

        recommendations = []
        for mi in my_items:
            matches = [m for m in all_items if _dish_similarity(mi.name, m.name) >= _MATCH_THRESHOLD]
            if not matches:
                continue
            market_prices = [m.price for m in matches]
            market_avg = round(sum(market_prices) / len(market_prices))
            market_max = max(market_prices)
            diff_pct = round((mi.price - market_avg) / market_avg * 100, 1)

            if abs(diff_pct) < 5:
                continue

            if diff_pct < -10:
                suggested = round(market_avg * 0.95)
                action = "raise"
                reason = f"Priced {abs(diff_pct)}% below market average"
            elif diff_pct > 20:
                suggested = round(market_avg * 1.10)
                action = "lower"
                reason = f"Priced {diff_pct}% above market average — risk of losing customers"
            elif diff_pct < -5:
                suggested = round(market_avg * 0.97)
                action = "raise"
                reason = f"Slightly below market — room to increase"
            elif diff_pct > 10:
                suggested = mi.price
                action = "monitor"
                reason = f"Premium pricing ({diff_pct}% above avg) — ensure quality justifies it"
            else:
                continue

            revenue_impact = suggested - mi.price

            recommendations.append({
                "dish": mi.name,
                "category": mi.category,
                "current_price": mi.price,
                "market_avg": market_avg,
                "market_max": market_max,
                "diff_pct": diff_pct,
                "suggested_price": suggested,
                "action": action,
                "reason": reason,
                "revenue_impact_per_sale": revenue_impact,
                "competitors_count": len(set(m.restaurant_id for m in matches)),
            })

        recommendations.sort(key=lambda x: abs(x["revenue_impact_per_sale"]), reverse=True)

        total_potential = sum(r["revenue_impact_per_sale"] for r in recommendations if r["action"] == "raise")

        return jsonify({
            "restaurant": rest.name,
            "recommendations": recommendations,
            "summary": {
                "total_items_analyzed": len(my_items),
                "items_with_suggestions": len(recommendations),
                "raise_count": sum(1 for r in recommendations if r["action"] == "raise"),
                "lower_count": sum(1 for r in recommendations if r["action"] == "lower"),
                "monitor_count": sum(1 for r in recommendations if r["action"] == "monitor"),
                "total_revenue_opportunity": total_potential,
            },
        })

    # ═══════════════════════════════════════════════════════════════════════════
    #  CSV EXPORT
    # ═══════════════════════════════════════════════════════════════════════════

    @app.route("/api/export/menu-data")
    @auth_required
    def export_menu_data():
        """Export all menu data as CSV for spreadsheet analysis."""
        rid = request.args.get("restaurant_id", type=int)
        q = MenuItem.query.join(Restaurant)
        if rid:
            q = q.filter(MenuItem.restaurant_id == rid)
        items = q.order_by(Restaurant.name, MenuItem.category, MenuItem.name).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Restaurant", "Segment", "District", "Category", "Dish Name",
            "Price (UZS)", "Food Cost (UZS)", "Margin %", "Description",
            "Notes", "Collected By", "Collected Date", "Last Updated",
        ])
        for m in items:
            margin = round((m.price - m.food_cost) / m.price * 100, 1) if m.food_cost and m.price else ""
            writer.writerow([
                m.restaurant.name if m.restaurant else "",
                m.restaurant.price_segment if m.restaurant else "",
                m.restaurant.district if m.restaurant else "",
                m.category,
                m.name,
                m.price,
                m.food_cost or "",
                margin,
                m.description or "",
                m.notes or "",
                m.collected_by or "",
                m.collected_date.isoformat() if m.collected_date else "",
                m.updated_at.isoformat() if m.updated_at else "",
            ])

        from flask import Response
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=menu_data.csv"},
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
