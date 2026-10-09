"""
Loomex storefront — FastAPI app.

Entrypoint file: Vercel automatically detects a `FastAPI` instance named
`app` in main.py at the project root, so this file needs zero extra
Vercel config to deploy.

Cart design: since there are no user accounts, the cart is stored in a
browser cookie as a small JSON list of {slug, size, color, qty}. Product
name/price/image are always re-fetched fresh from Supabase when needed
(cart page, checkout) so prices can never go stale in someone's cookie.
"""

import json
import uuid
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from supabase_client import supabase
import templates

app = FastAPI()

# Serving /static/* — Vercel promotes this to its CDN automatically.
app.mount("/static", StaticFiles(directory="static"), name="static")

CATEGORIES = ["tops", "tank-tops", "pants", "pullovers", "quarter-zips", "jackets"]
SUBCATEGORIES = {"pants": ["joggers", "checkered-pants"]}
CART_COOKIE = "loomex_cart"


# ------------------------------------------------------------- cart utils --
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


def _get_product_or_404(slug: str):
    result = supabase.table("products").select("*").eq("slug", slug).single().execute()
    return result.data


# ---------------------------------------------------------------- home ----
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    cart_count = cart_item_count(get_cart(request))
    return templates.landing_page(CATEGORIES, cart_count, subcategories=SUBCATEGORIES)


@app.get("/shop", response_class=HTMLResponse)
def shop(request: Request, category: str | None = None, subcategory: str | None = None):
    query = supabase.table("products").select("*").eq("in_stock", True)
    if category in CATEGORIES:
        query = query.eq("category", category)
        if subcategory in SUBCATEGORIES.get(category, []):
            query = query.eq("subcategory", subcategory)
        else:
            subcategory = None
    else:
        subcategory = None
    result = query.order("created_at", desc=True).execute()
    cart_count = cart_item_count(get_cart(request))
    return templates.shop_page(
        result.data, CATEGORIES, category, cart_count,
        subcategories=SUBCATEGORIES, active_subcategory=subcategory,
    )


# ------------------------------------------------------------- product ----
@app.get("/product/{slug}", response_class=HTMLResponse)
def product_detail(request: Request, slug: str):
    p = _get_product_or_404(slug)
    if not p:
        return HTMLResponse("<h1>Product not found</h1>", status_code=404)
    cart_count = cart_item_count(get_cart(request))
    return templates.product_page(p, CATEGORIES, cart_count, subcategories=SUBCATEGORIES)


# ----------------------------------------------------------------- cart ----
@app.post("/cart/add")
def add_to_cart(
    request: Request,
    product: str = Form(...),
    size: str = Form(""),
    color: str = Form(""),
    qty: int = Form(1),
):
    qty = max(1, min(qty, 10))
    cart = get_cart(request)

    for item in cart:
        if item["slug"] == product and item.get("size", "") == size and item.get("color", "") == color:
            item["qty"] = min(10, item["qty"] + qty)
            break
    else:
        cart.append({"slug": product, "size": size, "color": color, "qty": qty})

    resp = RedirectResponse(url="/cart", status_code=303)
    save_cart(resp, cart)
    return resp


@app.get("/cart", response_class=HTMLResponse)
def view_cart(request: Request):
    cart = get_cart(request)
    lines, subtotal = resolve_cart(cart)
    cart_count = cart_item_count(cart)
    return templates.cart_page(lines, subtotal, CATEGORIES, cart_count, subcategories=SUBCATEGORIES)


@app.post("/cart/update")
def update_cart_line(request: Request, index: int = Form(...), qty: int = Form(...)):
    cart = get_cart(request)
    qty = max(1, min(qty, 10))
    if 0 <= index < len(cart):
        cart[index]["qty"] = qty
    resp = RedirectResponse(url="/cart", status_code=303)
    save_cart(resp, cart)
    return resp


@app.post("/cart/remove")
def remove_cart_line(request: Request, index: int = Form(...)):
    cart = get_cart(request)
    if 0 <= index < len(cart):
        cart.pop(index)
    resp = RedirectResponse(url="/cart", status_code=303)
    save_cart(resp, cart)
    return resp


# ------------------------------------------------------------ checkout ----
@app.get("/checkout", response_class=HTMLResponse)
def checkout_form(request: Request):
    cart = get_cart(request)
    if not cart:
        return RedirectResponse(url="/cart", status_code=303)
    lines, subtotal = resolve_cart(cart)
    cart_count = cart_item_count(cart)
    return templates.checkout_page(lines, subtotal, CATEGORIES, cart_count, subcategories=SUBCATEGORIES)


@app.post("/checkout", response_class=HTMLResponse)
def place_order(
    request: Request,
    customer_name: str = Form(...),
    phone: str = Form(...),
    city: str = Form(...),
    address: str = Form(...),
):
    cart = get_cart(request)
    if not cart:
        return RedirectResponse(url="/cart", status_code=303)

    lines, subtotal = resolve_cart(cart)
    if not lines:
        return RedirectResponse(url="/cart", status_code=303)

    # -----------------------------------------------------------------
    # SHIPPING COST — placeholder for now.
    # -----------------------------------------------------------------
    # Once you have per-city delivery rates and coverage worked out, add
    # a lookup here, e.g.:
    #   SHIPPING_RATES = {"Cairo": 60, "Alexandria": 70, ...}
    #   shipping = SHIPPING_RATES.get(city, None)
    #   if shipping is None: show an error, that city isn't covered yet
    # and add `shipping` into `total` below. Until then, the order total
    # is just the product subtotal, and delivery cost/coverage is
    # confirmed with the customer by phone after ordering.
    total = subtotal

    order_number = f"LMX-{uuid.uuid4().hex[:8].upper()}"

    order_insert = supabase.table("orders").insert({
        "order_number": order_number,
        "customer_name": customer_name,
        "phone": phone,
        "address": address,
        "city": city,
        "payment_method": "cod",
        "payment_status": "pending",
        "total": total,
        "status": "new",
    }).execute()
    order_id = order_insert.data[0]["id"]

    for line in lines:
        supabase.table("order_items").insert({
            "order_id": order_id,
            "product_id": None,
            "product_name": line["name"],
            "size": line["size"],
            "color": line["color"],
            "quantity": line["qty"],
            "unit_price": line["price"],
        }).execute()

    resp = RedirectResponse(url=f"/order/{order_number}", status_code=303)
    save_cart(resp, [])  # empty the cart now that the order is placed
    return resp


# ------------------------------------------------------------- success ----
@app.get("/order/{order_number}", response_class=HTMLResponse)
def order_success(order_number: str):
    result = supabase.table("orders").select("*").eq("order_number", order_number).single().execute()
    if not result.data:
        return HTMLResponse("<h1>Order not found</h1>", status_code=404)
    return templates.success_page(result.data, CATEGORIES, subcategories=SUBCATEGORIES)