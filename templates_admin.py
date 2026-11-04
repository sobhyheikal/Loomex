"""Loomex admin panel HTML. Standalone: it does not use the storefront layout."""

from datetime import datetime, timezone
from html import escape

from config import PAYMENT_METHODS
from services.admin_data import ADMIN_TZ, ORDER_STATUSES, PAYMENT_STATUSES
from services.promotions import _parse, promo_state
from templates import FONTS

NAV = [("orders", "Orders"), ("products", "Products"), ("customers", "Customers"),
       ("promotions", "Promotions"), ("deleted", "Recently Deleted"), ("profile", "Profile")]

ADMIN_CSS = """
<style>
:root{--ink:#201c18;--ink-raised:#2a241e;--stone:#e7e2d6;--paper:#f1ece2;--paper-dim:#b9b2a4;
  --gold:#c79a46;--gold-dim:#8f7239;--teal:#4f6d6a;--line:rgba(241,236,226,.14);}
*{box-sizing:border-box;}
html,body{margin:0;background:var(--ink);color:var(--paper);font-family:"Inter",-apple-system,sans-serif;
  -webkit-font-smoothing:antialiased;}
a{color:inherit;text-decoration:none;}
.top{position:sticky;top:0;z-index:10;background:var(--ink);border-bottom:1px solid var(--line);}
.top-in{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;max-width:980px;margin:0 auto;padding:10px 18px;}
.logo{font-family:"Big Shoulders Display",sans-serif;font-weight:700;font-size:22px;letter-spacing:.12em;}
.logo span{color:var(--gold);} .logo small{font-family:Inter,sans-serif;font-size:11px;letter-spacing:.16em;
  color:var(--paper-dim);margin-left:10px;text-transform:uppercase;}
.am-toggle{display:none;}
.am-btn{display:flex;flex-direction:column;justify-content:center;gap:6px;width:24px;padding:10px 8px 10px 0;cursor:pointer;justify-self:start;}
.am-btn span{width:100%;height:1.5px;background:var(--paper);display:block;}
.am-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.5);opacity:0;pointer-events:none;transition:opacity .2s ease;z-index:29;}
.am-drawer{position:fixed;top:0;left:0;bottom:0;width:78%;max-width:300px;background:var(--ink);border-right:1px solid var(--line);
  z-index:30;transform:translateX(-100%);transition:transform .25s ease;padding:20px 22px 24px;overflow-y:auto;display:flex;flex-direction:column;}
.am-close{display:block;text-align:right;font-size:26px;color:var(--paper-dim);padding:4px 4px 14px;cursor:pointer;}
.am-drawer .dl{display:block;width:100%;text-align:left;background:none;border:none;cursor:pointer;
  font-family:"Big Shoulders Display",sans-serif;font-size:22px;text-transform:uppercase;letter-spacing:.03em;color:var(--paper);padding:10px 0;}
.am-drawer .dl.on{color:var(--gold);}
.am-out{margin:auto 0 0;padding-top:18px;border-top:1px solid var(--line);}
.am-out .dl{color:var(--paper-dim);}
.am-toggle:checked ~ .am-drawer{transform:translateX(0);}
.am-toggle:checked ~ .am-backdrop{opacity:1;pointer-events:auto;}
.page{max-width:980px;margin:0 auto;padding:22px 18px 70px;}
h1{font-family:"Big Shoulders Display",sans-serif;font-size:34px;text-transform:uppercase;margin:0 0 4px;line-height:1;}
.sub{color:var(--paper-dim);font-size:13px;margin:0 0 20px;}
.head{display:flex;justify-content:space-between;align-items:flex-end;gap:12px;flex-wrap:wrap;margin-bottom:18px;}
.flash{border:1px solid var(--gold);background:rgba(199,154,70,.1);padding:10px 14px;font-size:13px;margin-bottom:16px;}
.err{border:1px solid var(--gold);background:rgba(199,154,70,.1);padding:10px 14px;font-size:13px;margin-bottom:16px;}
.err strong{color:var(--gold);}
.btn{display:inline-block;padding:10px 16px;background:var(--gold);color:var(--ink);border:none;font:600 12.5px Inter,sans-serif;
  letter-spacing:.04em;text-transform:uppercase;cursor:pointer;text-align:center;}
.btn:hover{background:var(--gold-dim);}
.btn.sm{padding:7px 12px;font-size:11.5px;}
.btn.ghost{background:transparent;color:var(--paper);border:1px solid var(--paper-dim);}
.btn.ghost:hover{border-color:var(--gold);color:var(--gold);}
.link{background:none;border:none;color:var(--paper-dim);font:12px Inter,sans-serif;text-decoration:underline;cursor:pointer;padding:6px 4px;}
.link:hover{color:var(--gold);}
.row{display:flex;align-items:center;gap:12px;flex-wrap:wrap;background:var(--ink-raised);border:1px solid var(--line);padding:12px 14px;margin-bottom:8px;}
.grow{flex:1 1 200px;min-width:0;}
.t{margin:0 0 3px;font-size:14px;font-weight:600;word-break:break-word;} .s{margin:0;font-size:12.5px;color:var(--paper-dim);}
.thumb{width:46px;height:58px;flex:0 0 auto;background:rgba(128,128,128,.12);} .thumb img{width:100%;height:100%;object-fit:contain;display:block;}
.acts{display:flex;align-items:center;gap:6px;} .acts form{margin:0;}
.badge{display:inline-block;padding:3px 9px;border:1px solid var(--line);border-radius:999px;font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:var(--paper-dim);white-space:nowrap;}
.badge.ok{border-color:var(--gold);color:var(--gold);} .badge.good{border-color:var(--teal);color:var(--paper);background:rgba(79,109,106,.35);}
.search{display:flex;gap:8px;margin-bottom:18px;} .search input{flex:1;}
input[type=text],input[type=search],input[type=password],input[type=number],input[type=date],select,textarea{width:100%;padding:11px 13px;background:var(--ink-raised);
  border:1px solid var(--line);color:var(--paper);font:14px Inter,sans-serif;border-radius:0;}
textarea{min-height:90px;resize:vertical;line-height:1.5;} input:focus,select:focus,textarea:focus{outline:none;border-color:var(--gold);}
label.f{display:block;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--paper-dim);margin:0 0 6px;}
.fg{margin-bottom:16px;} .hint{font-size:12px;color:var(--paper-dim);margin:6px 0 0;line-height:1.5;}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px;} .three{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;}
.card{background:var(--ink-raised);border:1px solid var(--line);padding:18px;margin-bottom:18px;}
.check{display:flex;align-items:center;gap:10px;font-size:14px;} .check input{width:auto;accent-color:var(--gold);}
details.order{background:var(--ink-raised);border:1px solid var(--line);margin-bottom:8px;}
details.order summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:13px 14px;}
details.order summary::-webkit-details-marker{display:none;}
details.order[open] summary{border-bottom:1px solid var(--line);}
.ob{padding:16px 14px;display:grid;gap:18px;} .ob h3{margin:0 0 8px;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);font-weight:600;}
.ob p{margin:0 0 4px;font-size:13.5px;line-height:1.55;color:var(--paper);} .ob p span{color:var(--paper-dim);}
.ob a.u{color:var(--gold);text-decoration:underline;}
.items{width:100%;border-collapse:collapse;font-size:13px;} .items td,.items th{padding:8px 4px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;}
.items th{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--paper-dim);font-weight:500;} .items .r{text-align:right;white-space:nowrap;}
.sum{display:flex;justify-content:space-between;font-size:13.5px;padding:6px 0;} .sum.tot{font-weight:700;border-top:1px solid var(--line);margin-top:4px;padding-top:10px;}
.st{display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end;} .st .fg{margin:0;flex:1 1 140px;}
.empty{padding:36px 10px;text-align:center;color:var(--paper-dim);font-size:14px;}
.sec{font-family:"Big Shoulders Display",sans-serif;font-size:22px;text-transform:uppercase;margin:26px 0 10px;} .sec small{font:12px Inter,sans-serif;color:var(--paper-dim);margin-left:8px;}
.login{max-width:360px;margin:12vh auto;padding:0 18px;text-align:center;} .login .card{text-align:left;margin-top:22px;}
@media(max-width:560px){.two,.three{grid-template-columns:1fr;} h1{font-size:30px;}}
</style>
"""


