from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), default="")
    role = db.Column(db.String(20), default="manager")  # admin, manager, analyst, viewer
    photo_url = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    restaurants = db.relationship("Restaurant", backref="created_by_user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "company": self.company,
            "role": self.role,
            "photo_url": self.photo_url or "",
            "created_at": self.created_at.isoformat(),
        }


class Restaurant(db.Model):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
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
    __tablename__ = "menu_items"

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    name_normalized = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    food_cost = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text)
    notes = db.Column(db.Text, default="")
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
            "food_cost": self.food_cost,
            "margin_pct": round((self.price - self.food_cost) / self.price * 100, 1) if self.food_cost and self.price else None,
            "description": self.description,
            "notes": self.notes or "",
            "collected_by": self.collected_by,
            "collected_date": self.collected_date.isoformat() if self.collected_date else None,
            "updated_at": self.updated_at.isoformat(),
        }


class PriceHistory(db.Model):
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
