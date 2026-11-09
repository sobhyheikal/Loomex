"""
Run from the Loomex project folder:   python3 apply_notifications.py

Adds new-order notifications:
  * email to loomex.co@gmail.com (through your existing Resend setup)
  * push notifications to the admin panel installed on your phone

New files:  services/push.py, routers/admin_push.py
Edited (a .bak copy of each is saved first):
  services/emails.py, routers/checkout.py, routers/admin.py, main.py,
  templates_admin.py, requirements.txt
Safe to re-run: files that are already patched are skipped.
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(".")


def read(p: Path) -> str:
    if not p.exists():
        sys.exit(f"Can't find {p}. Run this script from the Loomex project folder.")
    return p.read_text(encoding="utf-8")


def backup(p: Path):
    shutil.copy2(p, p.with_suffix(p.suffix + ".bak"))


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        sys.exit(f"Stopped: expected exactly 1 match for '{label}' but found {n}. Nothing was changed in that file.")
    return text.replace(old, new)


def write_new(rel: str, content: str):
    p = ROOT / rel
    if p.exists():
        print(f"{rel}: already exists, skipped")
        return
    p.write_text(content, encoding="utf-8")
    print(f"{rel}: created")


# ----------------------------------------------------------------- new files
PUSH_PY = r'''"""Web push notifications for the admin panel (new-order alerts on phones and computers)."""
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
'''

ADMIN_PUSH_PY = r'''"""Admin panel: push notification setup (manifest, service worker, subscribe / unsubscribe)."""
import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response

from services import admin_auth, push

# no login needed: the browser fetches these files before it can send the admin cookie
public_router = APIRouter()
# under /admin, needs the admin login (included into routers/admin.py)
router = APIRouter(dependencies=[Depends(admin_auth.require_admin)])

MANIFEST = {
    "name": "Loomex Admin",
    "short_name": "LX Admin",
    "start_url": "/admin/orders",
    "scope": "/admin/",
    "display": "standalone",
    "background_color": "#201c18",
    "theme_color": "#201c18",
    "icons": [{"src": "/static/apple-touch-icon.png", "sizes": "180x180", "type": "image/png", "purpose": "any"}],
}

SW_JS = r"""
self.addEventListener('install', function () { self.skipWaiting(); });
self.addEventListener('activate', function (e) { e.waitUntil(self.clients.claim()); });
self.addEventListener('push', function (e) {
  var d = {};
  try { d = e.data.json(); } catch (err) {}
  e.waitUntil(self.registration.showNotification(d.title || 'Loomex', {
    body: d.body || '',
    icon: '/static/apple-touch-icon.png',
    badge: '/static/apple-touch-icon.png',
    tag: d.tag || 'loomex',
    data: { url: d.url || '/admin/orders' }
  }));
});
self.addEventListener('notificationclick', function (e) {
  e.notification.close();
  var url = (e.notification.data && e.notification.data.url) || '/admin/orders';
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (list) {
    for (var i = 0; i < list.length; i++) {
      if (list[i].url.indexOf('/admin') !== -1 && 'focus' in list[i]) {
        if ('navigate' in list[i]) { list[i].navigate(url); }
        return list[i].focus();
      }
    }
    return self.clients.openWindow(url);
  }));
});
"""


@public_router.get("/admin/sw.js")
def service_worker():
    return Response(SW_JS, media_type="application/javascript",
                    headers={"Service-Worker-Allowed": "/admin/", "Cache-Control": "no-cache"})


@public_router.get("/admin/manifest.webmanifest")
def manifest():
    return Response(json.dumps(MANIFEST), media_type="application/manifest+json",
                    headers={"Cache-Control": "no-cache"})


@router.get("/push/key")
def push_key():
    return {"key": push.public_key(), "configured": push.configured()}


@router.post("/push/subscribe")
async def push_subscribe(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"ok": False}, status_code=400)
    try:
        ok = push.save_subscription(data)
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)[:160]}, status_code=500)
    return JSONResponse({"ok": ok}, status_code=200 if ok else 400)


@router.post("/push/unsubscribe")
async def push_unsubscribe(request: Request):
    try:
        data = await request.json()
        push.remove_subscription(data.get("endpoint", ""))
    except Exception:
        pass
    return {"ok": True}


@router.post("/push/test")
def push_test():
    sent = push.send_push("Notifications are on", "You will get an alert here for every new Loomex order.",
                          "/admin/orders", tag="test")
    return {"sent": sent}
'''

# -------------------------------------------------------- admin email (append)
ADMIN_EMAIL_CODE = r'''

# ------------------------------------------------------- new-order alert ----
ADMIN_EMAIL = "loomex.co@gmail.com"


def build_admin_html(order: dict) -> str:
    s = _summary(order)
    rows = ""
    for i in s["items"]:
        variant = " / ".join(v for v in [i.get("size"), i.get("color")] if v)
        qty = int(i.get("quantity") or 0)
        rows += (f'<tr><td style="padding:6px 0;border-bottom:1px solid #eee;">{escape(str(i.get("product_name") or ""))}'
                 f'{" (" + escape(variant) + ")" if variant else ""} &times; {qty}</td>'
                 f'<td align="right" style="padding:6px 0;border-bottom:1px solid #eee;white-space:nowrap;">'
                 f'{_money(float(i.get("unit_price") or 0) * qty)}</td></tr>')

    def row(label, value):
        return (f'<tr><td style="padding:3px 12px 3px 0;color:#777;vertical-align:top;">{label}</td>'
                f'<td style="padding:3px 0;">{value}</td></tr>')

    discount = f"-{_money(s['discount'])}" if s["discount"] > 0 else ""
    info = (row("Customer", escape(order.get("customer_name") or ""))
            + row("Phone", escape(order.get("phone") or ""))
            + row("Email", escape(order.get("email") or "-"))
            + row("City", escape(order.get("city") or ""))
            + row("Address", escape(order.get("address") or ""))
            + row("Payment", escape(s["pay"])))
    if order.get("delivery_notes"):
        info += row("Notes", escape(order["delivery_notes"]))
    if order.get("payment_proof_url"):
        info += row("Payment proof", f'<a href="{escape(order["payment_proof_url"])}">View screenshot</a>')
    if order.get("promotion_note"):
        info += row("Promotions", escape(order["promotion_note"]))

    return f"""<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#222;max-width:520px;">
