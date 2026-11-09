from fastapi import APIRouter, HTTPException, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

import templates
from config import CATEGORIES, PAYMENT_METHODS, SHIPPING_RATES, SUBCATEGORIES
from services.cart import get_cart, save_cart, cart_item_count, resolve_cart, cart_pricing
from services.orders import create_order, get_order_by_number, upload_payment_proof

router = APIRouter()

MAX_PROOF_SIZE = 5 * 1024 * 1024  # 5MB, matches the Storage bucket's own limit


# ------------------------------------------------------------ checkout ----
@router.get("/checkout", response_class=HTMLResponse)
def checkout_form(request: Request):
    cart = get_cart(request)
    if not cart:
        return RedirectResponse(url="/cart", status_code=303)
    lines, subtotal = resolve_cart(cart)
    cart_count = cart_item_count(cart)
    pricing = cart_pricing(lines)
    return templates.checkout_page(lines, subtotal, CATEGORIES, cart_count, subcategories=SUBCATEGORIES,
                                   pricing=pricing)


@router.post("/checkout", response_class=HTMLResponse)
def place_order(
    request: Request,
    customer_name: str = Form(...),
    phone: str = Form(...),
    city: str = Form(...),
    address: str = Form(...),
    payment_method: str = Form("cod"),
    payment_proof: UploadFile | None = File(None),
):
    cart = get_cart(request)
    if not cart:
        return RedirectResponse(url="/cart", status_code=303)

    lines, subtotal = resolve_cart(cart)
    if not lines:
        return RedirectResponse(url="/cart", status_code=303)

    cart_count = cart_item_count(cart)
    pricing = cart_pricing(lines)

    if city not in SHIPPING_RATES:
        return templates.checkout_page(
            lines, subtotal, CATEGORIES, cart_count, subcategories=SUBCATEGORIES, pricing=pricing,
            error="Please select a valid city from the list.",
        )

    if payment_method not in PAYMENT_METHODS:
        return templates.checkout_page(
            lines, subtotal, CATEGORIES, cart_count, subcategories=SUBCATEGORIES, pricing=pricing,
            error="Please select a valid payment method.",
        )

    payment_proof_url = None
    if payment_method != "cod":
        if not payment_proof or not payment_proof.filename:
            return templates.checkout_page(
                lines, subtotal, CATEGORIES, cart_count, subcategories=SUBCATEGORIES, pricing=pricing,
                error=f"Please upload a screenshot showing your {PAYMENT_METHODS[payment_method]['label']} transfer.",
            )
        if not (payment_proof.content_type or "").startswith("image/"):
            return templates.checkout_page(
                lines, subtotal, CATEGORIES, cart_count, subcategories=SUBCATEGORIES, pricing=pricing,
                error="Payment proof must be an image (screenshot).",
            )
        proof_bytes = payment_proof.file.read()
        if len(proof_bytes) > MAX_PROOF_SIZE:
            return templates.checkout_page(
                lines, subtotal, CATEGORIES, cart_count, subcategories=SUBCATEGORIES, pricing=pricing,
                error="That screenshot is too large (max 5MB).",
            )
        payment_proof_url = upload_payment_proof(proof_bytes, payment_proof.content_type, payment_proof.filename)

    order_number = create_order(customer_name, phone, city, address, lines, subtotal,
                                 payment_method=payment_method, payment_proof_url=payment_proof_url,
                                 pricing=pricing)

    resp = RedirectResponse(url=f"/order/{order_number}", status_code=303)
    save_cart(resp, [])  # empty the cart now that the order is placed
    return resp


# ------------------------------------------------------------- success ----
@router.get("/order/{order_number}", response_class=HTMLResponse)
def order_success(order_number: str):
    order = get_order_by_number(order_number)
    if not order:
        raise HTTPException(status_code=404, detail="We couldn't find that order.")
    return templates.success_page(order, CATEGORIES, subcategories=SUBCATEGORIES)