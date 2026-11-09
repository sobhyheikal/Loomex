"""
Promotions shown on the storefront and applied to carts.

The site reads them through get_live_promotions(), cached for 30 seconds so
pages don't hit Supabase on every view. The admin panel clears the cache when
it changes something.

Pricing rules (price_cart):
  * A promotion WITH a discount code only applies when the customer types that code.
  * A promotion WITHOUT a code applies automatically.
  * Money discounts do not stack: the single biggest money discount wins.
  * Free shipping and free gifts from any matching promotion still apply.
  * "Selected products" empty = the promotion covers every product.
"""

import time
from datetime import datetime, timezone

from supabase_client import supabase

_TTL = 30
_cache = {"t": 0.0, "rows": []}

# key, label, required fields, optional fields, hint shown under the type picker
DISCOUNT_TYPES = [
    ("percent_off", "% off", ("value",), (),
     "Takes a percentage off each selected product."),
    ("fixed_off", "Fixed amount off", ("value",), (),
     "Takes a fixed amount (EGP) off every unit of the selected products."),
    ("bogo", "Buy 1 Get 1", (), (),
     "Buy one, get one free. In each pair the cheaper item is free."),
    ("second_item_pct", "2nd item at X% off", ("value",), (),
     "Every second item gets the percentage off (the cheaper one in each pair)."),
    ("buy_n_get_1", "Buy N, get 1 free", ("min_qty",), (),
     "Buy N items and the next one is free (the cheapest in each group)."),
    ("buy_n_pct", "Buy N+, get % off", ("min_qty", "value"), (),
     "Buy at least N items and get a percentage off all of them."),
    ("bundle_price", "Bundle price", ("min_qty", "value"), (),
     "N items together for one fixed price."),
    ("min_spend_pct", "% off over min. spend", ("min_spend", "value"), (),
     "A percentage off once the selected items add up to the minimum spend."),
    ("free_gift", "Free gift", ("gift_text",), ("min_spend",),
     "The customer gets a free gift. It is written on the order so you can pack it."),
    ("free_shipping", "Free shipping", (), ("min_spend",),
     "Shipping becomes free, optionally above a minimum spend."),
]
TYPE_BY_KEY = {t[0]: t for t in DISCOUNT_TYPES}

# what the "Value" box is called for each type
VALUE_LABELS = {
    "percent_off": "Percent off (%)",
    "fixed_off": "Amount off each item (EGP)",
    "second_item_pct": "Percent off the 2nd item (%)",
    "buy_n_pct": "Percent off (%)",
    "bundle_price": "Bundle price (EGP)",
    "min_spend_pct": "Percent off (%)",
}


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


def get_banner_promotions() -> list[dict]:
    """Live promotions that are switched on for the homepage banner."""
    return [p for p in get_live_promotions() if p.get("show_banner") is not False]


# ------------------------------------------------------------ helpers ----
def _num(x) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def _int(x) -> int:
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return 0


def _r(x: float) -> int:
    """Round to whole EGP (half up), so shop prices and cart discounts always agree."""
    return int(x + 0.5)


def describe(p: dict) -> str:
    """Short text for a promotion's discount, e.g. '50% off' or 'Buy 3, get 1 free'."""
    t, v, n, s = p.get("discount_type"), _num(p.get("value")), _int(p.get("min_qty")), _num(p.get("min_spend"))
    over = f" over {s:g} EGP" if s else ""
    if t == "percent_off":
        return f"{v:g}% off"
    if t == "fixed_off":
        return f"{v:g} EGP off"
    if t == "bogo":
        return "Buy 1 Get 1 free"
    if t == "second_item_pct":
        return f"2nd item {v:g}% off"
    if t == "buy_n_get_1":
        return f"Buy {n}, get 1 free"
    if t == "buy_n_pct":
        return f"Buy {n}+, get {v:g}% off"
    if t == "bundle_price":
        return f"{n} for {v:g} EGP"
    if t == "min_spend_pct":
        return f"{v:g}% off over {s:g} EGP"
    if t == "free_gift":
        return f"Free gift: {p.get('gift_text') or 'gift'}{over}"
    if t == "free_shipping":
        return f"Free shipping{over}"
    return "Banner only"


def _ids(promo: dict) -> set[str]:
    return {str(i) for i in (promo.get("product_ids") or [])}


