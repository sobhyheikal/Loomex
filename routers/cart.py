from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

import templates
from config import CATEGORIES, SUBCATEGORIES
from services.cart import get_cart, save_cart, cart_item_count, resolve_cart
from services.products import get_product_or_404
router = APIRouter()


def _wants_json(request: Request) -> bool:
    # The cart drawer's JS sends this header; normal form posts don't.
    return request.headers.get("x-requested-with") == "fetch"


def _drawer_payload(cart: list[dict]) -> dict:
    lines, subtotal = resolve_cart(cart)
    return {
        "count": cart_item_count(cart),
        "subtotal": subtotal,
        "lines": [
            {
                "index": l["index"],
                "name": l["name"],
                "variant": " · ".join(v for v in [l["size"], l["color"]] if v),
                "image_url": l["image_url"] or "",
                "qty": l["qty"],
                "line_total": l["line_total"],
            }
            for l in lines
        ],
    }


def _respond(request: Request, cart: list[dict]):
    """Drawer requests get the updated cart as JSON; plain form posts redirect to /cart."""
    if _wants_json(request):
        resp = JSONResponse(_drawer_payload(cart), headers={"Cache-Control": "no-store"})
    else:
        resp = RedirectResponse(url="/cart", status_code=303)
    save_cart(resp, cart)
    return resp


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

    # Refuse sold-out products and sold-out sizes, even if someone forces the request.
    p = get_product_or_404(product)
    if not p or not p.get("in_stock", True) or size in (p.get("sold_out_sizes") or []):
        if _wants_json(request):
            return JSONResponse({"error": "That item or size is sold out."}, status_code=409)
        return RedirectResponse(url=f"/product/{product}", status_code=303)

    cart = get_cart(request)

    for item in cart:
        if item["slug"] == product and item.get("size", "") == size and item.get("color", "") == color:
            item["qty"] = min(10, item["qty"] + qty)
            break
    else:
        cart.append({"slug": product, "size": size, "color": color, "qty": qty})

    return _respond(request, cart)


@router.get("/cart/drawer")
def cart_drawer(request: Request):
    return JSONResponse(_drawer_payload(get_cart(request)), headers={"Cache-Control": "no-store"})


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
    return _respond(request, cart)


@router.post("/cart/remove")
def remove_cart_line(request: Request, index: int = Form(...)):
    cart = get_cart(request)
    if 0 <= index < len(cart):
        cart.pop(index)
    return _respond(request, cart)