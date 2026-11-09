import uuid

from config import SHIPPING_RATES
from supabase_client import supabase

PAYMENT_PROOF_BUCKET = "payment_proofs"


def upload_payment_proof(file_bytes: bytes, content_type: str, filename: str) -> str:
    """Uploads a payment-proof screenshot to a private Supabase Storage
    bucket and returns a long-lived signed URL (10 years)."""
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "jpg").lower()
    path = f"{uuid.uuid4().hex}.{ext}"
    supabase.storage.from_(PAYMENT_PROOF_BUCKET).upload(
        path, file_bytes, {"content-type": content_type or "application/octet-stream"}
    )
    signed = supabase.storage.from_(PAYMENT_PROOF_BUCKET).create_signed_url(path, 60 * 60 * 24 * 365 * 10)
    return signed.get("signedURL") or signed.get("signed_url") or signed.get("signedUrl")


def create_order(customer_name: str, phone: str, city: str, address: str,
                 lines: list[dict], subtotal: float, payment_method: str = "cod",
                 payment_proof_url: str | None = None, pricing: dict | None = None,
                 email: str = "", delivery_notes: str = "") -> str:
    pricing = pricing or {}
    discount = float(pricing.get("discount") or 0)
    shipping = 0 if pricing.get("free_shipping") else SHIPPING_RATES.get(city, 0)
    total = max(subtotal - discount, 0) + shipping

    try:
        order_number = supabase.rpc("next_order_number").execute().data
        if not isinstance(order_number, str) or not order_number:
            raise ValueError("no order number")
    except Exception:
        order_number = f"LMX-{uuid.uuid4().hex[:8].upper()}"  # backup so checkout never breaks

    order_insert = supabase.table("orders").insert({
        "order_number": order_number,
        "customer_name": customer_name,
        "phone": phone,
        "email": email or None,
        "address": address,
        "city": city,
        "delivery_notes": delivery_notes or None,
        "payment_method": payment_method,
        "payment_status": "pending",
        "payment_proof_url": payment_proof_url,
        "shipping": shipping,
        "total": total,
        "discount": discount,
        "promotion_note": pricing.get("note") or None,
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

    return order_number


def get_order_by_number(order_number: str):
    result = supabase.table("orders").select("*").eq("order_number", order_number).maybe_single().execute()
    order = result.data if result else None
    if not order:
        return None
    items = supabase.table("order_items").select("*").eq("order_id", order["id"]).execute()
    order["items"] = items.data or []
    return order
