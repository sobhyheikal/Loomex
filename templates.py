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
        subs = subcategories.get(c, [])
        if subs:
            sub_links = []
            for s in subs:
                s_label = s.replace("-", " ").title()
                s_cls = " active" if active == c and active_sub == s else ""
                sub_links.append(
                    f'<a href="{base}?category={c}&amp;subcategory={s}" '
                    f'class="drawer-sub-sub-link{s_cls}">{escape(s_label)}</a>'
                )
            links.append(f'<div class="drawer-sub-nested">{"".join(sub_links)}</div>')
    return "".join(links)


def layout(title: str, body: str, categories: list, cart_count: int = 0,
           section_class: str = "", active_category: str | None = None,
           subcategories: dict | None = None, active_subcategory: str | None = None,
           show_back: bool = False) -> str:
    cat_links = _category_links(categories, subcategories, active_category, active_subcategory)
    cart_badge = f'<span class="cart-badge">{cart_count}</span>' if cart_count else ""
    back_btn = (
        '<button type="button" class="back-btn" aria-label="Go back"'
        ' onclick="window.history.length > 1 ? window.history.back() : window.location.href = \'/\'">&larr;</button>'
        if show_back else ""
    )

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
    <div class="topbar-left">
      <label for="menu-toggle" class="hamburger-btn" aria-label="Open menu">
        <span></span><span></span><span></span>
      </label>
    </div>
    <a href="/" class="logo">LOOM<span>EX</span></a>
    <a href="/cart" class="cart-link" aria-label="Cart">
      <svg class="cart-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
        stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="9" cy="21" r="1.3"></circle>
        <circle cx="19" cy="21" r="1.3"></circle>
        <path d="M2.5 3h2.2l2.1 12.1a2 2 0 0 0 2 1.65h8.6a2 2 0 0 0 2-1.6l1.5-7.4H6"></path>
      </svg>{cart_badge}
    </a>
  </div>
</header>
{f'<div class="back-btn-wrap">{back_btn}</div>' if show_back else ""}
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
SHOP_CSS = """
<style>
.card{position:relative;}
.card img{width:100%;height:auto;aspect-ratio:4/5;object-fit:contain;background:rgba(128,128,128,.10);display:none;}
.card img.active{display:block;}
.card-group{display:none;position:relative;}
.card-group.active{display:block;}
.card-arrow{position:absolute;top:50%;transform:translateY(-50%);width:26px;height:26px;border:0;border-radius:50%;
  background:rgba(0,0,0,.55);color:#fff;font-size:16px;line-height:1;cursor:pointer;z-index:2;display:flex;
  align-items:center;justify-content:center;padding:0;}
.card-prev{left:6px;}
.card-next{right:6px;}
.card-swatches{display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;}
.swatch{width:16px;height:16px;border-radius:50%;border:2px solid transparent;background-size:cover;
  background-position:center;cursor:pointer;padding:0;}
.swatch.active{border-color:var(--gold,#c9a24a);}
</style>
<script>
function cardShowColor(el, ci){
  var card = el.closest('.card');
  card.querySelectorAll('.card-group').forEach(function(g){
    g.classList.toggle('active', g.dataset.ci == ci);
  });
  card.querySelectorAll('.swatch').forEach(function(s, i){
    s.classList.toggle('active', i === ci);
  });
}
function cardStep(el, delta){
  var group = el.closest('.card-group');
  var imgs = group.querySelectorAll('img');
  var cur = 0;
  imgs.forEach(function(im, i){ if (im.classList.contains('active')) cur = i; });
  var next = (cur + delta + imgs.length) % imgs.length;
  imgs.forEach(function(im, i){ im.classList.toggle('active', i === next); });
}
</script>
"""

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
        cat_label = active_category.replace("-", " ").title()
        sub_tabs = [
            '<a href="/shop?category={}" class="subtab{}">All {}</a>'.format(
                active_category, "" if not active_subcategory else " active", escape(cat_label)
            )
        ]
        for s in sub_items:
            s_active = " active" if active_subcategory == s else ""
            s_label = s.replace("-", " ").title()
            sub_tabs.append(
                f'<a href="/shop?category={active_category}&subcategory={s}" '
                f'class="subtab{s_active}">{escape(s_label)}</a>'
            )
        sub_chips_html = f'<nav class="subtabs">{"".join(sub_tabs)}</nav>'

    if products:
        card_blocks = []
        for p in products:
            color_images = p.get("color_images") or {}
            colors = p.get("colors") or []
            fallback_img = p.get("image_url") or ""

            if color_images:
                groups = []
                swatches = []
                for ci, c in enumerate(colors):
                    urls = color_images.get(c) or [fallback_img]
                    imgs = "".join(
                        f'<img src="{escape(u)}" alt="{escape(p["name"])} in {escape(c)}" loading="lazy"'
                        f'{" class=active" if n == 0 else ""}>'
                        for n, u in enumerate(urls)
                    )
                    if len(urls) > 1:
                        arrows = (
                            f'<button type="button" class="card-arrow card-prev" '
                            f'onclick="event.preventDefault();event.stopPropagation();cardStep(this,-1);" '
                            f'aria-label="Previous photo">&#8249;</button>'
                            f'<button type="button" class="card-arrow card-next" '
                            f'onclick="event.preventDefault();event.stopPropagation();cardStep(this,1);" '
                            f'aria-label="Next photo">&#8250;</button>'
                        )
                    else:
                        arrows = ""
                    groups.append(
                        f'<div class="card-group{" active" if ci == 0 else ""}" data-ci="{ci}">{imgs}{arrows}</div>'
                    )
                    swatches.append(
                        f'<button type="button" class="swatch{" active" if ci == 0 else ""}" '
                        f"style=\"background-image:url('{escape(urls[0])}')\" "
                        f'onclick="event.preventDefault();event.stopPropagation();cardShowColor(this,{ci});" '
                        f'aria-label="{escape(c)}" title="{escape(c)}"></button>'
                    )
                media = f'<div class="card-media">{"".join(groups)}</div>'
                swatch_row = f'<div class="card-swatches">{"".join(swatches)}</div>'
            else:
                media = (
                    f'<div class="card-media"><img src="{escape(fallback_img)}" '
                    f'alt="{escape(p["name"])}" class="active" loading="lazy"></div>'
                )
                swatch_row = ""

            card_blocks.append(
                f"""<a href="/product/{escape(p['slug'])}" class="card">
                      {media}
                      <div class="card-body">
                        <p class="card-name">{escape(p['name'])}</p>
                        <p class="card-price">{p['price']:.0f} EGP</p>
                        {swatch_row}
                      </div>
                    </a>"""
            )
        grid = f'<div class="grid">{"".join(card_blocks)}</div>'
    else:
        grid = '<div class="empty">No products in this category yet.</div>'

    body = f"""
{SHOP_CSS}
<nav class="chips">{''.join(chips)}</nav>
{sub_chips_html}
{grid}
"""
    return layout("Shop", body, categories, cart_count, active_category=active_category,
                  subcategories=subcategories, active_subcategory=active_subcategory)