# --------------------------------------------------------- cart pricing ----
def _evaluate(promo: dict, lines: list[dict]) -> tuple[float, bool, str]:
    """(money discount, free shipping?, gift text) one promotion gives this cart.
    Each line needs: product_id, price (one unit), qty, line_total."""
    ids = _ids(promo)
    elig = [l for l in lines if not ids or str(l.get("product_id")) in ids]
    if not elig:
        return 0.0, False, ""
    units = sorted((u for l in elig for u in [float(l["price"])] * int(l["qty"])), reverse=True)
    es = sum(float(l["price"]) * int(l["qty"]) for l in elig)  # eligible subtotal
    t = promo.get("discount_type")
    v, n, s = _num(promo.get("value")), _int(promo.get("min_qty")), _num(promo.get("min_spend"))
    amount, ship, gift = 0.0, False, ""

    if t == "percent_off":
        amount = sum(u - _r(u * (1 - v / 100)) for u in units)
    elif t == "fixed_off":
        amount = sum(min(v, u) for u in units)
    elif t == "bogo":
        amount = sum(units[1::2])
    elif t == "second_item_pct":
        amount = sum(units[1::2]) * v / 100
    elif t == "buy_n_get_1" and n >= 1:
        amount = sum(units[n::n + 1])
    elif t == "buy_n_pct" and n >= 1 and len(units) >= n:
        amount = es * v / 100
    elif t == "bundle_price" and n >= 2:
        for i in range(0, len(units) - n + 1, n):
            amount += max(0.0, sum(units[i:i + n]) - v)
    elif t == "min_spend_pct" and es >= s:
        amount = es * v / 100
    elif t == "free_gift" and es >= s:
        gift = (promo.get("gift_text") or "Free gift").strip()
    elif t == "free_shipping" and es >= s:
        ship = True
    return round(min(amount, es), 2), ship, gift


def find_code(code: str | None, promos: list[dict] | None = None) -> dict | None:
    """The live promotion that owns this discount code (case-insensitive), or None."""
    code = (code or "").strip().lower()
    if not code:
        return None
    promos = get_live_promotions() if promos is None else promos
    for p in promos:
        if (p.get("code") or "").strip().lower() == code and p.get("discount_type"):
            return p
    return None


def price_cart(lines: list[dict], code: str | None = None, promos: list[dict] | None = None) -> dict:
    """What the promotions do to this cart.

    Returns: subtotal, discount (EGP), discount_title, free_shipping (bool),
    gifts (list of text), code_ok (None if no code typed, else True/False),
    note (one line for the order record, '' when nothing applied)."""
    promos = get_live_promotions() if promos is None else promos
    subtotal = round(sum(float(l["line_total"]) for l in lines), 2)
    code_promo = find_code(code, promos)

    best_amount, best_promo = 0.0, None
    free_ship, gifts, notes = False, [], []
    for p in promos:
        if not p.get("discount_type"):
            continue  # old banner-only promotion
        if p.get("code") and not (code_promo and p["id"] == code_promo["id"]):
            continue  # needs its code
        amount, ship, gift = _evaluate(p, lines)
        if ship:
            free_ship = True
        if gift and gift not in gifts:
            gifts.append(gift)
        if amount > best_amount:
            best_amount, best_promo = amount, p

    if best_promo:
        notes.append(f"{best_promo['message']} (-{best_amount:g} EGP)")
    if free_ship:
        notes.append("Free shipping")
    for g in gifts:
        notes.append(f"Free gift: {g}")
    return {
        "subtotal": subtotal,
        "discount": best_amount,
        "discount_title": best_promo["message"] if best_promo else "",
        "free_shipping": free_ship,
        "gifts": gifts,
        "code_ok": None if not (code or "").strip() else bool(code_promo),
        "note": " | ".join(notes),
    }


# ---------------------------------------------------------- shop prices ----
def apply_sale_prices(products: list[dict], promos: list[dict] | None = None) -> list[dict]:
    """Shop/product-page prices. Only '% off' and 'Fixed amount off' promotions that have
    no code change the price shown on a product. Sets price (sale), orig_price, sale_label.
    Products without a sale come back untouched."""
    promos = get_live_promotions() if promos is None else promos
    sale = [p for p in promos if p.get("discount_type") in ("percent_off", "fixed_off") and not p.get("code")]
    if not sale:
        return products
    out = []
    for prod in products:
        price = float(prod.get("price") or 0)
        best, label = price, ""
        for promo in sale:
            ids = _ids(promo)
            if ids and str(prod.get("id")) not in ids:
                continue
            v = _num(promo.get("value"))
            cand = _r(price * (1 - v / 100)) if promo["discount_type"] == "percent_off" else price - v
            cand = float(max(cand, 0))
            if cand < best:
                best, label = cand, describe(promo)
        if best < price:
            prod = dict(prod, price=best, orig_price=price, sale_label=label)
        out.append(prod)
    return out