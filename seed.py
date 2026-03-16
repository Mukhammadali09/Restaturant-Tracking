"""Seed the database with real Tashkent high-end restaurants, menu items, and sample reviews."""

import random
from datetime import date, timedelta

from models import MenuItem, Restaurant, Review, db

# ─── Real Tashkent High-End Restaurants ──────────────────────────────────────
# Must-haves from the holding + top competitors across the city

RESTAURANTS = [
    # ── Must-have restaurants (user's holding / key competitors) ──
    {"name": "Novikov Cafe", "cuisine": "Pan-Asian / European", "address": "Amir Temur Ave 107B", "district": "Yakkasaray", "phone": "+998 71 200 0707", "price_segment": "Luxury", "avg_bill_min": 400_000, "avg_bill_max": 1_200_000},
    {"name": "Syrovarnya", "cuisine": "Italian / Cheese Bar", "address": "Bobur St 10", "district": "Yakkasaray", "phone": "+998 71 200 3344", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 700_000},
    {"name": "Basilic", "cuisine": "European / Mediterranean", "address": "Shota Rustaveli St 68", "district": "Mirzo Ulugbek", "phone": "+998 71 252 8888", "price_segment": "Premium", "avg_bill_min": 300_000, "avg_bill_max": 800_000},
    {"name": "Gorynich", "cuisine": "Modern Russian / Grill", "address": "Amir Temur Ave 88", "district": "Shaykhantahur", "phone": "+998 71 140 0808", "price_segment": "Luxury", "avg_bill_min": 400_000, "avg_bill_max": 1_000_000},
    {"name": "City 21", "cuisine": "European Fine Dining", "address": "Islam Karimov St 21", "district": "Yunusabad", "phone": "+998 71 234 2121", "price_segment": "Luxury", "avg_bill_min": 350_000, "avg_bill_max": 1_000_000},
    {"name": "Cucucina", "cuisine": "Italian", "address": "Taras Shevchenko St 3", "district": "Mirzo Ulugbek", "phone": "+998 71 252 5500", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 650_000},

    # ── Top Fine Dining ──
    {"name": "Afsona", "cuisine": "Uzbek Fine Dining", "address": "Buyuk Turon St 36", "district": "Mirzo Ulugbek", "phone": "+998 71 120 0036", "price_segment": "Luxury", "avg_bill_min": 400_000, "avg_bill_max": 1_200_000},
    {"name": "The Brasserie", "cuisine": "French / European", "address": "Amir Temur Ave 88, Hilton Hotel", "district": "Shaykhantahur", "phone": "+998 71 140 1000", "price_segment": "Luxury", "avg_bill_min": 500_000, "avg_bill_max": 1_500_000},
    {"name": "Steam", "cuisine": "Modern Fusion", "address": "Islam Karimov St 17A", "district": "Yunusabad", "phone": "+998 71 234 5500", "price_segment": "Premium", "avg_bill_min": 300_000, "avg_bill_max": 800_000},
    {"name": "Mona Lisa", "cuisine": "Italian Fine Dining", "address": "Sharof Rashidov St 5", "district": "Shaykhantahur", "phone": "+998 71 236 3000", "price_segment": "Luxury", "avg_bill_min": 400_000, "avg_bill_max": 1_100_000},

    # ── Italian ──
    {"name": "La Mezzaluna", "cuisine": "Italian", "address": "Sharof Rashidov St 7", "district": "Shaykhantahur", "phone": "+998 71 236 7773", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 700_000},
    {"name": "Dolce Vita", "cuisine": "Italian / Lounge", "address": "Bobur St 20", "district": "Yakkasaray", "phone": "+998 71 254 8800", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 650_000},
    {"name": "Sorrento", "cuisine": "Italian", "address": "Osiyo St 44", "district": "Mirzo Ulugbek", "phone": "+998 71 268 1010", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 600_000},
    {"name": "Parmesan", "cuisine": "Italian / Wine Bar", "address": "Mustakillik Ave 59", "district": "Mirzo Ulugbek", "phone": "+998 71 252 0909", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 550_000},

    # ── Asian / Pan-Asian ──
    {"name": "Jumanji", "cuisine": "Pan-Asian / Grill", "address": "Nukus St 48", "district": "Shaykhantahur", "phone": "+998 71 200 3030", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 700_000},
    {"name": "KOI", "cuisine": "Japanese / Sushi", "address": "Amir Temur Ave 60", "district": "Yakkasaray", "phone": "+998 71 233 5678", "price_segment": "Luxury", "avg_bill_min": 400_000, "avg_bill_max": 1_200_000},
    {"name": "Osaka", "cuisine": "Japanese", "address": "Islam Karimov St 45", "district": "Yunusabad", "phone": "+998 71 234 0808", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 700_000},
    {"name": "Thai House", "cuisine": "Thai", "address": "Bobur St 6", "district": "Yakkasaray", "phone": "+998 71 254 3333", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 550_000},
    {"name": "Wok & Go", "cuisine": "Asian Fusion", "address": "Shota Rustaveli St 12", "district": "Mirzo Ulugbek", "phone": "+998 71 252 0303", "price_segment": "Upper Casual", "avg_bill_min": 120_000, "avg_bill_max": 350_000},

    # ── Uzbek / Central Asian Premium ──
    {"name": "Plov Centre", "cuisine": "Traditional Uzbek", "address": "Iftihor St 1", "district": "Mirzo Ulugbek", "phone": "+998 90 355 5555", "price_segment": "Upper Casual", "avg_bill_min": 80_000, "avg_bill_max": 250_000},
    {"name": "Caravan", "cuisine": "Central Asian", "address": "Mustakillik Ave 3", "district": "Chilanzar", "phone": "+998 71 245 0001", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 600_000},
    {"name": "Besh Qozon", "cuisine": "Uzbek Fine Dining", "address": "Shahrisabz St 22", "district": "Yakkasaray", "phone": "+998 71 233 5050", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 500_000},
    {"name": "Sato", "cuisine": "Modern Uzbek", "address": "Abdulla Qodiriy St 36", "district": "Yakkasaray", "phone": "+998 71 233 9999", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 550_000},
    {"name": "Samarkand Restaurant", "cuisine": "Uzbek / Tajik", "address": "Buyuk Turon St 50", "district": "Mirzo Ulugbek", "phone": "+998 71 120 5050", "price_segment": "Premium", "avg_bill_min": 180_000, "avg_bill_max": 450_000},

    # ── Steakhouse / Grill ──
    {"name": "Meat Point", "cuisine": "Steakhouse", "address": "Islam Karimov St 25", "district": "Yunusabad", "phone": "+998 71 234 6677", "price_segment": "Premium", "avg_bill_min": 300_000, "avg_bill_max": 900_000},
    {"name": "Smoke House", "cuisine": "BBQ / Grill", "address": "Shota Rustaveli St 38", "district": "Mirzo Ulugbek", "phone": "+998 71 252 7700", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 700_000},
    {"name": "Rib Eye", "cuisine": "Steakhouse", "address": "Afrosiyob St 12", "district": "Shaykhantahur", "phone": "+998 71 236 4455", "price_segment": "Luxury", "avg_bill_min": 400_000, "avg_bill_max": 1_200_000},

    # ── Mediterranean / Middle Eastern ──
    {"name": "Sim Sim", "cuisine": "Middle Eastern / Mediterranean", "address": "Shota Rustaveli St 54", "district": "Mirzo Ulugbek", "phone": "+998 71 252 7773", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 600_000},
    {"name": "Cafe Baku", "cuisine": "Azerbaijani", "address": "Abdulla Qodiriy St 22", "district": "Yakkasaray", "phone": "+998 71 233 1123", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 550_000},
    {"name": "Istanbul Grill", "cuisine": "Turkish", "address": "Mustakillik Ave 22", "district": "Mirzo Ulugbek", "phone": "+998 71 252 4040", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 500_000},

    # ── Hotel Restaurants ──
    {"name": "Hyatt Regency - Sette", "cuisine": "Italian Fine Dining", "address": "Navoi St 1A, Hyatt Regency", "district": "Shaykhantahur", "phone": "+998 71 207 1234", "price_segment": "Luxury", "avg_bill_min": 500_000, "avg_bill_max": 1_500_000},
    {"name": "InterContinental - Piazza", "cuisine": "Mediterranean", "address": "Amir Temur Ave 55, InterContinental", "district": "Yakkasaray", "phone": "+998 71 120 8000", "price_segment": "Luxury", "avg_bill_min": 450_000, "avg_bill_max": 1_300_000},
    {"name": "Wyndham - Terrace", "cuisine": "International", "address": "Amir Temur Ave 7, Wyndham", "district": "Yakkasaray", "phone": "+998 71 120 4000", "price_segment": "Premium", "avg_bill_min": 300_000, "avg_bill_max": 800_000},

    # ── Trendy / Lounge ──
    {"name": "Level", "cuisine": "European / Lounge", "address": "Islam Karimov St 55", "district": "Yunusabad", "phone": "+998 71 234 7000", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 700_000},
    {"name": "Oasis Lounge", "cuisine": "Mediterranean / Hookah", "address": "Bobur St 30", "district": "Yakkasaray", "phone": "+998 71 254 9000", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 600_000},
    {"name": "Sky Bar", "cuisine": "Cocktail Bar / Snacks", "address": "Amir Temur Ave 88, Hilton 22F", "district": "Shaykhantahur", "phone": "+998 71 140 1022", "price_segment": "Luxury", "avg_bill_min": 350_000, "avg_bill_max": 1_000_000},
    {"name": "Nikkei", "cuisine": "Japanese-Peruvian Fusion", "address": "Buyuk Ipak Yoli 105", "district": "Mirzo Ulugbek", "phone": "+998 71 268 2222", "price_segment": "Luxury", "avg_bill_min": 400_000, "avg_bill_max": 1_100_000},
    {"name": "Cha Cha", "cuisine": "Georgian / Wine Bar", "address": "Nukus St 55", "district": "Shaykhantahur", "phone": "+998 71 200 5500", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 550_000},
    {"name": "Moxie", "cuisine": "Modern European", "address": "Shahrisabz St 8", "district": "Yakkasaray", "phone": "+998 71 233 6677", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 650_000},
    {"name": "Tkemali", "cuisine": "Georgian", "address": "Abdulla Qodiriy St 10", "district": "Yakkasaray", "phone": "+998 71 233 8080", "price_segment": "Premium", "avg_bill_min": 180_000, "avg_bill_max": 500_000},
]

