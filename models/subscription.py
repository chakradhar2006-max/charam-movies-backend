from datetime import datetime, timedelta
from database.db import db

PLAN_PRICES = {"free": 0, "premium": 299}  # mock pricing, no real payments


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    plan = db.Column(db.Enum("free", "premium", name="sub_plan"), nullable=False, default="free")
    subscription_start = db.Column(db.DateTime, nullable=True)
    subscription_end = db.Column(db.DateTime, nullable=True)
    payment_status = db.Column(
        db.Enum("none", "paid", "cancelled", "expired", name="payment_status"),
        nullable=False,
        default="none",
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def is_active(self):
        if self.plan == "free":
            return True
        return bool(self.subscription_end and self.subscription_end > datetime.utcnow())

    def to_dict(self):
        return {
            "plan": self.plan,
            "subscription_start": self.subscription_start.isoformat()
            if self.subscription_start
            else None,
            "subscription_end": self.subscription_end.isoformat()
            if self.subscription_end
            else None,
            "payment_status": self.payment_status,
            "is_active": self.is_active(),
            "price": PLAN_PRICES.get(self.plan, 0),
        }
