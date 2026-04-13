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
    price_segment = db.Column(db.String(30), default="Premium")
    avg_bill_min = db.Column(db.Integer, default=0)
    avg_bill_max = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    menu_items = db.relationship("MenuItem", backref="restaurant", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "cuisine": self.cuisine,
            "address": self.address,
            "district": self.district,
            "phone": self.phone,
            "price_segment": self.price_segment,
            "avg_bill_min": self.avg_bill_min,
            "avg_bill_max": self.avg_bill_max,
            "created_at": self.created_at.isoformat(),
        }


class MenuItem(db.Model):
    """Menu position with price — ONLY from real manual data entry."""
    __tablename__ = "menu_items"

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    name_normalized = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    collected_by = db.Column(db.String(100), default="")
    collected_date = db.Column(db.Date)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    price_history = db.relationship("PriceHistory", backref="menu_item", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "restaurant_id": self.restaurant_id,
            "restaurant_name": self.restaurant.name if self.restaurant else None,
            "restaurant_segment": self.restaurant.price_segment if self.restaurant else None,
            "category": self.category,
            "name": self.name,
            "price": self.price,
            "description": self.description,
            "collected_by": self.collected_by,
            "collected_date": self.collected_date.isoformat() if self.collected_date else None,
            "updated_at": self.updated_at.isoformat(),
        }


class PriceHistory(db.Model):
    """Logs every price change so we can track trends over time."""
    __tablename__ = "price_history"

    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
    old_price = db.Column(db.Integer, nullable=False)
    new_price = db.Column(db.Integer, nullable=False)
    changed_by = db.Column(db.String(100), default="")
    changed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "menu_item_id": self.menu_item_id,
            "dish_name": self.menu_item.name if self.menu_item else None,
            "restaurant_name": self.menu_item.restaurant.name if self.menu_item and self.menu_item.restaurant else None,
            "old_price": self.old_price,
            "new_price": self.new_price,
            "change_pct": round((self.new_price - self.old_price) / self.old_price * 100, 1) if self.old_price else 0,
            "changed_by": self.changed_by,
            "changed_at": self.changed_at.isoformat(),
        }