# ─── Common Menu Positions (for cross-restaurant price comparison) ───────────
# Realistic menu items that many upscale restaurants share.
# Prices vary by restaurant segment.

MENU_CATEGORIES = {
    "Salads": [
        ("Caesar Salad", "Classic romaine, parmesan, croutons, anchovy dressing"),
        ("Greek Salad", "Tomato, cucumber, feta, olives, red onion"),
        ("Burrata Salad", "Burrata, cherry tomatoes, basil, pesto"),
        ("Tashkent Salad", "Beef, egg, radish, herbs, mayonnaise"),
        ("Niçoise Salad", "Tuna, egg, green beans, olives, potato"),
    ],
    "Cold Starters": [
        ("Beef Tartare", "Hand-cut beef, capers, egg yolk, mustard"),
        ("Salmon Tartare", "Fresh salmon, avocado, soy-citrus dressing"),
        ("Vitello Tonnato", "Veal, tuna sauce, capers"),
        ("Bruschetta", "Toasted bread, tomatoes, garlic, basil"),
        ("Carpaccio", "Thinly sliced beef, arugula, parmesan, truffle oil"),
    ],
    "Hot Starters": [
        ("Manti", "Steamed dumplings, meat filling, sour cream"),
        ("Khinkali", "Georgian dumplings, beef-lamb filling"),
        ("Samsa", "Baked pastry, lamb, onion"),
        ("Tom Yum", "Spicy Thai soup, shrimp, lemongrass, galangal"),
        ("French Onion Soup", "Caramelized onion, gruyère crouton"),
    ],
    "Mains — Meat": [
        ("Ribeye Steak", "300g prime beef, grilled, seasonal vegetables"),
        ("Rack of Lamb", "New Zealand lamb, herb crust, jus"),
        ("Beef Stroganoff", "Tender beef strips, mushroom cream sauce, rice"),
        ("Plov", "Traditional Uzbek rice pilaf, lamb, chickpeas, carrots"),
        ("Shashlik (Lamb)", "Marinated lamb skewers, grilled over charcoal"),
        ("Duck Breast", "Pan-seared, cherry sauce, potato gratin"),
        ("Chicken Kyiv", "Stuffed chicken breast, garlic butter, herbs"),
    ],
    "Mains — Fish": [
        ("Salmon Fillet", "Grilled salmon, asparagus, lemon butter"),
        ("Sea Bass", "Whole grilled sea bass, Mediterranean vegetables"),
        ("Shrimp Risotto", "Arborio rice, tiger shrimp, parmesan"),
        ("Tuna Steak", "Seared tuna, sesame crust, wasabi, soy"),
    ],
    "Pasta & Pizza": [
        ("Pasta Carbonara", "Spaghetti, guanciale, egg, pecorino"),
        ("Penne Arrabiata", "Penne, spicy tomato sauce, garlic, chili"),
        ("Truffle Pasta", "Tagliatelle, black truffle, parmesan cream"),
        ("Margherita Pizza", "Tomato, mozzarella, basil"),
        ("Pizza Quattro Formaggi", "Four cheese pizza"),
    ],
    "Sushi & Asian": [
        ("Philadelphia Roll", "Salmon, cream cheese, avocado, 8 pcs"),
        ("Dragon Roll", "Shrimp tempura, eel, avocado, unagi sauce"),
        ("Sashimi Set", "Chef's selection, 15 pcs"),
        ("Pad Thai", "Rice noodles, shrimp, peanuts, tamarind"),
        ("Wok Udon", "Thick noodles, vegetables, teriyaki"),
    ],
    "Desserts": [
        ("Tiramisu", "Classic Italian coffee-mascarpone dessert"),
        ("Crème Brûlée", "Vanilla custard, caramelized sugar"),
        ("Cheesecake", "New York style, berry compote"),
        ("Chocolate Fondant", "Molten center, vanilla ice cream"),
        ("Napoleon Cake", "Layered puff pastry, custard cream"),
    ],
    "Drinks": [
        ("Espresso", "Double shot"),
        ("Cappuccino", "Espresso, steamed milk, foam"),
        ("Fresh Orange Juice", "Squeezed to order"),
        ("Lemonade", "House-made, seasonal fruit"),
        ("Mojito (non-alc)", "Mint, lime, sugar, soda"),
    ],
}

