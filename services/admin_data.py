"""
Everything the admin panel reads and writes in Supabase.

Soft delete: products, orders and promotions get a `deleted_at` timestamp
instead of being removed. They vanish from the site and the admin lists, show
up in Recently Deleted, and are removed for good after RETENTION_DAYS.
"""
import re
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote

from config import CATEGORIES, SUBCATEGORIES
from services import promotions as promo_svc
from supabase_client import supabase
BUCKET = "product_images"
IMAGE_TYPES = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/gif": "gif"}
MAX_UPLOAD = 8 * 1024 * 1024
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


def set_visible(pid: str, visible: bool):
    """Switch a product ON (shown on the website) or OFF (hidden there, kept in the admin)."""
    supabase.table("products").update({"is_visible": bool(visible)}).eq("id", pid).execute()


def insert_product(row: dict):
    supabase.table("products").insert(row).execute()


def update_product(pid: str, row: dict):
    old = (supabase.table("products").select("image_url,color_images").eq("id", pid)
           .limit(1).execute().data or [None])[0]
    supabase.table("products").update(row).eq("id", pid).execute()
    try:
        delete_unused_photos(old, row, pid)
    except Exception:
        pass  # a failed clean-up must never stop the product from saving


PUBLIC_MARK = f"/storage/v1/object/public/{BUCKET}/"


def _bucket_path(url: str) -> str | None:
    """The file path inside the bucket for one of our own photo links, otherwise None."""
    mark = f"/storage/v1/object/public/{BUCKET}/"
    if mark not in (url or ""):
        return None
    return unquote(url.split(mark, 1)[1].split("?", 1)[0]) or None
    """The file path inside the bucket for one of our own photo links, otherwise None."""
    if PUBLIC_MARK not in (url or ""):
        return None
    return unquote(url.split(PUBLIC_MARK, 1)[1].split("?", 1)[0]) or None


def _photo_urls(p: dict | None) -> set[str]:
    urls = set()
    if not p:
        return urls
    if p.get("image_url"):
        urls.add(p["image_url"])
    for v in (p.get("color_images") or {}).values():
        urls.update([v] if isinstance(v, str) else (v or []))
    return {u for u in urls if u}


def _all_photo_urls(skip_id: str | None = None) -> set[str]:
    """Every photo link any product uses, deleted ones too (they can still be restored)."""
    urls = set()
    for p in supabase.table("products").select("id,image_url,color_images").execute().data or []:
        if skip_id and str(p["id"]) == str(skip_id):
            continue
        urls |= _photo_urls(p)
    return urls


def _remove_files(urls):
    paths = [x for x in (_bucket_path(u) for u in urls) if x]
    if paths:
        supabase.storage.from_(BUCKET).remove(paths)


def delete_unused_photos(old: dict | None, new_row: dict, pid: str):
    """After a product is saved: delete the photos it no longer uses from the bucket,
    unless another product still uses the same file."""
    gone = _photo_urls(old) - _photo_urls(new_row)
    if gone:
        _remove_files(gone - _all_photo_urls(skip_id=pid))


