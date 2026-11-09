"""Web push notifications for the admin panel (new-order alerts on phones and computers)."""
import json
import os

from supabase_client import supabase

TABLE = "push_subscriptions"


def public_key() -> str:
    return os.environ.get("VAPID_PUBLIC_KEY", "").strip()


def _private_key() -> str:
    return os.environ.get("VAPID_PRIVATE_KEY", "").strip()


def _subject() -> str:
    return os.environ.get("VAPID_SUBJECT", "").strip() or "mailto:loomex.co@gmail.com"


def configured() -> bool:
    return bool(public_key() and _private_key())


def save_subscription(sub: dict) -> bool:
    endpoint = (sub or {}).get("endpoint")
    keys = (sub or {}).get("keys") or {}
    if not endpoint or not keys.get("p256dh") or not keys.get("auth"):
        return False
    supabase.table(TABLE).upsert(
        {"endpoint": endpoint, "p256dh": keys["p256dh"], "auth": keys["auth"]},
        on_conflict="endpoint",
    ).execute()
    return True


def remove_subscription(endpoint: str):
    if endpoint:
        supabase.table(TABLE).delete().eq("endpoint", endpoint).execute()


def send_push(title: str, body: str, url: str = "/admin/orders", tag: str | None = None) -> int:
    """Send one notification to every saved device. Returns how many accepted it. Never raises."""
    if not configured():
        return 0
    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        print("Push skipped: pywebpush is not installed")
        return 0
    try:
        rows = supabase.table(TABLE).select("*").execute().data or []
    except Exception as e:
        print("Push skipped, could not read subscriptions:", e)
        return 0
    payload = json.dumps({"title": title, "body": body, "url": url, "tag": tag or "loomex"})
    sent = 0
    for r in rows:
        try:
            webpush(
                subscription_info={"endpoint": r["endpoint"], "keys": {"p256dh": r["p256dh"], "auth": r["auth"]}},
                data=payload,
                vapid_private_key=_private_key(),
                vapid_claims={"sub": _subject()},
                ttl=86400,
                timeout=8,
            )
            sent += 1
        except WebPushException as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status in (404, 410):  # this device unsubscribed or was removed
                try:
                    remove_subscription(r["endpoint"])
                except Exception:
                    pass
            else:
                print("Push failed:", e)
        except Exception as e:
            print("Push failed:", e)
    return sent


def send_order_push(order: dict) -> int:
    """New-order alert. Never raises."""
    try:
        items = order.get("items") or []
        count = sum(int(i.get("quantity") or 0) for i in items)
        total = f"{float(order.get('total') or 0):.0f} EGP"
        who = (order.get("customer_name") or "Customer").strip()
        city = (order.get("city") or "").strip()
        body = " · ".join(x for x in [who, city, f"{count} item{'s' if count != 1 else ''}", total] if x)
        return send_push(f"New order {order.get('order_number', '')}", body, "/admin/orders",
                         tag=str(order.get("order_number") or "order"))
    except Exception as e:
        print("Order push error:", e)
        return 0