# Price multiplier by segment (base prices are for "Upper Casual")
SEGMENT_MULTIPLIERS = {
    "Upper Casual": 1.0,
    "Premium": 1.5,
    "Luxury": 2.3,
}

# Base prices (UZS) for Upper Casual segment
BASE_PRICES = {
    "Caesar Salad": 45_000, "Greek Salad": 40_000, "Burrata Salad": 65_000,
    "Tashkent Salad": 38_000, "Niçoise Salad": 52_000,
    "Beef Tartare": 75_000, "Salmon Tartare": 80_000, "Vitello Tonnato": 70_000,
    "Bruschetta": 35_000, "Carpaccio": 72_000,
    "Manti": 35_000, "Khinkali": 32_000, "Samsa": 18_000,
    "Tom Yum": 48_000, "French Onion Soup": 42_000,
    "Ribeye Steak": 180_000, "Rack of Lamb": 165_000, "Beef Stroganoff": 85_000,
    "Plov": 45_000, "Shashlik (Lamb)": 65_000, "Duck Breast": 140_000,
    "Chicken Kyiv": 65_000,
    "Salmon Fillet": 120_000, "Sea Bass": 150_000, "Shrimp Risotto": 95_000,
    "Tuna Steak": 130_000,
    "Pasta Carbonara": 55_000, "Penne Arrabiata": 48_000, "Truffle Pasta": 95_000,
    "Margherita Pizza": 48_000, "Pizza Quattro Formaggi": 55_000,
    "Philadelphia Roll": 58_000, "Dragon Roll": 72_000, "Sashimi Set": 150_000,
    "Pad Thai": 55_000, "Wok Udon": 48_000,
    "Tiramisu": 45_000, "Crème Brûlée": 42_000, "Cheesecake": 48_000,
    "Chocolate Fondant": 52_000, "Napoleon Cake": 38_000,
    "Espresso": 18_000, "Cappuccino": 25_000, "Fresh Orange Juice": 28_000,
    "Lemonade": 30_000, "Mojito (non-alc)": 35_000,
}