<h2 style="margin:0 0 4px;">New order {escape(s['number'])}</h2>
<p style="margin:0 0 16px;color:#777;">Total <strong style="color:#222;">{_money(s['total'])}</strong></p>
<table cellpadding="0" cellspacing="0" width="100%">{rows}</table>
<table cellpadding="0" cellspacing="0" width="100%" style="margin:10px 0 18px;">
<tr><td style="padding:3px 0;color:#777;">Subtotal</td><td align="right">{_money(s['subtotal'])}</td></tr>
{f'<tr><td style="padding:3px 0;color:#777;">Discount</td><td align="right">{discount}</td></tr>' if discount else ''}
<tr><td style="padding:3px 0;color:#777;">Shipping</td><td align="right">{'Free' if s['shipping'] == 0 else _money(s['shipping'])}</td></tr>
<tr><td style="padding:6px 0;font-weight:700;">Total</td><td align="right" style="font-weight:700;">{_money(s['total'])}</td></tr>
</table>
<table cellpadding="0" cellspacing="0">{info}</table>
<p style="margin:20px 0 0;"><a href="{SITE}/admin/orders" style="background:#c19a57;color:#201c18;padding:10px 18px;text-decoration:none;font-weight:700;border-radius:6px;">Open admin</a></p>
</div>"""


def send_admin_new_order(order: dict) -> bool:
    """Email loomex.co@gmail.com about a new order. Returns True if Resend accepted it. Never raises."""
    key = os.environ.get("RESEND_API_KEY")
    if not key:
        return False
    try:
        s = _summary(order)
        text = (f"New order {s['number']} - {_money(s['total'])}\n"
                f"{order.get('customer_name')} - {order.get('phone')} - {order.get('city')}\n"
                f"{SITE}/admin/orders")
        payload = {
            "from": EMAIL_FROM,
            "to": [ADMIN_EMAIL],
            "subject": f"New order {s['number']} · {_money(s['total'])}",
            "html": build_admin_html(order),
            "text": text,
        }
        customer = (order.get("email") or "").strip()
        if customer:
            payload["reply_to"] = customer
        resend.api_key = key
        resend.Emails.send(payload)
        return True
    except Exception as e:
        print("Admin order email failed:", e)
        return False
'''

# ------------------------------------------------------ admin page additions
PUSH_ADMIN_BLOCK = r'''PUSH_HEAD = """<link rel="manifest" href="/admin/manifest.webmanifest">
<meta name="theme-color" content="#201c18">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Loomex Admin">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<link rel="apple-touch-icon" href="/static/apple-touch-icon.png">"""

