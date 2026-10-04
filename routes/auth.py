from datetime import datetime
from flask import Blueprint, request
from database.db import db
from models.user import User
from models.subscription import Subscription
from utils.validators import is_valid_email, is_strong_password, sanitize_str
from utils.jwt_utils import generate_access_token, generate_refresh_token
from utils.responses import ok, err
from middleware.auth import token_required
from utils.token_blocklist import revoke

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    full_name = sanitize_str(data.get("full_name"), 120)
    email = sanitize_str(data.get("email"), 190)
    password = data.get("password") or ""

    if not full_name or not email or not password:
        return err("full_name, email and password are required", 422)
    if not is_valid_email(email):
        return err("Enter a valid email address", 422)
    if not is_strong_password(password):
        return err("Password must be at least 6 characters", 422)

    if User.query.filter_by(email=email.lower()).first():
        return err("An account with this email already exists", 409)

    user = User(full_name=full_name, email=email.lower(), role="user", subscription_type="free")
    user.set_password(password)
    db.session.add(user)
    db.session.flush()  # get user.id before commit

    sub = Subscription(user_id=user.id, plan="free", payment_status="none")
    db.session.add(sub)
    db.session.commit()

    access = generate_access_token(user.id, user.role)
    refresh = generate_refresh_token(user.id)
    return ok(
        {"user": user.to_dict(), "access_token": access, "refresh_token": refresh},
        "Registration successful",
        201,
    )


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = sanitize_str(data.get("email"), 190)
    password = data.get("password") or ""

    if not email or not password:
        return err("Email and password are required", 422)

    user = User.query.filter_by(email=email.lower()).first()
    if not user or not user.check_password(password):
        return err("Invalid email or password", 401)
    if not user.is_active:
        return err("This account has been deactivated", 403)

    access = generate_access_token(user.id, user.role)
    refresh = generate_refresh_token(user.id)
    return ok({"user": user.to_dict(), "access_token": access, "refresh_token": refresh}, "Login successful")


@auth_bp.post("/logout")
@token_required
def logout(current_user):
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    revoke(token)
    return ok(message="Logged out successfully")


@auth_bp.get("/me")
@token_required
def me(current_user):
    return ok({"user": current_user.to_dict()}, "Profile retrieved successfully")


@auth_bp.put("/me")
@token_required
def update_profile(current_user):
    data = request.get_json(silent=True) or {}
    full_name = sanitize_str(data.get("full_name"), 120)
    if full_name:
        current_user.full_name = full_name

    new_email = sanitize_str(data.get("email"), 190)
    if new_email and new_email.lower() != current_user.email:
        if not is_valid_email(new_email):
            return err("Enter a valid email address", 422)
        if User.query.filter_by(email=new_email.lower()).first():
            return err("Email already in use", 409)
        current_user.email = new_email.lower()

    current_user.updated_at = datetime.utcnow()
    db.session.commit()
    return ok({"user": current_user.to_dict()}, "Profile updated successfully")


@auth_bp.post("/change-password")
@token_required
def change_password(current_user):
    data = request.get_json(silent=True) or {}
    old_password = data.get("old_password") or ""
    new_password = data.get("new_password") or ""

    if not current_user.check_password(old_password):
        return err("Current password is incorrect", 401)
    if not is_strong_password(new_password):
        return err("New password must be at least 6 characters", 422)

    current_user.set_password(new_password)
    db.session.commit()
    return ok(message="Password changed successfully")