def _dt(iso) -> str:
    d = _parse(iso)
    return d.astimezone(ADMIN_TZ).strftime("%d %b %Y, %I:%M %p") if d else ""


def _money(n) -> str:
    return f"{float(n or 0):,.0f} EGP"


def _first_image(p: dict) -> str:
    for v in (p.get("color_images") or {}).values():
        if isinstance(v, list) and v:
            return v[0]
        if isinstance(v, str) and v:
            return v
    return p.get("image_url") or ""


def admin_page(title: str, body: str, active: str = "", msg: str | None = None) -> str:
    links = "".join(f'<a href="/admin/{k}" class="dl{" on" if k == active else ""}">{label}</a>' for k, label in NAV)
    flash = f'<div class="flash">{escape(msg)}</div>' if msg else ""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow"><title>{escape(title)} · Loomex Admin</title>
{FONTS}<link rel="icon" type="image/svg+xml" href="/static/favicon.svg">{ADMIN_CSS}</head>
<body>
<input type="checkbox" id="am" class="am-toggle">
<label for="am" class="am-backdrop"></label>
<nav class="am-drawer"><label for="am" class="am-close">&times;</label>{links}
<form method="post" action="/admin/logout" class="am-out"><button class="dl">Log out</button></form></nav>
<header class="top"><div class="top-in">
  <label for="am" class="am-btn" aria-label="Open menu"><span></span><span></span><span></span></label>
  <a href="/admin/orders" class="logo">LOOM<span>EX</span><small>Admin</small></a><span></span>
