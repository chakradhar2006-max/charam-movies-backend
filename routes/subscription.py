from datetime import datetime, timedelta
from flask import Blueprint, request
from database.db import db
from models.subscription import Subscription, PLAN_PRICES
from utils.responses import ok, err
from middleware.auth import token_required

subscription_bp = Blueprint("subscription", __name__, url_prefix="/api/subscription")


@subscription_bp.get("")
@token_required
def get_subscription(current_user):
    sub = current_user.subscription
    if not sub:
        sub = Subscription(user_id=current_user.id, plan="free", payment_status="none")
        db.session.add(sub)
        db.session.commit()
    return ok({"subscription": sub.to_dict()}, "Subscription retrieved successfully")


@subscription_bp.post("/upgrade")
@token_required
def upgrade_subscription(current_user):
    """Mock payment flow — no real payment gateway is integrated.
    Body: {"plan": "premium", "months": 1}"""
    data = request.get_json(silent=True) or {}
    plan = data.get("plan", "premium")
    months = max(int(data.get("months", 1) or 1), 1)

    if plan not in PLAN_PRICES:
        return err("Unknown plan", 422)

    sub = current_user.subscription or Subscription(user_id=current_user.id)
    sub.plan = plan
    sub.subscription_start = datetime.utcnow()
    sub.subscription_end = datetime.utcnow() + timedelta(days=30 * months)
    sub.payment_status = "paid"  # mock: assume the (fake) payment succeeded
    current_user.subscription_type = plan
    db.session.add(sub)
    db.session.commit()

    return ok(
        {"subscription": sub.to_dict(), "amount_charged_mock": PLAN_PRICES[plan] * months},
        "Subscription upgraded (mock payment, no real charge was made)",
    )


@subscription_bp.post("/cancel")
@token_required
def cancel_subscription(current_user):
    sub = current_user.subscription
    if not sub or sub.plan == "free":
        return err("No active paid subscription to cancel", 400)
    sub.payment_status = "cancelled"
    sub.plan = "free"
    current_user.subscription_type = "free"
    db.session.commit()
    return ok({"subscription": sub.to_dict()}, "Subscription cancelled")


@subscription_bp.get("/status")
@token_required
def subscription_status(current_user):
    sub = current_user.subscription
    active = sub.is_active() if sub else True
    return ok({"plan": sub.plan if sub else "free", "is_active": active})
