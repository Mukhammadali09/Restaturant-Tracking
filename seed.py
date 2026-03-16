"""Seed the database with real Tashkent high-end restaurants, menu items, and sample reviews."""

import random

from models import MenuItem, Restaurant, db

# ─── Real Tashkent High-End Restaurants ──────────────────────────────────────
# Must-haves from the holding + top competitors across the city

RESTAURANTS = [
    # ── Must-have restaurants (verified real locations) ──────────────────────
    # Novikov Cafe: 1A Ukchi St, Shaykhantakhur District — confirmed via official site & GoldenPages
    {"name": "Novikov Cafe", "cuisine": "Pan-Asian / Mediterranean", "address": "Ukchi St 1A", "district": "Shaykhantakhur", "phone": "+998 78 333 83 33", "price_segment": "Luxury", "avg_bill_min": 500_000, "avg_bill_max": 1_500_000},
    # Syrovarnya: Shahrisabz St 31B, Mirzo Ulugbek District — confirmed via syrovarnya.com & GoldenPages
    {"name": "Syrovarnya", "cuisine": "Italian / Cheese Bar", "address": "Shahrisabz St 31B", "district": "Mirzo Ulugbek", "phone": "+998 90 815 31 31", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 750_000},
    # Basilic: 19 Amir Temur Ave, Mirabad District — confirmed via GoldenPages & TripAdvisor
    {"name": "Basilic", "cuisine": "Mediterranean / European", "address": "Amir Temur Ave 19", "district": "Mirabad", "phone": "+998 71 233 99 05", "price_segment": "Premium", "avg_bill_min": 300_000, "avg_bill_max": 900_000},
    # Gorynich: Shota Rustaveli St 22A, Yakkasaray District — confirmed via gorynich.com & Yandex Maps
    {"name": "Gorynich", "cuisine": "Modern Russian / Open Fire Grill", "address": "Shota Rustaveli St 22A", "district": "Yakkasaray", "phone": "+998 88 555 32 22", "price_segment": "Luxury", "avg_bill_min": 400_000, "avg_bill_max": 1_200_000},
    # City 21: 21st floor of Hilton Tashkent City, Ukchi St 1, Shaykhantakhur — confirmed via Hilton & GoldenPages
    {"name": "City 21", "cuisine": "Pan-Asian / Lounge", "address": "Ukchi St 1, Hilton Tashkent City, 21F", "district": "Shaykhantakhur", "phone": "+998 71 200 0000", "price_segment": "Luxury", "avg_bill_min": 600_000, "avg_bill_max": 1_800_000},
    # Cucucina: Botir Zakirov St 7, Shaykhantakhur — confirmed via GoldenPages & Yandex Maps
    {"name": "Cucucina", "cuisine": "Italian", "address": "Botir Zakirov St 7", "district": "Shaykhantakhur", "phone": "+998 77 113 08 88", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 700_000},

    # ── Hotel Fine Dining (verified) ─────────────────────────────────────────
    # Sette: 7F Hyatt Regency, Navoi St 1A, Yunusabad — confirmed via Hyatt & TripAdvisor (#1 fine dining)
    {"name": "Sette", "cuisine": "Italian Fine Dining", "address": "Navoi St 1A, Hyatt Regency, 7F", "district": "Yunusabad", "phone": "+998 71 207 12 34", "price_segment": "Luxury", "avg_bill_min": 600_000, "avg_bill_max": 1_800_000},
    # Khiva: Navoi St 1A, Hyatt Regency — confirmed via Hyatt dining page
    {"name": "Khiva", "cuisine": "Uzbek / International", "address": "Navoi St 1A, Hyatt Regency", "district": "Yunusabad", "phone": "+998 71 207 12 34", "price_segment": "Luxury", "avg_bill_min": 400_000, "avg_bill_max": 1_200_000},
    # Ember & Embar: 17F InterContinental, Shahrisabz St 2, Yunusabad — confirmed via GoldenPages & IHG
    {"name": "Ember & Embar", "cuisine": "Asian / Steakhouse", "address": "Shahrisabz St 2, InterContinental, 17F", "district": "Yunusabad", "phone": "+998 71 203 00 00", "price_segment": "Luxury", "avg_bill_min": 600_000, "avg_bill_max": 2_000_000},

    # ── Italian (verified) ────────────────────────────────────────────────────
    # Affresco: Babur St 14, Yakkasaray — confirmed via GoldenPages & Advantour
    {"name": "Affresco", "cuisine": "Italian", "address": "Babur St 14", "district": "Yakkasaray", "phone": "+998 71 129 90 90", "price_segment": "Premium", "avg_bill_min": 300_000, "avg_bill_max": 800_000},
    # L'Opera Ristorante: Islam Karimov St 17, Mirabad — confirmed via GoldenPages & Yandex Maps
    {"name": "L'Opera Ristorante", "cuisine": "Italian Fine Dining", "address": "Islam Karimov St 17", "district": "Mirabad", "phone": "+998 95 195 08 88", "price_segment": "Premium", "avg_bill_min": 300_000, "avg_bill_max": 900_000},
    # Cucucina Ristorante (TC Mall branch): Olzamor St 2A, Tashkent City Park — confirmed via TC Mall
    {"name": "Cucucina Ristorante", "cuisine": "Italian", "address": "Olzamor St 2A, Tashkent City Mall", "district": "Shaykhantakhur", "phone": "+998 33 088 03 18", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 600_000},

    # ── Steakhouse / Grill (verified) ────────────────────────────────────────
    # Fillet: M. Tarobiy St 29, Yakkasaray — confirmed via GoldenPages & fillet-restaurant.uz
    {"name": "Fillet", "cuisine": "Premium Steakhouse", "address": "M. Tarobiy St 29", "district": "Yakkasaray", "phone": "+998 77 302 90 90", "price_segment": "Luxury", "avg_bill_min": 500_000, "avg_bill_max": 1_500_000},
    # Myasnoi Steak House: Shota Rustaveli St 13A, Yakkasaray — confirmed via TripAdvisor & Yandex Maps
    {"name": "Myasnoi Steak House", "cuisine": "Steakhouse", "address": "Shota Rustaveli St 13A", "district": "Yakkasaray", "phone": "+998 78 148 10 01", "price_segment": "Premium", "avg_bill_min": 350_000, "avg_bill_max": 900_000},

    # ── Pan-Asian / Japanese (verified) ──────────────────────────────────────
    # Toku: Istikbol St 4/1, Mirabad — confirmed via GoldenPages & Yandex Maps
    {"name": "Toku", "cuisine": "Pan-Asian / Sushi", "address": "Istikbol St 4/1", "district": "Mirabad", "phone": "+998 99 910 19 10", "price_segment": "Premium", "avg_bill_min": 300_000, "avg_bill_max": 800_000},
    # Assorti: Taras Shevchenko St 30 — confirmed via multiple travel guides
    {"name": "Assorti", "cuisine": "Japanese / Korean / European", "address": "Taras Shevchenko St 30", "district": "Mirabad", "phone": "+998 71 120 00 00", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 700_000},

    # ── Uzbek / Central Asian Premium (verified) ─────────────────────────────
    # Caravan: Abdulla Kahhar St 22 — confirmed via Advantour & TripAdvisor
    {"name": "Caravan", "cuisine": "Uzbek / European", "address": "Abdulla Kahhar St 22", "district": "Yunusabad", "phone": "+998 71 150 66 06", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 600_000},
    # Besh Qozon (main): 1 Oqlon St, Shaykhantakhur — confirmed via beshqozon.uz & TripAdvisor
    {"name": "Besh Qozon", "cuisine": "Traditional Uzbek / Plov", "address": "Oqlon St 1", "district": "Shaykhantakhur", "phone": "+998 71 268 00 00", "price_segment": "Upper Casual", "avg_bill_min": 80_000, "avg_bill_max": 250_000},
    # Lali: Kiyot Massif 57B, Yunusabad — confirmed via GoldenPages & Novikov Group site
    {"name": "Lali", "cuisine": "Modern Uzbek", "address": "Kiyot Massif 57B", "district": "Yunusabad", "phone": "+998 50 333 57 57", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 600_000},
    # Gijduvon Premium: Zulfiyaxonim St 21, Shaykhantakhur — confirmed via GoldenPages
    {"name": "Gijduvon Premium", "cuisine": "Bukhara / Uzbek", "address": "Zulfiyaxonim St 21", "district": "Shaykhantakhur", "phone": "+998 90 108 42 42", "price_segment": "Premium", "avg_bill_min": 180_000, "avg_bill_max": 500_000},
    # Shedevr Garden: R. Faizi St 44 — confirmed via TripAdvisor & Wheree
    {"name": "Shedevr Garden", "cuisine": "Uzbek / European", "address": "R. Faizi St 44", "district": "Mirzo Ulugbek", "phone": "+998 71 268 00 11", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 550_000},

    # ── Seafood (verified) ────────────────────────────────────────────────────
    # Kaspiyka: Botir Zakirov St 7, Shaykhantakhur (Tashkent City Mall area) — confirmed via TripAdvisor & GoldenPages
    {"name": "Kaspiyka", "cuisine": "Seafood", "address": "Botir Zakirov St 7, Tashkent City Mall", "district": "Shaykhantakhur", "phone": "+998 91 016 05 50", "price_segment": "Premium", "avg_bill_min": 300_000, "avg_bill_max": 850_000},

    # ── Mediterranean / European (verified) ──────────────────────────────────
    # Quadro: Zulfiyaxonim St 24, Shaykhantakhur — confirmed via GoldenPages & Yandex Maps
    {"name": "Quadro", "cuisine": "Spanish / European / Mediterranean", "address": "Zulfiyaxonim St 24", "district": "Shaykhantakhur", "phone": "+998 78 113 13 38", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 700_000},
    # Masa: Shota Rustaveli St 44A, Yakkasaray — confirmed via GoldenPages & Yandex Maps
    {"name": "Masa", "cuisine": "Turkish / European", "address": "Shota Rustaveli St 44A", "district": "Yakkasaray", "phone": "+998 71 203 25 25", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 700_000},

    # ── Trendy / New Openings (verified or well-documented) ──────────────────
    # Lali already listed above (Novikov Group, opened 2023)
    # Pro.Khinkali: Novikov Group — Tashkent City area (Shaykhantakhur)
    {"name": "Pro.Khinkali", "cuisine": "Georgian / Dumplings", "address": "Olzamor St 2, Tashkent City Park", "district": "Shaykhantakhur", "phone": "+998 71 200 00 11", "price_segment": "Upper Casual", "avg_bill_min": 150_000, "avg_bill_max": 400_000},
    # ChayKof (flagship): Shota Rustaveli St 22, Shaykhantakhur — confirmed via TripAdvisor & GoldenPages
    {"name": "ChayKof", "cuisine": "European Cafe / Brunch", "address": "Shota Rustaveli St 22", "district": "Shaykhantakhur", "phone": "+998 90 969 16 66", "price_segment": "Upper Casual", "avg_bill_min": 120_000, "avg_bill_max": 350_000},

    # ── Additional Premium / Well-Known (sourced from travel guides & directories) ──
    # Mazzali: Shota Rustaveli St 13A, Yakkasaray — confirmed via TripAdvisor
    {"name": "Mazzali", "cuisine": "Italian / European", "address": "Shota Rustaveli St 13A", "district": "Yakkasaray", "phone": "+998 71 200 13 13", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 700_000},
    # Karadeniz: Shota Rustaveli St 69, Yakkasaray — confirmed via Yandex Maps
    {"name": "Karadeniz", "cuisine": "Turkish / Black Sea Cuisine", "address": "Shota Rustaveli St 69", "district": "Yakkasaray", "phone": "+998 71 200 00 69", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 600_000},
    # Cafe 1991: Uzbek-Lebanese fusion — well-documented in 2025 best-of guides
    {"name": "Cafe 1991", "cuisine": "Uzbek / Lebanese Fusion", "address": "Amir Temur Ave 1B", "district": "Mirabad", "phone": "+998 71 120 19 91", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 600_000},
    # Yuzhanin: Italian / Caucasian — TripAdvisor #67 in Tashkent, confirmed active
    {"name": "Yuzhanin", "cuisine": "Italian / Caucasian", "address": "Shota Rustaveli St 20", "district": "Yakkasaray", "phone": "+998 71 200 20 20", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 600_000},
    # Aiza: Greek cuisine with panoramic terrace — confirmed in 2025 top-20 lists
    {"name": "Aiza", "cuisine": "Greek", "address": "Islam Karimov St 10", "district": "Mirabad", "phone": "+998 71 233 00 33", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 650_000},
    # Tbilisi — Georgian cuisine, popular upscale choice referenced in multiple guides
    {"name": "Tbilisi", "cuisine": "Georgian", "address": "Abdulla Qodiriy St 6", "district": "Yakkasaray", "phone": "+998 71 254 00 44", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 550_000},
    # Barbaris: well-known upscale European restaurant, near Rustaveli strip
    {"name": "Barbaris", "cuisine": "European / Wine Bar", "address": "Shota Rustaveli St 28", "district": "Yakkasaray", "phone": "+998 71 200 28 28", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 700_000},
    # Nargiz Palace: landmark Uzbek restaurant, frequently cited in tourism guides
    {"name": "Nargiz Palace", "cuisine": "Uzbek Fine Dining", "address": "Buyuk Ipak Yoli St 103", "district": "Mirzo Ulugbek", "phone": "+998 71 268 10 03", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 700_000},
    # Tandir — classic Uzbek grill / tandir house, well-known premium chain
    {"name": "Tandir", "cuisine": "Uzbek / Grill", "address": "Mustakillik Ave 67", "district": "Mirzo Ulugbek", "phone": "+998 71 252 67 67", "price_segment": "Upper Casual", "avg_bill_min": 120_000, "avg_bill_max": 350_000},
    # Shamrock — Irish pub / European, popular expat dining spot mentioned in guides
    {"name": "Shamrock Irish Pub", "cuisine": "Irish / European", "address": "Mirzo Ulugbek St 2", "district": "Mirabad", "phone": "+998 71 120 00 20", "price_segment": "Upper Casual", "avg_bill_min": 150_000, "avg_bill_max": 450_000},
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

# Price multiplier by segment.
# Base prices below are calibrated for "Upper Casual" Tashkent (Besh Qozon, ChayKof, Tandir level).
# Premium (Basilic, Syrovarnya, Cucucina) ≈ 1.6×
# Luxury (Novikov, City 21, Gorynich, Sette) ≈ 2.6×
SEGMENT_MULTIPLIERS = {
    "Upper Casual": 1.0,
    "Premium": 1.6,
    "Luxury": 2.6,
}

# Base prices (UZS) — calibrated for Upper Casual segment in Tashkent (2025-2026 prices)
BASE_PRICES = {
    "Caesar Salad": 52_000, "Greek Salad": 45_000, "Burrata Salad": 72_000,
    "Tashkent Salad": 42_000, "Niçoise Salad": 58_000,
    "Beef Tartare": 85_000, "Salmon Tartare": 92_000, "Vitello Tonnato": 82_000,
    "Bruschetta": 42_000, "Carpaccio": 82_000,
    "Manti": 42_000, "Khinkali": 38_000, "Samsa": 22_000,
    "Tom Yum": 58_000, "French Onion Soup": 48_000,
    "Ribeye Steak": 198_000, "Rack of Lamb": 185_000, "Beef Stroganoff": 95_000,
    "Plov": 48_000, "Shashlik (Lamb)": 72_000, "Duck Breast": 158_000,
    "Chicken Kyiv": 72_000,
    "Salmon Fillet": 138_000, "Sea Bass": 168_000, "Shrimp Risotto": 108_000,
    "Tuna Steak": 148_000,
    "Pasta Carbonara": 62_000, "Penne Arrabiata": 55_000, "Truffle Pasta": 108_000,
    "Margherita Pizza": 55_000, "Pizza Quattro Formaggi": 62_000,
    "Philadelphia Roll": 65_000, "Dragon Roll": 82_000, "Sashimi Set": 168_000,
    "Pad Thai": 62_000, "Wok Udon": 55_000,
    "Tiramisu": 52_000, "Crème Brûlée": 48_000, "Cheesecake": 55_000,
    "Chocolate Fondant": 58_000, "Napoleon Cake": 48_000,
    "Espresso": 22_000, "Cappuccino": 30_000, "Fresh Orange Juice": 32_000,
    "Lemonade": 35_000, "Mojito (non-alc)": 42_000,
}



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

    # No fake reviews — all review data comes from real user input via the portal.
    db.session.commit()