</div></header>
<main class="page">{flash}{body}</main>
{LIVE_SEARCH_JS}
</body></html>"""


LIVE_SEARCH_JS = """<script>
/* Search boxes marked data-live update the results as you type, no button needed */
document.querySelectorAll('input[data-live]').forEach(function (inp) {
  var form = inp.form, timer = null, seq = 0;
  function run() {
    var q = inp.value.trim();
    var url = form.getAttribute('action') + (q ? '?q=' + encodeURIComponent(q) : '');
    var mine = ++seq;
    fetch(url, { credentials: 'same-origin' }).then(function (r) { return r.text(); }).then(function (html) {
      if (mine !== seq) return;
      var doc = new DOMParser().parseFromString(html, 'text/html');
      var fresh = doc.getElementById('results'), cur = document.getElementById('results');
      if (fresh && cur) cur.innerHTML = fresh.innerHTML;
      history.replaceState(null, '', url);
    }).catch(function () {});
  }
  inp.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(run, 200); });
});
</script>"""


def login_page(configured: bool = True, error: str | None = None, first_time: bool = False) -> str:
    if not configured:
        inner = ('<div class="card"><p class="s">Admin login isn\'t set up yet. Add <b>ADMIN_PASSWORD</b> and '
                 '<b>ADMIN_SECRET</b> to your .env file (and to Vercel) and restart.</p></div>')
    else:
        err = f'<div class="err"><strong>{escape(error)}</strong></div>' if error else ""
        note = ('<p class="hint" style="margin:0 0 14px">First time? Leave the email empty and use the password from '
                'your .env file, then set your email and password in Profile.</p>' if first_time else "")
        inner = f"""<div class="card"><form method="post" action="/admin/login">{err}{note}
<div class="fg"><label class="f" for="em">Email</label><input type="text" id="em" name="email" autocomplete="username" autofocus></div>
<div class="fg"><label class="f" for="pw">Password</label><input type="password" id="pw" name="password" autocomplete="current-password" required></div>
<button class="btn" style="width:100%">Log in</button></form></div>"""
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"><meta name="robots" content="noindex, nofollow">
<title>Admin login · Loomex</title>{FONTS}<link rel="icon" type="image/svg+xml" href="/static/favicon.svg">{ADMIN_CSS}</head>
<body><div class="login"><div class="logo" style="font-size:30px">LOOM<span>EX</span></div>
<p class="sub" style="margin-top:6px">Admin panel</p>{inner}</div></body></html>"""