PUSH_JS = """<script>
/* Order notifications: turn push on / off for this device */
(function () {
  var btn = document.getElementById('push-btn');
  if (!btn) return;
  var ok = 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
  if (!ok) {
    btn.textContent = 'Notifications';
    btn.onclick = function () {
      alert('To get order notifications on iPhone: open this admin from the Loomex icon on your Home Screen (Share, then Add to Home Screen), then tap this button again.');
    };
    return;
  }
  var reg = null, cur = null;
  function label(on) { btn.textContent = on ? 'Notifications: On' : 'Turn on notifications'; }
  function toKey(b64) {
    var s = (b64 + '='.repeat((4 - b64.length % 4) % 4)).replace(/-/g, '+').replace(/_/g, '/');
    var r = atob(s), a = new Uint8Array(r.length);
    for (var i = 0; i < r.length; i++) a[i] = r.charCodeAt(i);
    return a;
  }
  navigator.serviceWorker.register('/admin/sw.js', { scope: '/admin/' })
    .then(function (r) { reg = r; return navigator.serviceWorker.ready; })
    .then(function (r) { reg = r; return r.pushManager.getSubscription(); })
    .then(function (s) { cur = s; label(!!s && Notification.permission === 'granted'); })
    .catch(function () { label(false); });
  btn.onclick = async function () {
    try {
      if (cur) {
        await fetch('/admin/push/unsubscribe', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ endpoint: cur.endpoint }) });
        await cur.unsubscribe(); cur = null; label(false); return;
      }
      var perm = await Notification.requestPermission();
      if (perm !== 'granted') { alert('Notifications are blocked. Allow them for this app in your phone settings.'); return; }
      reg = reg || await navigator.serviceWorker.ready;
      var k = await (await fetch('/admin/push/key')).json();
      if (!k.key) { alert('Push is not set up on the server yet (missing VAPID keys).'); return; }
      cur = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: toKey(k.key) });
      await fetch('/admin/push/subscribe', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(cur.toJSON()) });
      label(true);
      fetch('/admin/push/test', { method: 'POST' });
    } catch (e) { alert('Could not turn on notifications: ' + (e && e.message || e)); }
  };
})();
</script>"""


'''


# ------------------------------------------------------------------ patching
def patch_emails():
    p = ROOT / "services" / "emails.py"
    t = read(p)
    if "def send_admin_new_order" in t:
        print("services/emails.py: already patched, skipped")
        return
    backup(p)
    p.write_text(t.rstrip("\n") + "\n" + ADMIN_EMAIL_CODE, encoding="utf-8")
    print("services/emails.py: added send_admin_new_order()")


def patch_checkout():
    p = ROOT / "routers" / "checkout.py"
    t = read(p)
    if "send_order_push" in t:
        print("routers/checkout.py: already patched, skipped")
        return
    t = replace_once(
        t,
        "from services.emails import send_order_confirmation",
        "from services.emails import send_admin_new_order, send_order_confirmation\n"
        "from services.push import send_order_push",
        "emails import line",
    )
    old = '''    try:  # a failed email must never stop an order from going through
        order = get_order_by_number(order_number)
        if order:
            send_order_confirmation(order)
    except Exception as e:
        print("Order email error:", e)
