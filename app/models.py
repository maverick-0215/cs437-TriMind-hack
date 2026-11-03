from datetime import datetime

from flask import current_app
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db, login_manager

CATEGORIES = [
    "Electronics",
    "Wallet/Purse",
    "ID Card",
    "Keys",
    "Bottle",
    "Bag",
    "Clothing",
    "Umbrella",
    "Cycle",
    "Books/Stationery",
    "Jewellery/Watch",
    "Other",
]


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        """S2: admin if the email is listed in ADMIN_EMAILS."""
        raw = current_app.config.get("ADMIN_EMAILS", "")
        admins = {e.strip().lower() for e in raw.split(",") if e.strip()}
        return self.email.lower() in admins


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class FoundItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(40), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    date_found = db.Column(db.Date, nullable=False)
    general_area = db.Column(db.String(120), nullable=False)
    # Private details: only admins may see these.
    exact_location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    photo_path = db.Column(db.String(200))
    status = db.Column(db.String(20), nullable=False, default="AVAILABLE")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def public_dict(self):
        """The only fields that may leave the server for non-admins (S6, S7)."""
        return {
            "id": self.id,
            "category": self.category,
            "title": self.title,
            "date_found": self.date_found.isoformat(),
            "general_area": self.general_area,
        }


class LostReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category = db.Column(db.String(40), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    date_lost = db.Column(db.Date, nullable=False)
    place_lost = db.Column(db.String(120), nullable=False)
    private_details = db.Column(db.Text, nullable=False)
    linked_item_id = db.Column(db.Integer, db.ForeignKey("found_item.id"))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    student = db.relationship("User")
    linked_item = db.relationship("FoundItem")


class Claim(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("found_item.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    features = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="PENDING")
    pickup_code = db.Column(db.String(6))
    code_used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    item = db.relationship("FoundItem")
    student = db.relationship("User")


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)


class Handover(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("found_item.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    handed_over_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    item = db.relationship("FoundItem")
    student = db.relationship("User", foreign_keys=[student_id])
    admin = db.relationship("User", foreign_keys=[admin_id])