def profile_page(email: str, msg: str | None = None, error: str | None = None, form_email: str = "") -> str:
    err = f'<div class="err"><strong>{escape(error)}</strong></div>' if error else ""
    shown = email or "Not set yet"
    body = f"""<div class="head"><div><h1>Profile</h1>
<p class="sub">Your admin login. Both owners use this one account.</p></div></div>{err}
<form method="post" action="/admin/profile" class="card">
<div class="fg"><label class="f">Current email</label><input type="text" value="{escape(shown)}" readonly></div>
<div class="fg"><label class="f">New email</label><input type="text" name="email" value="{escape(form_email)}" autocomplete="email"
placeholder="{"leave empty to keep it" if email else "your email"}"></div>
<div class="fg"><label class="f">New password</label><input type="password" name="new_password" autocomplete="new-password">
<p class="hint">At least 8 characters. Leave empty to keep your current password. Changing it logs out your other devices.</p></div>
<div class="fg"><label class="f">Confirm new password</label><input type="password" name="confirm_password" autocomplete="new-password"></div>
<div class="fg" style="border-top:1px solid var(--line);padding-top:16px"><label class="f">Current password (required to save)</label>
<input type="password" name="current_password" autocomplete="current-password" required></div>
<button class="btn">Save profile</button></form>"""
    return admin_page("Profile", body, "profile", msg)


# ------------------------------------------------------------- products ----
def products_page(products: list, msg: str | None = None) -> str:
    rows = []
    for p in products:
        img = _first_image(p)
        thumb = f'<img src="{escape(img)}" alt="" loading="lazy">' if img else ""
        sub = f" · {escape(p['subcategory'].replace('-', ' ').title())}" if p.get("subcategory") else ""
        stock = '<span class="badge ok">In stock</span>' if p.get("in_stock") else '<span class="badge">Out of stock</span>'
        rows.append(f"""<div class="row"><div class="thumb">{thumb}</div>
<div class="grow"><p class="t">{escape(p['name'])}</p>
<p class="s">{escape(p['category'].replace('-', ' ').title())}{sub} · {_money(p['price'])}</p></div>{stock}
<div class="acts"><a class="btn sm ghost" href="/admin/products/{p['id']}">Edit</a>
<form method="post" action="/admin/products/{p['id']}/delete" onsubmit="return confirm('Move this product to Recently Deleted?')">
<button class="link">Delete</button></form></div></div>""")
    listing = "".join(rows) or '<div class="empty">No products yet.</div>'
    body = f"""<div class="head"><div><h1>Products</h1><p class="sub">{len(products)} on the site</p></div>
<a class="btn" href="/admin/products/new">+ Add product</a></div>{listing}"""
    return admin_page("Products", body, "products", msg)