REVIEWERS = [
    "Aziz M.", "Dilnoza K.", "Rustam S.", "Nigora T.", "Bobur A.",
    "Kamola R.", "Jasur N.", "Malika D.", "Timur F.", "Zarina H.",
    "Otabek L.", "Gulnara P.", "Sherzod V.", "Lola B.", "Farrukh I.",
    "Sardor K.", "Madina Y.", "Alisher R.", "Nozima S.", "Jamshid B.",
    "Elena V.", "Alexander K.", "Dmitry P.", "Irina T.", "Mikhail S.",
]

COMMENTS = [
    "Outstanding experience, world-class service.",
    "Beautifully presented dishes but portions are small for the price.",
    "The lamb was perfectly cooked. Will return!",
    "Overpriced but the ambiance makes up for it.",
    "Best plov in the city, hands down.",
    "Wine list is impressive. Great sommelier.",
    "Service was slow on a busy evening.",
    "A gem! Every dish was a delight.",
    "Good but not worth the premium price tag.",
    "Exquisite flavors, creative menu. Highly recommended.",
    "Decent food, exceptional rooftop view of Tashkent.",
    "Average taste, but beautiful interior design.",
    "Perfect for a special occasion dinner.",
    "Fresh ingredients, you can taste the quality.",
    "The dessert menu alone is worth a visit.",
    "Staff was attentive and professional throughout.",
    "Noisy atmosphere, hard to have a conversation.",
    "One of the best new openings in Tashkent.",
    "Consistent quality every time we visit.",
    "Great for business lunches. Private rooms available.",
    "The steak was cooked exactly as ordered. Impressive.",
    "Went with a large group — handled perfectly.",
    "Value for money is questionable at this level.",
    "The chef's tasting menu is a must-try.",
    "Parking is a nightmare but the food compensates.",
]


