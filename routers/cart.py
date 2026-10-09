from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

import templates
from config import CATEGORIES, SUBCATEGORIES
from services.cart import get_cart, save_cart, cart_item_count, resolve_cart

router = APIRouter()


# ----------------------------------------------------------------- cart ----
@router.post("/cart/add")
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


@router.get("/cart", response_class=HTMLResponse)
def view_cart(request: Request):
    cart = get_cart(request)
    lines, subtotal = resolve_cart(cart)
    cart_count = cart_item_count(cart)
    return templates.cart_page(lines, subtotal, CATEGORIES, cart_count, subcategories=SUBCATEGORIES)


@router.post("/cart/update")
def update_cart_line(request: Request, index: int = Form(...), qty: int = Form(...)):
    cart = get_cart(request)
    qty = max(1, min(qty, 10))
    if 0 <= index < len(cart):
        cart[index]["qty"] = qty
    resp = RedirectResponse(url="/cart", status_code=303)
    save_cart(resp, cart)
    return resp


@router.post("/cart/remove")
def remove_cart_line(request: Request, index: int = Form(...)):
    cart = get_cart(request)
    if 0 <= index < len(cart):
        cart.pop(index)
    resp = RedirectResponse(url="/cart", status_code=303)
    save_cart(resp, cart)
    return resp
