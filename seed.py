"""Seed the database with Tashkent high-end restaurants and sample reviews."""

import random
from datetime import date, timedelta

from models import Restaurant, Review, db

RESTAURANTS = [
    {"name": "Afsona", "cuisine": "Uzbek Fine Dining", "address": "Buyuk Turon St 36", "district": "Mirzo Ulugbek", "phone": "+998 71 120 0036"},
    {"name": "The Brasserie", "cuisine": "European", "address": "Amir Temur Ave 88, Hilton Hotel", "district": "Shaykhantahur", "phone": "+998 71 140 1000"},
    {"name": "Sim Sim", "cuisine": "Middle Eastern / Mediterranean", "address": "Shota Rustaveli St 54", "district": "Mirzo Ulugbek", "phone": "+998 71 252 7773"},
    {"name": "Cafe Baku", "cuisine": "Azerbaijani", "address": "Abdulla Qodiriy St 22", "district": "Yakkasaray", "phone": "+998 71 233 1123"},
    {"name": "Steam", "cuisine": "Modern Fusion", "address": "Islam Karimov St 17A", "district": "Yunusabad", "phone": "+998 71 234 5500"},
    {"name": "Plov Centre", "cuisine": "Traditional Uzbek", "address": "Iftihor St 1", "district": "Mirzo Ulugbek", "phone": "+998 90 355 5555"},
    {"name": "La Mezzaluna", "cuisine": "Italian", "address": "Sharof Rashidov St 7", "district": "Shaykhantahur", "phone": "+998 71 236 7773"},
    {"name": "Caravan", "cuisine": "Central Asian", "address": "Mustakillik Ave 3", "district": "Chilanzar", "phone": "+998 71 245 0001"},
    {"name": "Dolce Vita", "cuisine": "Italian / Lounge", "address": "Bobur St 20", "district": "Yakkasaray", "phone": "+998 71 254 8800"},
    {"name": "Jumanji", "cuisine": "Pan-Asian / Grill", "address": "Nukus St 48", "district": "Shaykhantahur", "phone": "+998 71 200 3030"},
]

REVIEWERS = [
    "Aziz M.", "Dilnoza K.", "Rustam S.", "Nigora T.", "Bobur A.",
    "Kamola R.", "Jasur N.", "Malika D.", "Timur F.", "Zarina H.",
    "Otabek L.", "Gulnara P.", "Sherzod V.", "Lola B.", "Farrukh I.",
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
]


def seed_database():
    """Insert sample restaurants and reviews spanning the last 30 days."""
    if Restaurant.query.first():
        return  # already seeded

    restaurants = []
    for data in RESTAURANTS:
        r = Restaurant(**data)
        db.session.add(r)
        restaurants.append(r)
    db.session.flush()

    today = date.today()
    for r in restaurants:
        for day_offset in range(30):
            visit_day = today - timedelta(days=day_offset)
            num_reviews = random.randint(1, 4)
            for _ in range(num_reviews):
                review = Review(
                    restaurant_id=r.id,
                    reviewer_name=random.choice(REVIEWERS),
                    rating=random.randint(3, 5),
                    bill_amount=random.randint(150_000, 800_000),  # UZS
                    comment=random.choice(COMMENTS),
                    visit_date=visit_day,
                )
                db.session.add(review)

    db.session.commit()
