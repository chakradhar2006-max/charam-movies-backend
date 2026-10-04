from datetime import datetime
import bcrypt
from database.db import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(190), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("user", "admin", name="user_role"), nullable=False, default="user")
    subscription_type = db.Column(
        db.Enum("free", "premium", name="subscription_type"),
        nullable=False,
        default="free",
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    watchlist_items = db.relationship(
        "Watchlist", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    history_items = db.relationship(
        "WatchHistory", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    reviews = db.relationship(
        "Review", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    subscription = db.relationship(
        "Subscription",
        backref="user",
        uselist=False,
        lazy=True,
        cascade="all, delete-orphan",
    )

    # ---- password helpers ----
    def set_password(self, raw_password: str) -> None:
        hashed = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt())
        self.password_hash = hashed.decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        if not raw_password or not self.password_hash:
            return False
        return bcrypt.checkpw(
            raw_password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    def to_dict(self, include_private=False):
        data = {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role,
            "subscription_type": self.subscription_type,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        # password_hash is intentionally NEVER included, even with include_private
        return data

    def __repr__(self):
        return f"<User {self.id} {self.email}>"