def product_form_page(v: dict, categories: list, subcategories: dict, error: str | None = None,
                      product_id: str | None = None, msg: str | None = None) -> str:
    def opt(val, label, current):
        return f'<option value="{escape(val)}"{" selected" if val == current else ""}>{escape(label)}</option>'

    cats = "".join(opt(c, c.replace("-", " ").title(), v.get("category")) for c in categories)
    groups = "".join(
        f'<optgroup label="{escape(c.replace("-", " ").title())}">'
        + "".join(opt(s, s.replace("-", " ").title(), v.get("subcategory")) for s in subs) + "</optgroup>"
        for c, subs in subcategories.items() if subs)
    subs = opt("", "None", v.get("subcategory") or "") + groups
    err = f'<div class="err"><strong>{escape(error)}</strong></div>' if error else ""
    editing = bool(product_id)
    slug_field = (f'<input type="text" value="{escape(v.get("slug", ""))}" readonly>'
                  '<p class="hint">The slug is the product\'s web address and stays fixed, so carts and links never break.</p>'
                  if editing else
                  f'<input type="text" name="slug" value="{escape(v.get("slug", ""))}" placeholder="made from the name if left empty">')
    action = f"/admin/products/{product_id}" if editing else "/admin/products/new"
    body = f"""<div class="head"><div><h1>{"Edit product" if editing else "New product"}</h1>
<p class="sub"><a href="/admin/products" class="link" style="padding:0">&larr; Back to products</a></p></div></div>
{err}
<form method="post" action="{action}">
<div class="card">
<div class="fg"><label class="f">Name</label><input type="text" name="name" value="{escape(v.get('name', ''))}" required></div>
<div class="fg"><label class="f">Slug</label>{slug_field}</div>
<div class="fg"><label class="f">Description</label><textarea name="description">{escape(v.get('description', ''))}</textarea></div>
<div class="three">
<div class="fg"><label class="f">Category</label><select name="category">{cats}</select></div>
<div class="fg"><label class="f">Sub-category</label><select name="subcategory">{subs}</select></div>
<div class="fg"><label class="f">Price (EGP)</label><input type="number" name="price" min="0" step="0.01" value="{escape(v.get('price', ''))}" required></div>
</div>
<div class="two">
<div class="fg"><label class="f">Sizes</label><input type="text" name="sizes" value="{escape(v.get('sizes', ''))}">
<p class="hint">Separate with commas.</p></div>
<div class="fg"><label class="f">Colors</label><input type="text" name="colors" value="{escape(v.get('colors', ''))}">
<p class="hint">Separate with commas.</p></div>
</div>
<label class="check"><input type="checkbox" name="in_stock" value="1"{" checked" if v.get("in_stock") else ""}> In stock</label>
</div>
<div class="card">
<div class="fg"><label class="f">Main photo URL</label><input type="text" name="image_url" value="{escape(v.get('image_url', ''))}">
<p class="hint">Used for social sharing and as the fallback. If you leave it empty, the first color photo is used.</p></div>
<div class="fg" style="margin-bottom:0"><label class="f">Photos per color</label>
<textarea name="photos" style="min-height:130px" placeholder="Black = front-url | back-url | model-url">{escape(v.get('photos', ''))}</textarea>
<p class="hint">One color per line, photo links separated by <b>|</b>. The first link is shown as Front and the second as Back.
The color name must match the Colors field exactly.</p></div>
</div>
<button class="btn">{"Save changes" if editing else "Add product"}</button>
</form>"""
    return admin_page("Edit product" if editing else "New product", body, "products", msg)


