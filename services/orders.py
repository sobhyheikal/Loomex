import uuid

from supabase_client import supabase


def create_order(customer_name: str, phone: str, city: str, address: str,
                  lines: list[dict], subtotal: float) -> str:
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

    return order_number


def get_order_by_number(order_number: str):
    result = supabase.table("orders").select("*").eq("order_number", order_number).single().execute()
    return result.data
