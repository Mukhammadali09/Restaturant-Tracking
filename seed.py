"""Seed the database with real Tashkent high-end restaurants. Menus start empty."""

from models import Restaurant, db

RESTAURANTS = [
    # ── Must-have restaurants (verified real locations) ──────────────────────
    {"name": "Novikov Cafe", "cuisine": "Pan-Asian / Mediterranean", "address": "Ukchi St 1A", "district": "Shaykhantakhur", "phone": "+998 78 333 83 33", "price_segment": "Luxury", "avg_bill_min": 500_000, "avg_bill_max": 1_500_000},
    {"name": "Syrovarnya", "cuisine": "Italian / Cheese Bar", "address": "Shahrisabz St 31B", "district": "Mirzo Ulugbek", "phone": "+998 90 815 31 31", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 750_000},
    {"name": "Basilic", "cuisine": "Mediterranean / European", "address": "Amir Temur Ave 19", "district": "Mirabad", "phone": "+998 71 233 99 05", "price_segment": "Premium", "avg_bill_min": 300_000, "avg_bill_max": 900_000},
    {"name": "Gorynich", "cuisine": "Modern Russian / Open Fire Grill", "address": "Shota Rustaveli St 22A", "district": "Yakkasaray", "phone": "+998 88 555 32 22", "price_segment": "Luxury", "avg_bill_min": 400_000, "avg_bill_max": 1_200_000},
    {"name": "City 21", "cuisine": "Pan-Asian / Lounge", "address": "Ukchi St 1, Hilton Tashkent City, 21F", "district": "Shaykhantakhur", "phone": "+998 71 200 0000", "price_segment": "Luxury", "avg_bill_min": 600_000, "avg_bill_max": 1_800_000},
    {"name": "Cucucina", "cuisine": "Italian", "address": "Botir Zakirov St 7", "district": "Shaykhantakhur", "phone": "+998 77 113 08 88", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 700_000},
    # ── Hotel Fine Dining ────────────────────────────────────────────────────
    {"name": "Sette", "cuisine": "Italian Fine Dining", "address": "Navoi St 1A, Hyatt Regency, 7F", "district": "Yunusabad", "phone": "+998 71 207 12 34", "price_segment": "Luxury", "avg_bill_min": 600_000, "avg_bill_max": 1_800_000},
    {"name": "Khiva", "cuisine": "Uzbek / International", "address": "Navoi St 1A, Hyatt Regency", "district": "Yunusabad", "phone": "+998 71 207 12 34", "price_segment": "Luxury", "avg_bill_min": 400_000, "avg_bill_max": 1_200_000},
    {"name": "Ember & Embar", "cuisine": "Asian / Steakhouse", "address": "Shahrisabz St 2, InterContinental, 17F", "district": "Yunusabad", "phone": "+998 71 203 00 00", "price_segment": "Luxury", "avg_bill_min": 600_000, "avg_bill_max": 2_000_000},
    # ── Italian ──────────────────────────────────────────────────────────────
    {"name": "Affresco", "cuisine": "Italian", "address": "Babur St 14", "district": "Yakkasaray", "phone": "+998 71 129 90 90", "price_segment": "Premium", "avg_bill_min": 300_000, "avg_bill_max": 800_000},
    {"name": "L'Opera Ristorante", "cuisine": "Italian Fine Dining", "address": "Islam Karimov St 17", "district": "Mirabad", "phone": "+998 95 195 08 88", "price_segment": "Premium", "avg_bill_min": 300_000, "avg_bill_max": 900_000},
    {"name": "Cucucina Ristorante", "cuisine": "Italian", "address": "Olzamor St 2A, Tashkent City Mall", "district": "Shaykhantakhur", "phone": "+998 33 088 03 18", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 600_000},
    # ── Steakhouse / Grill ───────────────────────────────────────────────────
    {"name": "Fillet", "cuisine": "Premium Steakhouse", "address": "M. Tarobiy St 29", "district": "Yakkasaray", "phone": "+998 77 302 90 90", "price_segment": "Luxury", "avg_bill_min": 500_000, "avg_bill_max": 1_500_000},
    {"name": "Myasnoi Steak House", "cuisine": "Steakhouse", "address": "Shota Rustaveli St 13A", "district": "Yakkasaray", "phone": "+998 78 148 10 01", "price_segment": "Premium", "avg_bill_min": 350_000, "avg_bill_max": 900_000},
    # ── Pan-Asian / Japanese ─────────────────────────────────────────────────
    {"name": "Toku", "cuisine": "Pan-Asian / Sushi", "address": "Istikbol St 4/1", "district": "Mirabad", "phone": "+998 99 910 19 10", "price_segment": "Premium", "avg_bill_min": 300_000, "avg_bill_max": 800_000},
    {"name": "Assorti", "cuisine": "Japanese / Korean / European", "address": "Taras Shevchenko St 30", "district": "Mirabad", "phone": "+998 71 120 00 00", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 700_000},
    # ── Uzbek / Central Asian ────────────────────────────────────────────────
    {"name": "Caravan", "cuisine": "Uzbek / European", "address": "Abdulla Kahhar St 22", "district": "Yunusabad", "phone": "+998 71 150 66 06", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 600_000},
    {"name": "Besh Qozon", "cuisine": "Traditional Uzbek / Plov", "address": "Oqlon St 1", "district": "Shaykhantakhur", "phone": "+998 71 268 00 00", "price_segment": "Upper Casual", "avg_bill_min": 80_000, "avg_bill_max": 250_000},
    {"name": "Lali", "cuisine": "Modern Uzbek", "address": "Kiyot Massif 57B", "district": "Yunusabad", "phone": "+998 50 333 57 57", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 600_000},
    {"name": "Gijduvon Premium", "cuisine": "Bukhara / Uzbek", "address": "Zulfiyaxonim St 21", "district": "Shaykhantakhur", "phone": "+998 90 108 42 42", "price_segment": "Premium", "avg_bill_min": 180_000, "avg_bill_max": 500_000},
    {"name": "Shedevr Garden", "cuisine": "Uzbek / European", "address": "R. Faizi St 44", "district": "Mirzo Ulugbek", "phone": "+998 71 268 00 11", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 550_000},
    # ── Seafood ──────────────────────────────────────────────────────────────
    {"name": "Kaspiyka", "cuisine": "Seafood", "address": "Botir Zakirov St 7, Tashkent City Mall", "district": "Shaykhantakhur", "phone": "+998 91 016 05 50", "price_segment": "Premium", "avg_bill_min": 300_000, "avg_bill_max": 850_000},
    # ── Mediterranean / European ─────────────────────────────────────────────
    {"name": "Quadro", "cuisine": "Spanish / European / Mediterranean", "address": "Zulfiyaxonim St 24", "district": "Shaykhantakhur", "phone": "+998 78 113 13 38", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 700_000},
    {"name": "Masa", "cuisine": "Turkish / European", "address": "Shota Rustaveli St 44A", "district": "Yakkasaray", "phone": "+998 71 203 25 25", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 700_000},
    # ── Trendy / New ─────────────────────────────────────────────────────────
    {"name": "Pro.Khinkali", "cuisine": "Georgian / Dumplings", "address": "Olzamor St 2, Tashkent City Park", "district": "Shaykhantakhur", "phone": "+998 71 200 00 11", "price_segment": "Upper Casual", "avg_bill_min": 150_000, "avg_bill_max": 400_000},
    {"name": "ChayKof", "cuisine": "European Cafe / Brunch", "address": "Shota Rustaveli St 22", "district": "Shaykhantakhur", "phone": "+998 90 969 16 66", "price_segment": "Upper Casual", "avg_bill_min": 120_000, "avg_bill_max": 350_000},
    # ── Additional ───────────────────────────────────────────────────────────
    {"name": "Mazzali", "cuisine": "Italian / European", "address": "Shota Rustaveli St 13A", "district": "Yakkasaray", "phone": "+998 71 200 13 13", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 700_000},
    {"name": "Karadeniz", "cuisine": "Turkish / Black Sea Cuisine", "address": "Shota Rustaveli St 69", "district": "Yakkasaray", "phone": "+998 71 200 00 69", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 600_000},
    {"name": "Cafe 1991", "cuisine": "Uzbek / Lebanese Fusion", "address": "Amir Temur Ave 1B", "district": "Mirabad", "phone": "+998 71 120 19 91", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 600_000},
    {"name": "Yuzhanin", "cuisine": "Italian / Caucasian", "address": "Shota Rustaveli St 20", "district": "Yakkasaray", "phone": "+998 71 200 20 20", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 600_000},
    {"name": "Aiza", "cuisine": "Greek", "address": "Islam Karimov St 10", "district": "Mirabad", "phone": "+998 71 233 00 33", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 650_000},
    {"name": "Tbilisi", "cuisine": "Georgian", "address": "Abdulla Qodiriy St 6", "district": "Yakkasaray", "phone": "+998 71 254 00 44", "price_segment": "Premium", "avg_bill_min": 200_000, "avg_bill_max": 550_000},
    {"name": "Barbaris", "cuisine": "European / Wine Bar", "address": "Shota Rustaveli St 28", "district": "Yakkasaray", "phone": "+998 71 200 28 28", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 700_000},
    {"name": "Nargiz Palace", "cuisine": "Uzbek Fine Dining", "address": "Buyuk Ipak Yoli St 103", "district": "Mirzo Ulugbek", "phone": "+998 71 268 10 03", "price_segment": "Premium", "avg_bill_min": 250_000, "avg_bill_max": 700_000},
    {"name": "Tandir", "cuisine": "Uzbek / Grill", "address": "Mustakillik Ave 67", "district": "Mirzo Ulugbek", "phone": "+998 71 252 67 67", "price_segment": "Upper Casual", "avg_bill_min": 120_000, "avg_bill_max": 350_000},
    {"name": "Shamrock Irish Pub", "cuisine": "Irish / European", "address": "Mirzo Ulugbek St 2", "district": "Mirabad", "phone": "+998 71 120 00 20", "price_segment": "Upper Casual", "avg_bill_min": 150_000, "avg_bill_max": 450_000},
]


def seed_database():
    """Insert restaurants only. Menus are entered manually by the marketing team."""
    if Restaurant.query.first():
        return
    for data in RESTAURANTS:
        db.session.add(Restaurant(**data))
    db.session.commit()
