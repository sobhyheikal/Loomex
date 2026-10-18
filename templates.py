"""
HTML is built with small Python functions instead of separate .html files
(see comment history / README for why — keeps Vercel bundling simple).
"""

import json
from datetime import datetime
from html import escape

from config import META_PIXEL_ID, PAYMENT_METHODS, SHIPPING_RATES, SITE_URL, TIKTOK_PIXEL_ID

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700&'
    'family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">'
)

DEFAULT_DESCRIPTION = (
    "Loomex — heavyweight cotton homewear. Tops, pants, pullovers, "
    "quarter-zips and jackets built for the hours that don't need an outfit."
)
# A real product photo used as the fallback social-share image for pages
# that aren't about one specific product (home, shop, cart, legal pages...).
DEFAULT_OG_IMAGE = (
    "https://djeqpdphxcjceognytrv.supabase.co/storage/v1/object/public/"
    "product_images/Tank_Top-Front.JPG"
)

# ----------------------------------------------------------------------
# AD PIXELS — ids live in config.py (META_PIXEL_ID / TIKTOK_PIXEL_ID).
# Leave an id blank there to keep that pixel fully disabled.
# ----------------------------------------------------------------------
def _meta_pixel_script(extra_events: str = "") -> str:
    if not META_PIXEL_ID:
        return "<!-- Meta Pixel disabled — set META_PIXEL_ID in config.py to enable -->"
    return f"""
<!-- Meta Pixel Code -->
<script>
!function(f,b,e,v,n,t,s)
{{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)}};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '{META_PIXEL_ID}');
fbq('track', 'PageView');
{extra_events}
</script>
<noscript><img height="1" width="1" style="display:none"
src="https://www.facebook.com/tr?id={META_PIXEL_ID}&ev=PageView&noscript=1"
/></noscript>
<!-- End Meta Pixel Code -->
"""


def _tiktok_pixel_script(extra_events: str = "") -> str:
    if not TIKTOK_PIXEL_ID:
        return "<!-- TikTok Pixel disabled — set TIKTOK_PIXEL_ID in config.py to enable -->"
    return f"""
<!-- TikTok Pixel Code Start -->
<script>
!function (w, d, t) {{
  w.TiktokAnalyticsObject=t;var ttq=w[t]=w[t]||[];ttq.methods=["page","track","identify","instances","debug","on","off","once","ready","alias","group","enableCookie","disableCookie","holdConsent","revokeConsent","grantConsent"],ttq.setAndDefer=function(t,e){{t[e]=function(){{t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}}};for(var i=0;i<ttq.methods.length;i++)ttq.setAndDefer(ttq,ttq.methods[i]);ttq.instance=function(t){{for(
var e=ttq._i[t]||[],n=0;n<ttq.methods.length;n++)ttq.setAndDefer(e,ttq.methods[n]);return e}},ttq.load=function(e,n){{var r="https://analytics.tiktok.com/i18n/pixel/events.js",o=n&&n.partner;ttq._i=ttq._i||{{}},ttq._i[e]=[],ttq._i[e]._u=r,ttq._t=ttq._t||{{}},ttq._t[e]=+new Date,ttq._o=ttq._o||{{}},ttq._o[e]=n||{{}};n=document.createElement("script")
;n.type="text/javascript",n.async=!0,n.src=r+"?sdkid="+e+"&lib="+t;e=document.getElementsByTagName("script")[0];e.parentNode.insertBefore(n,e)}};

  ttq.load('{TIKTOK_PIXEL_ID}');
  ttq.page();
  {extra_events}
}}(window, document, 'ttq');
</script>
<!-- TikTok Pixel Code End -->
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
           show_back: bool = False, description: str | None = None,
           image: str | None = None, path: str = "",
           meta_pixel_events: str = "", tiktok_pixel_events: str = "") -> str:
    cat_links = _category_links(categories, subcategories, active_category, active_subcategory)
    cart_badge = f'<span class="cart-badge">{cart_count}</span>' if cart_count else ""
    back_btn = (
        '<button type="button" class="back-btn" aria-label="Go back"'
        ' onclick="window.history.length > 1 ? window.history.back() : window.location.href = \'/\'">&larr;</button>'
        if show_back else ""
    )

    page_title = f"{title} · Loomex"
    description = description or DEFAULT_DESCRIPTION
    image = image or DEFAULT_OG_IMAGE
    og_url_tag = f'<meta property="og:url" content="{escape(SITE_URL + path)}">' if SITE_URL else ""
    pixel_snippet = _meta_pixel_script(meta_pixel_events) + _tiktok_pixel_script(tiktok_pixel_events)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(page_title)}</title>
<meta name="description" content="{escape(description)}">
<meta property="og:site_name" content="Loomex">
<meta property="og:type" content="website">
<meta property="og:title" content="{escape(page_title)}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:image" content="{escape(image)}">
{og_url_tag}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escape(page_title)}">
<meta name="twitter:description" content="{escape(description)}">
<meta name="twitter:image" content="{escape(image)}">
{FONTS}
<link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
<link rel="apple-touch-icon" href="/static/apple-touch-icon.png">
<link rel="stylesheet" href="/static/style.css">
{pixel_snippet}
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
    <nav class="footer-links">
      <a href="/about">About &amp; Contact</a>
      <a href="/returns">Returns &amp; Exchanges</a>
      <a href="/terms">Terms of Service</a>
      <a href="/privacy-policy">Privacy Policy</a>
    </nav>
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
    return layout("Loomex — Homewear", body, categories, cart_count, subcategories=subcategories, path="/")
SHOP_CSS = """
<style>
.search-form{display:flex;align-items:center;gap:8px;padding:18px 18px 0;max-width:var(--max);margin:0 auto;}
.search-form input[type=search]{flex:1;padding:10px 14px;border:1px solid var(--line);background:var(--ink-raised);
  color:var(--paper);font-size:14px;font-family:inherit;border-radius:999px;}
