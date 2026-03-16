from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Restaurant(db.Model):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    cuisine = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(300), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(30))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    reviews = db.relationship("Review", backref="restaurant", lazy=True, cascade="all, delete-orphan")
    daily_stats = db.relationship("DailyStat", backref="restaurant", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "cuisine": self.cuisine,
            "address": self.address,
            "district": self.district,
            "phone": self.phone,
            "created_at": self.created_at.isoformat(),
        }


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)
    reviewer_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    bill_amount = db.Column(db.Float, nullable=False)  # in UZS
    comment = db.Column(db.Text)
    visit_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "restaurant_id": self.restaurant_id,
            "restaurant_name": self.restaurant.name if self.restaurant else None,
            "reviewer_name": self.reviewer_name,
            "rating": self.rating,
            "bill_amount": self.bill_amount,
            "comment": self.comment,
            "visit_date": self.visit_date.isoformat(),
            "created_at": self.created_at.isoformat(),
        }


class DailyStat(db.Model):
    """Auto-generated daily statistics per restaurant."""
    __tablename__ = "daily_stats"

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    review_count = db.Column(db.Integer, default=0)
    avg_bill = db.Column(db.Float, default=0.0)
    avg_rating = db.Column(db.Float, default=0.0)
    min_bill = db.Column(db.Float, default=0.0)
    max_bill = db.Column(db.Float, default=0.0)
    computed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint("restaurant_id", "date", name="uq_restaurant_date"),)

    def to_dict(self):
        return {
            "id": self.id,
            "restaurant_id": self.restaurant_id,
            "restaurant_name": self.restaurant.name if self.restaurant else None,
            "date": self.date.isoformat(),
            "review_count": self.review_count,
            "avg_bill": round(self.avg_bill, 2),
            "avg_rating": round(self.avg_rating, 2),
            "min_bill": round(self.min_bill, 2),
            "max_bill": round(self.max_bill, 2),
            "computed_at": self.computed_at.isoformat(),
        }
