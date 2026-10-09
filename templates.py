"""
HTML is built with small Python functions instead of separate .html files
(see comment history / README for why — keeps Vercel bundling simple).
"""

from html import escape

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700&'
    'family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">'
)

# ----------------------------------------------------------------------
# AD PIXELS — paste your Meta Pixel + TikTok Pixel base code here once you
# have them (Meta Events Manager / TikTok Events Manager -> "Set up pixel").
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


def _category_links(categories: list, subcategories: dict | None = None, active: str | None = None,
                     active_sub: str | None = None, base: str = "/shop") -> str:
    subcategories = subcategories or {}
    links = []
    for c in categories:
        label = c.replace("-", " ").title()
        cls = " active" if active == c and not active_sub else ""
        links.append(f'<a href="{base}?category={c}" class="drawer-sub-link{cls}">{escape(label)}</a>')
        for s in subcategories.get(c, []):
            s_label = s.replace("-", " ").title()
            s_cls = " active" if active == c and active_sub == s else ""
            links.append(
                f'<a href="{base}?category={c}&amp;subcategory={s}" '
                f'class="drawer-sub-link drawer-sub-sub-link{s_cls}">{escape(s_label)}</a>'
            )
    return "".join(links)


def layout(title: str, body: str, categories: list, cart_count: int = 0,
           section_class: str = "", active_category: str | None = None,
           subcategories: dict | None = None, active_subcategory: str | None = None) -> str:
    cat_links = _category_links(categories, subcategories, active_category, active_subcategory)
    cart_badge = f'<span class="cart-badge">{cart_count}</span>' if cart_count else ""

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
<input type="checkbox" id="menu-toggle" class="menu-toggle-input">
<label for="menu-toggle" class="drawer-backdrop"></label>
<nav class="drawer">
  <label for="menu-toggle" class="drawer-close">&times;</label>
  <a href="/" class="drawer-link">Home</a>
  <a href="/shop" class="drawer-link">Shop All</a>
  <div class="drawer-sub">{cat_links}</div>
  <hr class="thread-rule">
  <a href="/cart" class="drawer-link">Cart{f' ({cart_count})' if cart_count else ''}</a>
</nav>

<header class="topbar">
  <div class="topbar-inner">
    <label for="menu-toggle" class="hamburger-btn" aria-label="Open menu">
      <span></span><span></span><span></span>
    </label>
    <a href="/" class="logo">LOOM<span>EX</span></a>
    <a href="/cart" class="cart-link">
      Cart{cart_badge}
    </a>
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


def landing_page(categories: list, cart_count: int = 0, subcategories: dict | None = None) -> str:
    body = """
<section class="hero warp-bg">
  <div class="wrap">
    <p class="eyebrow">Homewear, basic by design</p>
    <h1 class="display">Made to be<br>worn in.</h1>
    <p>Heavyweight cotton essentials — tops, joggers, pullovers, quarter-zips
    and jackets built for the hours that don't need an outfit.</p>
    <a href="/shop" class="btn" style="margin-top:24px;max-width:220px;">Shop Loomex</a>
  </div>
</section>
"""
    return layout("Loomex — Homewear", body, categories, cart_count, subcategories=subcategories)