.search-form input[type=search]::placeholder{color:var(--paper-dim);}
.search-btn{display:flex;align-items:center;justify-content:center;width:38px;height:38px;flex:0 0 auto;
  border:1px solid var(--line);background:transparent;color:var(--paper);border-radius:50%;cursor:pointer;padding:0;}
.search-btn svg{width:17px;height:17px;}
.search-btn:hover{border-color:var(--gold);color:var(--gold);}
.search-clear{flex:0 0 auto;color:var(--paper-dim);font-size:12.5px;text-decoration:underline;white-space:nowrap;}
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
              subcategories: dict | None = None, active_subcategory: str | None = None,
              search: str | None = None) -> str:
    subcategories = subcategories or {}
    search = (search or "").strip()
    q_suffix = f"&q={escape(search)}" if search else ""

    chips = ['<a href="/shop{}" class="chip{}">All</a>'.format(
        f"?q={escape(search)}" if search else "", " active" if not active_category else ""
    )]
    for c in categories:
        active = " active" if active_category == c else ""
        label = c.replace("-", " ").title()
        chips.append(f'<a href="/shop?category={c}{q_suffix}" class="chip{active}">{escape(label)}</a>')

    sub_chips_html = ""
    sub_items = subcategories.get(active_category) if active_category else None
    if sub_items:
        cat_label = active_category.replace("-", " ").title()
        sub_tabs = [
            '<a href="/shop?category={}{}" class="subtab{}">All {}</a>'.format(
                active_category, q_suffix, "" if not active_subcategory else " active", escape(cat_label)
            )
        ]
        for s in sub_items:
            s_active = " active" if active_subcategory == s else ""
            s_label = s.replace("-", " ").title()
            sub_tabs.append(
                f'<a href="/shop?category={active_category}&subcategory={s}{q_suffix}" '
                f'class="subtab{s_active}">{escape(s_label)}</a>'
            )
        sub_chips_html = f'<nav class="subtabs">{"".join(sub_tabs)}</nav>'

    search_form = f"""
<form action="/shop" method="get" class="search-form">
  {f'<input type="hidden" name="category" value="{escape(active_category)}">' if active_category else ""}
  {f'<input type="hidden" name="subcategory" value="{escape(active_subcategory)}">' if active_subcategory else ""}
  <input type="search" name="q" value="{escape(search)}" placeholder="Search products..." aria-label="Search products">
  <button type="submit" class="search-btn" aria-label="Search">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"></circle><path d="m21 21-4.3-4.3"></path></svg>
  </button>
  {f'<a href="/shop{("?category=" + active_category) if active_category else ""}" class="search-clear">Clear</a>' if search else ""}
</form>
"""

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
    elif search:
        grid = f'<div class="empty">No products match "{escape(search)}".</div>'
    else:
        grid = '<div class="empty">No products in this category yet.</div>'

    body = f"""
{SHOP_CSS}
{search_form}
<nav class="chips">{''.join(chips)}</nav>
{sub_chips_html}
{grid}
"""
    if search:
        shop_title = f'"{search}"'
        shop_description = f'Search results for "{search}" at Loomex.'
    else:
        shop_title = active_category.replace("-", " ").title() if active_category else "Shop All"
        shop_description = (
            f"Shop {shop_title} at Loomex — heavyweight cotton homewear made for comfort."
            if active_category else DEFAULT_DESCRIPTION
        )
    return layout(shop_title, body, categories, cart_count, active_category=active_category,
                  subcategories=subcategories, active_subcategory=active_subcategory,
                  description=shop_description, path="/shop")
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

    add_to_cart_js = (
        f"if(window.fbq){{fbq('track','AddToCart',{{content_ids:['{p['slug']}'],content_type:'product',"
        f"value:{p['price']:.2f}*(this.qty.value||1),currency:'EGP'}});}}"
        f"if(window.ttq){{ttq.track('AddToCart',{{content_id:'{p['slug']}',content_type:'product',"
        f"quantity:Number(this.qty.value||1),price:{p['price']:.2f},"
        f"value:{p['price']:.2f}*(this.qty.value||1),currency:'EGP'}});}}"
    )

    body = f"""
<div class="pd-layout">
{image_block}
<div class="pd-body">
  <h1 class="pd-name display">{escape(p['name'])}</h1>
  <p class="pd-price">{p['price']:.0f} EGP</p>
  <p class="pd-desc">{escape(p.get('description') or '')}</p>

  <form action="/cart/add" method="post" onsubmit="{add_to_cart_js}">
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
</div>
"""
    product_description = p.get("description") or f"{p['name']} — {p['price']:.0f} EGP at Loomex."
    meta_view_content = (
        f"fbq('track', 'ViewContent', {{content_ids: ['{p['slug']}'], content_type: 'product', "
        f"value: {p['price']:.2f}, currency: 'EGP'}});"
    )
    tiktok_view_content = (
        f"ttq.track('ViewContent', {{content_id: '{p['slug']}', content_type: 'product', "
        f"value: {p['price']:.2f}, currency: 'EGP'}});"
    )
    return layout(p["name"], body, categories, cart_count, subcategories=subcategories, show_back=True,
                  description=product_description, image=p.get("image_url"), path=f"/product/{p['slug']}",
                  meta_pixel_events=meta_view_content, tiktok_pixel_events=tiktok_view_content)


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
        return layout("Your Cart", body, categories, cart_count, subcategories=subcategories, path="/cart",
                      section_class="cart-page")

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
  <p style="color:var(--paper-dim);font-size:12.5px;margin:8px 0 20px;">Shipping cost is calculated at checkout based on your city.</p>
  <a href="/checkout" class="btn">Checkout</a>
