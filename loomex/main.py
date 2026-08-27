"""
Loomex storefront — FastAPI app.

Entrypoint file: Vercel automatically detects a `FastAPI` instance named
`app` in main.py at the project root, so this file needs zero extra
Vercel config to deploy.
"""

import uuid
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from supabase_client import supabase
import templates

app = FastAPI()

# Serving /static/* — Vercel promotes this to its CDN automatically
# (see "Serving frontend and static assets" in the Vercel FastAPI docs).
app.mount("/static", StaticFiles(directory="static"), name="static")

CATEGORIES = ["tops", "tank-tops", "pants", "shorts"]


# ---------------------------------------------------------------- home ----
@app.get("/", response_class=HTMLResponse)
def home(category: str | None = None):
    query = supabase.table("products").select("*").eq("in_stock", True)
    if category in CATEGORIES:
        query = query.eq("category", category)
    result = query.order("created_at", desc=True).execute()
    return templates.home_page(result.data, CATEGORIES, category)


# ------------------------------------------------------------- product ----
@app.get("/product/{slug}", response_class=HTMLResponse)
def product_detail(slug: str):
    result = supabase.table("products").select("*").eq("slug", slug).single().execute()
    if not result.data:
        return HTMLResponse("<h1>Product not found</h1>", status_code=404)
    return templates.product_page(result.data)


# ------------------------------------------------------------ checkout ----
def _get_product_or_404(slug: str):
    result = supabase.table("products").select("*").eq("slug", slug).single().execute()
    return result.data


@app.get("/checkout", response_class=HTMLResponse)
def checkout_form(product: str, size: str = "", color: str = "", qty: int = 1):
    p = _get_product_or_404(product)
    if not p:
        return HTMLResponse("<h1>Product not found</h1>", status_code=404)
    qty = max(1, min(qty, 10))
    return templates.checkout_page(p, size, color, qty)


@app.post("/checkout", response_class=HTMLResponse)
def place_order(
    product: str = Form(...),
    size: str = Form(""),
    color: str = Form(""),
    qty: int = Form(1),
    customer_name: str = Form(...),
    phone: str = Form(...),
    city: str = Form(...),
    address: str = Form(...),
    payment_method: str = Form(...),
):
    p = _get_product_or_404(product)
    if not p:
        return HTMLResponse("<h1>Product not found</h1>", status_code=404)

    qty = max(1, min(qty, 10))
    total = float(p["price"]) * qty
    order_number = f"LMX-{uuid.uuid4().hex[:8].upper()}"

    # -----------------------------------------------------------------
    # ONLINE PAYMENT INTEGRATION POINT
    # -----------------------------------------------------------------
    # Egypt-friendly gateways that work well for a small brand: Paymob,
    # Kashier, or Fawry. Once you have a merchant account with one of
    # them, this is where you'd call their API to create a payment
    # intent/iframe link, then redirect the customer to it instead of
    # straight to the success page. Until then, online orders are still
    # recorded, just marked as "awaiting_online_payment" so you can
    # follow up manually. See README step 6 for links to get started.
    payment_status = "pending" if payment_method == "cod" else "awaiting_online_payment"

    order_insert = supabase.table("orders").insert({
        "order_number": order_number,
        "customer_name": customer_name,
        "phone": phone,
        "address": address,
        "city": city,
        "payment_method": payment_method,
        "payment_status": payment_status,
        "total": total,
        "status": "new",
    }).execute()

    order_id = order_insert.data[0]["id"]

    supabase.table("order_items").insert({
        "order_id": order_id,
        "product_id": p["id"],
        "product_name": p["name"],
        "size": size,
        "color": color,
        "quantity": qty,
        "unit_price": p["price"],
    }).execute()

    return RedirectResponse(url=f"/order/{order_number}", status_code=303)


# ------------------------------------------------------------- success ----
@app.get("/order/{order_number}", response_class=HTMLResponse)
def order_success(order_number: str):
    result = supabase.table("orders").select("*").eq("order_number", order_number).single().execute()
    if not result.data:
        return HTMLResponse("<h1>Order not found</h1>", status_code=404)
    return templates.success_page(result.data)