def shop_page(products: list, categories: list, active_category: str | None, cart_count: int = 0,
              subcategories: dict | None = None, active_subcategory: str | None = None) -> str:
    subcategories = subcategories or {}
    chips = ['<a href="/shop" class="chip{}">All</a>'.format(" active" if not active_category else "")]
    for c in categories:
        active = " active" if active_category == c else ""
        label = c.replace("-", " ").title()
        chips.append(f'<a href="/shop?category={c}" class="chip{active}">{escape(label)}</a>')

    sub_chips_html = ""
    sub_items = subcategories.get(active_category) if active_category else None
    if sub_items:
        sub_chips = [
            '<a href="/shop?category={}" class="chip chip-sub{}">All</a>'.format(
                active_category, "" if not active_subcategory else " active"
            )
        ]
        for s in sub_items:
            s_active = " active" if active_subcategory == s else ""
            s_label = s.replace("-", " ").title()
            sub_chips.append(
                f'<a href="/shop?category={active_category}&subcategory={s}" '
                f'class="chip chip-sub{s_active}">{escape(s_label)}</a>'
            )
        sub_chips_html = f'<nav class="chips chips-sub">{"".join(sub_chips)}</nav>'

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
<nav class="chips">{''.join(chips)}</nav>
{sub_chips_html}
{grid}
"""
    return layout("Shop", body, categories, cart_count, active_category=active_category,
                  subcategories=subcategories, active_subcategory=active_subcategory)


def product_page(p: dict, categories: list, cart_count: int = 0, subcategories: dict | None = None) -> str:
    size_pills = "".join(
        f'<label class="pill"><input type="radio" name="size" value="{escape(s)}"'
        f'{" checked" if i == 0 else ""}>{escape(s)}</label>'
        for i, s in enumerate(p["sizes"])
    )

    # color_images format: {"Black": ["url1", "url2"], "Olive": ["url3"]}
    # Each color can have its own set of photos, swipeable via the carousel.
    # Tapping a color pill swaps which color's photo set is showing (plain
    # inline JS toggling display — no page reload needed).
    color_images = p.get("color_images") or {}
    colors = p.get("colors") or []

    if color_images:
        groups = "".join(
            f"""<div class="gallery-group" id="ggroup-{escape(c)}" style="display:{'block' if i == 0 else 'none'};">
                  <div class="carousel">{"".join(
                      f'<div class="carousel-slide"><img src="{escape(url)}" alt="{escape(p["name"])} in {escape(c)}"></div>'
                      for url in (color_images.get(c) or [p.get("image_url") or ""])
                  )}</div>
                </div>"""
            for i, c in enumerate(colors)
        )
        image_block = f'<div class="gallery">{groups}</div>'
        color_pills = "".join(
            f'<label class="pill" onclick="document.querySelectorAll(\'.gallery-group\').forEach(g=>g.style.display=\'none\');'
            f"document.getElementById('ggroup-{escape(c)}').style.display='block';\">"
            f'<input type="radio" name="color" value="{escape(c)}"'
            f'{" checked" if i == 0 else ""} style="display:none;">{escape(c)}</label>'
            for i, c in enumerate(colors)
        )
    else:
        image_block = f'<div class="pd-image"><img src="{escape(p.get("image_url") or "")}" alt="{escape(p["name"])}"></div>'
        color_pills = "".join(
            f'<label class="pill"><input type="radio" name="color" value="{escape(c)}"'
            f'{" checked" if i == 0 else ""}>{escape(c)}</label>'
            for i, c in enumerate(colors)
        )

    body = f"""
{image_block}
<div class="pd-body">
  <h1 class="pd-name display">{escape(p['name'])}</h1>
  <p class="pd-price">{p['price']:.0f} EGP</p>
  <p class="pd-desc">{escape(p.get('description') or '')}</p>

  <form action="/cart/add" method="post">
    <input type="hidden" name="product" value="{escape(p['slug'])}">

    <span class="field-label">Size</span>
    <div class="pill-row">{size_pills}</div>

    {"<span class='field-label'>Color</span><div class='pill-row'>" + color_pills + "</div>" if color_pills else ""}

    <span class="field-label">Quantity</span>
    <div class="qty-row">
      <input type="number" name="qty" value="1" min="1" max="10">
    </div>

    <button class="btn" type="submit">Add to Cart</button>
  </form>
</div>
"""
    return layout(p["name"], body, categories, cart_count, subcategories=subcategories)


def cart_page(lines: list, subtotal: float, categories: list, cart_count: int = 0,
              subcategories: dict | None = None) -> str:
    if not lines:
        body = """
<div class="wrap">
  <h1 class="display">Your Cart</h1>
  <p style="color:var(--paper-dim);font-size:14px;margin-bottom:24px;">Your cart is empty.</p>
  <a href="/shop" class="btn">Continue Shopping</a>
</div>
"""
        return layout("Your Cart", body, categories, cart_count, subcategories=subcategories)

    rows = []
    for line in lines:
        variant = " · ".join(v for v in [line["size"], line["color"]] if v)
        rows.append(f"""