GALLERY_CSS = """
<style>
.pg{max-width:340px;margin:0 auto;padding:12px 16px 0;}
.pg-group{display:none;}
.pg-group.active{display:block;}
.pg-view{position:relative;aspect-ratio:4/5;border-radius:10px;overflow:hidden;background:rgba(128,128,128,.12);}
.pg-view img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;display:none;}
.pg-view img.active{display:block;}
.pg-arrow{position:absolute;top:50%;transform:translateY(-50%);width:34px;height:34px;border:0;border-radius:50%;
  background:rgba(0,0,0,.55);color:#fff;font-size:22px;line-height:1;cursor:pointer;z-index:2;}
.pg-prev{left:8px;}
.pg-next{right:8px;}
.pg-dots{display:flex;justify-content:center;gap:8px;margin-top:10px;}
.pg-dot{width:9px;height:9px;border-radius:5px;border:0;padding:0;background:rgba(128,128,128,.55);cursor:pointer;transition:width .2s;}
.pg-dot.active{width:22px;background:var(--gold,#c9a24a);}
</style>
"""

GALLERY_JS = """
<script>
function pgShowColor(ci){
  document.querySelectorAll('.pg-group').forEach(function(g){
    g.classList.toggle('active', g.dataset.ci == ci);
  });
}
function pgSet(ci, idx){
  var g = document.querySelector('.pg-group[data-ci="' + ci + '"]');
  var imgs = g.querySelectorAll('.pg-view img');
  var dots = g.querySelectorAll('.pg-dot');
  imgs.forEach(function(im, i){ im.classList.toggle('active', i === idx); });
  dots.forEach(function(d, i){ d.classList.toggle('active', i === idx); });
}
function pgStep(ci, delta){
  var g = document.querySelector('.pg-group[data-ci="' + ci + '"]');
  var imgs = g.querySelectorAll('.pg-view img');
  var cur = 0;
  imgs.forEach(function(im, i){ if (im.classList.contains('active')) cur = i; });
  pgSet(ci, (cur + delta + imgs.length) % imgs.length);
}
</script>
"""

def product_page(p: dict, categories: list, cart_count: int = 0, subcategories: dict | None = None) -> str:
    size_pills = "".join(
        f'<label class="pill"><input type="radio" name="size" value="{escape(s)}"'
        f'{" checked" if i == 0 else ""}>{escape(s)}</label>'
        for i, s in enumerate(p["sizes"])
    )

    # color_images format: {"Black": ["url1", "url2"], "Olive": ["url3"]}
    color_images = p.get("color_images") or {}
    colors = p.get("colors") or []

    if color_images:
        groups = []
        for ci, c in enumerate(colors):
            urls = color_images.get(c) or [p.get("image_url") or ""]
            imgs = "".join(
                f'<img src="{escape(u)}" alt="{escape(p["name"])} in {escape(c)}"'
                f'{" class=active" if n == 0 else ""}>'
                for n, u in enumerate(urls)
            )
            if len(urls) > 1:
                arrows = (
                    f'<button type="button" class="pg-arrow pg-prev" onclick="pgStep({ci},-1)" aria-label="Previous photo">&#8249;</button>'
                    f'<button type="button" class="pg-arrow pg-next" onclick="pgStep({ci},1)" aria-label="Next photo">&#8250;</button>'
                )
                dots = '<div class="pg-dots">' + "".join(
                    f'<button type="button" class="pg-dot{" active" if n == 0 else ""}" '
                    f'onclick="pgSet({ci},{n})" aria-label="Photo {n + 1}"></button>'
                    for n in range(len(urls))
                ) + "</div>"
            else:
                arrows, dots = "", ""
            groups.append(
                f'<div class="pg-group{" active" if ci == 0 else ""}" data-ci="{ci}">'
                f'<div class="pg-view">{imgs}{arrows}</div>{dots}</div>'
            )
        image_block = f'{GALLERY_CSS}<div class="pg">{"".join(groups)}</div>{GALLERY_JS}'
        color_pills = "".join(
            f'<label class="pill"><input type="radio" name="color" value="{escape(c)}"'
            f'{" checked" if i == 0 else ""} onchange="pgShowColor({i})">{escape(c)}</label>'
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
    return layout(p["name"], body, categories, cart_count, subcategories=subcategories, show_back=True)


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