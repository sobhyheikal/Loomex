"""
Everything the admin panel reads and writes in Supabase.

Soft delete: products, orders and promotions get a `deleted_at` timestamp
instead of being removed. They vanish from the site and the admin lists, show
up in Recently Deleted, and are removed for good after RETENTION_DAYS.
"""

import re
from datetime import datetime, timedelta, timezone

from config import CATEGORIES, SUBCATEGORIES
from services import promotions as promo_svc
from supabase_client import supabase

try:
    from zoneinfo import ZoneInfo
    ADMIN_TZ = ZoneInfo("Africa/Cairo")
except Exception:  # tzdata missing
    ADMIN_TZ = timezone.utc

RETENTION_DAYS = 30
KINDS = ("products", "orders", "promotions")

ORDER_STATUSES = ["new", "confirmed", "shipped", "delivered", "cancelled"]
PAYMENT_STATUSES = ["pending", "paid"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _clean_search(q: str | None) -> str:
    """Strip characters that would break a PostgREST or_() filter."""
    return re.sub(r"[,()%*\\\"']", " ", (q or "")).strip()[:60]


def _digits(s: str | None) -> str:
    return re.sub(r"\D", "", s or "")


# ------------------------------------------------------------- products ----
def list_products() -> list[dict]:
    return (supabase.table("products").select("*").is_("deleted_at", "null")
            .order("created_at", desc=True).execute().data or [])


def get_product(pid: str) -> dict | None:
    rows = (supabase.table("products").select("*").eq("id", pid)
            .is_("deleted_at", "null").limit(1).execute().data)
    return rows[0] if rows else None


def insert_product(row: dict):
    supabase.table("products").insert(row).execute()


def update_product(pid: str, row: dict):
    supabase.table("products").update(row).eq("id", pid).execute()


def _split(text: str) -> list[str]:
    return [x.strip() for x in (text or "").replace("\n", ",").split(",") if x.strip()]


def parse_photos(text: str) -> dict:
    """'Black = url1 | url2' per line -> {"Black": ["url1", "url2"]}"""
    out = {}
    for line in (text or "").splitlines():
        color, _, rest = line.partition("=")
        color = color.strip()
        urls = [u.strip() for u in rest.split("|") if u.strip()]
        if color and urls:
            out[color] = urls
    return out


def photos_to_text(color_images: dict | None) -> str:
    lines = []
    for color, urls in (color_images or {}).items():
        if isinstance(urls, str):
            urls = [urls]
        lines.append(f"{color} = " + " | ".join(urls))
    return "\n".join(lines)


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")


def blank_product_form() -> dict:
    return {"name": "", "slug": "", "description": "", "category": CATEGORIES[0],
            "subcategory": "", "price": "", "sizes": "S, M, L, XL", "colors": "",
            "image_url": "", "photos": "", "in_stock": True}


def product_to_form(p: dict) -> dict:
    return {
        "name": p.get("name") or "", "slug": p.get("slug") or "",
        "description": p.get("description") or "", "category": p.get("category") or "",
        "subcategory": p.get("subcategory") or "",
        "price": f"{float(p.get('price') or 0):g}",
        "sizes": ", ".join(p.get("sizes") or []), "colors": ", ".join(p.get("colors") or []),
        "image_url": p.get("image_url") or "",
        "photos": photos_to_text(p.get("color_images")),
        "in_stock": bool(p.get("in_stock", True)),
    }


def build_product_row(form: dict, creating: bool) -> tuple[dict | None, str | None]:
    """Validate the product form. Returns (row, None) or (None, error message)."""
    name = form["name"].strip()
    if not name:
        return None, "Name is required."
    try:
        price = round(float(form["price"]), 2)
    except ValueError:
        return None, "Price must be a number."
    if price <= 0:
        return None, "Price must be more than 0."
    category = form["category"]
    if category not in CATEGORIES:
        return None, "Pick a category."
    sub = form["subcategory"] or None
    if sub and sub not in SUBCATEGORIES.get(category, []):
        return None, f"'{sub}' isn't a sub-category of {category}."
    sizes = _split(form["sizes"])
    if not sizes:
        return None, "Add at least one size."
    colors = _split(form["colors"])
    photos = parse_photos(form["photos"])
    if not colors and photos:
        colors = list(photos)
    lower = {c.lower() for c in colors}
    for c in photos:
        if c.lower() not in lower:
            return None, f"Photos line '{c}' doesn't match any color. Colors must be spelled exactly the same."
    # keep the exact color spelling from the colors list
    exact = {c.lower(): c for c in colors}
    photos = {exact[c.lower()]: u for c, u in photos.items()}
    image_url = form["image_url"].strip()
    if not image_url and photos:
        image_url = next(iter(photos.values()))[0]

    row = {
        "name": name, "description": form["description"].strip() or None,
        "category": category, "subcategory": sub, "price": price, "sizes": sizes,
        "colors": colors, "image_url": image_url or None, "color_images": photos,
        "in_stock": bool(form["in_stock"]),
    }
    if creating:
        slug = slugify(form["slug"] or name)
        if not slug:
            return None, "Enter a slug (letters and numbers)."
        row["slug"] = slug
    return row, None


def friendly_db_error(e: Exception) -> str:
    s = str(e)
    if "duplicate key" in s and "slug" in s:
        return "That slug is already used. It may belong to a product in Recently Deleted."
    return "Couldn't save: " + s[:160]


# --------------------------------------------------------------- orders ----
def list_orders(q: str | None = None, limit: int = 100) -> list[dict]:
    qb = supabase.table("orders").select("*, order_items(*)").is_("deleted_at", "null")
    q = _clean_search(q)
    if q:
        qb = qb.or_(f"order_number.ilike.*{q}*,customer_name.ilike.*{q}*,"
                    f"phone.ilike.*{q}*,email.ilike.*{q}*")
    return qb.order("created_at", desc=True).limit(limit).execute().data or []


def update_order_status(oid: str, status: str, payment_status: str):
    supabase.table("orders").update(
        {"status": status[:40], "payment_status": payment_status[:40]}
    ).eq("id", oid).execute()


# ------------------------------------------------------------ customers ----
def list_customers(q: str | None = None) -> list[dict]:
    """Customers are built from orders (the shop has no accounts)."""
    rows = (supabase.table("orders")
            .select("customer_name,phone,email,total,status,created_at")
            .is_("deleted_at", "null").order("created_at", desc=True)
            .limit(5000).execute().data or [])
    people: dict[str, dict] = {}
    for r in rows:  # newest first, so the first row seen has the latest details
        key = _digits(r.get("phone")) or (r.get("email") or "").lower() or (r.get("customer_name") or "").lower()
        c = people.setdefault(key, {"name": r.get("customer_name") or "", "phone": r.get("phone") or "",
                                    "email": "", "orders": 0, "spent": 0.0, "last": r.get("created_at")})
        c["orders"] += 1
        if not c["email"] and r.get("email"):
            c["email"] = r["email"]
        if r.get("status") != "cancelled":
            c["spent"] += float(r.get("total") or 0)
    out = list(people.values())
    q = (q or "").strip().lower()
    if q:
        qd = _digits(q)
        out = [c for c in out if q in c["name"].lower() or q in c["email"].lower()
               or q in c["phone"].lower() or (qd and qd in _digits(c["phone"]))]
    return out


# ----------------------------------------------------------- promotions ----
def list_promotions() -> list[dict]:
    return (supabase.table("promotions").select("*").is_("deleted_at", "null")
            .order("created_at", desc=True).execute().data or [])


def _day_to_ts(day: str, end: bool) -> str | None:
    if not day:
        return None
    d = datetime.strptime(day, "%Y-%m-%d")
    d = d.replace(hour=23, minute=59, second=59) if end else d
    return d.replace(tzinfo=ADMIN_TZ).isoformat()


def build_promotion_row(message, link_text, link_url, starts, ends) -> tuple[dict | None, str | None]:
    message = (message or "").strip()
    if not message:
        return None, "Write the promotion text."
    if len(message) > 160:
        return None, "Keep the promotion text under 160 characters."
    url = (link_url or "").strip()
    if url and not promo_svc.safe_link(url):
        return None, "The link must start with / or https://"
    try:
        s, e = _day_to_ts(starts, False), _day_to_ts(ends, True)
    except ValueError:
        return None, "Dates must look like 2026-12-31."
    if s and e and e < s:
        return None, "The end date is before the start date."
    return {"message": message, "link_url": url or None,
            "link_text": ((link_text or "").strip() or "Shop now") if url else None,
            "starts_at": s, "ends_at": e, "is_active": True}, None


def add_promotion(row: dict):
    supabase.table("promotions").insert(row).execute()
    promo_svc.clear_cache()


def toggle_promotion(pid: str):
    rows = supabase.table("promotions").select("is_active").eq("id", pid).limit(1).execute().data
    if rows:
        supabase.table("promotions").update({"is_active": not rows[0]["is_active"]}).eq("id", pid).execute()
        promo_svc.clear_cache()


# ------------------------------------------------- recently deleted -------
def soft_delete(kind: str, rid: str):
    supabase.table(kind).update({"deleted_at": _now().isoformat()}).eq("id", rid).execute()
    promo_svc.clear_cache()


def restore(kind: str, rid: str):
    supabase.table(kind).update({"deleted_at": None}).eq("id", rid).execute()
    promo_svc.clear_cache()


def purge(kind: str, rid: str):
    if kind == "products":  # keep past orders; they still hold the product name
        supabase.table("order_items").update({"product_id": None}).eq("product_id", rid).execute()
    supabase.table(kind).delete().eq("id", rid).execute()  # order_items cascade with orders
    promo_svc.clear_cache()


def purge_expired():
    cutoff = (_now() - timedelta(days=RETENTION_DAYS)).isoformat()
    for kind in KINDS:
        for r in supabase.table(kind).select("id").lt("deleted_at", cutoff).execute().data or []:
            purge(kind, r["id"])


def list_deleted() -> dict:
    spec = {
        "products": "id,name,category,price,deleted_at",
        "orders": "id,order_number,customer_name,total,deleted_at",
        "promotions": "id,message,deleted_at",
    }
    out = {}
    now = _now()
    for kind, cols in spec.items():
        rows = (supabase.table(kind).select(cols).not_.is_("deleted_at", "null")
                .order("deleted_at", desc=True).execute().data or [])
        items = []
        for r in rows:
            when = promo_svc._parse(r["deleted_at"]) or now
            left = max(0, RETENTION_DAYS - (now - when).days)
            if kind == "products":
                label, detail = r["name"], f"{r['category']} · {float(r['price']):.0f} EGP"
            elif kind == "orders":
                label, detail = f"Order {r['order_number']}", f"{r['customer_name']} · {float(r['total']):.0f} EGP"
            else:
                label, detail = r["message"], "Promotion"
            items.append({"id": r["id"], "label": label, "detail": detail,
                          "deleted_at": r["deleted_at"], "days_left": left})
        out[kind] = items
    return out