</div>
"""
    return layout("Your Cart", body, categories, cart_count, subcategories=subcategories, path="/cart",
                  section_class="cart-page")


CHECKOUT_CSS = """
<style>
.checkout-hint { color: var(--paper-dim); font-size: 12.5px; margin: -8px 0 20px; }
.pay-option input[type=radio] { margin: 3px 0 0; accent-color: var(--gold); flex: 0 0 auto; }
.payment-proof-box {
  border: 1px solid var(--line); background: var(--ink-raised); padding: 14px;
  margin: -2px 0 10px; font-size: 13px;
}
.payment-proof-detail { color: var(--paper); margin: 0; line-height: 1.6; }
.payment-proof-box input[type=file] {
  width: 100%; margin-top: 8px; padding: 10px; border: 1px solid var(--line);
  background: var(--ink); color: var(--paper); font-size: 13px; font-family: inherit;
}
</style>
"""


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

    city_options = "".join(
        f'<option value="{escape(city)}">{escape(city)}</option>' for city in SHIPPING_RATES
    )
    rates_json = json.dumps(SHIPPING_RATES)

    payment_options = "".join(
        f"""<label class="pay-option">
              <input type="radio" name="payment_method" value="{key}"{' checked' if key == 'cod' else ''}
                onchange="loomexShowPayment('{key}')">
              <span><strong>{escape(m['label'])}</strong><span>{escape(m['description'])}</span></span>
            </label>"""
        for key, m in PAYMENT_METHODS.items()
    )
    payment_details_json = json.dumps({k: m["detail"] for k, m in PAYMENT_METHODS.items() if k != "cod"})

    body = f"""
{CHECKOUT_CSS}
<div class="wrap">
  <h1 class="display">Checkout</h1>
  <p class="sub">Almost there — fill in your details below.</p>

  {summary_rows}
  <div class="summary-line">
    <span>Subtotal</span>
    <span>{subtotal:.0f} EGP</span>
  </div>
  <div class="summary-line" id="shipping-row">
    <span>Shipping</span>
    <span id="shipping-amount">—</span>
  </div>
  <div class="summary-line summary-total">
    <span>Total</span>
    <span id="total-amount">{subtotal:.0f} EGP</span>
  </div>
  <p class="checkout-hint" id="shipping-hint">Select your city below to see the shipping cost.</p>

  {error_html}

  <form action="/checkout" method="post" enctype="multipart/form-data" style="margin-top:10px;">
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
      <select name="city" id="city-select" required onchange="loomexUpdateShipping(this.value)">
        <option value="" disabled selected>Select your city</option>
        {city_options}
      </select>
    </div>
    <div class="form-group">
      <label>Full address</label>
      <input type="text" name="address" required>
    </div>

    <span class="field-label">Payment Method</span>
    {payment_options}

    <div class="payment-proof-box" id="payment-proof-box" style="display:none;">
      <p class="payment-proof-detail" id="payment-proof-detail"></p>
      <label class="field-label" style="margin-top:14px;">Upload payment screenshot</label>
      <input type="file" name="payment_proof" accept="image/*" id="payment-proof-input">
    </div>

    <button class="btn" type="submit" style="margin-top:20px;">Place Order</button>
  </form>