# --------------------------------------------------------------- orders ----
def _order_card(o: dict, q: str) -> str:
    items = o.get("order_items") or []
    subtotal = sum(float(i["unit_price"]) * int(i["quantity"]) for i in items)
    pay = PAYMENT_METHODS.get(o.get("payment_method"), {}).get("label") or (o.get("payment_method") or "")
    status = o.get("status") or "new"
    pstatus = o.get("payment_status") or "pending"
    cls = "good" if status in ("delivered", "shipped") else ("ok" if status in ("new", "confirmed") else "")
    rows = "".join(
        f"<tr><td>{escape(i['product_name'])}"
        f"<br><span class='s'>{escape(' / '.join(x for x in [i.get('size'), i.get('color')] if x))}</span></td>"
        f"<td class='r'>{int(i['quantity'])}</td><td class='r'>{_money(i['unit_price'])}</td>"
        f"<td class='r'>{_money(float(i['unit_price']) * int(i['quantity']))}</td></tr>" for i in items)
    email = (f'<a class="u" href="mailto:{escape(o["email"])}">{escape(o["email"])}</a>'
             if o.get("email") else '<span>No email given</span>')
    proof = (f'<p><a class="u" href="{escape(o["payment_proof_url"])}" target="_blank" rel="noopener">View payment proof</a></p>'
             if o.get("payment_proof_url") else "")

    def sel(name, values, current):
        vals = values + ([current] if current not in values else [])
        return f'<select name="{name}">' + "".join(
            f'<option value="{escape(x)}"{" selected" if x == current else ""}>{escape(x.title())}</option>' for x in vals) + "</select>"

    return f"""<details class="order"><summary>
<div class="grow"><p class="t">#{escape(o['order_number'])} · {escape(o['customer_name'])}</p>
<p class="s">{_dt(o.get('created_at'))} · {len(items)} item{'s' if len(items) != 1 else ''}</p></div>
<span class="badge {cls}">{escape(status)}</span><strong>{_money(o['total'])}</strong></summary>
<div class="ob">
<div><h3>Customer</h3><p>{escape(o['customer_name'])}</p>
<p><a class="u" href="tel:{escape(o['phone'])}">{escape(o['phone'])}</a></p><p>{email}</p>
<p><span>{escape(o['address'])}, {escape(o['city'])}</span></p></div>
<div><h3>Items</h3><table class="items"><tr><th>Item</th><th class="r">Qty</th><th class="r">Price</th><th class="r">Total</th></tr>{rows}</table>
<div style="margin-top:10px"><div class="sum"><span>Subtotal</span><span>{_money(subtotal)}</span></div>
<div class="sum"><span>Shipping ({escape(o['city'])})</span><span>{_money(o.get('shipping'))}</span></div>
<div class="sum tot"><span>Total</span><span>{_money(o['total'])}</span></div></div></div>
<div><h3>Payment</h3><p>{escape(pay)} · <span>{escape(pstatus)}</span></p>{proof}</div>
<form method="post" action="/admin/orders/{o['id']}/status"><h3>Update</h3><input type="hidden" name="q" value="{escape(q)}">
<div class="st"><div class="fg"><label class="f">Order status</label>{sel('status', ORDER_STATUSES, status)}</div>
<div class="fg"><label class="f">Payment</label>{sel('payment_status', PAYMENT_STATUSES, pstatus)}</div>
<button class="btn sm">Save</button></div></form>
<form method="post" action="/admin/orders/{o['id']}/delete" onsubmit="return confirm('Move this order to Recently Deleted?')">
<input type="hidden" name="q" value="{escape(q)}"><button class="link" style="padding-left:0">Delete order</button></form>
</div></details>"""


def orders_page(orders: list, q: str, msg: str | None = None) -> str:
    cards = "".join(_order_card(o, q) for o in orders)
    if not cards:
        cards = f'<div class="empty">{"No orders match that search." if q else "No orders yet."}</div>'
    body = f"""<div class="head"><div><h1>Orders</h1><p class="sub">Newest first · tap an order for the full details</p></div></div>
<form class="search" method="get" action="/admin/orders"><input type="search" name="q" value="{escape(q)}" data-live autocomplete="off"
placeholder="Search order number, name, phone or email"></form><div id="results">{cards}</div>"""
    return admin_page("Orders", body, "orders", msg)


# ------------------------------------------------------------ customers ----
def customers_page(customers: list, q: str) -> str:
    rows = []
    for c in customers:
        email = escape(c["email"]) if c["email"] else "No email"
        rows.append(f"""<div class="row"><div class="grow"><p class="t">{escape(c['name'])}</p>
<p class="s">{escape(c['phone'])} · {email}</p></div>
<div class="s">{c['orders']} order{'s' if c['orders'] != 1 else ''} · {_money(c['spent'])}<br>Last: {_dt(c['last'])}</div>
<a class="btn sm ghost" href="/admin/orders?q={escape(c['phone'] or c['name'])}">View orders</a></div>""")
    listing = "".join(rows) or f'<div class="empty">{"No customers match that search." if q else "No customers yet."}</div>'
    body = f"""<div class="head"><div><h1>Customers</h1><p class="sub">Built from orders · {len(customers)} shown</p></div></div>
<form class="search" method="get" action="/admin/customers"><input type="search" name="q" value="{escape(q)}" data-live autocomplete="off"
placeholder="Search by name, phone or email"></form><div id="results">{listing}</div>"""
    return admin_page("Customers", body, "customers")