def seed_database():
    """Insert restaurants, menu items, and sample reviews spanning the last 30 days."""
    if Restaurant.query.first():
        return  # already seeded

    restaurants = []
    for data in RESTAURANTS:
        r = Restaurant(**data)
        db.session.add(r)
        restaurants.append(r)
    db.session.flush()

    # ── Menu Items ───────────────────────────────────────────────────────────
    for r in restaurants:
        multiplier = SEGMENT_MULTIPLIERS.get(r.price_segment, 1.5)
        # Each restaurant gets 60-80% of all menu positions (realistic variety)
        for category, items in MENU_CATEGORIES.items():
            # Skip some categories for variety
            if random.random() < 0.15:
                continue
            for item_name, description in items:
                if random.random() < 0.25:
                    continue  # not every restaurant has every dish
                base = BASE_PRICES.get(item_name, 50_000)
                # Add ±15% randomness so prices differ between restaurants
                jitter = random.uniform(0.85, 1.15)
                price = int(base * multiplier * jitter / 1000) * 1000  # round to nearest 1000
                mi = MenuItem(
                    restaurant_id=r.id,
                    category=category,
                    name=item_name,
                    name_normalized=item_name.lower(),
                    price=price,
                    description=description,
                )
                db.session.add(mi)

    # ── Reviews (30 days) ────────────────────────────────────────────────────
    today = date.today()
    for r in restaurants:
        for day_offset in range(30):
            visit_day = today - timedelta(days=day_offset)
            num_reviews = random.randint(1, 5)
            for _ in range(num_reviews):
                # Bill amount within the restaurant's declared range
                bill = random.randint(r.avg_bill_min, r.avg_bill_max)
                # Higher-end places tend to have higher ratings (slight bias)
                base_rating = 4 if r.price_segment == "Luxury" else 3
                rating = min(5, max(1, base_rating + random.choice([-1, 0, 0, 1, 1])))
                review = Review(
                    restaurant_id=r.id,
                    reviewer_name=random.choice(REVIEWERS),
                    rating=rating,
                    bill_amount=bill,
                    comment=random.choice(COMMENTS),
                    visit_date=visit_day,
                )
                db.session.add(review)

    db.session.commit()
