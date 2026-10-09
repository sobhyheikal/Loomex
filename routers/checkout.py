from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

import templates
from config import CATEGORIES, SUBCATEGORIES
from services.cart import get_cart, save_cart, cart_item_count, resolve_cart
from services.orders import create_order, get_order_by_number

router = APIRouter()


# ------------------------------------------------------------ checkout ----
@router.get("/checkout", response_class=HTMLResponse)
def checkout_form(request: Request):
    cart = get_cart(request)
    if not cart:
        return RedirectResponse(url="/cart", status_code=303)
    lines, subtotal = resolve_cart(cart)
    cart_count = cart_item_count(cart)
    return templates.checkout_page(lines, subtotal, CATEGORIES, cart_count, subcategories=SUBCATEGORIES)


@router.post("/checkout", response_class=HTMLResponse)
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

    order_number = create_order(customer_name, phone, city, address, lines, subtotal)

    resp = RedirectResponse(url=f"/order/{order_number}", status_code=303)
    save_cart(resp, [])  # empty the cart now that the order is placed
    return resp


# ------------------------------------------------------------- success ----
@router.get("/order/{order_number}", response_class=HTMLResponse)
def order_success(order_number: str):
    order = get_order_by_number(order_number)
    if not order:
        return HTMLResponse("<h1>Order not found</h1>", status_code=404)
    return templates.success_page(order, CATEGORIES, subcategories=SUBCATEGORIES)