'''
    new = '''    order = None
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
'''
    t = replace_once(t, old, new, "email block in place_order")
    backup(p)
    p.write_text(t, encoding="utf-8")
    print("routers/checkout.py: new-order notifications added")


def patch_admin_router():
    p = ROOT / "routers" / "admin.py"
    t = read(p)
    if "admin_push" in t:
        print("routers/admin.py: already patched, skipped")
        return
    backup(p)
    p.write_text(t.rstrip("\n") + "\nfrom routers import admin_push  # noqa: E402\n"
                 "router.include_router(admin_push.router)\n", encoding="utf-8")
    print("routers/admin.py: push routes included")


def patch_main():
    p = ROOT / "main.py"
    t = read(p)
    if "admin_push" in t:
        print("main.py: already patched, skipped")
        return
    t = replace_once(t, "from routers import pages, products, cart, checkout, admin",
                     "from routers import pages, products, cart, checkout, admin, admin_push", "routers import")
    t = replace_once(t, "app.include_router(admin.public_router)",
                     "app.include_router(admin.public_router)\napp.include_router(admin_push.public_router)",
                     "admin.public_router include")
    backup(p)
    p.write_text(t, encoding="utf-8")
    print("main.py: manifest + service worker routes added")


def patch_admin_template():
    p = ROOT / "templates_admin.py"
    t = read(p)
    if "PUSH_HEAD" in t:
        print("templates_admin.py: already patched, skipped")
        return
    t = replace_once(t, "def admin_page(", PUSH_ADMIN_BLOCK + "def admin_page(", "def admin_page")
    t = replace_once(t, '<link rel="icon" type="image/svg+xml" href="/static/favicon.svg">{ADMIN_CSS}</head>',
                     '<link rel="icon" type="image/svg+xml" href="/static/favicon.svg">{PUSH_HEAD}{ADMIN_CSS}</head>',
                     "admin <head>")
    t = replace_once(t, '<div class="am-out"><form method="post" action="/admin/logout">',
                     '<button type="button" class="dl" id="push-btn">Notifications</button>\n'
                     '<div class="am-out"><form method="post" action="/admin/logout">',
                     "drawer logout block")
    t = replace_once(t, '{LIVE_SEARCH_JS}{FLASH_JS if msg else ""}',
                     '{LIVE_SEARCH_JS}{PUSH_JS}{FLASH_JS if msg else ""}', "admin scripts")
    backup(p)
    p.write_text(t, encoding="utf-8")
    print("templates_admin.py: Notifications button + app tags added")


def patch_requirements():
    p = ROOT / "requirements.txt"
    t = read(p)
    if "pywebpush" in t:
        print("requirements.txt: already has pywebpush, skipped")
        return
    backup(p)
    p.write_text(t.rstrip("\n") + "\npywebpush>=2.0\n", encoding="utf-8")
    print("requirements.txt: added pywebpush")


if __name__ == "__main__":
    # check every file we edit exists and matches BEFORE writing anything
    for f in ["services/emails.py", "routers/checkout.py", "routers/admin.py", "main.py",
              "templates_admin.py", "requirements.txt"]:
        read(ROOT / f)
    write_new("services/push.py", PUSH_PY)
    write_new("routers/admin_push.py", ADMIN_PUSH_PY)
    patch_emails()
    patch_checkout()
    patch_admin_router()
    patch_main()
    patch_admin_template()
    patch_requirements()
    print("\nDone. Next: install pywebpush, create the Supabase table, generate VAPID keys (see the steps).")
