"""
Admin login for Loomex.

Accounts: one shared admin account (email + password) stored in the
`admin_account` table, changeable from Admin -> Profile. Until a profile has
been saved, the ADMIN_PASSWORD from .env is the login (email is ignored).

The login cookie is a signed timestamp that also covers the current password,
so changing the password logs every other device out.

.env / Vercel variables:
  ADMIN_PASSWORD  first-time login, before a profile exists
  ADMIN_SECRET    any long random string (signs the login cookie)
"""

import hashlib
import hmac
import os
import re
import time
from datetime import datetime, timezone

from fastapi import Request

import config  # noqa: F401  (makes sure .env is loaded before we read it)
from supabase_client import supabase

COOKIE = "loomex_admin"
MAX_AGE = 60 * 60 * 24 * 14  # stay logged in for 14 days
MIN_PASSWORD = 8
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AdminLoginRequired(Exception):
    pass


def _env_password() -> str:
    return os.environ.get("ADMIN_PASSWORD", "")


def _secret() -> str:
    return os.environ.get("ADMIN_SECRET", "") or _env_password()


# ------------------------------------------------------------- account ----
def get_account() -> dict | None:
    try:
        rows = supabase.table("admin_account").select("*").eq("id", 1).limit(1).execute().data
    except Exception:  # table not created yet -> fall back to the .env password
        return None
    return rows[0] if rows else None


def valid_email(email: str) -> bool:
    return bool(_EMAIL.match(email or ""))


def hash_password(pw: str) -> str:
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 200_000)
    return f"pbkdf2${salt.hex()}${h.hex()}"


def _verify_hash(pw: str, stored: str) -> bool:
    try:
        _, salt, h = stored.split("$")
        calc = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200_000)
        return hmac.compare_digest(calc.hex(), h)
    except Exception:
        return False


def _env_match(pw: str) -> bool:
    return bool(_env_password()) and hmac.compare_digest(pw.encode(), _env_password().encode())


def configured(acct: dict | None = None) -> bool:
    return bool(acct) or bool(_env_password())


def verify_current(password: str, acct: dict | None) -> bool:
    """Is this the current admin password?"""
    return _verify_hash(password, acct["password_hash"]) if acct else _env_match(password)


def verify_login(password: str) -> bool:
    acct = get_account()
    if acct:
        return _verify_hash(password, acct["password_hash"])
    return _env_match(password)


def save_account(password_hash: str):
    acct = get_account()
    email = acct["email"] if acct else "admin@loomex.local"
    supabase.table("admin_account").upsert({
        "id": 1, "email": email, "password_hash": password_hash,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).execute()


# --------------------------------------------------------------- cookie ----
def _fingerprint(acct: dict | None) -> str:
    return acct["password_hash"][-24:] if acct else "env"


def _sign(ts: str, acct: dict | None) -> str:
    return hmac.new(_secret().encode(), f"{ts}.{_fingerprint(acct)}".encode(), hashlib.sha256).hexdigest()


def make_token(acct: dict | None) -> str:
    ts = str(int(time.time()))
    return f"{ts}.{_sign(ts, acct)}"


def valid_token(token: str | None, acct: dict | None) -> bool:
    if not token or "." not in token:
        return False
    ts, sig = token.split(".", 1)
    if not ts.isdigit() or not hmac.compare_digest(sig, _sign(ts, acct)):
        return False
    return time.time() - int(ts) < MAX_AGE


def require_admin(request: Request):
    acct = get_account()
    if not configured(acct) or not valid_token(request.cookies.get(COOKIE), acct):
        raise AdminLoginRequired()


def set_login_cookie(response, request: Request, acct: dict | None):
    secure = (request.url.scheme == "https"
              or request.headers.get("x-forwarded-proto", "") == "https")
    response.set_cookie(COOKIE, make_token(acct), max_age=MAX_AGE, httponly=True,
                        samesite="lax", secure=secure)