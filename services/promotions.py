"""
Promotions shown on the storefront and applied to carts.

The site reads them through get_live_promotions(), cached for 30 seconds so
pages don't hit Supabase on every view. The admin panel clears the cache when
it changes something.

Pricing rules (price_cart):
  * Any number of promotions can be live at the same time. ALL that match the cart apply.
  * A promotion WITH a discount code only applies when the customer types that code.
  * A promotion WITHOUT a code applies automatically.
  * "Selected products" empty = the promotion covers every product.
  * In deals like Buy 1 Get 1, the customer always pays for the MORE EXPENSIVE item;
    the cheaper one is the free / discounted one.
  * Promotions apply one after another on what is left to pay, so two promotions can
    never take more than the price. Order: price cuts (% off, fixed off), then quantity
    deals (BOGO, 2nd item, buy N, bundle), then % off over a minimum spend.
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
     "Buy one, get one free. In each pair the customer pays the more expensive item."),
    ("second_item_pct", "2nd item at X% off", ("value",), (),
     "Every second item gets the percentage off (the cheaper one in each pair)."),
    ("buy_n_get_1", "Buy N, get 1 free", ("min_qty",), (),
     "e.g. 2 for \"buy 2, get 1 free\". The cheapest item in each group is the free one."),
    ("buy_n_pct", "Buy N+, get % off", ("min_qty", "value"), (),
     "Buy at least N items and get a percentage off all of them."),
    ("bundle_price", "Bundle price", ("min_qty", "value"), ("same_product",),
     "N items together for one fixed price."),
    ("min_spend_pct", "% off over min. spend", ("min_spend", "value"), (),
     "A percentage off once the selected items add up to the minimum spend."),
    ("free_gift", "Free gift", ("min_spend",), (),
     "Customers spending over the minimum see that a free gift is included with their order."),
    ("free_shipping", "Free shipping", (), (),
     "Shipping is free on orders that include the selected products."),
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

# order promotions are applied in (see the rules above)
_GROUP = {"percent_off": 0, "fixed_off": 0, "bogo": 1, "second_item_pct": 1, "buy_n_get_1": 1,
          "buy_n_pct": 1, "bundle_price": 1, "min_spend_pct": 2, "free_gift": 3, "free_shipping": 3}


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
        same = " (same product)" if p.get("bundle_same_product_only") else ""
        return f"{n} for {v:g} EGP{same}"
    if t == "min_spend_pct":
        return f"{v:g}% off over {s:g} EGP"
    if t == "free_gift":
        return f"Free gift over {s:g} EGP"
    if t == "free_shipping":
        return "Free shipping"
    return "Banner only"


def _ids(promo: dict) -> set[str]:
    return {str(i) for i in (promo.get("product_ids") or [])}


# --------------------------------------------------------- cart pricing ----
def _apply(promo: dict, units: list[dict]) -> tuple[float, bool, bool]:
    """Apply one promotion to the cart's units (each: pid, orig, cur = what is left to pay).
    Lowers `cur` on the units it discounts. Returns (money taken off, free shipping?, free gift?)."""
    ids = _ids(promo)
    elig = sorted((u for u in units if not ids or u["pid"] in ids), key=lambda u: (-u["orig"], -u["cur"]))  # dearest first (normal price decides, then what is left)
    if not elig:
        return 0.0, False, False
    t = promo.get("discount_type")
    v, n, s = _num(promo.get("value")), _int(promo.get("min_qty")), _num(promo.get("min_spend"))
    spend = sum(u["orig"] for u in elig)  # thresholds look at the normal prices
    taken, ship, gift = 0.0, False, False

    def cut(u, amount):
        nonlocal taken
        amount = max(0.0, min(amount, u["cur"]))
        u["cur"] -= amount
        taken += amount

    if t == "percent_off":
        for u in elig:
            cut(u, u["cur"] - _r(u["cur"] * (1 - v / 100)))
    elif t == "fixed_off":
        for u in elig:
            cut(u, v)
    elif t == "bogo":
        for u in elig[1::2]:                      # the cheaper item of each pair is free
            cut(u, u["cur"])
    elif t == "second_item_pct":
        for u in elig[1::2]:
            cut(u, u["cur"] * v / 100)
    elif t == "buy_n_get_1" and n >= 1:
        for u in elig[n::n + 1]:                  # every (N+1)th item, the cheaper one of its group
            cut(u, u["cur"])
    elif t == "buy_n_pct" and n >= 1 and len(elig) >= n:
        for u in elig:
            cut(u, u["cur"] * v / 100)
    elif t == "bundle_price" and n >= 2:
        pools = [elig]
        if promo.get("bundle_same_product_only"):
            by_pid: dict[str, list] = {}
            for u in elig:
                by_pid.setdefault(u["pid"], []).append(u)
            pools = list(by_pid.values())
        for pool in pools:
            for i in range(0, len(pool) - n + 1, n):
                group = pool[i:i + n]
                total = sum(u["cur"] for u in group)
                if total > v > 0:
                    k = v / total                 # spread the saving over the items in the bundle
                    for u in group:
                        cut(u, u["cur"] * (1 - k))
    elif t == "min_spend_pct" and spend >= s:
        for u in elig:
            cut(u, u["cur"] * v / 100)
    elif t == "free_gift" and spend >= s:
        gift = True
    elif t == "free_shipping":
        ship = True
    return round(taken, 2), ship, gift


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
    """What the promotions do to this cart. Each line needs: product_id, price (one unit), qty, line_total.

    Returns: subtotal, discount (EGP, all promotions together), applied (list of {title, amount, what}),
    free_shipping (bool), gifts (list of text), code_ok (None if no code typed, else True/False),
    note (one line for the order record, '' when nothing applied)."""
    promos = get_live_promotions() if promos is None else promos
    subtotal = round(sum(float(l["line_total"]) for l in lines), 2)
    code_promo = find_code(code, promos)
    units = [{"pid": str(l.get("product_id")), "orig": float(l["price"]), "cur": float(l["price"])}
             for l in lines for _ in range(int(l["qty"]))]

    usable = [p for p in promos if p.get("discount_type")
              and (not p.get("code") or (code_promo and p["id"] == code_promo["id"]))]
    usable.sort(key=lambda p: _GROUP.get(p["discount_type"], 9))  # stable: keeps newest-first inside a group

    applied, free_ship, gifts = [], False, []
    for p in usable:
        amount, ship, gift = _apply(p, units)
        if amount > 0:
            applied.append({"title": p["message"], "amount": amount, "what": describe(p)})
        if ship:
            free_ship = True
        if gift:
            gifts.append(p["message"])

    discount = round(sum(a["amount"] for a in applied), 2)
    notes = [f"{a['title']} (-{a['amount']:g} EGP)" for a in applied]
    if free_ship:
        notes.append("Free shipping")
    notes += [f"Free gift: {g}" for g in gifts]
    return {
        "subtotal": subtotal, "discount": discount, "applied": applied,
        "free_shipping": free_ship, "gifts": gifts,
        "code_ok": None if not (code or "").strip() else bool(code_promo),
        "note": " | ".join(notes),
    }


# ---------------------------------------------------------- shop prices ----
def apply_sale_prices(products: list[dict], promos: list[dict] | None = None) -> list[dict]:
    """Shop/product-page prices. Only '% off' and 'Fixed amount off' promotions that have
    no code change the price shown on a product (all of them, one after another, same as the cart).
    Sets price (sale), orig_price, sale_label. Products without a sale come back untouched."""
    promos = get_live_promotions() if promos is None else promos
    sale = [p for p in promos if p.get("discount_type") in ("percent_off", "fixed_off") and not p.get("code")]
    if not sale:
        return products
    out = []
    for prod in products:
        orig = float(prod.get("price") or 0)
        price, labels = orig, []
        for promo in sale:
            ids = _ids(promo)
            if ids and str(prod.get("id")) not in ids:
                continue
            v = _num(promo.get("value"))
            new = _r(price * (1 - v / 100)) if promo["discount_type"] == "percent_off" else max(price - v, 0)
            if new < price:
                price = float(new)
                labels.append(describe(promo))
        if price < orig:
            prod = dict(prod, price=price, orig_price=orig, sale_label=" + ".join(labels))
        out.append(prod)
    return out