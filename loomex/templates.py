"""
HTML is built with small Python functions instead of separate .html files.

Why: Vercel's Python runtime bundles whatever your code imports; keeping
templates as plain Python strings avoids any question of whether a
`templates/` folder gets shipped to production. It also means zero extra
dependencies (no Jinja2 needed).

If your team later wants real Jinja2 templates, that's a fine upgrade —
just make sure to test a production deploy after switching, since static
file bundling is the one part of Vercel's Python support worth double
checking.
"""

from html import escape

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700&'
    'family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">'
)

# ----------------------------------------------------------------------
# AD PIXELS — paste your Meta Pixel + TikTok Pixel base code here once you
# have them (Meta Events Manager / TikTok Events Manager → "Set up pixel").
# This snippet loads on every single page, which is what pixels need.
# See ads_plan.md, section "Install tracking before you spend a cent".
# ----------------------------------------------------------------------
PIXEL_SNIPPET = """
<!-- Meta Pixel — replace YOUR_PIXEL_ID, then uncomment
<script>
!function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;
n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window,
document,'script','https://connect.facebook.net/en_US/fbevents.js');
fbq('init', 'YOUR_PIXEL_ID');
fbq('track', 'PageView');
</script>
-->

<!-- TikTok Pixel — replace YOUR_TIKTOK_PIXEL_ID, then uncomment
<script>
!function (w, d, t) {{ w.TiktokAnalyticsObject=t;var ttq=w[t]=w[t]||[];ttq.methods=["page","track","identify","instances","debug","on","off","once","ready","alias","group","enableCookie","disableCookie"],ttq.setAndDefer=function(t,e){{t[e]=function(){{t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}}};for(var i=0;i<ttq.methods.length;i++)ttq.setAndDefer(ttq,ttq.methods[i]);ttq.load=function(e,n){{var i="https://analytics.tiktok.com/i18n/pixel/events.js";ttq._i=ttq._i||{{}},ttq._i[e]=[],ttq._i[e]._u=i,ttq._t=ttq._t||{{}},ttq._t[e]=+new Date,ttq._o=ttq._o||{{}},ttq._o[e]=n||{{}};var o=document.createElement("script");o.type="text/javascript",o.async=!0,o.src=i+"?sdkid="+e+"&lib="+t;var a=document.getElementsByTagName("script")[0];a.parentNode.insertBefore(o,a)}};ttq.load('YOUR_TIKTOK_PIXEL_ID');ttq.page();}}(window, document, 'ttq');
</script>
-->
"""


def layout(title: str, body: str, section_class: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)} · Loomex</title>
{FONTS}
<link rel="stylesheet" href="/static/style.css">
{PIXEL_SNIPPET}
</head>
<body class="{section_class}">
<header class="topbar">
  <div class="topbar-inner">
    <a href="/" class="logo">LOOM<span>EX</span></a>
  </div>
</header>
{body}
<footer class="footer">
  <div class="wrap">
    <p>LOOMEX — HOMEWEAR, WOVEN FOR REST</p>
  </div>
</footer>
</body>
</html>"""


def home_page(products: list, categories: list, active_category: str | None) -> str:
    chips = ['<a href="/" class="chip{}">All</a>'.format(" active" if not active_category else "")]
    for c in categories:
        active = " active" if active_category == c else ""
        label = c.replace("-", " ").title()
        chips.append(f'<a href="/?category={c}" class="chip{active}">{escape(label)}</a>')

    if products:
        cards = "".join(
            f"""<a href="/product/{escape(p['slug'])}" class="card">
                  <img src="{escape(p.get('image_url') or '')}" alt="{escape(p['name'])}" loading="lazy">
                  <div class="card-body">
                    <p class="card-name">{escape(p['name'])}</p>
                    <p class="card-price">{p['price']:.0f} EGP</p>
                  </div>
                </a>"""
            for p in products
        )
        grid = f'<div class="grid">{cards}</div>'
    else:
        grid = '<div class="empty">No products in this category yet.</div>'

    body = f"""
<section class="hero warp-bg">
  <div class="wrap">
    <p class="eyebrow">Homewear, basic by design</p>
    <h1 class="display">Made to be<br>worn in.</h1>
    <p>Heavyweight cotton essentials — tops, tanks, pants and shorts built for
    the hours that don't need an outfit.</p>
  </div>