def delete_photo_if_unused(url: str):
    """Used when you tap x on a photo: delete the file only if no product uses it."""
    if url and url not in _all_photo_urls():
        _remove_files([url])


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
            "image_url": "", "photos": "", "in_stock": True, "sold_out": [], "sold_out_colors": []}


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
        "sold_out": list(p.get("sold_out_sizes") or []),
        "sold_out_colors": list(p.get("sold_out_colors") or []),
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
    if not sub and SUBCATEGORIES.get(category):
        return None, f"Choose a sub-category for {category.replace('-', ' ').title()} first."
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

    sc = form.get("sold_out_colors") or []
    if isinstance(sc, str):
        sc = _split(sc)
    sold_colors = {c.strip().lower() for c in sc}

    row = {
        "name": name, "description": form["description"].strip() or None,
        "category": category, "subcategory": sub, "price": price, "sizes": sizes,
        "colors": colors, "image_url": image_url or None, "color_images": photos,
        "in_stock": bool(form["in_stock"]),
        "sold_out_sizes": [s for s in sizes if s in form.get("sold_out", [])],
        "sold_out_colors": [c for c in colors if c.lower() in sold_colors],
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
BUCKET = "product_images"
IMAGE_TYPES = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/gif": "gif"}
MAX_UPLOAD = 8 * 1024 * 1024


def upload_image(folder: str, filename: str, content: bytes, content_type: str) -> str:
    """Put a photo in the storage bucket and return its public link."""
    ext = IMAGE_TYPES.get((content_type or "").lower())
    if not ext:
        raise ValueError("Choose a PNG, JPG, WEBP or GIF image.")
    if not content:
        raise ValueError("That file is empty.")
    if len(content) > MAX_UPLOAD:
        raise ValueError("That image is too big (8 MB max).")
    stem = slugify(filename.rsplit(".", 1)[0]) or "photo"
    folder = slugify(folder) or "uploads"
    path = f"{folder}/{stem}-{secrets.token_hex(3)}.{ext}"
    supabase.storage.from_(BUCKET).upload(path, content, {"content-type": content_type, "upsert": "false"})
    url = supabase.storage.from_(BUCKET).get_public_url(path)
    if isinstance(url, dict):
        url = url.get("publicURL") or url.get("publicUrl") or ""
    return str(url).rstrip("?")

# --------------------------------------------------------------- orders ----
_CACHE: dict = {}


def _cached(key, ttl, fn):
    """Remember fn()'s result for ttl seconds so repeat page views skip the database."""
    from time import monotonic
    hit = _CACHE.get(key)
    if hit and monotonic() - hit[0] < ttl:
        return hit[1]
    val = fn()
    _CACHE[key] = (monotonic(), val)
    return val


def _photo_products() -> list[dict]:
    return _cached("photo_products", 120, lambda: supabase.table("products")
                   .select("id,name,image_url,color_images").execute().data or [])


def _customer_rows() -> list[dict]:
    return _cached("customer_rows", 30, lambda: supabase.table("orders")
                   .select("customer_name,phone,email,total,status,created_at")
                   .is_("deleted_at", "null").order("created_at", desc=True)
                   .limit(5000).execute().data or [])
def list_orders(q: str | None = None, limit: int = 100) -> list[dict]:
    qb = supabase.table("orders").select("*, order_items(*)").is_("deleted_at", "null")
    q = _clean_search(q)
    if q:
        qb = qb.or_(f"order_number.ilike.*{q}*,customer_name.ilike.*{q}*,"
                    f"phone.ilike.*{q}*,email.ilike.*{q}*")
    orders = qb.order("created_at", desc=True).limit(limit).execute().data or []
    _attach_item_images(orders)
    return orders


def _attach_item_images(orders: list[dict]):
    """Give every order item an `image` (the photo of the color that was bought).
    Items are matched to their product by product_id, or by product name when the id is missing."""
    items = [i for o in orders for i in (o.get("order_items") or [])]
    ids = {str(i["product_id"]) for i in items if i.get("product_id")}
    names = {(i.get("product_name") or "").strip().lower() for i in items if not i.get("product_id")}
    names.discard("")
    by_id, by_name = {}, {}
    by_id, by_name = {}, {}
    try:
        for p in _photo_products():
            by_id[str(p["id"])] = p
            by_name[(p.get("name") or "").strip().lower()] = p
    except Exception:
        return  # photos are a nice extra: never break the orders page over them
    for i in items:
        p = by_id.get(str(i.get("product_id"))) or by_name.get((i.get("product_name") or "").strip().lower())
        if not p:
            continue
        wanted = (i.get("color") or "").strip().lower()
        photo = None
        for color, urls in (p.get("color_images") or {}).items():
            if color.strip().lower() == wanted:
                photo = urls[0] if isinstance(urls, list) and urls else (urls if isinstance(urls, str) else None)
                break
        i["image"] = photo or p.get("image_url") or ""


def update_order_status(oid: str, status: str, payment_status: str = ""):
    """Delivered and Paid go together:
      * choosing Delivered marks the order Paid
      * choosing Paid marks the order Delivered
      * moving a delivered order back to New / Confirmed / Shipped makes it unpaid again,
        so it returns to the Active tab.
    `delivered_at` remembers when the order was delivered (for the Completed tab)."""
    status = status[:40]
    payment_status = payment_status[:40]
    old = (supabase.table("orders").select("status,payment_status,delivered_at").eq("id", oid)
           .limit(1).execute().data or [None])[0] or {}
    old_status, old_pay = old.get("status") or "new", old.get("payment_status") or "pending"

    status_changed = status != old_status
    pay_changed = bool(payment_status) and payment_status != old_pay
    pay = payment_status  # "" means: leave the payment alone (cancelled orders send only a status)

    if status_changed:
        if status == "delivered":
            pay = "paid"
        elif old_status == "delivered" and status != "cancelled":
            pay = "pending"
    elif pay_changed and payment_status == "paid" and status != "cancelled":
        status = "delivered"
    if status == "delivered" and pay != "paid" and (status_changed or pay_changed):
        pay = "paid"

    row = {"status": status}
    if pay:
        row["payment_status"] = pay[:40]
    if status == "delivered":
        if old_status != "delivered" or not old.get("delivered_at"):
            row["delivered_at"] = _now().isoformat()
    else:
        row["delivered_at"] = None
    supabase.table("orders").update(row).eq("id", oid).execute()


ORDER_VIEWS = [("active", "Active"), ("cancelled", "Cancelled"),
               ("completed", "Completed"), ("history", "History")]


def filter_orders(orders: list[dict], view: str) -> list[dict]:
    """Orders tabs. Completed = delivered within the last 7 days, History = delivered earlier.
    The 7 days count from the day it was marked delivered (older rows fall back to the order date)."""
    if view == "all":
        return orders
    week_ago = _now() - timedelta(days=7)
    out = []
    for o in orders:
        status = o.get("status") or "new"
        when = promo_svc._parse(o.get("delivered_at")) or promo_svc._parse(o.get("created_at")) or _now()
        if view == "active" and status not in ("delivered", "cancelled"):
            out.append(o)
        elif view == "cancelled" and status == "cancelled":
            out.append(o)
        elif view == "completed" and status == "delivered" and when >= week_ago:
            out.append(o)
        elif view == "history" and status == "delivered" and when < week_ago:
            out.append(o)
    return out


# ------------------------------------------------------------ customers ----
def list_customers(q: str | None = None) -> list[dict]:
    """Customers are built from orders (the shop has no accounts)."""
    rows = _customer_rows()
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


def dashboard_data() -> dict:
    """Numbers for the admin Home page. Cancelled orders never count towards sales."""
    from datetime import timedelta
    now = _now().astimezone(ADMIN_TZ)
    today = now.date()
    from concurrent.futures import ThreadPoolExecutor

    def _orders():  # only the 3 columns the numbers need
        return (supabase.table("orders").select("total,status,created_at").is_("deleted_at", "null")
                .order("created_at", desc=True).limit(1000).execute().data or [])

    def _recent():
        return (supabase.table("orders").select("*").is_("deleted_at", "null")
                .order("created_at", desc=True).limit(5).execute().data or [])

    def _prods():
        return (supabase.table("products").select("id,in_stock,is_visible")
                .is_("deleted_at", "null").execute().data or [])

    def _safe(fn):
        try:
            return fn()
        except Exception:
            return []

    with ThreadPoolExecutor(max_workers=3) as pool:  # the 3 queries run at the same time
        f1, f2, f3 = pool.submit(_safe, _orders), pool.submit(_safe, _recent), pool.submit(_safe, _prods)
        orders, recent, prods = f1.result(), f2.result(), f3.result()

    def state(o):
        s = str(o.get("status") or "").lower()
        if "cancel" in s:
            return "cancelled"
        if "complete" in s or "deliver" in s:
            return "done"
        return "open"

    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    by_day = {d: 0.0 for d in days}
    today_sales = month_sales = 0.0
    today_orders = month_orders = open_orders = 0
    for o in orders:
        st = state(o)
        if st == "open":
            open_orders += 1
        if st == "cancelled":
            continue
        when = promo_svc._parse(o.get("created_at"))
        if not when:
            continue
        day = when.astimezone(ADMIN_TZ).date()
        total = float(o.get("total") or 0)
        if day == today:
            today_sales += total
            today_orders += 1
        if 0 <= (today - day).days < 30:
            month_sales += total
            month_orders += 1
        if day in by_day:
            by_day[day] += total

    visible = [p for p in prods if p.get("is_visible") is not False]
    return {
        "hour": now.hour,
        "weekday": now.strftime("%A %d %B"),
        "today_sales": today_sales, "today_orders": today_orders,
        "month_sales": month_sales, "month_orders": month_orders,
        "open_orders": open_orders,
        "week": [{"label": d.strftime("%a"), "sales": by_day[d], "today": d == today} for d in days],
         "recent": recent,
        "visible_products": len(visible),
        "sold_out": sum(1 for p in visible if p.get("in_stock") is False),
        "live_promos": len(promo_svc.get_live_promotions()),
    }
