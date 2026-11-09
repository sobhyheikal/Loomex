import re

from fastapi import APIRouter, HTTPException, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

import templates
from config import CATEGORIES, PAYMENT_METHODS, SHIPPING_RATES, SUBCATEGORIES
from services.cart import get_cart, save_cart, cart_item_count, resolve_cart, cart_pricing
from services.emails import send_admin_new_order, send_order_confirmation
from services.push import send_order_push
from services.orders import create_order, get_order_by_number, upload_payment_proof

router = APIRouter()

MAX_PROOF_SIZE = 5 * 1024 * 1024  # 5MB, matches the Storage bucket's own limit
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _clean(s: str, limit: int) -> str:
    return " ".join((s or "").split())[:limit]


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
    email: str = Form(...),
    city: str = Form(...),
    street: str = Form(...),
    area: str = Form(...),
    building: str = Form(...),
    floor: str = Form(...),
    delivery_notes: str = Form(""),
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

    def fail(message: str):
        return templates.checkout_page(
            lines, subtotal, CATEGORIES, cart_count, subcategories=SUBCATEGORIES,
            pricing=pricing, error=message,
        )

    customer_name = _clean(customer_name, 80)
    phone = _clean(phone, 20)
    email = _clean(email, 120).lower()
    street = _clean(street, 120)
    area = _clean(area, 80)
    building = _clean(building, 60)
    floor = _clean(floor, 60)
    delivery_notes = (delivery_notes or "").strip()[:500]

    if not (customer_name and phone and street and area and building and floor):
        return fail("Please fill in all the required fields.")
    if not EMAIL_RE.match(email):
        return fail("Please enter a valid email address.")
    if city not in SHIPPING_RATES:
        return fail("Please select a valid delivery zone from the list.")
    if payment_method not in PAYMENT_METHODS:
        return fail("Please select a valid payment method.")

    payment_proof_url = None
    if payment_method != "cod":
        if not payment_proof or not payment_proof.filename:
            return fail(f"Please upload a screenshot showing your {PAYMENT_METHODS[payment_method]['label']} transfer.")
        if not (payment_proof.content_type or "").startswith("image/"):
            return fail("Payment proof must be an image (screenshot).")
        proof_bytes = payment_proof.file.read()
        if len(proof_bytes) > MAX_PROOF_SIZE:
            return fail("That screenshot is too large (max 5MB).")
        payment_proof_url = upload_payment_proof(proof_bytes, payment_proof.content_type, payment_proof.filename)

    address = f"{street}, {area}, Building {building}, Floor/Apt {floor}"

    order_number = create_order(customer_name, phone, city, address, lines, subtotal,
                                payment_method=payment_method, payment_proof_url=payment_proof_url,
                                pricing=pricing, email=email, delivery_notes=delivery_notes)

    order = None
    try:
        order = get_order_by_number(order_number)
    except Exception as e:
        print("Order lookup error:", e)
    if order:
        # alerts for you first, then the customer's confirmation.
        # Each one may fail without stopping the order from going through.
        for notify in (send_order_push, send_admin_new_order, send_order_confirmation):
            try:
                notify(order)
            except Exception as e:
                print("Order notification error:", e)

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
