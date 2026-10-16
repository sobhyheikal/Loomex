import uuid

from config import SHIPPING_RATES
from supabase_client import supabase


def create_order(customer_name: str, phone: str, city: str, address: str,
                  lines: list[dict], subtotal: float) -> str:
    shipping = SHIPPING_RATES.get(city, 0)
    total = subtotal + shipping

    order_number = f"LMX-{uuid.uuid4().hex[:8].upper()}"

    order_insert = supabase.table("orders").insert({
        "order_number": order_number,
        "customer_name": customer_name,
        "phone": phone,
        "address": address,
        "city": city,
        "payment_method": "cod",
        "payment_status": "pending",
        "shipping": shipping,
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

    return order_number


def get_order_by_number(order_number: str):
    result = supabase.table("orders").select("*").eq("order_number", order_number).maybe_single().execute()
    order = result.data if result else None
    if not order:
        return None
    items = supabase.table("order_items").select("*").eq("order_id", order["id"]).execute()
    order["items"] = items.data or []
    return order