</section>
<nav class="chips">{''.join(chips)}</nav>
{grid}
"""
    return layout("Loomex — Homewear", body)


def product_page(p: dict) -> str:
    size_pills = "".join(
        f'<label class="pill"><input type="radio" name="size" value="{escape(s)}"'
        f'{" checked" if i == 0 else ""}>{escape(s)}</label>'
        for i, s in enumerate(p["sizes"])
    )
    color_pills = "".join(
        f'<label class="pill"><input type="radio" name="color" value="{escape(c)}"'
        f'{" checked" if i == 0 else ""}>{escape(c)}</label>'
        for i, c in enumerate(p.get("colors") or [])
    )

    body = f"""
<div class="pd-image"><img src="{escape(p.get('image_url') or '')}" alt="{escape(p['name'])}"></div>
<div class="pd-body">
  <h1 class="pd-name display">{escape(p['name'])}</h1>
  <p class="pd-price">{p['price']:.0f} EGP</p>
  <p class="pd-desc">{escape(p.get('description') or '')}</p>

  <form action="/checkout" method="get">
    <input type="hidden" name="product" value="{escape(p['slug'])}">

    <span class="field-label">Size</span>
    <div class="pill-row">{size_pills}</div>

    {"<span class='field-label'>Color</span><div class='pill-row'>" + color_pills + "</div>" if color_pills else ""}

    <span class="field-label">Quantity</span>
    <div class="qty-row">
      <input type="number" name="qty" value="1" min="1" max="10">
    </div>

    <button class="btn" type="submit">Buy Now</button>
  </form>
</div>
"""
    return layout(p["name"], body)


def checkout_page(product: dict, size: str, color: str, qty: int, error: str | None = None) -> str:
    total = product["price"] * qty
    error_html = f'<p style="color:#a33;font-size:13px;margin-bottom:14px;">{escape(error)}</p>' if error else ""

    body = f"""
<div class="wrap">
  <h1 class="display">Checkout</h1>
  <p class="sub">Almost there — fill in your details below.</p>

  <div class="summary-line">
    <span>{escape(product['name'])} ({escape(size)}{", " + escape(color) if color else ""}) × {qty}</span>
    <span>{total:.0f} EGP</span>
  </div>
  <div class="summary-line summary-total">
    <span>Total</span>
    <span>{total:.0f} EGP</span>
  </div>

  {error_html}

  <form action="/checkout" method="post" style="margin-top:22px;">
    <input type="hidden" name="product" value="{escape(product['slug'])}">
    <input type="hidden" name="size" value="{escape(size)}">
    <input type="hidden" name="color" value="{escape(color)}">
    <input type="hidden" name="qty" value="{qty}">

    <div class="form-group">
      <label>Full name</label>
      <input type="text" name="customer_name" required>
    </div>
    <div class="form-group">
      <label>Phone number</label>
      <input type="tel" name="phone" required placeholder="01xxxxxxxxx">
    </div>
    <div class="form-group">
      <label>City</label>
      <input type="text" name="city" required>
    </div>
    <div class="form-group">
      <label>Full address</label>
      <input type="text" name="address" required>
    </div>

    <span class="field-label">Payment</span>
    <label class="pay-option">
      <input type="radio" name="payment_method" value="cod" checked>
      <span><strong>Cash on Delivery</strong><span>Pay in cash when your order arrives.</span></span>
    </label>
    <label class="pay-option">
      <input type="radio" name="payment_method" value="online">
      <span><strong>Pay Online</strong><span>Card or wallet payment (set up in step 6 of the README).</span></span>
    </label>

    <button class="btn" type="submit" style="margin-top:20px;">Place Order</button>
  </form>
</div>
"""
    return layout("Checkout", body, section_class="checkout")


def success_page(order: dict) -> str:
    # This is the one page where you fire a "Purchase" event, so the pixels
    # know an order actually happened (not just a page view). Once you've
    # uncommented the pixel snippets above, add here — right after
    # <body ...> is fine — something like:
    #   <script>fbq('track', 'Purchase', {{value: {order['total']}, currency: 'EGP'}});</script>
    #   <script>ttq.track('CompletePayment', {{value: {order['total']}, currency: 'EGP'}});</script>
    body = f"""
<div class="wrap">
  <div style="text-align:center;">
    <p class="eyebrow" style="color:var(--gold);">Order confirmed</p>
    <p class="order-no">{escape(order['order_number'])}</p>
    <p style="color:var(--paper-dim);font-size:14px;">
      Thanks, {escape(order['customer_name'])} — we've got your order.
      {"We'll call to confirm before delivery." if order['payment_method'] == 'cod' else "You'll receive a payment link shortly."}
    </p>
    <a href="/" class="btn btn-outline" style="margin-top:26px;max-width:220px;margin-left:auto;margin-right:auto;">Back to shop</a>
  </div>
</div>
"""
    return layout("Order confirmed", body, section_class="success")
