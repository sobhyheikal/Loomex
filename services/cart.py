"""
Cart cookie design: since there are no user accounts, the cart is stored in a
browser cookie as a small JSON list of {slug, size, color, qty}. Product
name/price/image are always re-fetched fresh from Supabase when needed
(cart page, checkout) so prices can never go stale in someone's cookie.
"""

import json

from fastapi import Request

from config import CART_COOKIE
from supabase_client import supabase


def get_cart(request: Request) -> list[dict]:
    raw = request.cookies.get(CART_COOKIE)
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_cart(response, cart: list[dict]):
    response.set_cookie(
        CART_COOKIE,
        json.dumps(cart),
        max_age=60 * 60 * 24 * 30,  # 30 days
        httponly=True,
        samesite="lax",
    )


def cart_item_count(cart: list[dict]) -> int:
    return sum(item.get("qty", 0) for item in cart)


def sold_out_reason(product: dict, size: str = "", color: str = "") -> str | None:
    """Why this product / size / color can't be bought right now, or None if it can."""
    if not product.get("in_stock", True):
        return "This product is sold out."
    sizes_out = {str(s).strip().lower() for s in (product.get("sold_out_sizes") or [])}
    colors_out = {str(c).strip().lower() for c in (product.get("sold_out_colors") or [])}
    if size and size.strip().lower() in sizes_out:
        return f"Size {size} is sold out."
    if color and color.strip().lower() in colors_out:
        return f"{color} is sold out."
    return None


def _line_image(product: dict, color: str):
    """First photo of the chosen color, else the product's main photo."""
    imgs = (product.get("color_images") or {}).get(color)
    if isinstance(imgs, list) and imgs:
        return imgs[0]
    if isinstance(imgs, str) and imgs:
        return imgs
    return product.get("image_url")


def resolve_cart(cart: list[dict]):
    """Turn the cookie's {slug, size, color, qty} list into full line items
    with live name/price/image pulled from Supabase, plus a subtotal."""
    if not cart:
        return [], 0.0
    slugs = list({item["slug"] for item in cart})
    result = (supabase.table("products").select("*").in_("slug", slugs)
              .is_("deleted_at", "null").eq("is_visible", True).execute())
    by_slug = {p["slug"]: p for p in result.data}

    lines = []
    subtotal = 0.0
    for i, item in enumerate(cart):
        p = by_slug.get(item["slug"])
        if not p:
            continue  # product was deleted/renamed since being added to cart
        line_total = float(p["price"]) * item["qty"]
        subtotal += line_total
        lines.append({
            "index": i,
                      "product_id": p["id"],
            "slug": p["slug"],
            "name": p["name"],
            "price": float(p["price"]),
            "image_url": _line_image(p, item.get("color", "")),
            "size": item.get("size", ""),
            "color": item.get("color", ""),
            "qty": item["qty"],
            "line_total": line_total,
        })
    return lines, subtotal


def cart_pricing(lines: list[dict]) -> dict:
    """Promotion discounts for these cart lines (see services/promotions.price_cart)."""
    try:
        from services.promotions import price_cart
        return price_cart(lines)
    except Exception:
        subtotal = round(sum(float(l["line_total"]) for l in lines), 2)
        return {"subtotal": subtotal, "discount": 0.0, "applied": [], "free_shipping": False,
                "gifts": [], "code_ok": None, "note": ""}