# ----------------------------------------------------------- promotions ----
def promotions_page(promos: list, msg: str | None = None, error: str | None = None, form: dict | None = None) -> str:
    f = form or {}
    err = f'<div class="err"><strong>{escape(error)}</strong></div>' if error else ""
    labels = {"live": ("Live on site", "ok"), "scheduled": ("Scheduled", ""), "ended": ("Ended", ""), "off": ("Off", "")}
    rows = []
    for p in promos:
        text, cls = labels[promo_state(p)]
        dates = " → ".join(x for x in [
            _dt(p.get("starts_at")).split(",")[0] if p.get("starts_at") else "",
            _dt(p.get("ends_at")).split(",")[0] if p.get("ends_at") else ""] if x)
        link = f" · {escape(p['link_text'] or '')} → {escape(p['link_url'])}" if p.get("link_url") else ""
        flip = "Turn off" if p.get("is_active") else "Turn on"
        rows.append(f"""<div class="row"><div class="grow"><p class="t">{escape(p['message'])}</p>
<p class="s">{escape(dates) or 'No dates set'}{link}</p></div><span class="badge {cls}">{text}</span>
<div class="acts"><form method="post" action="/admin/promotions/{p['id']}/toggle"><button class="link">{flip}</button></form>
<form method="post" action="/admin/promotions/{p['id']}/delete" onsubmit="return confirm('Move this promotion to Recently Deleted?')">
<button class="link">Delete</button></form></div></div>""")
    listing = "".join(rows) or '<div class="empty">No promotions yet.</div>'
    body = f"""<div class="head"><div><h1>Promotions</h1>
<p class="sub">Live promotions appear in a gold bar at the top of the website (changes show within a minute).</p></div></div>{err}
<form method="post" action="/admin/promotions/new" class="card">
<div class="fg"><label class="f">Promotion text</label><input type="text" name="message" maxlength="160" value="{escape(f.get('message', ''))}"
placeholder="e.g. Free shipping on orders over 1500 EGP" required></div>
<div class="two"><div class="fg"><label class="f">Button text (optional)</label><input type="text" name="link_text" value="{escape(f.get('link_text', ''))}" placeholder="Shop now"></div>
<div class="fg"><label class="f">Link (optional)</label><input type="text" name="link_url" value="{escape(f.get('link_url', ''))}" placeholder="/shop?category=pants"></div></div>
<div class="two"><div class="fg"><label class="f">Starts (optional)</label><input type="date" name="starts" value="{escape(f.get('starts', ''))}"></div>
<div class="fg"><label class="f">Ends (optional)</label><input type="date" name="ends" value="{escape(f.get('ends', ''))}"></div></div>
<button class="btn">Add promotion</button></form>{listing}"""
    return admin_page("Promotions", body, "promotions", msg)


# ------------------------------------------------------ recently deleted ----
def deleted_page(groups: dict, days: int, msg: str | None = None) -> str:
    titles = {"products": "Products", "orders": "Orders", "promotions": "Promotions"}
    total = sum(len(v) for v in groups.values())
    out = []
    for kind, items in groups.items():
        rows = "".join(f"""<div class="row"><div class="grow"><p class="t">{escape(i['label'])}</p>
<p class="s">{escape(i['detail'])} · deleted {_dt(i['deleted_at'])}</p></div>
<span class="badge">{i['days_left']} day{'s' if i['days_left'] != 1 else ''} left</span>
<div class="acts"><form method="post" action="/admin/deleted/{kind}/{i['id']}/restore"><button class="btn sm ghost">Restore</button></form>
<form method="post" action="/admin/deleted/{kind}/{i['id']}/purge" onsubmit="return confirm('Delete this forever? This cannot be undone.')">
<button class="link">Delete forever</button></form></div></div>""" for i in items)
        out.append(f'<h2 class="sec">{titles[kind]}<small>{len(items)}</small></h2>' +
                   (rows or '<div class="empty" style="padding:14px 0;text-align:left">Nothing here.</div>'))
    body = f"""<div class="head"><div><h1>Recently deleted</h1>
<p class="sub">Deleted items stay here for {days} days, then are removed for good. {total} item{'s' if total != 1 else ''} right now.</p></div></div>{''.join(out)}"""
    return admin_page("Recently deleted", body, "deleted", msg)