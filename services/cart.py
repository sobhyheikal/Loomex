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


def resolve_cart(cart: list[dict]):
    """Turn the cookie's {slug, size, color, qty} list into full line items
    with live name/price/image pulled from Supabase, plus a subtotal."""
    if not cart:
        return [], 0.0
    slugs = list({item["slug"] for item in cart})
    result = supabase.table("products").select("*").in_("slug", slugs).execute()
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
            "slug": p["slug"],
            "name": p["name"],
            "price": float(p["price"]),
            "image_url": p.get("image_url"),
            "size": item.get("size", ""),
            "color": item.get("color", ""),
            "qty": item["qty"],
            "line_total": line_total,
        })
    return lines, subtotal
