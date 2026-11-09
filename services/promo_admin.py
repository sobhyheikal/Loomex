"""
Admin-side promotion helpers: validate the form, create, edit, switch on/off.
Kept separate from admin_data.py so that file does not need to change.
"""
import re
from uuid import UUID

from datetime import datetime

from services import promotions as promo_svc
from services.admin_data import ADMIN_TZ
from supabase_client import supabase

_CODE = re.compile(r"^[A-Za-z0-9_-]{3,30}$")
PCT_TYPES = {"percent_off", "second_item_pct", "buy_n_pct", "min_spend_pct"}


def products_for_picker() -> list[dict]:
    return (supabase.table("products").select("id,name,slug,category").is_("deleted_at", "null")
            .order("name").execute().data or [])


def list_promotions() -> list[dict]:
    return (supabase.table("promotions").select("*").is_("deleted_at", "null")
            .order("created_at", desc=True).execute().data or [])


def get_promotion(pid: str) -> dict | None:
    rows = (supabase.table("promotions").select("*").eq("id", pid)
            .is_("deleted_at", "null").limit(1).execute().data)
    return rows[0] if rows else None


# ---------------------------------------------------------------- form ----
def blank_form() -> dict:
    return {"title": "", "subtitle": "", "link_choice": "/shop", "link_url": "", "code": "",
            "product_ids": [], "discount_type": "", "value": "", "min_qty": "", "min_spend": "",
            "same_product": "", "starts": "", "ends": "", "show_banner": "1"}


def _g(x) -> str:
    """number -> text without trailing zeros (25.0 -> '25')"""
    return "" if x is None else f"{float(x):g}"


def _local(ts) -> str:
    """saved time -> what a date-and-time box shows (Cairo time)"""
    d = promo_svc._parse(ts)
    return d.astimezone(ADMIN_TZ).strftime("%Y-%m-%dT%H:%M") if d else ""


def _local_to_ts(v: str) -> str | None:
    """what a date-and-time box sends (Cairo time) -> value to save"""
    v = (v or "").strip()
    if not v:
        return None
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(v, fmt).replace(tzinfo=ADMIN_TZ).isoformat()
        except ValueError:
            pass
    raise ValueError(v)


def row_to_form(r: dict) -> dict:
    """A saved promotion -> the values shown in the form."""
    url = r.get("link_url") or ""
    f = blank_form()
    if not url:
        f["link_choice"] = "__none"
    elif url == "/shop" or url.startswith(("/shop?category=", "/product/")):
        f["link_choice"] = url
    else:
        f["link_choice"], f["link_url"] = "__custom", url
    f.update({
        "title": r.get("message") or "", "subtitle": r.get("subtitle") or "",
        "code": r.get("code") or "",
        "product_ids": [str(i) for i in (r.get("product_ids") or [])],
        "discount_type": r.get("discount_type") or "",
        "value": _g(r.get("value")), "min_qty": _g(r.get("min_qty")), "min_spend": _g(r.get("min_spend")),
        "same_product": "1" if r.get("bundle_same_product_only") else "",
        "starts": _local(r.get("starts_at")), "ends": _local(r.get("ends_at")),
        "show_banner": "" if r.get("show_banner") is False else "1",
    })
    return f


def build_row(f: dict) -> tuple[dict | None, str | None]:
    """Check the form. Returns (row, None) or (None, error message)."""
    title = f["title"].strip()
    if not title:
        return None, "Write a title for the promotion."
    if len(title) > 160:
        return None, "Keep the title under 160 characters."
    subtitle = f["subtitle"].strip()
    if len(subtitle) > 160:
        return None, "Keep the subtitle under 160 characters."

    choice = f["link_choice"]
    if choice == "__none":
        url = ""
    elif choice == "__custom":
        url = f["link_url"].strip()
        if not url:
            return None, "Type the banner link, or pick another option for 'Banner links to'."
        if not promo_svc.safe_link(url):
            return None, "The banner link must start with / or https://"
    else:
        url = choice if promo_svc.safe_link(choice) else "/shop"

    code = f["code"].strip()
    if code and not _CODE.match(code):
        return None, "The discount code can only use letters, numbers, - and _ (3 to 30 characters)."

    dtype = f["discount_type"]
    if dtype not in promo_svc.TYPE_BY_KEY:
        return None, "Choose a discount type."
    _, _, needs, optional, _ = promo_svc.TYPE_BY_KEY[dtype]
    names = {"value": promo_svc.VALUE_LABELS.get(dtype, "Value"), "min_qty": "Number of items",
             "min_spend": "Minimum spend"}
    vals = {"value": None, "min_qty": None, "min_spend": None}
    for name in (*needs, *optional):
        if name == "same_product":
            continue  # a tick box, handled below
        raw = (f.get(name) or "").strip()
        if not raw:
            if name in needs:
                return None, f"{names[name]} is required."
            continue
        try:
            x = float(raw)
        except ValueError:
            return None, f"{names[name]} must be a number."
        if x <= 0:
            return None, f"{names[name]} must be more than 0."
        if name == "value" and dtype in PCT_TYPES and x > 100:
            return None, f"{names[name]} can't be more than 100."
        if name == "min_qty":
            if x != int(x):
                return None, "Number of items must be a whole number."
            x = int(x)
            if x < (2 if dtype == "bundle_price" else 1):
                return None, "A bundle needs at least 2 items." if dtype == "bundle_price" else "Number of items must be at least 1."
        vals[name] = x

    ids = []
    for x in f.get("product_ids") or []:
        try:
            ids.append(str(UUID(x)))
        except ValueError:
            pass

    try:
        s, e = _local_to_ts(f["starts"]), _local_to_ts(f["ends"])
    except ValueError:
        return None, "Dates must look like 2026-12-31 18:00."
    if s and e and promo_svc._parse(e) < promo_svc._parse(s):
        return None, "The end is before the start."

    return {"message": title, "subtitle": subtitle or None,
            "link_url": url or None, "link_text": "Shop now" if url else None,
            "code": code.upper() or None, "product_ids": ids, "discount_type": dtype,
            "value": vals["value"], "min_qty": vals["min_qty"], "min_spend": vals["min_spend"],
            "bundle_same_product_only": bool(f.get("same_product")) and dtype == "bundle_price",
            "starts_at": s, "ends_at": e,
            "show_banner": bool(f.get("show_banner"))}, None


def friendly_error(e: Exception) -> str:
    s = str(e)
    if "promotions_code_unique" in s or ("duplicate key" in s and "code" in s):
        return "That discount code is already used by another promotion."
    if "does not exist" in s or "PGRST204" in s or "schema cache" in s:
        return "The database isn't updated yet. Run migration_promotions.sql in Supabase first."
    return "Couldn't save: " + s[:160]


# --------------------------------------------------------------- writes ----
def add(row: dict):
    supabase.table("promotions").insert(row).execute()
    promo_svc.clear_cache()


def update(pid: str, row: dict):
    supabase.table("promotions").update(row).eq("id", pid).execute()
    promo_svc.clear_cache()


def toggle_active(pid: str):
    p = get_promotion(pid)
    if p:
        update(pid, {"is_active": not p.get("is_active")})


def toggle_banner(pid: str):
    p = get_promotion(pid)
    if p:
        update(pid, {"show_banner": p.get("show_banner") is False})