</div>
<script>
var LOOMEX_RATES = {rates_json};
var LOOMEX_SUBTOTAL = {subtotal:.2f};
var LOOMEX_PAYMENT_DETAILS = {payment_details_json};
function loomexUpdateShipping(city) {{
  var rate = LOOMEX_RATES[city];
  if (rate === undefined) return;
  document.getElementById('shipping-amount').textContent = rate.toFixed(0) + ' EGP';
  document.getElementById('total-amount').textContent = (LOOMEX_SUBTOTAL + rate).toFixed(0) + ' EGP';
  document.getElementById('shipping-hint').style.display = 'none';
}}
function loomexShowPayment(method) {{
  var box = document.getElementById('payment-proof-box');
  var input = document.getElementById('payment-proof-input');
  var detail = LOOMEX_PAYMENT_DETAILS[method];
  if (detail) {{
    box.style.display = 'block';
    input.required = true;
    document.getElementById('payment-proof-detail').innerHTML =
      'Send the <strong>total</strong> shown above to:<br><strong>' + detail + '</strong>';
  }} else {{
    box.style.display = 'none';
    input.required = false;
  }}
}}
</script>
"""
    return layout("Checkout", body, categories, cart_count, section_class="checkout", subcategories=subcategories, path="/checkout")


PAYMENT_LABELS = {k: m["label"] for k, m in PAYMENT_METHODS.items()}

RECEIPT_CSS = """
<style>
.success .wrap { padding: 46px 18px 60px; text-align: center; }
.success-check {
  width: 44px; height: 44px; margin: 0 auto 16px; border-radius: 50%;
  background: var(--teal); color: #fff; font-size: 20px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.success-title { font-size: 26px; margin: 0 0 6px; color: var(--paper); }
.success-sub { color: var(--paper-dim); font-size: 13.5px; margin: 0 0 30px; }

.receipt {
  background: #fff;
  border: 1px solid var(--stone-line);
  box-shadow: 0 10px 30px rgba(32, 28, 24, 0.08);
  max-width: 360px;
  margin: 0 auto;
  padding: 26px 22px;
  text-align: left;
  font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  color: var(--ink-on-stone);
  font-size: 12px;
}
.receipt-brand {
  text-align: center;
  font-family: "Big Shoulders Display", sans-serif;
  font-weight: 700;
  letter-spacing: 0.1em;
  font-size: 22px;
  color: var(--ink-on-stone);
}
.receipt-tagline { text-align: center; color: var(--ink-dim-on-stone); font-size: 10.5px; margin: 4px 0 18px; }
.receipt-rule { border: none; border-top: 1px dashed var(--stone-line); margin: 16px 0; }
.receipt-meta-row { display: flex; justify-content: space-between; padding: 2px 0; letter-spacing: 0.04em; }
.receipt-meta-row span:first-child { color: var(--ink-dim-on-stone); }
.receipt-meta-row strong { font-weight: 700; }
.receipt-section-label {
  font-weight: 700; letter-spacing: 0.08em; font-size: 11px; margin-bottom: 8px;
}
.receipt-customer p { margin: 0 0 3px; }
.receipt-items-head {
  display: grid; grid-template-columns: 1fr 34px 64px; gap: 6px;
  text-transform: uppercase; letter-spacing: 0.06em; font-size: 10.5px;
  color: var(--ink-dim-on-stone); padding-bottom: 6px;
}
.receipt-item { padding: 9px 0; border-bottom: 1px dashed var(--stone-line); }
.receipt-item:last-child { border-bottom: none; }
.receipt-item-top { display: grid; grid-template-columns: 1fr 34px 64px; gap: 6px; font-weight: 700; }
.receipt-item-top span:nth-child(2) { text-align: center; font-weight: 400; }
.receipt-item-top span:nth-child(3) { text-align: right; }
.receipt-item-variant, .receipt-item-unit {
  font-size: 10.5px; color: var(--ink-dim-on-stone); margin-top: 2px;
}
.receipt-totals { margin-top: 2px; }
.receipt-total-row { display: flex; justify-content: space-between; padding: 4px 0; }
.receipt-total-main {
  border-top: 1px solid var(--ink-on-stone); margin-top: 6px; padding-top: 10px;
  font-weight: 700; font-size: 14px;
}
.receipt-payment-box {
  margin-top: 16px; padding: 12px; text-align: center;
  border: 1px solid var(--stone-line);
}
.receipt-payment-label { font-size: 10px; letter-spacing: 0.08em; color: var(--ink-dim-on-stone); margin: 0 0 3px; }
.receipt-payment-value { font-weight: 700; margin: 0; }
.receipt-thanks { text-align: center; }
.receipt-thanks p { margin: 0 0 4px; }
.receipt-thanks-note { color: var(--ink-dim-on-stone); font-size: 10.5px; }
.receipt-brand-small {
  font-family: "Big Shoulders Display", sans-serif; font-weight: 700;
  letter-spacing: 0.08em; font-size: 12px; margin-top: 8px !important;
}
</style>
"""


def success_page(order: dict, categories: list, subcategories: dict | None = None) -> str:
    items = order.get("items") or []
    subtotal = sum(float(i["unit_price"]) * int(i["quantity"]) for i in items)
    shipping = float(order.get("shipping") or 0)
    total = float(order.get("total") or (subtotal + shipping))
    payment_label = PAYMENT_LABELS.get(order.get("payment_method"), "Cash on Delivery")

    created_at = order.get("created_at") or ""
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        date_str = dt.strftime("%d/%m/%Y")
        time_str = dt.strftime("%I:%M %p")
    except ValueError:
        date_str, time_str = "", ""

    item_rows = "".join(
        f"""<div class="receipt-item">
              <div class="receipt-item-top">
                <span>{escape(i['product_name'])}</span>
                <span>{int(i['quantity'])}</span>
                <span>{float(i['unit_price']) * int(i['quantity']):.0f} EGP</span>
              </div>
              {f'<div class="receipt-item-variant">{escape(" / ".join(filter(None, [i.get("size"), i.get("color")])))}</div>' if i.get("size") or i.get("color") else ""}
              <div class="receipt-item-unit">{float(i['unit_price']):.0f} EGP x {int(i['quantity'])}</div>
            </div>"""
        for i in items
    )

    customer_lines = "".join(
        f"<p>{escape(v)}</p>" for v in [order.get("customer_name"), order.get("phone"),
                                         order.get("address"), order.get("city")] if v
    )

    body = f"""
{RECEIPT_CSS}
<div class="wrap">
  <div class="success-check">&#10003;</div>
  <h1 class="success-title display">Order Confirmed</h1>
  <p class="success-sub">Thank you for shopping with Loomex.</p>

  <div class="receipt">
    <div class="receipt-brand">LOOMEX</div>
    <p class="receipt-tagline">Homewear, woven for rest</p>

    <div class="receipt-meta-row"><span>ORDER</span><strong>{escape(order['order_number'])}</strong></div>
    <div class="receipt-meta-row"><span>DATE</span><strong>{escape(date_str)}</strong></div>
    <div class="receipt-meta-row"><span>TIME</span><strong>{escape(time_str)}</strong></div>
    <div class="receipt-meta-row"><span>PAYMENT</span><strong>{escape(payment_label.upper())}</strong></div>

    <hr class="receipt-rule">

    <div class="receipt-section-label">CUSTOMER</div>
    <div class="receipt-customer">{customer_lines}</div>

    <hr class="receipt-rule">

    <div class="receipt-items-head"><span>ITEM</span><span>QTY</span><span>AMOUNT</span></div>
    {item_rows}

    <div class="receipt-totals">
      <div class="receipt-total-row"><span>SUBTOTAL</span><span>{subtotal:.0f} EGP</span></div>
      <div class="receipt-total-row"><span>SHIPPING</span><span>{shipping:.0f} EGP</span></div>
      <div class="receipt-total-row receipt-total-main"><span>TOTAL</span><span>{total:.0f} EGP</span></div>
    </div>

    <div class="receipt-payment-box">
      <p class="receipt-payment-label">PAYMENT METHOD</p>
      <p class="receipt-payment-value">{escape(payment_label.upper())}</p>
    </div>

    <hr class="receipt-rule">

    <div class="receipt-thanks">
      <p><strong>THANK YOU!</strong></p>
      <p class="receipt-thanks-note">Thank you for choosing Loomex.<br>Your order will be prepared with care.</p>
      <p class="receipt-brand-small">LOOMEX</p>
    </div>
  </div>

  <a href="/shop" class="btn" style="margin-top:26px;max-width:260px;margin-left:auto;margin-right:auto;">Continue Shopping</a>
</div>
"""
    # Each guarded with its own localStorage key so reloading/revisiting
    # this confirmation page (e.g. the customer bookmarks it, or refreshes)
    # doesn't fire a duplicate Purchase/CompletePayment and inflate ad
    # reporting. Separate keys per platform so one firing doesn't suppress
    # the other on the same visit.
    order_number_js = json.dumps(order["order_number"])
    content_ids_js = json.dumps([i["product_name"] for i in items])
    meta_purchase_event = (
        "(function(){try{"
        "var k='loomex_purchase_tracked_meta';"
        "var tracked=JSON.parse(localStorage.getItem(k)||'[]');"
        f"if(tracked.indexOf({order_number_js})===-1){{"
        f"fbq('track','Purchase',{{value:{total:.2f},currency:'EGP',"
        f"content_ids:{content_ids_js},content_type:'product',num_items:{len(items)}}});"
        f"tracked.push({order_number_js});"
        "localStorage.setItem(k,JSON.stringify(tracked));"
        "}}catch(e){}})();"
    )
    tiktok_purchase_event = (
        "(function(){try{"
        "var k='loomex_purchase_tracked_tiktok';"
        "var tracked=JSON.parse(localStorage.getItem(k)||'[]');"
        f"if(tracked.indexOf({order_number_js})===-1){{"
        f"ttq.track('CompletePayment',{{value:{total:.2f},currency:'EGP',"
        f"contents:{content_ids_js}.map(function(n){{return {{content_id:n,content_type:'product'}};}})}});"
        f"tracked.push({order_number_js});"
        "localStorage.setItem(k,JSON.stringify(tracked));"
        "}}catch(e){}})();"
    )
    return layout("Order confirmed", body, categories, 0, section_class="success", subcategories=subcategories,
                  description="Your Loomex order is confirmed.", meta_pixel_events=meta_purchase_event,
                  tiktok_pixel_events=tiktok_purchase_event)


# ----------------------------------------------------------------------
# LEGAL / TRUST PAGES — About, Privacy, Terms, Returns.
# ----------------------------------------------------------------------
LEGAL_UPDATED = "October 2026"

LEGAL_CSS = """
<style>
.legal .wrap { padding: 30px 18px 60px; max-width: 620px; }
.legal .wrap h1 { font-size: 28px; margin: 0 0 6px; color: var(--paper); }
.legal-updated { color: var(--paper-dim); font-size: 12px; margin-bottom: 28px; }
.legal .wrap h2 { font-size: 15px; color: var(--gold); margin: 28px 0 10px; text-transform: uppercase; letter-spacing: 0.04em; }
.legal .wrap p { color: var(--paper-dim); font-size: 14px; line-height: 1.7; margin: 0 0 14px; }
.legal .wrap ul { color: var(--paper-dim); font-size: 14px; line-height: 1.7; margin: 0 0 14px; padding-left: 20px; }
.legal .wrap li { margin-bottom: 6px; }
.legal .wrap a { color: var(--gold); text-decoration: underline; }
.legal-contact-block { background: var(--ink-raised); border: 1px solid var(--line); padding: 18px; margin: 10px 0 20px; }
.legal-contact-block p { margin: 0 0 10px; color: var(--paper); }
.legal-contact-block p:last-child { margin-bottom: 0; }
.legal-contact-block .label {
  color: var(--paper-dim); font-size: 11px; text-transform: uppercase;
  letter-spacing: 0.08em; display: block; margin-bottom: 2px;
}
</style>
"""


def legal_page(title: str, body: str, categories: list, cart_count: int = 0,
                subcategories: dict | None = None, description: str | None = None,
                path: str = "") -> str:
    full = f"""
{LEGAL_CSS}
<div class="wrap">
  <h1 class="display">{escape(title)}</h1>
  <p class="legal-updated">Last updated {LEGAL_UPDATED}</p>
  {body}
</div>
"""
    return layout(title, full, categories, cart_count, section_class="legal", subcategories=subcategories,
                  description=description, path=path)


def about_page(categories: list, cart_count: int = 0, subcategories: dict | None = None) -> str:
    body = """
<p>Loomex makes heavyweight cotton homewear — tops, pants, pullovers,
quarter-zips and jackets built for the hours that don't need an outfit.</p>

<h2>Get in touch</h2>
<p>Questions about an order, sizing, or anything else — reach us any time:</p>
<div class="legal-contact-block">
  <p><span class="label">Email</span><a href="mailto:loomex.co@gmail.com">loomex.co@gmail.com</a></p>
  <p><span class="label">Phone / WhatsApp</span><a href="tel:+201130704895">01130704895</a></p>
</div>
<p>We currently ship within Egypt and accept Cash on Delivery only.
Delivery cost and timing are confirmed by phone after you place an order.</p>
"""
    return legal_page("About & Contact", body, categories, cart_count, subcategories=subcategories,
                      description="Get in touch with Loomex — questions about an order, sizing, or anything else.",
                      path="/about")


def returns_page(categories: list, cart_count: int = 0, subcategories: dict | None = None) -> str:
    body = """
<p>We want you to be happy with your order. If something isn't right,
here's how returns and exchanges work.</p>

<h2>Return window</h2>
<p>You have <strong>7 days from the date your order is delivered</strong> to
request a return or exchange.</p>

<h2>Condition</h2>
<ul>
  <li>Items must be unworn, unwashed, and in their original condition.</li>
  <li>Tags (if any) must still be attached.</li>
</ul>

<h2>Return shipping</h2>
<p>Return shipping is paid by the customer. We recommend a trackable courier —
we can't issue a refund or exchange for an item that doesn't reach us.</p>

<h2>Refunds</h2>
<p>Since we currently accept Cash on Delivery only, refunds are issued as
store credit, or by bank/wallet transfer if you'd prefer — just let us know
when you reach out.</p>

<h2>How to start a return</h2>
<p>Email <a href="mailto:loomex.co@gmail.com">loomex.co@gmail.com</a> or message
us at <a href="tel:+201130704895">01130704895</a> with your order number and the
reason for the return, and we'll walk you through the next steps.</p>
"""
    return legal_page("Returns & Exchanges", body, categories, cart_count, subcategories=subcategories,
                      description="Loomex returns and exchanges policy — 7-day return window, how refunds work.",
                      path="/returns")


def terms_page(categories: list, cart_count: int = 0, subcategories: dict | None = None) -> str:
    body = """
<p>These terms apply to any order placed through the Loomex website. By
placing an order, you agree to them.</p>

<h2>Products &amp; pricing</h2>
<p>All prices are listed in Egyptian Pounds (EGP). We try to keep product
photos, descriptions, and sizing accurate, but occasional errors can happen —
if a listed price or description is wrong, we'll contact you before
processing the order.</p>

<h2>Orders &amp; payment</h2>
<p>We currently accept Cash on Delivery only. Placing an order is a request
to buy, not a guaranteed sale — we may decline or cancel an order, for
example if a product turns out to be out of stock or we can't confirm
delivery details by phone.</p>

<h2>Delivery</h2>
<p>Delivery areas, cost, and estimated timing are confirmed by phone after
you place an order, based on your city and address.</p>

<h2>Returns &amp; exchanges</h2>
<p>See our <a href="/returns">Returns &amp; Exchanges</a> page for the full policy.</p>

<h2>Intellectual property</h2>
<p>All content on this site — including the Loomex name, logo, product
photography, and text — belongs to Loomex and may not be reused without
permission.</p>

<h2>Limitation of liability</h2>
<p>Loomex isn't liable for indirect or incidental damages arising from use
of this site or its products, to the extent permitted by law.</p>

<h2>Contact</h2>
<p>Questions about these terms? Reach us at
<a href="mailto:loomex.co@gmail.com">loomex.co@gmail.com</a>.</p>
"""
    return legal_page("Terms of Service", body, categories, cart_count, subcategories=subcategories,
                      description="Terms of Service for shopping with Loomex.",
                      path="/terms")


def privacy_page(categories: list, cart_count: int = 0, subcategories: dict | None = None) -> str:
    body = """
<p>This page explains what information Loomex collects when you shop with
us, and how it's used.</p>

<h2>What we collect</h2>
<p>When you place an order, we collect the information you provide at
checkout: your name, phone number, delivery address, and city. We don't
collect payment card details, since we currently accept Cash on Delivery
only.</p>

<h2>How we use it</h2>
<ul>
  <li>To process and deliver your order.</li>
  <li>To contact you by phone to confirm delivery details and cost.</li>
</ul>
<p>We don't sell your personal information, and we don't share your name,
phone number, or address with advertising platforms.</p>

<h2>Cookies &amp; analytics</h2>
<p>We use a single cookie to remember what's in your shopping cart. It
doesn't track you across other websites.</p>
<p>We also use the Meta (Facebook/Instagram) Pixel, which sets its own
cookies and collects browsing data — such as which pages and products you
view — to help us understand site traffic and measure the performance of
our ads. This is separate from the order information above: the pixel
doesn't receive your name, phone number, or address. You can opt out of
this kind of tracking in your browser or ad settings; see Meta's own
<a href="https://www.facebook.com/privacy/policy/" target="_blank" rel="noopener">privacy policy</a>
for how they handle this data.</p>

<h2>Data storage</h2>
<p>Order information is stored securely in our database and kept only as
long as needed to fulfill and keep records of your order.</p>

<h2>Your rights</h2>
<p>You can ask us what information we hold about you, or ask us to delete
it, by emailing <a href="mailto:loomex.co@gmail.com">loomex.co@gmail.com</a>.</p>
"""
    return legal_page("Privacy Policy", body, categories, cart_count, subcategories=subcategories,
                      description="How Loomex collects and uses your information.",
                      path="/privacy-policy")


# ----------------------------------------------------------------------
# ERROR PAGES — 404 and other HTTP errors, styled to match the site
# instead of a bare <h1>.
# ----------------------------------------------------------------------
ERROR_CSS = """
<style>
.error-page .wrap { padding: 60px 18px; text-align: center; min-height: 50vh;
  display: flex; flex-direction: column; align-items: center; justify-content: center; }
.error-code { font-family: "Big Shoulders Display", sans-serif; font-weight: 700;
  font-size: 72px; color: var(--gold); letter-spacing: 0.05em; margin: 0; }
.error-message { font-size: 15px; color: var(--paper-dim); margin: 10px 0 28px; max-width: 32ch; }
</style>
"""


def error_page(categories: list, cart_count: int = 0, subcategories: dict | None = None,
                status_code: int = 404, message: str | None = None) -> str:
    message = message or "That page doesn't exist — it may have been moved or the link is out of date."
    body = f"""
{ERROR_CSS}
<div class="error-page">
  <div class="wrap">
    <p class="error-code">{status_code}</p>
    <p class="error-message">{escape(message)}</p>
    <a href="/shop" class="btn" style="max-width:220px;">Back to Shop</a>
  </div>
</div>
"""
    title = "Page not found" if status_code == 404 else "Something went wrong"
    return layout(title, body, categories, cart_count, subcategories=subcategories)