<div class="cart-line">
  <img src="{escape(line.get('image_url') or '')}" alt="{escape(line['name'])}" class="cart-line-img">
  <div class="cart-line-body">
    <p class="cart-line-name">{escape(line['name'])}</p>
    <p class="cart-line-variant">{escape(variant)}</p>
    <p class="cart-line-price">{line['price']:.0f} EGP</p>
    <div class="cart-line-controls">
      <form action="/cart/update" method="post" class="qty-inline-form">
        <input type="hidden" name="index" value="{line['index']}">
        <input type="number" name="qty" value="{line['qty']}" min="1" max="10" onchange="this.form.submit()">
      </form>
      <form action="/cart/remove" method="post">
        <input type="hidden" name="index" value="{line['index']}">
        <button type="submit" class="cart-remove-btn">Remove</button>
      </form>
    </div>
  </div>
  <p class="cart-line-total">{line['line_total']:.0f} EGP</p>
</div>
""")

    body = f"""
<div class="wrap">
  <h1 class="display">Your Cart</h1>
  <div class="cart-lines">{''.join(rows)}</div>
  <div class="summary-line summary-total" style="border-top:1px solid var(--line);margin-top:10px;padding-top:14px;">
    <span>Subtotal</span>
    <span>{subtotal:.0f} EGP</span>
  </div>
  <p style="color:var(--paper-dim);font-size:12.5px;margin:8px 0 20px;">Delivery cost confirmed by phone after ordering.</p>
  <a href="/checkout" class="btn">Checkout</a>
</div>
"""
    return layout("Your Cart", body, categories, cart_count, subcategories=subcategories)


def checkout_page(lines: list, subtotal: float, categories: list, cart_count: int = 0, error: str | None = None,
                   subcategories: dict | None = None) -> str:
    summary_rows = "".join(
        f"""<div class="summary-line">
              <span>{escape(l['name'])} ({escape(l['size'])}{", " + escape(l['color']) if l['color'] else ""}) × {l['qty']}</span>
              <span>{l['line_total']:.0f} EGP</span>
            </div>"""
        for l in lines
    )
    error_html = f'<p style="color:#a33;font-size:13px;margin-bottom:14px;">{escape(error)}</p>' if error else ""

    body = f"""
<div class="wrap">
  <h1 class="display">Checkout</h1>
  <p class="sub">Almost there — fill in your details below.</p>

  {summary_rows}
  <div class="summary-line summary-total">
    <span>Subtotal</span>
    <span>{subtotal:.0f} EGP</span>
  </div>
  <p style="color:var(--ink-dim-on-stone);font-size:12.5px;margin:6px 0 20px;">
    Delivery destination coverage and shipping cost will be confirmed by phone after you order.
  </p>

  {error_html}

  <form action="/checkout" method="post" style="margin-top:10px;">
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

    <div class="pay-option" style="cursor:default;">
      <span><strong>Cash on Delivery</strong><span>Pay in cash when your order arrives — the only payment option right now.</span></span>
    </div>

    <button class="btn" type="submit" style="margin-top:20px;">Place Order</button>
  </form>
</div>
"""
    return layout("Checkout", body, categories, cart_count, section_class="checkout", subcategories=subcategories)


def success_page(order: dict, categories: list, subcategories: dict | None = None) -> str:
    # Fire pixel "Purchase"/"CompletePayment" events here once pixels are
    # uncommented above — see PIXEL_SNIPPET comment for how.
    body = f"""
<div class="wrap">
  <div style="text-align:center;">
    <p class="eyebrow" style="color:var(--gold);">Order confirmed</p>
    <p class="order-no">{escape(order['order_number'])}</p>
    <p style="color:var(--paper-dim);font-size:14px;">
      Thanks, {escape(order['customer_name'])} — we've got your order.
      We'll call to confirm delivery details and cost before it ships.
    </p>
    <a href="/shop" class="btn btn-outline" style="margin-top:26px;max-width:220px;margin-left:auto;margin-right:auto;">Back to shop</a>
  </div>
</div>
"""
    return layout("Order confirmed", body, categories, 0, section_class="success", subcategories=subcategories)