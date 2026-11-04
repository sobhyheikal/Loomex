"""
Promotions shown on the storefront. The site reads them through
get_live_promotions(), cached for 30 seconds so pages don't hit Supabase on
every view. The admin panel clears the cache when it changes something.
"""

import time
from datetime import datetime, timezone

from supabase_client import supabase

_TTL = 30
_cache = {"t": 0.0, "rows": []}


def clear_cache():
    _cache["t"] = 0.0


def _parse(ts):
    if not ts:
        return None
    try:
        d = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def promo_state(p: dict, now: datetime | None = None) -> str:
    """'live', 'scheduled', 'ended' or 'off'."""
    now = now or datetime.now(timezone.utc)
    if not p.get("is_active"):
        return "off"
    start, end = _parse(p.get("starts_at")), _parse(p.get("ends_at"))
    if start and now < start:
        return "scheduled"
    if end and now > end:
        return "ended"
    return "live"


def safe_link(url: str | None) -> str:
    """Only allow site-relative or http(s) links (blocks javascript: etc.)."""
    url = (url or "").strip()
    if url.startswith("/") and not url.startswith("//"):
        return url
    if url.startswith(("https://", "http://")):
        return url
    return ""


def get_live_promotions() -> list[dict]:
    now_t = time.time()
    if now_t - _cache["t"] >= _TTL:
        _cache["t"] = now_t  # also on failure, so a missing table can't slow every page
        try:
            _cache["rows"] = (
                supabase.table("promotions").select("*")
                .eq("is_active", True).is_("deleted_at", "null")
                .order("created_at", desc=True).execute().data or []
            )
        except Exception:
            _cache["rows"] = []
    return [p for p in _cache["rows"] if promo_state(p) == "live"]