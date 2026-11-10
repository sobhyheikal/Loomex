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
    'family=Playfair+Display:ital,wght@0,600;1,500&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">'
)

DEFAULT_DESCRIPTION = (
    "Loomex — heavyweight cotton homewear. Tops, pants, hoodies, "
    "sweatshirts and jackets built for the hours that don't need an outfit."
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

CART_DRAWER_CSS = """
<style>
.cart-backdrop {
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.5);
  opacity: 0; pointer-events: none; transition: opacity 0.2s ease; z-index: 39;
}
.cart-backdrop.open { opacity: 1; pointer-events: auto; }
.cart-drawer {
  position: fixed; top: 0; right: 0; bottom: 0; width: 100%; max-width: 400px;
  background: var(--ink); border-left: 1px solid var(--line); z-index: 40;
  display: flex; flex-direction: column;
  transform: translateX(100%); visibility: hidden;
  transition: transform 0.25s ease, visibility 0s linear 0.25s;
}
.cart-drawer.open { transform: translateX(0); visibility: visible; transition: transform 0.25s ease, visibility 0s; }
.cart-drawer-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 20px; border-bottom: 1px solid var(--line);
}
.cart-drawer-title {
  font-family: "Big Shoulders Display", sans-serif; font-weight: 700; font-size: 22px;
  letter-spacing: 0.03em; text-transform: uppercase; color: var(--paper);
}
.cart-drawer-close {
  background: none; border: none; color: var(--paper-dim);
  font-size: 28px; line-height: 1; cursor: pointer; padding: 0 4px;
}
.cart-drawer-body { flex: 1; overflow-y: auto; padding: 0 20px; }
.cart-drawer-foot { padding: 16px 20px 22px; border-top: 1px solid var(--line); }
.cart-drawer-foot:empty { display: none; }
.cd-line {
  display: grid; grid-template-columns: 64px 1fr auto; gap: 12px;
  padding: 16px 0; border-bottom: 1px solid var(--line); align-items: flex-start;
}
.cd-img { width: 64px; aspect-ratio: 4/5; object-fit: contain; background: rgba(128, 128, 128, 0.12); }
.cd-name { font-size: 14px; margin: 0 0 2px; color: var(--paper); }
.cd-variant { font-size: 12px; color: var(--paper-dim); margin: 0 0 10px; text-transform: capitalize; }
.cd-qty { display: inline-flex; align-items: center; border: 1px solid var(--line); }
.cd-qty button {
  width: 30px; height: 30px; background: none; border: none;
  color: var(--paper); font-size: 16px; cursor: pointer;
}
.cd-qty button:disabled { color: var(--paper-dim); opacity: 0.4; cursor: default; }
.cd-qty span { min-width: 28px; text-align: center; font-size: 13px; color: var(--paper); }
.cd-side { display: flex; flex-direction: column; align-items: flex-end; gap: 10px; }
.cd-total { font-size: 13px; font-weight: 600; white-space: nowrap; margin: 0; color: var(--paper); }
.cd-remove {
  background: none; border: none; color: var(--paper-dim);
  font-size: 12px; text-decoration: underline; cursor: pointer; padding: 0;
}
.cd-empty { color: var(--paper-dim); font-size: 14px; padding: 30px 0; text-align: center; }
.cd-subtotal { display: flex; justify-content: space-between; font-weight: 700; font-size: 15px; margin-bottom: 6px; }
.cd-note { color: var(--paper-dim); font-size: 12px; margin: 0 0 14px; }
.cd-viewcart {
  display: block; text-align: center; color: var(--paper-dim);
  font-size: 12.5px; text-decoration: underline; margin-top: 12px;
}
body.cart-open { overflow: hidden; }
.cart-line-img { object-fit: contain; background: rgba(128, 128, 128, 0.12); }
</style>
"""
FOOTER_CSS = """
<style>
.footer { padding: 0; margin-top: 30px; border-top: 1px solid var(--line); background: var(--ink); }
.footer-inner {
  display: grid; grid-template-columns: 1fr auto 1fr; align-items: center;
  padding: 14px 18px; max-width: var(--max); margin: 0 auto;
}
.footer-left { justify-self: start; }
.footer-privacy { color: var(--paper-dim); font-size: 11.5px; text-decoration: underline; }
.footer-social { justify-self: end; display: flex; align-items: center; gap: 14px; }
.social-link { display: inline-flex; color: var(--paper); }
.social-link svg { width: 22px; height: 22px; }
a.social-link:hover { color: var(--gold); }
span.social-link { cursor: default; }
@media (min-width: 900px) { .footer-inner { max-width: var(--max-wide); padding: 16px 32px; } }
</style>
"""
_PROMO_BANNER_JS = """<script>
(function(){
  var v=document.querySelector('.promo-banner-view');
  if(!v)return;
  var t=v.firstElementChild;
  var orig=t.innerHTML, SPEED=45, GAP=48, lastW=0, timer=null;
  function setup(){
    lastW=v.clientWidth;
    t.classList.remove('scroll');
    t.innerHTML=orig;
    t.style.animationDuration='';
    t.style.animationDelay='';
    if(t.scrollWidth<=v.clientWidth+1)return;
    var dur=Math.max(8,(t.scrollWidth+GAP)/SPEED);
    t.innerHTML=orig+orig;
    t.classList.add('scroll');
    var t0=Date.now();
    try{
      var s=parseInt(sessionStorage.getItem('promoBannerT0'),10);
      if(s){t0=s;}else{sessionStorage.setItem('promoBannerT0',String(t0));}
    }catch(e){}
    var off=((Date.now()-t0)/1000)%dur;
    t.style.animationDuration=dur+'s';
    t.style.animationDelay='-'+off+'s';
  }
  function start(){setup();}
  if(document.fonts&&document.fonts.ready){document.fonts.ready.then(start);}
  else{window.addEventListener('load',start);}
  window.addEventListener('resize',function(){
    clearTimeout(timer);
    timer=setTimeout(function(){if(v.clientWidth!==lastW)setup();},150);
  });
  window.addEventListener('pageshow',function(e){if(e.persisted)setup();});
})();
</script>"""


def _promo_banner_html() -> str:
    try:
        from services.promotions import get_banner_promotions
        promos = get_banner_promotions()
    except Exception:
        return ""
    if not promos:
        return ""
    p = promos[0]  # newest live promotion

    message = (p.get("message") or "").strip()
    if not message:
        return ""
    subtitle = (p.get("subtitle") or "").strip()
    url = (p.get("link_url") or "").strip()
    safe = (url.startswith("/") and not url.startswith("//")) or url.startswith(("https://", "http://"))

    sub_html = f'<span class="promo-banner-sub">{escape(subtitle)}</span>' if subtitle else ""
    btn = ""
    if url and safe:
        btn_label = (p.get("link_text") or "").strip() or "Shop now"
        btn = f'<a class="promo-banner-btn" href="{escape(url)}">{escape(btn_label)}</a>'

    return (
        '<div class="promo-banner"><div class="promo-banner-view"><div class="promo-banner-track">'
        f'<span class="promo-banner-item"><span class="promo-banner-text">{escape(message)}</span>{sub_html}</span>'
        f'</div></div>{btn}</div>{_PROMO_BANNER_JS}'
    )


_BADGE_TYPES = {"percent_off", "fixed_off", "bogo", "second_item_pct",
                "buy_n_get_1", "buy_n_pct", "bundle_price", "min_spend_pct"}


def _promo_badge(p: dict) -> str:
    try:
        from services.promotions import get_live_promotions, describe
        pid = str(p.get("id") or "")
        for promo in get_live_promotions():  # newest first
            if promo.get("discount_type") not in _BADGE_TYPES or promo.get("code"):
                continue
            ids = {str(i) for i in (promo.get("product_ids") or [])}
            if ids and pid not in ids:  # empty list = covers every product
                continue
            return f'<span class="promo-badge">{escape(describe(promo))}</span>'
    except Exception:
        pass
    return ""
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
    promo_banner = _promo_banner_html()
    body_class = f"{section_class} has-banner".strip() if promo_banner else section_class

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
<link rel="stylesheet" href="/static/style.css?v=6">
{pixel_snippet}
</head>
<body class="{body_class}">
<input type="checkbox" id="menu-toggle" class="menu-toggle-input">
<label for="menu-toggle" class="drawer-backdrop"></label>
<nav class="drawer">
  <label for="menu-toggle" class="drawer-close">&times;</label>
  <a href="/" class="drawer-link">Home</a>
  <a href="/shop" class="drawer-link">Shop All</a>
     <div class="drawer-sub">{cat_links}</div>
  <hr class="thread-rule">
  <a href="/returns" class="drawer-link">Return Policy</a>
</nav>

<header class="topbar">
{promo_banner}
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
{CART_DRAWER_CSS}
<div class="cart-backdrop" id="cart-backdrop"></div>
<aside class="cart-drawer" id="cart-drawer" aria-hidden="true" aria-label="Shopping cart">
  <div class="cart-drawer-head">
    <span class="cart-drawer-title">Your Cart</span>
    <button type="button" class="cart-drawer-close" data-act="close" aria-label="Close cart">&times;</button>
  </div>
  <div class="cart-drawer-body" id="cart-drawer-body"></div>
  <div class="cart-drawer-foot" id="cart-drawer-foot"></div>
</aside>
{f'<div class="back-btn-wrap">{back_btn}</div>' if show_back else ""}
{body}
{FOOTER_CSS}
<footer class="footer">
  <div class="footer-inner">
    <div class="footer-left"></div>
    <a href="/" class="logo">LOOM<span>EX</span></a>
    <div class="footer-social">
      <a href="https://www.instagram.com/loomex_clothing" target="_blank" rel="noopener" class="social-link" aria-label="Instagram">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
          <circle cx="12" cy="12" r="4"></circle>
          <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
        </svg>
      </a>
      <span class="social-link" aria-label="TikTok">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M21 7.917v4.034a9.948 9.948 0 0 1 -5 -1.951v4.5a6.5 6.5 0 1 1 -8 -6.326v4.326a2.5 2.5 0 1 0 4 2v-11.5h4.083a6.005 6.005 0 0 0 4.917 4.917z"></path>
        </svg>
      </span>
    </div>
  </div>
</footer>
<script src="/static/cart-drawer.js?v=2" defer></script>
</body>
</html>"""

HOME_CSS = """
<style>
.hp { overflow-x: hidden; }
.hp-wrap { max-width: var(--max); margin: 0 auto; padding: 0 18px; }

@keyframes hp-rise { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: none; } }
.hp-rise { animation: hp-rise 0.7s ease both; }
.hp-rise.d1 { animation-delay: 0.08s; }
.hp-rise.d2 { animation-delay: 0.18s; }
.hp-rise.d3 { animation-delay: 0.28s; }

/* hero */
.hp-hero { padding: 44px 0 46px; }
.hp-hero-grid { display: grid; gap: 40px; align-items: center; }
.hp-eyebrow {
  display: flex; align-items: center; gap: 10px; margin: 0 0 14px;
  font-size: 12px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--gold);
}
.hp-eyebrow::before { content: ""; width: 28px; height: 1px; background: var(--gold); }
.hp-title { font-size: clamp(58px, 17vw, 118px); margin: 0 0 18px; color: var(--paper); }
.hp-title em { font-style: normal; color: var(--gold); }
.hp-lead { color: var(--paper-dim); font-size: 15.5px; line-height: 1.6; max-width: 38ch; margin: 0 0 26px; }
.hp-cta { display: flex; gap: 10px; flex-wrap: wrap; }
.hp-cta .btn { display: inline-block; width: auto; min-width: 150px; padding: 15px 26px; text-decoration: none; }
.hp-cta .btn.hp-ghost { background: transparent; color: var(--paper); border: 1px solid var(--paper-dim); }
.hp-cta .btn.hp-ghost:hover { background: transparent; border-color: var(--gold); color: var(--gold); }
/* hero over banner */
.hp-hero { position: relative; isolation: isolate; display: flex; align-items: flex-end;
  min-height: min(88vh, 720px); padding: 0; overflow: hidden; }
.hp-hero-bg { position: absolute; inset: 0; z-index: -2; }
.hp-hero-bg img { display: block; width: 100%; height: 100%; object-fit: cover; object-position: center; }
.hp-hero::after { content: ""; position: absolute; inset: 0; z-index: -1;
  background: linear-gradient(to top, rgba(18,15,12,.94) 0%, rgba(18,15,12,.6) 42%, rgba(18,15,12,.12) 100%); }
.hp-hero .hp-wrap { box-sizing: border-box; width: 100%; padding-top: 120px; padding-bottom: 44px; }
.hp-hero-copy { max-width: 560px; }
.hp-hero .hp-title { color: #f5f0e8; text-shadow: 0 2px 24px rgba(0,0,0,.45); }
.hp-hero .hp-lead { color: #e4ddd1; text-shadow: 0 1px 12px rgba(0,0,0,.5); }
.hp-hero .hp-cta .btn.hp-ghost { color: #f5f0e8; border-color: rgba(245,240,232,.7); background: rgba(18,15,12,.25); }
@media (min-width: 900px) {
  .hp-hero { min-height: min(84vh, 760px); }
  .hp-hero::after { background: linear-gradient(to right, rgba(18,15,12,.92) 0%, rgba(18,15,12,.62) 40%, rgba(18,15,12,.08) 75%); }
  .hp-hero .hp-wrap { padding-bottom: 90px; }
}
@media (max-width: 699px) {
  /* the image sets the height; a dark band above it (--hero-extra) holds the text, and the photo fades into it.
     If your image has the logo/cart baked into its top edge, set --hero-crop to that height (about 11vw). */
  .hp-hero { --hero-crop: 0px; --hero-extra: 22vw; display: block; min-height: 0; padding: 0; background: var(--ink); }
  .hp-hero::after { display: none; }
  .hp-hero-bg { position: relative; inset: auto; z-index: 0; overflow: hidden; margin-top: var(--hero-extra); }
  .hp-hero-bg img { display: block; width: 100%; height: auto; margin-top: calc(var(--hero-crop) * -1); }
  .hp-hero-bg::after { content: ""; position: absolute; inset: 0; pointer-events: none;
    background: linear-gradient(to bottom, var(--ink) 0, rgba(33,30,26,.72) 12vw, rgba(33,30,26,0) 34vw); }
  .hp-hero .hp-wrap { position: absolute; top: 0; left: 0; right: 0; z-index: 1; padding: 5vw 18px 0; text-align: center; }
  .hp-hero-copy { margin: 0 auto; max-width: none; }
  .hp-eyebrow { justify-content: center; gap: 2.6vw; font-size: max(10.5px, 2.8vw); letter-spacing: 0.2em; margin: 0 0 1.6vw; }
  .hp-eyebrow::before, .hp-eyebrow::after { content: ""; flex: 1 1 0; max-width: 20vw; height: 1px; background: var(--gold); }
  .hp-hero .hp-title { font-size: 14vw; line-height: 0.9; margin: 0 0 2.6vw; white-space: nowrap; }
  .hp-hero .hp-lead { font-size: max(12.5px, 3.3vw); line-height: 1.45; max-width: 66vw; margin: 0 auto 3.4vw; letter-spacing: 0.02em; }
  .hp-hero .hp-cta { flex-direction: column; align-items: center; gap: 2vw; }
  .hp-hero .hp-cta .btn { width: 56vw; min-width: 0; padding: 0; height: max(38px, 10vw); line-height: max(38px, 10vw);
    font-size: max(12px, 3.2vw); text-align: center; }
}

/* ticker */
.hp-marquee { border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); overflow: hidden; background: var(--ink-raised); }
.hp-marquee-track { display: flex; width: max-content; animation: hp-scroll 32s linear infinite; }
.hp-marquee-set { display: flex; align-items: center; flex-shrink: 0; }
.hp-marquee span {
  font-family: "Big Shoulders Display", sans-serif; font-weight: 700; font-size: 18px;
  text-transform: uppercase; letter-spacing: 0.14em; padding: 14px 0; white-space: nowrap; color: var(--paper);
}
.hp-marquee i { color: var(--gold); font-style: normal; padding: 0 22px; }
@keyframes hp-scroll { to { transform: translateX(-50%); } }

/* sections */
.hp-section { padding: 56px 0 0; }
.hp-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; margin-bottom: 22px; }
.hp-kicker { font-size: 11.5px; letter-spacing: 0.16em; text-transform: uppercase; color: var(--gold); margin: 0 0 8px; }
.hp-h2 { font-size: 38px; margin: 0; color: var(--paper); }
.hp-more { color: var(--paper-dim); font-size: 13px; text-decoration: underline; white-space: nowrap; padding-bottom: 4px; }
.hp-more:hover { color: var(--gold); }

.hp-cats {
  display: flex; gap: 12px; overflow-x: auto; scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch; scrollbar-width: none;
  margin: 0 -18px; padding: 0 18px 4px; scroll-padding-left: 18px;
}
.hp-cats::-webkit-scrollbar { display: none; }
.hp-cats .hp-cat { flex: 0 0 62%; max-width: 240px; scroll-snap-align: start; }
.hp-head-right { display: flex; align-items: center; gap: 16px; }
.hp-arrows { display: none; gap: 8px; }
.hp-arrow {
  width: 38px; height: 38px; border: 1px solid var(--line); background: transparent;
  color: var(--paper); border-radius: 50%; font-size: 20px; line-height: 1; cursor: pointer; padding: 0;
}
.hp-arrow:hover { border-color: var(--gold); color: var(--gold); }
.hp-cat { display: block; background: var(--ink-raised); border: 1px solid var(--line); transition: border-color 0.2s ease; }
.hp-cat:hover { border-color: var(--gold); }
.hp-cat-img { aspect-ratio: 4/5; background: rgba(128, 128, 128, 0.10); overflow: hidden; }
.hp-cat-img img { width: 100%; height: 100%; object-fit: contain; display: block; transition: transform 0.4s ease; }
.hp-cat:hover .hp-cat-img img { transform: scale(1.04); }
.hp-cat-img.empty {
  background-image: repeating-linear-gradient(90deg, var(--line) 0px, var(--line) 1px, transparent 1px, transparent 14px);
}
.hp-cat-label {
  display: flex; justify-content: space-between; align-items: center; padding: 12px 14px;
  font-family: "Big Shoulders Display", sans-serif; font-weight: 700; font-size: 20px;
  letter-spacing: 0.04em; text-transform: uppercase; color: var(--paper);
}
.hp-cat-label span:last-child { color: var(--gold); }

.hp-products { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.hp-card { display: block; }
.hp-card-img { aspect-ratio: 4/5; background: rgba(128, 128, 128, 0.10); border: 1px solid var(--line); overflow: hidden; }
.hp-card-img img { width: 100%; height: 100%; object-fit: contain; display: block; transition: transform 0.4s ease; }
.hp-card:hover .hp-card-img img { transform: scale(1.04); }
.hp-card-name { font-size: 13.5px; margin: 10px 0 2px; color: var(--paper); }
.hp-card-price { font-size: 13px; color: var(--gold); font-weight: 600; margin: 0; }

/* light band */
.hp-band { background: var(--stone); color: var(--ink-on-stone); margin-top: 64px; padding: 56px 0 60px; }
.hp-band .hp-kicker { color: var(--ink-dim-on-stone); }
.hp-band .hp-h2 { color: var(--ink-on-stone); }
.hp-values { display: grid; gap: 26px; margin-top: 28px; }
.hp-value { border-top: 1px solid var(--stone-line); padding-top: 16px; }
.hp-value-num { font-family: "Big Shoulders Display", sans-serif; font-weight: 700; font-size: 15px; letter-spacing: 0.1em; color: var(--gold-dim); }
.hp-value h3 {
  font-family: "Big Shoulders Display", sans-serif; font-weight: 700; font-size: 26px;
  text-transform: uppercase; letter-spacing: 0.02em; margin: 6px 0 8px; color: var(--ink-on-stone);
}
.hp-value p { margin: 0; color: var(--ink-dim-on-stone); font-size: 14px; line-height: 1.65; }

/* trust strip */
.hp-trust { display: grid; border: 1px solid var(--line); margin-top: 56px; }
.hp-trust > div { padding: 20px 18px; border-bottom: 1px solid var(--line); }
.hp-trust > div:last-child { border-bottom: none; }
.hp-trust strong { display: block; font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--gold); margin-bottom: 6px; }
.hp-trust span { font-size: 13.5px; color: var(--paper-dim); line-height: 1.55; }

/* closing call to action */
.hp-close { position: relative; overflow: hidden; margin: 56px 0 30px; padding: 54px 22px 46px; text-align: center;
  border: 1px solid rgba(199,154,70,.38);
  background: radial-gradient(80% 90% at 50% 0%, rgba(199,154,70,.15) 0%, rgba(199,154,70,0) 65%), var(--ink-raised); }
.hp-close::before { content: "LOOMEX"; position: absolute; left: 50%; bottom: -0.2em; transform: translateX(-50%);
  font-family: "Big Shoulders Display", sans-serif; font-weight: 700; font-size: clamp(110px, 40vw, 320px); line-height: 1;
  letter-spacing: 0.04em; color: transparent; -webkit-text-stroke: 1px rgba(245,240,232,.09);
  white-space: nowrap; pointer-events: none; }
.hp-close > * { position: relative; z-index: 1; }
.hp-close-kicker { display: flex; align-items: center; justify-content: center; gap: 12px; margin: 0 0 16px;
  font-size: 12px; letter-spacing: .2em; text-transform: uppercase; color: var(--gold); }
.hp-close-kicker::before, .hp-close-kicker::after { content: ""; width: 28px; height: 1px; background: var(--gold); }
.hp-close h2 { font-size: clamp(44px, 12.5vw, 92px); line-height: .95; margin: 0 0 16px; color: var(--paper); }
.hp-close h2 em { font-style: normal; color: var(--gold); }
.hp-close p.hp-close-lead { color: var(--paper-dim); font-size: 15px; line-height: 1.6; max-width: 36ch; margin: 0 auto 26px; }
.hp-close-actions { display: flex; flex-direction: column; align-items: center; gap: 10px; }
.hp-close-actions .btn { display: inline-flex; align-items: center; justify-content: center; gap: 10px;
  width: 100%; max-width: 320px; min-width: 0; padding: 15px 24px; text-decoration: none; }
.hp-close-actions .btn svg { width: 18px; height: 18px; flex: 0 0 auto; }
.hp-close-actions .btn.hp-ghost { background: transparent; color: var(--paper); border: 1px solid var(--paper-dim); }
.hp-close-actions .btn.hp-ghost:hover { background: transparent; border-color: var(--gold); color: var(--gold); }

@media (min-width: 900px) {
  .hp-wrap { max-width: var(--max-wide); padding: 0 32px; }
  .hp-lead { font-size: 17px; }
  .hp-section { padding-top: 84px; }
  .hp-h2 { font-size: 50px; }
  .hp-cats { gap: 20px; margin: 0 -32px; padding: 0 32px 4px; scroll-padding-left: 32px; }
  .hp-cats .hp-cat { flex-basis: 260px; }
  .hp-arrows { display: flex; }
  .hp-products { grid-template-columns: repeat(4, 1fr); gap: 20px; }
  .hp-band { margin-top: 90px; padding: 80px 0 84px; }
  .hp-values { grid-template-columns: repeat(3, 1fr); gap: 44px; }
  .hp-trust { grid-template-columns: repeat(3, 1fr); margin-top: 80px; }
  .hp-trust > div { border-bottom: none; border-right: 1px solid var(--line); padding: 26px 24px; }
  .hp-trust > div:last-child { border-right: none; }
  .hp-close { margin-top: 80px; padding: 88px 40px 76px; }
  .hp-close-actions { flex-direction: row; justify-content: center; gap: 14px; }
  .hp-close-actions .btn { width: auto; max-width: none; min-width: 230px; }
}
@media (prefers-reduced-motion: reduce) {
  .hp-rise, .hp-marquee-track { animation: none; }
}

/* ---- Shop by category: grid with overlay labels ---- */
.hp-cats {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;
  overflow: visible; margin: 0; padding: 0; scroll-snap-type: none;
}
.hp-cats .hp-cat {
  position: relative; flex: none; max-width: none; overflow: hidden;
  border: 1px solid var(--line);
  background:
    radial-gradient(120% 90% at 50% 28%, rgba(199, 154, 70, 0.16) 0%, rgba(199, 154, 70, 0) 62%),
    var(--ink-raised);
  transition: border-color 0.25s ease, transform 0.25s ease;
}
.hp-cats .hp-cat:hover { border-color: var(--gold); transform: translateY(-3px); }
.hp-cat-img { aspect-ratio: 4/5; background: none; padding: 16px 16px 64px; box-sizing: border-box; }
.hp-cat-img img { object-fit: contain; filter: drop-shadow(0 16px 18px rgba(0, 0, 0, 0.4)); }
.hp-cat-img.empty { background-image: none; }
.hp-cat-label {
  position: absolute; left: 0; right: 0; bottom: 0; padding: 18px 14px 14px;
  background: linear-gradient(to top, rgba(18, 15, 12, 0.95) 30%, rgba(18, 15, 12, 0));
  font-size: 19px; letter-spacing: 0.06em;
}
.hp-cat-label span:last-child {
  width: 30px; height: 30px; border: 1px solid var(--gold); border-radius: 50%;
  display: flex; align-items: center; justify-content: center; font-size: 14px;
  transition: background 0.2s ease, color 0.2s ease;
}
.hp-cat:hover .hp-cat-label span:last-child { background: var(--gold); color: var(--ink); }
.hp-arrows { display: none !important; }
@media (min-width: 900px) {
  .hp-cats { grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 0; padding: 0; }
  .hp-cat-label { font-size: 24px; padding: 22px 20px 18px; }
}

/* ---- Trust strip ---- */
.hp-trust { display: grid; gap: 0; margin-top: 56px; border: none;
  border-top: 1px solid rgba(199,154,70,.45); border-bottom: 1px solid rgba(199,154,70,.45); }
.hp-trust > div,
.hp-trust > div:last-child {
  display: grid; grid-template-columns: 28px 1fr; column-gap: 14px; align-items: center;
  padding: 16px 4px; border: none; border-bottom: 1px solid var(--line); background: none; text-align: left;
}
.hp-trust > div:last-child { border-bottom: none; }
.hp-trust-icon { grid-row: 1 / span 2; width: 28px; height: 28px; color: var(--gold);
  display: flex; align-items: center; justify-content: center; }
.hp-trust-icon svg { width: 26px; height: 26px; }
.hp-trust strong { display: block; margin: 0 0 2px; font-family: "Big Shoulders Display", sans-serif; font-weight: 700;
  font-size: 19px; letter-spacing: .06em; text-transform: uppercase; color: var(--paper); }
.hp-trust p { margin: 0; font-size: 13px; line-height: 1.5; color: var(--paper-dim); }
@media (min-width: 900px) {
  .hp-trust { grid-template-columns: repeat(3, 1fr); margin-top: 80px; }
  .hp-trust > div,
  .hp-trust > div:last-child { padding: 28px 30px; border-bottom: none; border-right: 1px solid var(--line); column-gap: 16px; }
  .hp-trust > div:last-child { border-right: none; }
  .hp-trust-icon { width: 32px; height: 32px; }
  .hp-trust-icon svg { width: 30px; height: 30px; }
  .hp-trust strong { font-size: 22px; }
  .hp-trust p { font-size: 13.5px; }
}

/* ---- The Sets Edit ---- */
.hp-sets { margin-top: 64px; padding: 44px 0 48px; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line);
  background: radial-gradient(90% 120% at 15% 50%, rgba(199,154,70,.10) 0%, rgba(199,154,70,0) 60%), var(--ink-raised); }
.hp-sets-grid { display: grid; gap: 30px; align-items: center; }
.hp-sets-copy { text-align: center; }
.hp-sets-kicker { display: flex; align-items: center; justify-content: center; gap: 12px; margin: 0 0 12px;
  font-size: 12px; letter-spacing: .2em; text-transform: uppercase; color: var(--gold); }
.hp-sets-kicker::before, .hp-sets-kicker::after { content: ""; width: 28px; height: 1px; background: var(--gold); }
.hp-sets-title { font-size: clamp(46px, 13vw, 84px); line-height: .95; margin: 0 0 12px; color: var(--paper); }
.hp-sets-title em { font-style: normal; color: var(--gold); }
.hp-sets-lead { color: var(--paper-dim); font-size: 15px; margin: 0 0 22px; }
.hp-sets-copy .btn { display: inline-block; width: auto; min-width: 0; padding: 14px 26px; text-decoration: none;
  background: transparent; color: var(--paper); border: 1px solid var(--gold); }
.hp-sets-copy .btn:hover { background: var(--gold); color: var(--ink); }
.hp-sets-cols { display: grid; grid-template-columns: repeat(2, 1fr); }
.hp-set { display: flex; flex-direction: column; align-items: center; padding: 16px 10px;
  border-left: 1px solid var(--line); border-top: 1px solid var(--line); }
.hp-set:nth-child(odd) { border-left: none; }
.hp-set:nth-child(-n+2) { border-top: none; }
.hp-set-img { display: block; width: 100%; max-width: 160px; aspect-ratio: 4/5; }
.hp-set-img img { width: 100%; height: 100%; object-fit: contain; display: block;
  filter: drop-shadow(0 12px 14px rgba(0,0,0,.4)); transition: transform .3s ease; }
.hp-set-img:hover img { transform: scale(1.05); }
.hp-set-name { margin-top: 10px; font-size: 20px; letter-spacing: .08em; text-transform: uppercase; color: var(--paper); }
.hp-set-name:hover { color: var(--gold); }
@media (min-width: 900px) {
  .hp-sets { padding: 64px 0; margin-top: 90px; }
  .hp-sets-grid { grid-template-columns: .85fr 1.7fr; gap: 56px; }
  .hp-sets-copy { text-align: left; }
  .hp-sets-kicker { justify-content: flex-start; }
  .hp-sets-kicker::after { display: none; }
  .hp-sets-cols { grid-template-columns: none; grid-auto-flow: column; grid-auto-columns: 1fr; }
  .hp-set, .hp-set:nth-child(-n+2) { border-top: none; border-left: 1px solid var(--line); padding: 0 16px; }
  .hp-set:first-child { border-left: none; }
  .hp-set-img { max-width: 190px; }
  .hp-set-name { font-size: 22px; }
}
/* sets heading: elegant serif, two lines */
.hp-sets .hp-sets-title {
  font-family: "Playfair Display", Georgia, "Times New Roman", serif; font-weight: 600; text-transform: none;
  letter-spacing: -0.01em; line-height: 1.12; margin: 0 0 20px;
  font-size: clamp(30px, 8.6vw, 46px);
}
.hp-sets .hp-sets-title em { font-style: italic; font-weight: 500; color: var(--gold); }
@media (min-width: 900px) {
  .hp-sets .hp-sets-title { font-size: clamp(36px, 3.4vw, 52px); }
}

/* category tiles: the photo box is sized explicitly so it sits ABOVE the label strip,
   and the garment is centered inside that box (see hpPlace in HOME_JS) */
.hp-cats .hp-cat-img { position: relative !important; padding: 0 !important; }
.hp-cats .hp-cat-img img {
  position: absolute !important; left: 16px !important; top: 16px !important;
  width: calc(100% - 32px) !important; height: calc(100% - 84px) !important;
  object-fit: contain !important; object-position: center !important;
}
@media (min-width: 900px) {
  .hp-cats .hp-cat-img img { height: calc(100% - 100px) !important; }
}

/* ---- Why Loomex (playful band) ---- */
.hp-why { position: relative; margin-top: 0; padding: 64px 0 72px; overflow: hidden;
  background-color: var(--stone); color: var(--ink-on-stone);
  background-image: radial-gradient(rgba(18,15,12,.09) 1.3px, transparent 1.4px); background-size: 20px 20px; }
.hp-why .hp-wrap { position: relative; }
.hp-why-kicker { margin: 0 0 10px; font-size: 12px; letter-spacing: .2em; text-transform: uppercase; color: var(--gold-dim); text-align: center; }
.hp-why-title { margin: 0 0 12px; text-align: center; font-size: clamp(46px, 14vw, 92px); line-height: .95; color: var(--ink-on-stone); }
.hp-why-title em { font-style: normal; color: var(--gold-dim); text-decoration: underline wavy var(--gold);
  text-decoration-thickness: 3px; text-underline-offset: 7px; text-decoration-skip-ink: none; }
.hp-why-lead { margin: 0 auto 38px; max-width: 34ch; text-align: center; font-size: 15.5px; line-height: 1.55; color: var(--ink-dim-on-stone); }
.hp-why-grid { display: grid; gap: 22px; grid-template-columns: 1fr; }
.hp-why-card { position: relative; padding: 24px 22px 22px; background: var(--ink); color: var(--paper);
  border: 2px solid var(--ink); box-shadow: 7px 7px 0 var(--gold);
  transition: rotate .25s ease, translate .25s ease, box-shadow .25s ease; }
.hp-why-card.c1 { rotate: -1.6deg; } .hp-why-card.c2 { rotate: 1.3deg; }
.hp-why-card.c3 { rotate: -1deg; }   .hp-why-card.c4 { rotate: 1.8deg; }
.hp-why-card:hover { rotate: 0deg; translate: 0 -6px; box-shadow: 11px 11px 0 var(--gold); }
.hp-why-num { position: absolute; top: -16px; right: 14px; display: flex; align-items: center; justify-content: center;
  width: 42px; height: 42px; border-radius: 50%; background: var(--gold); color: var(--ink);
  font-family: "Big Shoulders Display", sans-serif; font-weight: 700; font-size: 20px; rotate: 8deg; }
.hp-why-ico { width: 44px; height: 44px; margin-bottom: 14px; color: var(--gold); }
.hp-why-ico svg { width: 100%; height: 100%; display: block; }
.hp-why-card h3 { margin: 0 0 8px; font-family: "Big Shoulders Display", sans-serif; font-weight: 700; font-size: 27px;
  line-height: 1; letter-spacing: .02em; text-transform: uppercase; color: var(--paper); }
.hp-why-card p { margin: 0; font-size: 14px; line-height: 1.6; color: var(--paper-dim); }
.hp-why-sticker { display: none; }
@keyframes hp-wobble { from { rotate: 9deg; } to { rotate: 17deg; } }
@media (min-width: 560px) { .hp-why-grid { grid-template-columns: 1fr 1fr; gap: 28px; } }
@media (min-width: 900px) {
  .hp-why { padding: 96px 0 104px; }
  .hp-why-grid { grid-template-columns: repeat(4, 1fr); gap: 26px; }
  .hp-why-lead { font-size: 17px; margin-bottom: 52px; }
  .hp-why-sticker { display: flex; align-items: center; justify-content: center; text-align: center; position: absolute;
    top: -8px; right: 8px; width: 112px; height: 112px; border-radius: 50%; background: var(--gold); color: var(--ink);
    border: 2px solid var(--ink); font-family: "Big Shoulders Display", sans-serif; font-weight: 700; font-size: 20px;
    line-height: 1; letter-spacing: .04em; text-transform: uppercase; padding: 10px; box-sizing: border-box;
    animation: hp-wobble 3.6s ease-in-out infinite alternate; }
}
@media (prefers-reduced-motion: reduce) { .hp-why-sticker { animation: none; } .hp-why-card { transition: none; } }
</style>
"""
WHY_HTML = """
  <section class="hp-why" id="why">
    <div class="hp-wrap">
      <div class="hp-why-sticker">No dress code</div>
      <p class="hp-why-kicker">Why Loomex</p>
      <h2 class="hp-why-title display">Why <em>Loomex?</em></h2>
      <p class="hp-why-lead">Because &ldquo;basically&rdquo; should never mean boring.</p>
      <div class="hp-why-grid">
        <article class="hp-why-card c1">
          <span class="hp-why-num">01</span>
          <div class="hp-why-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3 3 8l9 5 9-5-9-5z"></path><path d="m3 13 9 5 9-5"></path><path d="m3 17.5 9 5 9-5"></path></svg></div>
          <h3>Thick where it counts</h3>
          <p>Heavyweight cotton that feels like a hug and keeps its shape.</p>
        </article>
        <article class="hp-why-card c2">
          <span class="hp-why-num">02</span>
          <div class="hp-why-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M16 3h5v5"></path><path d="M4 20 21 3"></path><path d="M21 16v5h-5"></path><path d="m15 15 6 6"></path><path d="m4 4 5 5"></path></svg></div>
          <h3>Mix it. Match it.</h3>
          <p>Wear one piece solo or grab the matching set. Both look like you tried.</p>
        </article>
        <article class="hp-why-card c3">
          <span class="hp-why-num">03</span>
          <div class="hp-why-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="6" width="20" height="12" rx="2"></rect><circle cx="12" cy="12" r="2.5"></circle><path d="M6 12h.01M18 12h.01"></path></svg></div>
          <h3>Pay at the door</h3>
          <p>Cash on delivery. See it, feel it, then pay for it.</p>
        </article>
        <article class="hp-why-card c4">
          <span class="hp-why-num">04</span>
          <div class="hp-why-ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7"></path><path d="M3 4v5h5"></path></svg></div>
          <h3>Change your mind</h3>
          <p>You get 7 days after delivery to start a return. No drama.</p>
        </article>
      </div>
    </div>
  </section>
"""
HOME_JS = """
<script>
function hpScroll(dir) {
  var row = document.getElementById('hp-cats');
  if (!row) return;
  var tile = row.querySelector('.hp-cat');
  var step = (tile ? tile.getBoundingClientRect().width : 260) + 20;
  row.scrollBy({ left: dir * step * 2, behavior: 'smooth' });
}

/* ---- Center each category photo in its tile ----
   The six photos have different amounts of empty space around the garment, so
   the garments sit at different heights. For each photo we find where the
   garment really is (ignoring transparent / plain background) and shift the
   photo so the garment's middle lands on the middle of the tile.
   The photo that is measured is the very same <img> on the page (loaded with
   crossorigin so the browser lets us read its pixels). If anything goes wrong
   the photo is simply left where it is and a warning is printed in the console. */
function hpPlace(img) {
  var fx = parseFloat(img.dataset.fx), fy = parseFloat(img.dataset.fy);
  var nw = img.naturalWidth, nh = img.naturalHeight;
  if (isNaN(fx) || isNaN(fy) || !nw || !nh) return;
  var bw = img.clientWidth, bh = img.clientHeight;
  if (!bw || !bh) return;
  var s = Math.min(bw / nw, bh / nh);
  var dx = (0.5 - fx) * nw * s, dy = (0.5 - fy) * nh * s;
  img.style.translate = dx.toFixed(1) + 'px ' + dy.toFixed(1) + 'px';
}

function hpMeasure(img) {
  if (img.dataset.fx !== undefined) { hpPlace(img); return; }
  var nw = img.naturalWidth, nh = img.naturalHeight;
  if (!nw || !nh) return;
  try {
    var sc = Math.min(1, 240 / Math.max(nw, nh));
    var w = Math.max(1, Math.round(nw * sc)), h = Math.max(1, Math.round(nh * sc));
    var c = document.createElement('canvas');
    c.width = w; c.height = h;
    var ctx = c.getContext('2d', { willReadFrequently: true });
    ctx.drawImage(img, 0, 0, w, h);
    var d = ctx.getImageData(0, 0, w, h).data;
    var br = d[0], bg = d[1], bb = d[2], opaqueBg = d[3] > 240;
    var colCount = new Uint16Array(w), rowCount = new Uint16Array(h);
    for (var y = 0; y < h; y++) {
      for (var x = 0; x < w; x++) {
        var i = (y * w + x) * 4, on;
        if (opaqueBg) on = Math.abs(d[i] - br) + Math.abs(d[i + 1] - bg) + Math.abs(d[i + 2] - bb) > 60;
        else on = d[i + 3] > 40;
        if (on) { colCount[x]++; rowCount[y]++; }
      }
    }
    function span(a) {
      var mx = 0, k, lo = -1, hi = -1;
      for (k = 0; k < a.length; k++) if (a[k] > mx) mx = a[k];
      var t = Math.max(2, mx * 0.04);
      for (k = 0; k < a.length; k++) if (a[k] >= t) { if (lo < 0) lo = k; hi = k; }
      return [lo, hi];
    }
    var xs = span(colCount), ys = span(rowCount);
    if (xs[0] < 0 || ys[0] < 0) { console.warn('[Loomex] no garment found in', img.alt); return; }
    img.dataset.fx = ((xs[0] + xs[1] + 1) / 2) / w;
    img.dataset.fy = ((ys[0] + ys[1] + 1) / 2) / h;
    console.log('[Loomex] centered', img.alt, img.dataset.fx, img.dataset.fy);
    hpPlace(img);
  } catch (e) {
    console.warn('[Loomex] could not center', img.alt, '-', e && e.message);
  }
}

function hpInit() {
  document.querySelectorAll('.hp-cat-img img').forEach(function (img) {
    if (img.complete && img.naturalWidth) hpMeasure(img);
    else img.addEventListener('load', function () { hpMeasure(img); }, { once: true });
  });
}
hpInit();
window.addEventListener('resize', function () {
  document.querySelectorAll('.hp-cat-img img').forEach(hpPlace);
});
</script>
"""
def _home_image(p: dict) -> str:
    """First photo of the product: first color's first image, else the main image."""
    color_images = p.get("color_images") or {}
    for c in p.get("colors") or []:
        v = color_images.get(c)
        if isinstance(v, list) and v:
            return v[0]
        if isinstance(v, str) and v:
            return v
    return p.get("image_url") or ""


# Which colorway each set shows on the homepage "sets" section (key = the products' set_name,
# lowercase). The hoodie/top and the pants both show this colorway, so they always match.
# A set that isn't listed here, or a product that doesn't have that colorway, falls back to
# its first color. Colorway names must match the product's color names exactly.
HOME_SET_COLORS = {
    "slash": "Olive / Beige",
}


def _home_image_for(p: dict, color: str | None = None) -> str:
    """Front photo of `color` for this product; first-color photo if it has no such color."""
    if color:
        v = (p.get("color_images") or {}).get(color)
        if isinstance(v, list) and v:
            return v[0]
        if isinstance(v, str) and v:
            return v
    return _home_image(p)


# If the image host ever refuses cross-origin reads, the tile photo would fail to load.
# This puts back the plain photo (no centering) instead of leaving an empty tile.
_CAT_IMG_ONERROR = (
    "if(!this.dataset.plain){this.dataset.plain=1;this.removeAttribute('crossorigin');"
    "this.src=this.dataset.src;}"
)


def landing_page(categories: list, cart_count: int = 0, subcategories: dict | None = None,
                 products: list | None = None) -> str:
    products = products or []
    with_img = [(p, _home_image(p)) for p in products if _home_image(p)]
    real = [(p, u) for p, u in with_img if "placehold.co" not in u]
    pool = real or with_img  # prefer real photos, placeholders only if that's all there is
    # hero banner
    HERO_BANNER = "https://djeqpdphxcjceognytrv.supabase.co/storage/v1/object/public/product_images/hero%20section/banner%20img.jpeg"
    HERO_BANNER_MOBILE = "https://djeqpdphxcjceognytrv.supabase.co/storage/v1/object/public/product_images/hero%20section/banner%20image%20portrait.jpeg"

    # ticker
    words = ["MADE TO STAND OUT", "SIMPLICITY WITH PURPOSE", "BUILT TO LAST", "QUALITY WITHOUT COMPROMISE"] * 2
    ticker_set = "".join(f"<span>{w}</span><i>&#10022;</i>" for w in words)
    ticker = (
        f'<div class="hp-marquee" aria-hidden="true"><div class="hp-marquee-track">'
        f'<div class="hp-marquee-set">{ticker_set}</div><div class="hp-marquee-set">{ticker_set}</div>'
        f'</div></div>'
    )

    # category tiles
    tiles = []
    for c in categories:
        label = c.replace("-", " ").title()
        img = next((u for p, u in pool if p.get("category") == c), "")
        if img:
            # "c=1" gives these tile photos their own cache entry, so the browser never
            # re-uses a copy that was cached without cross-origin permission.
            img_src = img + ("&" if "?" in img else "?") + "c=1"
            media = (
                f'<div class="hp-cat-img"><img src="{escape(img_src)}" data-src="{escape(img)}" '
                f'crossorigin="anonymous" onerror="{_CAT_IMG_ONERROR}" '
                f'alt="{escape(label)}" loading="lazy"></div>'
            )
        else:
            media = '<div class="hp-cat-img empty"></div>'
        tiles.append(
            f'<a href="/shop?category={escape(c)}" class="hp-cat">{media}'
            f'<div class="hp-cat-label"><span>{escape(label)}</span><span>&rarr;</span></div></a>'
        )
    cats_html = f'<div class="hp-cats" id="hp-cats">{"".join(tiles)}</div>'

    # shop the sets
    sets = {}
    for p in products:
        if p.get("set_name"):
            sets.setdefault(p["set_name"], []).append(p)
    set_cols = []
    for set_key, items in sets.items():
        set_color = HOME_SET_COLORS.get(str(set_key).lower())
        bottoms = [p for p in items if p.get("category") == "pants"]
        tops = [p for p in items if p.get("category") != "pants"]
        if not bottoms or not tops:
            continue
        top, bottom = tops[0], bottoms[0]
        t_img, b_img = _home_image_for(top, set_color), _home_image_for(bottom, set_color)
        if not t_img or not b_img:
            continue
        title = bottom["name"].removesuffix(" Pants")
        set_cols.append(
            f'<div class="hp-set">'
            f'<a href="/product/{escape(top["slug"])}" class="hp-set-img"><img src="{escape(t_img)}" alt="{escape(top["name"])}" loading="lazy"></a>'
            f'<a href="/product/{escape(bottom["slug"])}" class="hp-set-img"><img src="{escape(b_img)}" alt="{escape(bottom["name"])}" loading="lazy"></a>'
            f'<a href="/product/{escape(top["slug"])}" class="hp-set-name display">{escape(title)}</a>'
            f'</div>'
        )
    sets_html = ""
    if set_cols:
        sets_html = f"""
  <section class="hp-sets" id="sets">
    <div class="hp-wrap hp-sets-grid">
      <div class="hp-sets-copy">
        <p class="hp-sets-kicker">The Loomex collection</p>
        <h2 class="hp-sets-title display">Wear one <em>or</em><br>wear the set.</h2>
        
        <a href="/shop" class="btn">Shop the sets &rarr;</a>
      </div>
      <div class="hp-sets-cols">{"".join(set_cols)}</div>
    </div>
  </section>"""

    body = HOME_CSS + f"""
<div class="hp">
   <section class="hp-hero">
    <div class="hp-hero-bg"><picture>
      <source media="(max-width: 699px)" srcset="{escape(HERO_BANNER_MOBILE)}">
      <img src="{escape(HERO_BANNER)}" alt="Loomex collection" fetchpriority="high">
    </picture></div>
    <div class="hp-wrap">
      <div class="hp-hero-copy">
        <p class="hp-eyebrow hp-rise">Built around your everyday.</p>
        <h1 class="hp-title display hp-rise d1">BASICALLY
<br><em>UNBASIC</em></h1>
       
        <div class="hp-cta hp-rise d3">
          <a href="/shop" class="btn">Shop our collection &rarr;</a>
          <a href="#categories" class="btn hp-ghost">Explore categories</a>
        </div>
      </div>
    </div>
  </section>

  {ticker}

  <section class="hp-section" id="categories">
    <div class="hp-wrap">
      <div class="hp-head">
        <div><h2 class="hp-h2 display">Shop by category</h2></div>
        <div class="hp-head-right">
          <div class="hp-arrows">
            <button type="button" class="hp-arrow" onclick="hpScroll(-1)" aria-label="Previous categories">&#8249;</button>
            <button type="button" class="hp-arrow" onclick="hpScroll(1)" aria-label="Next categories">&#8250;</button>
          </div>
          <a href="/shop" class="hp-more">Shop all</a>
        </div>
      </div>
      {cats_html}
    </div>
  </section>

  {sets_html}

  {WHY_HTML}

  <div class="hp-wrap">
    <section class="hp-close">
      <p class="hp-close-kicker">Loomex</p>
      <h2 class="display">Not dressed up.<br><em>Never dressed down.</em></h2>
      <p class="hp-close-lead">Effortless fits. Matching sets. Everyday comfort, without compromise.</p>

      <div class="hp-close-actions">
        <a href="/shop" class="btn">Shop the collection &rarr;</a>
        <a href="https://www.instagram.com/loomex_clothing" target="_blank" rel="noopener" class="btn hp-ghost"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><circle cx="12" cy="12" r="4"></circle><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line></svg>@loomex_clothing</a>
      </div>
    </section>
  </div>
</div>
"""
    body += HOME_JS
    return layout("Loomex — Homewear", body, categories, cart_count,
                  subcategories=subcategories, path="/")


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
.subtabs{gap:0;padding:14px 18px 8px;border-bottom:1px solid var(--line);}
.subtab{flex:0 0 auto;margin:0;padding:6px 16px;border:none;border-radius:0;background:transparent;
  font-family:"Big Shoulders Display",sans-serif;font-size:19px;font-weight:700;
  text-transform:uppercase;letter-spacing:.06em;color:var(--paper-dim);}
.subtab + .subtab{border-left:1px solid var(--line);}
.subtab.active{color:var(--gold);background:none;box-shadow:inset 0 -2px 0 var(--gold);}
@media (min-width:560px){.subtabs{justify-content:center;}}
@media (min-width:900px){.subtabs{padding-left:32px;padding-right:32px;}}
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
                active_category, q_suffix, " active" if not active_subcategory else "", escape(cat_label)
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
  <input type="search" name="q" id="shop-search" value="{escape(search)}" placeholder="Search products..." aria-label="Search products" autocomplete="off">
  <button type="submit" class="search-btn" aria-label="Search">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"></circle><path d="m21 21-4.3-4.3"></path></svg>
  </button>
  <a href="/shop{('?category=' + escape(active_category)) if active_category else ''}" class="search-clear" id="shop-clear"{'' if search else ' hidden'}>Clear</a>
</form>
"""

    if products:
        card_blocks = []
        for p in products:
            color_images = p.get("color_images") or {}
            colors = p.get("colors") or []
            fallback_img = p.get("image_url") or ""
            card_sold = {str(x).strip().lower() for x in (p.get("sold_out_colors") or [])}

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
                                                f'<button type="button" class="swatch{" active" if ci == 0 else ""}'
                        f'{" soldout" if c.lower() in card_sold else ""}" '
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

            gone = _fully_sold_out(p)
            if gone:
                media = media.replace('<div class="card-media">', '<div class="card-media"><span class="card-ribbon">Sold out</span>', 1)
            card_blocks.append(
                f"""<a href="/product/{escape(p['slug'])}" class="card{' is-sold' if gone else ''}">
                      {media}
                      <div class="card-body">
                      {_promo_badge(p)}<p class="card-name">{escape(p['name'])}</p>
                        <p class="card-price">{p['price']:.0f} EGP</p>
                        {swatch_row}
                        {'<span class="card-soldbtn">Sold out</span>' if gone else ''}
                      </div>
                    </a>"""
            )
        grid = f'{SOLD_CSS}<div class="grid">{"".join(card_blocks)}</div>'
    elif search:
        grid = f'<div class="empty">No products match "{escape(search)}".</div>'
    else:
        grid = '<div class="empty">No products in this category yet.</div>'

    body = f"""
{SHOP_CSS}
{search_form}
<div id="shop-filters"><nav class="chips">{''.join(chips)}</nav>
{sub_chips_html}</div>
<div id="shop-results">{grid}</div>
<script src="/static/shop-search.js?v=2" defer></script>
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
.pg-label{position:absolute;left:8px;top:8px;z-index:2;padding:4px 10px;border-radius:999px;
  background:rgba(0,0,0,.55);color:#fff;font-size:11px;font-weight:600;letter-spacing:.06em;
  text-transform:uppercase;pointer-events:none;}
.pg-label:empty{display:none;}
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
  var lab = g.querySelector('.pg-label');
  if (lab) lab.textContent = imgs[idx].dataset.label || '';
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
SOLD_OUT_CSS = """
<style>
.pill-out{position:relative;overflow:hidden;opacity:.5;color:var(--paper-dim);cursor:not-allowed;}
.pill-out input{cursor:not-allowed;}
.pill-out::after{content:"";position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(to top right,transparent calc(50% - 1px),var(--gold,#c79a46) calc(50% - 1px),var(--gold,#c79a46) calc(50% + 1px),transparent calc(50% + 1px));}
.pill-out.viewing{opacity:.85;border-color:var(--gold,#c79a46);color:var(--gold,#c79a46);}
.btn-soldout{background:transparent;color:var(--paper-dim);border:1px solid var(--line);cursor:not-allowed;}
.so-box{display:flex;flex-direction:column;align-items:flex-start;gap:8px;margin:0 0 16px;}
.so-badge{display:inline-flex;align-items:center;flex-wrap:wrap;gap:4px 10px;padding:8px 16px;border:1px solid rgba(224,88,74,.75);
  border-radius:999px;background:rgba(224,88,74,.12);font:600 11.5px Inter,sans-serif;letter-spacing:.1em;text-transform:uppercase;color:#f0aaa1;}
.so-badge .so-dot{width:8px;height:8px;border-radius:50%;background:#e0584a;flex:0 0 auto;}
.so-badge .so-what{color:#fff;letter-spacing:.06em;text-transform:none;font-weight:500;}
</style>
"""
def _fully_sold_out(p: dict) -> bool:
    """True when nothing can be bought: product off, every size sold out, or every color sold out."""
    if not p.get("in_stock", True):
        return True
    sizes = p.get("sizes") or []
    sold_s = {str(x).strip().lower() for x in (p.get("sold_out_sizes") or [])}
    if sizes and all(x.lower() in sold_s for x in sizes):
        return True
    colors = p.get("colors") or []
    sold_c = {str(x).strip().lower() for x in (p.get("sold_out_colors") or [])}
    return bool(colors) and all(x.lower() in sold_c for x in colors)


SOLD_CSS = ("<style>"
            ".card.is-sold .card-media{position:relative;}"
            ".card.is-sold .card-media img{opacity:.45;filter:grayscale(.4);}"
            ".card-ribbon{position:absolute;left:8px;top:8px;z-index:3;padding:5px 12px;border-radius:999px;"
            "background:var(--gold,#c79a46);color:#201c18;font:700 10.5px Inter,sans-serif;letter-spacing:.12em;"
            "text-transform:uppercase;pointer-events:none;}"
            ".card-soldbtn{display:block;margin-top:10px;padding:9px 0;text-align:center;border:1px solid var(--gold,#c79a46);"
            "color:var(--gold,#c79a46);font:600 11.5px Inter,sans-serif;letter-spacing:.12em;text-transform:uppercase;}"
            ".pd-soldtag{display:inline-block;margin:0 0 14px;padding:6px 16px;border:1px solid var(--gold,#c79a46);"
            "border-radius:999px;color:var(--gold,#c79a46);font:700 11.5px Inter,sans-serif;letter-spacing:.14em;text-transform:uppercase;}"
            ".swatch.soldout{opacity:.35;position:relative;}"
            ".swatch.soldout::after{content:'';position:absolute;left:-2px;right:-2px;top:50%;"
            "border-top:2px solid #c0392b;transform:rotate(-45deg);}</style>")


def product_page(p: dict, categories: list, cart_count: int = 0, subcategories: dict | None = None) -> str:
    sizes = p.get("sizes") or []
    sold_out_sizes = {str(x).strip().lower() for x in (p.get("sold_out_sizes") or [])}
    first_size = next((x for x in sizes if x.lower() not in sold_out_sizes), None)
    size_pills = "".join(
        (f'<label class="pill pill-out" title="Sold out"><input type="radio" name="size" value="{escape(x)}" disabled>'
         f'{escape(x)}</label>')
        if x.lower() in sold_out_sizes else
        (f'<label class="pill"><input type="radio" name="size" value="{escape(x)}"'
         f'{" checked" if x == first_size else ""}>{escape(x)}</label>')
        for x in sizes
    )

    # color_images format: {"Black": ["url1", "url2"], "Olive": ["url3"]}
    color_images = p.get("color_images") or {}
    colors = p.get("colors") or []
    sold_colors = {str(c).strip().lower() for c in (p.get("sold_out_colors") or [])}
    first_ok = next((i for i, c in enumerate(colors) if c.lower() not in sold_colors), None)
    all_colors_sold = bool(colors) and first_ok is None
    all_sizes_sold = bool(sizes) and first_size is None
    is_sold_out = (not p.get("in_stock", True)) or all_sizes_sold or all_colors_sold
    add_btn = (
        '<button class="btn btn-soldout" type="button" disabled>Sold out</button>'
        if is_sold_out else '<button class="btn" id="add-btn" data-live="1" type="submit">Add to Cart</button>'
    )

    soldout_tag = '<span class="pd-soldtag">Sold out</span>' if is_sold_out else ""

    if color_images:
        groups = []
        labeled = True

        def _label(n):
            return ("Front", "Back")[n] if labeled and n < 2 else ""

        for ci, c in enumerate(colors):
            urls = color_images.get(c) or [p.get("image_url") or ""]
            imgs = "".join(
                f'<img src="{escape(u)}" alt="{escape(p["name"])} in {escape(c)}" data-label="{_label(n)}"'
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
                f'<div class="pg-view">{imgs}<span class="pg-label">{_label(0)}</span>{arrows}</div>{dots}</div>'
            )
        image_block = f'{GALLERY_CSS}<div class="pg">{"".join(groups)}</div>{GALLERY_JS}'
        color_pills = "".join(
            (f'<label class="pill pill-out" data-color="1" title="Sold out">'
             f'<input type="radio" name="color" value="{escape(c)}" data-sold="1" onchange="pgShowColor({i})">{escape(c)}</label>')
            if c.lower() in sold_colors else
            (f'<label class="pill"><input type="radio" name="color" value="{escape(c)}"'
             f'{" checked" if i == first_ok else ""} onchange="pgShowColor({i})">{escape(c)}</label>')
            for i, c in enumerate(colors)
        )
        if first_ok not in (None, 0):
            image_block += f"<script>pgShowColor({first_ok});</script>"
    else:
        image_block = f'<div class="pd-image"><img src="{escape(p.get("image_url") or "")}" alt="{escape(p["name"])}"></div>'
        color_pills = "".join(
            (f'<label class="pill pill-out" data-color="1"><input type="radio" name="color" value="{escape(c)}" data-sold="1">'
             f'{escape(c)}</label>')
            if c.lower() in sold_colors else
            (f'<label class="pill"><input type="radio" name="color" value="{escape(c)}"'
             f'{" checked" if i == first_ok else ""}>{escape(c)}</label>')
            for i, c in enumerate(colors)
        )

    add_to_cart_js = (
        f"if(window.fbq){{fbq('track','AddToCart',{{content_ids:['{p['slug']}'],content_type:'product',"
        f"value:{p['price']:.2f},currency:'EGP'}});}}"
        f"if(window.ttq){{ttq.track('AddToCart',{{content_id:'{p['slug']}',content_type:'product',"
        f"quantity:1,price:{p['price']:.2f},"
        f"value:{p['price']:.2f},currency:'EGP'}});}}"
    )

    body = f"""
    {SOLD_OUT_CSS}
<div class="pd-layout">
{image_block}
<div class="pd-body">
  <h1 class="pd-name display">{escape(p['name'])}</h1>
  <p class="pd-price">{p['price']:.0f} EGP</p>
    {soldout_tag}
  <p class="pd-desc">{escape(p.get('description') or '')}</p>

  <form action="/cart/add" method="post" onsubmit="{add_to_cart_js}">
    <input type="hidden" name="product" value="{escape(p['slug'])}">

    <span class="field-label">Size</span>
    <div class="pill-row">{size_pills}</div>

    {"<span class='field-label'>Color</span><div class='pill-row'>" + color_pills + "</div>" if color_pills else ""}

   

    {add_btn}
  </form>
  <script>
  (function(){{
    var btn = document.getElementById('add-btn');
    if (!btn || btn.dataset.live !== '1') return;
    var form = btn.form, viewing = false;
    function setSold(on){{
      viewing = on;
      btn.disabled = on;
      btn.type = on ? 'button' : 'submit';
      btn.classList.toggle('btn-soldout', on);
      btn.textContent = on ? 'Sold out' : 'Add to Cart';
    }}
    form.addEventListener('submit', function(e){{ if (viewing) e.preventDefault(); }});
    form.querySelectorAll('input[name=color]').forEach(function(r){{
      r.addEventListener('change', function(){{
        form.querySelectorAll('.pill-out.viewing').forEach(function(l){{ l.classList.remove('viewing'); }});
        var sold = r.dataset.sold === '1';
        if (sold) r.closest('label').classList.add('viewing');
        setSold(sold);
      }});
    }});
  }})();
  </script>
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
              subcategories: dict | None = None, pricing: dict | None = None) -> str:
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

    pricing = pricing or {"discount": 0, "applied": []}
    discount_html = "".join(
        f'<div class="summary-line" style="color:var(--gold);"><span>{escape(a["title"])} ({escape(a["what"])})</span>'
        f'<span>&minus;{a["amount"]:.0f} EGP</span></div>'
        for a in pricing["applied"]
    )
    total = subtotal - pricing["discount"]
    gift_html = (
        '<div style="margin:14px 0;padding:12px 14px;border:1px dashed var(--gold);color:var(--gold);'
        'font-size:13.5px;line-height:1.5;text-align:center;">'
        '&#127873; <strong>Good news!</strong> You\'ll get a free gift with this order.</div>'
        if pricing.get("gifts") else ""
    )
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
           <form action="/cart/update" method="post" class="cd-qty">
        <input type="hidden" name="index" value="{line['index']}">
        <button type="submit" name="qty" value="{line['qty'] - 1}"{' disabled' if line['qty'] <= 1 else ''} aria-label="Decrease quantity">&minus;</button>
        <span>{line['qty']}</span>
        <button type="submit" name="qty" value="{line['qty'] + 1}"{' disabled' if line['qty'] >= 10 else ''} aria-label="Increase quantity">+</button>
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
   <div class="summary-line" style="border-top:1px solid var(--line);margin-top:10px;padding-top:14px;">
    <span>Subtotal</span>
    <span>{subtotal:.0f} EGP</span>
  </div>
  {discount_html}
  {gift_html}
  <div class="summary-line summary-total">
    <span>Total</span>
    <span>{total:.0f} EGP</span>
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
.req { color: var(--gold); font-weight: 700; }
.checkout-required { color: var(--paper-dim); font-size: 12.5px; margin: 0 0 14px; }
.field-error { color: #e5806b; font-size: 12.5px; line-height: 1.4; margin: 6px 0 0; }
.field-error[hidden] { display: none; }
.form-group input.invalid, .form-group select.invalid { border-color: #e5806b; }
.pay-other { color: var(--paper-dim); font-size: 13px; line-height: 1.6; margin: 10px 0 0;
  padding: 12px 14px; border: 1px solid var(--line); background: var(--ink-raised); font-weight: 700; }
.pay-other a { color: var(--gold); text-decoration: underline; }
.btn-ghost { background: transparent; color: var(--paper); border: 1px solid var(--paper-dim); }
.btn-ghost:hover { background: transparent; border-color: var(--gold); color: var(--gold); }
.review-backdrop { position: fixed; inset: 0; z-index: 60; display: flex; align-items: flex-end; justify-content: center;
  background: rgba(0, 0, 0, 0.62); padding: 0; }
.review-backdrop[hidden] { display: none; }
.review-card { width: 100%; max-width: 460px; max-height: 92vh; overflow-y: auto; background: var(--ink);
  border: 1px solid var(--line); padding: 22px 20px 20px; }
.review-card h2 { font-size: 30px; margin: 0 0 4px; color: var(--paper); }
.review-sub { color: var(--paper-dim); font-size: 13px; margin: 0 0 14px; }
.review-row { display: flex; justify-content: space-between; gap: 16px; padding: 9px 0; border-bottom: 1px solid var(--line); font-size: 13.5px; }
.review-row span:first-child { color: var(--paper-dim); flex: 0 0 auto; }
.review-row span:last-child { color: var(--paper); text-align: right; word-break: break-word; }
.review-row.total span:last-child { color: var(--gold); font-weight: 700; }
.review-actions { display: grid; gap: 10px; margin-top: 18px; }
.review-actions .btn { width: 100%; }
@media (min-width: 560px) { .review-backdrop { align-items: center; padding: 18px; } }
</style>
"""

CHECKOUT_FORM_CSS = """
<style>
.checkout-section-title { font-size: 13px; letter-spacing: 0.2em; text-transform: uppercase; font-weight: 700; margin: 26px 0 4px; }
#checkout-form .form-group label { text-transform: uppercase; letter-spacing: 0.04em; font-size: 12px; font-weight: 700; }
#checkout-form input[type=text], #checkout-form input[type=tel], #checkout-form input[type=email],
#checkout-form select, #checkout-form textarea { border-radius: 14px; padding: 14px 16px; }
#checkout-form textarea { display: block; width: 100%; min-height: 110px; resize: vertical; font: inherit;
  color: inherit; background: transparent; border: 1px solid rgba(255,255,255,0.25); box-sizing: border-box; }
#checkout-form input[readonly] { opacity: 0.7; cursor: not-allowed; }
.optional-tag { text-transform: uppercase; font-weight: 600; opacity: 0.7; }
.delivery-box { display: flex; align-items: center; gap: 14px; margin: 22px 0 0; padding: 16px 18px;
  border-radius: 16px; border: 1px solid rgba(193,154,87,0.35); background: rgba(193,154,87,0.08); }
.delivery-icon { width: 42px; height: 42px; border-radius: 50%; display: flex; align-items: center;
  justify-content: center; background: rgba(193,154,87,0.18); color: #c19a57; flex: none; }
.delivery-box strong { font-size: 14px; }
#place-order-btn { border-radius: 999px; width: 100%; }
</style>
"""


def checkout_page(lines: list, subtotal: float, categories: list, cart_count: int = 0, error: str | None = None,
                   subcategories: dict | None = None, pricing: dict | None = None) -> str:
    from config import DELIVERY_TIME_TEXT
    pricing = pricing or {}
    discount = float(pricing.get("discount") or 0)
    free_ship = bool(pricing.get("free_shipping"))
    net = max(subtotal - discount, 0)
    shipping_text = "Free" if free_ship else "—"
    free_ship_js = "true" if free_ship else "false"
    hint_style = ' style="display:none"' if free_ship else ""
    discount_rows = "".join(
        f'<div class="summary-line" style="color:var(--gold);"><span>{escape(a["title"])} ({escape(a["what"])})</span>'
        f'<span>&minus;{a["amount"]:.0f} EGP</span></div>'
        for a in pricing.get("applied", [])
    )
    gift_rows = "".join(
        f'<div class="summary-line" style="color:var(--gold);"><span>Free gift: {escape(g)}</span><span>Included</span></div>'
        for g in pricing.get("gifts", [])
    )
    summary_rows = "".join(
        f"""<div class="summary-line">
              <span>{escape(l['name'])} ({escape(l['size'])}{", " + escape(l['color']) if l['color'] else ""}) × {l['qty']}</span>
              <span>{l['line_total']:.0f} EGP</span>
            </div>"""
        for l in lines
    )
    error_html = f'<p style="color:#e5806b;font-size:13px;margin-bottom:14px;">{escape(error)}</p>' if error else ""

    city_options = "".join(
        f'<option value="{escape(city)}">{escape(city)}</option>' for city in SHIPPING_RATES
    )
    rates_json = json.dumps(SHIPPING_RATES)

    cod = PAYMENT_METHODS.get("cod", {})
    cod_label = cod.get("label", "Cash on Delivery")
    cod_desc = cod.get("description", "Pay in cash when your order arrives.")

    delivery_box = ""
    if (DELIVERY_TIME_TEXT or "").strip():
        delivery_box = (
            '<div class="delivery-box"><span class="delivery-icon">'
            '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="M1 6h13v10H1z"/><path d="M14 9h4l3 3v4h-7z"/>'
            '<circle cx="6" cy="18" r="2"/><circle cx="17" cy="18" r="2"/></svg></span>'
            f'<strong>{escape(DELIVERY_TIME_TEXT.strip())}</strong></div>'
        )

    body = f"""
{CHECKOUT_CSS}
{CHECKOUT_FORM_CSS}
<div class="wrap">
  <h1 class="display">Checkout</h1>
  <p class="sub">Almost there — fill in your details below.</p>

  {summary_rows}
    <div class="summary-line">
    <span>Subtotal</span>
    <span>{subtotal:.0f} EGP</span>
  </div>
  {discount_rows}
  {gift_rows}
  <div class="summary-line" id="shipping-row">
    <span>Shipping</span>
    <span id="shipping-amount">{shipping_text}</span>
  </div>
  <div class="summary-line summary-total">
    <span>Total</span>
    <span id="total-amount">{net:.0f} EGP</span>
  </div>
  <p class="checkout-hint" id="shipping-hint"{hint_style}>Select your delivery zone below to see the shipping cost.</p>
  {error_html}

  <h2 class="checkout-section-title">Delivery details</h2>
  <p class="checkout-required"><span class="req">*</span> All fields marked are required.</p>

  <form action="/checkout" method="post" enctype="multipart/form-data" id="checkout-form" novalidate style="margin-top:10px;">
    <div class="form-group">
      <label for="f-customer_name">Full name <span class="req">*</span></label>
      <input type="text" name="customer_name" id="f-customer_name" required maxlength="80" autocomplete="name">
      <p class="field-error" id="err-customer_name" hidden></p>
    </div>
    <div class="form-group">
      <label for="f-phone">Phone number <span class="req">*</span></label>
      <input type="tel" name="phone" id="f-phone" required maxlength="20" inputmode="tel" autocomplete="tel"
        placeholder="01012345678">
      <p class="field-error" id="err-phone" hidden></p>
    </div>
    <div class="form-group">
      <label for="f-email">Email address <span class="req">*</span></label>
      <input type="email" name="email" id="f-email" required maxlength="120" inputmode="email" autocomplete="email"
        placeholder="you@example.com">
      <p class="field-error" id="err-email" hidden></p>
    </div>
    <div class="form-group">
      <label for="city-select">Delivery zone <span class="req">*</span></label>
      <select name="city" id="city-select" required onchange="loomexUpdateShipping(this.value)">
        <option value="" disabled selected>Select…</option>
        {city_options}
      </select>
      <p class="field-error" id="err-city" hidden></p>
    </div>
    <div class="form-group">
      <label for="f-country">Country <span class="req">*</span></label>
      <input type="text" id="f-country" value="Egypt" readonly tabindex="-1">
    </div>
    <div class="form-group">
      <label for="f-street">Street <span class="req">*</span></label>
      <input type="text" name="street" id="f-street" required maxlength="120" autocomplete="address-line1"
        placeholder="e.g. Street 66 / El Tahrir St.">
      <p class="field-error" id="err-street" hidden></p>
    </div>
    <div class="form-group">
      <label for="f-area">Area / Neighborhood <span class="req">*</span></label>
      <input type="text" name="area" id="f-area" required maxlength="80" autocomplete="address-level3"
        placeholder="e.g. Smouha, Maadi, Sheikh Zayed">
      <p class="field-error" id="err-area" hidden></p>
    </div>
    <div class="form-group">
      <label for="f-building">Building no. / Name <span class="req">*</span></label>
      <input type="text" name="building" id="f-building" required maxlength="60">
      <p class="field-error" id="err-building" hidden></p>
    </div>
    <div class="form-group">
      <label for="f-floor">Floor / Apartment <span class="req">*</span></label>
      <input type="text" name="floor" id="f-floor" required maxlength="60" placeholder="e.g. 3rd floor, apt 7">
      <p class="field-error" id="err-floor" hidden></p>
    </div>
    <div class="form-group">
      <label for="f-notes">Delivery notes <span class="optional-tag">· optional</span></label>
      <textarea name="delivery_notes" id="f-notes" maxlength="500"></textarea>
    </div>

    <span class="field-label">Payment method <span class="req">*</span></span>
    <label class="pay-option">
      <input type="radio" name="payment_method" value="cod" checked>
      <span><strong>{escape(cod_label)}</strong><span>{escape(cod_desc)}</span></span>
    </label>
    <p class="pay-other">
      Want to pay another way, like InstaPay or an e-wallet? Choose <strong>{escape(cod_label)}</strong> here,
      then send us a DM on Instagram
      <a href="https://www.instagram.com/loomex_clothing" target="_blank" rel="noopener">@loomex_clothing</a>
      and we'll arrange it with you.
    </p>

    {delivery_box}

    <button class="btn" type="submit" id="place-order-btn" style="margin-top:20px;">Place Order</button>
  </form>
</div>

<div class="review-backdrop" id="review" hidden>
  <div class="review-card" role="dialog" aria-modal="true" aria-labelledby="review-title">
    <h2 class="display" id="review-title">Check your order</h2>
    <p class="review-sub">Please make sure everything is correct before you place your order.</p>
    <div id="review-rows"></div>
    <div class="review-actions">
      <button type="button" class="btn" id="review-confirm">Confirm &amp; place order</button>
      <button type="button" class="btn btn-ghost" id="review-edit">Edit my details</button>
    </div>
  </div>
</div>

<script>
var LOOMEX_RATES = {rates_json};
var LOOMEX_SUBTOTAL = {net:.2f};
var LOOMEX_FREE_SHIP = {free_ship_js};
function loomexUpdateShipping(city) {{
  var rate = LOOMEX_RATES[city];
  if (rate === undefined) return;
  if (LOOMEX_FREE_SHIP) rate = 0;
  document.getElementById('shipping-amount').textContent = LOOMEX_FREE_SHIP ? 'Free' : rate.toFixed(0) + ' EGP';
  document.getElementById('total-amount').textContent = (LOOMEX_SUBTOTAL + rate).toFixed(0) + ' EGP';
  document.getElementById('shipping-hint').style.display = 'none';
  loomexCheckCity();
}}

function loomexSetError(fieldId, errId, msg) {{
  var f = document.getElementById(fieldId);
  var e = document.getElementById(errId);
  if (msg) {{
    e.textContent = msg; e.hidden = false;
    f.classList.add('invalid'); f.setAttribute('aria-invalid', 'true');
  }} else {{
    e.textContent = ''; e.hidden = true;
    f.classList.remove('invalid'); f.removeAttribute('aria-invalid');
  }}
  return !msg;
}}
function loomexVal(id) {{
  return document.getElementById(id).value.trim().replace(/ +/g, ' ');
}}
function loomexCleanName() {{ return loomexVal('f-customer_name'); }}
function loomexNormPhone(raw) {{
  var p = raw.replace(/[^0-9+]/g, '');
  if (p.indexOf('+20') === 0) p = '0' + p.slice(3);
  else if (p.indexOf('0020') === 0) p = '0' + p.slice(4);
  else if (p.indexOf('20') === 0 && p.length === 12) p = '0' + p.slice(2);
  return p;
}}

function loomexCheckName() {{
  var v = loomexCleanName(), words = v ? v.split(' ') : [], msg = '';
  if (!v) msg = 'Please enter your full name.';
  else if (/[0-9]/.test(v)) msg = 'Your name should not contain numbers.';
  else if (words.length < 2 || words.some(function (w) {{ return w.length < 2; }}))
    msg = 'Please enter your first and last name.';
  return loomexSetError('f-customer_name', 'err-customer_name', msg);
}}
function loomexCheckPhone() {{
  var raw = document.getElementById('f-phone').value.trim(), msg = '';
  var p = loomexNormPhone(raw);
  if (!raw) msg = 'Please enter your phone number.';
  else if (p.length !== 11 || !/^01[0125][0-9]+$/.test(p))
    msg = 'Enter a valid Egyptian mobile number, like 01012345678.';
  return loomexSetError('f-phone', 'err-phone', msg);
}}
function loomexCheckEmail() {{
  var v = document.getElementById('f-email').value.trim(), msg = '';
  if (!v) msg = 'Please enter your email address.';
  else if (!/^[^@ ]+@[^@ ]+[.][^@ ]+$/.test(v)) msg = 'Please enter a valid email address.';
  return loomexSetError('f-email', 'err-email', msg);
}}
function loomexCheckCity() {{
  var msg = document.getElementById('city-select').value ? '' : 'Please select your delivery zone.';
  return loomexSetError('city-select', 'err-city', msg);
}}
function loomexRequired(id, errId, msg) {{
  return loomexSetError(id, errId, loomexVal(id) ? '' : msg);
}}
function loomexCheckStreet() {{ return loomexRequired('f-street', 'err-street', 'Please enter your street.'); }}
function loomexCheckArea() {{ return loomexRequired('f-area', 'err-area', 'Please enter your area or neighborhood.'); }}
function loomexCheckBuilding() {{ return loomexRequired('f-building', 'err-building', 'Please enter your building number or name.'); }}
function loomexCheckFloor() {{ return loomexRequired('f-floor', 'err-floor', 'Please enter your floor or apartment.'); }}

var LOOMEX_CHECKS = [
  ['f-customer_name', loomexCheckName], ['f-phone', loomexCheckPhone], ['f-email', loomexCheckEmail],
  ['city-select', loomexCheckCity], ['f-street', loomexCheckStreet], ['f-area', loomexCheckArea],
  ['f-building', loomexCheckBuilding], ['f-floor', loomexCheckFloor]
];
LOOMEX_CHECKS.forEach(function (c) {{
  var el = document.getElementById(c[0]);
  el.addEventListener('blur', c[1]);
  el.addEventListener('input', function () {{ if (el.classList.contains('invalid')) c[1](); }});
}});

function loomexRow(label, value, cls) {{
  var row = document.createElement('div');
  row.className = 'review-row' + (cls ? ' ' + cls : '');
  var a = document.createElement('span'); a.textContent = label;
  var b = document.createElement('span'); b.textContent = value;
  row.appendChild(a); row.appendChild(b);
  return row;
}}
function loomexOpenReview() {{
  var city = document.getElementById('city-select').value;
  var rate = LOOMEX_FREE_SHIP ? 0 : (LOOMEX_RATES[city] || 0);
  var rows = document.getElementById('review-rows');
  rows.innerHTML = '';
  rows.appendChild(loomexRow('Name', loomexCleanName()));
  rows.appendChild(loomexRow('Phone', document.getElementById('f-phone').value));
  rows.appendChild(loomexRow('Email', document.getElementById('f-email').value.trim()));
  rows.appendChild(loomexRow('Delivery zone', city));
  rows.appendChild(loomexRow('Address', loomexVal('f-street') + ', ' + loomexVal('f-area') + ', Building ' +
    loomexVal('f-building') + ', Floor/Apt ' + loomexVal('f-floor')));
  var notes = loomexVal('f-notes');
  if (notes) rows.appendChild(loomexRow('Notes', notes));
  rows.appendChild(loomexRow('Payment', 'Cash on Delivery'));
  rows.appendChild(loomexRow('Items (after discount)', LOOMEX_SUBTOTAL.toFixed(0) + ' EGP'));
  rows.appendChild(loomexRow('Shipping', LOOMEX_FREE_SHIP ? 'Free' : rate.toFixed(0) + ' EGP'));
  rows.appendChild(loomexRow('Total', (LOOMEX_SUBTOTAL + rate).toFixed(0) + ' EGP', 'total'));
  document.getElementById('review').hidden = false;
  document.getElementById('review-confirm').focus();
}}
function loomexCloseReview() {{ document.getElementById('review').hidden = true; }}

var LOOMEX_FORM = document.getElementById('checkout-form');
LOOMEX_FORM.addEventListener('submit', function (e) {{
  e.preventDefault();
  var results = LOOMEX_CHECKS.map(function (c) {{ return [c[0], c[1]()]; }});
  var bad = results.filter(function (r) {{ return !r[1]; }});
  if (bad.length) {{
    var first = document.getElementById(bad[0][0]);
    first.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
    first.focus();
    return;
  }}
  // store the cleaned values so the server always gets a consistent format
  document.getElementById('f-customer_name').value = loomexCleanName();
  document.getElementById('f-phone').value = loomexNormPhone(document.getElementById('f-phone').value);
  ['f-street', 'f-area', 'f-building', 'f-floor'].forEach(function (id) {{
    document.getElementById(id).value = loomexVal(id);
  }});
  loomexOpenReview();
}});
document.getElementById('review-edit').addEventListener('click', loomexCloseReview);
document.getElementById('review').addEventListener('click', function (e) {{ if (e.target === this) loomexCloseReview(); }});
document.addEventListener('keydown', function (e) {{ if (e.key === 'Escape') loomexCloseReview(); }});
document.getElementById('review-confirm').addEventListener('click', function () {{
  this.disabled = true; this.textContent = 'Placing your order...';
  document.getElementById('review-edit').disabled = true;
  LOOMEX_FORM.submit();
}});
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
    discount = float(order.get("discount") or 0)
    total = float(order.get("total") or (subtotal - discount + shipping))
    note_parts = [x.strip() for x in (order.get("promotion_note") or "").split("|")]
    free_ship = shipping == 0 and "Free shipping" in note_parts
    shipping_text = "FREE" if free_ship else f"{shipping:.0f} EGP"
    gifts = [x[len("Free gift:"):].strip() for x in note_parts if x.startswith("Free gift:")]
    gift_rows = "".join(
        f'<div class="receipt-total-row"><span>FREE GIFT</span><span>{escape(g)}</span></div>' for g in gifts
    )
    discount_row = (
        f'<div class="receipt-total-row"><span>DISCOUNT</span><span>-{discount:.0f} EGP</span></div>'
        if discount > 0 else ""
    )
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
      {discount_row}
      <div class="receipt-total-row"><span>SHIPPING</span><span>{shipping_text}</span></div>
      {gift_rows}
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
RETURNS_CSS = """
<style>
.rt { max-width: 620px; margin: 0 auto; padding: 34px 18px 60px; }
.rt-eyebrow { font-size: 12px; letter-spacing: 0.16em; text-transform: uppercase; color: var(--gold); margin: 0 0 10px; }
.rt-title { font-size: 40px; margin: 0 0 14px; color: var(--paper); }
.rt-lead { color: var(--paper-dim); font-size: 15px; line-height: 1.6; margin: 0 0 26px; max-width: 46ch; }

.rt-glance { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 28px; }
.rt-stat { background: var(--ink-raised); border: 1px solid var(--line); padding: 16px 10px; text-align: center; }
.rt-stat strong {
  display: block; font-family: "Big Shoulders Display", sans-serif; font-size: 22px;
  text-transform: uppercase; color: var(--gold); line-height: 1; margin-bottom: 8px; letter-spacing: 0.02em;
}
.rt-stat span { display: block; font-size: 11.5px; color: var(--paper-dim); line-height: 1.4; }

.rt-card { background: var(--ink-raised); border: 1px solid var(--line); padding: 20px 18px; margin-bottom: 12px; }
.rt-card-head { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.rt-num {
  flex: 0 0 auto; width: 30px; height: 30px; border-radius: 50%; border: 1px solid var(--gold);
  color: var(--gold); display: flex; align-items: center; justify-content: center;
  font-family: "Big Shoulders Display", sans-serif; font-size: 16px; font-weight: 700;
}
.rt-card h2 { margin: 0; font-size: 14px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--paper); font-weight: 600; }
.rt-card p { margin: 0 0 10px; color: var(--paper-dim); font-size: 14px; line-height: 1.7; }
.rt-card p:last-child { margin-bottom: 0; }
.rt-card strong { color: var(--paper); }
.rt-card a { color: var(--gold); text-decoration: underline; }
.rt-note {
  border-left: 2px solid var(--gold); background: rgba(199, 154, 70, 0.08);
  padding: 12px 14px; margin-top: 14px; color: var(--paper-dim); font-size: 13.5px; line-height: 1.65;
}
.rt-note strong { color: var(--gold); }

.rt-refund {
  display: flex; justify-content: space-between; align-items: center; gap: 14px;
  padding: 12px 0; border-bottom: 1px solid var(--line); font-size: 13.5px;
}
.rt-refund:last-child { border-bottom: none; padding-bottom: 0; }
.rt-refund span:first-child { color: var(--paper-dim); }
.rt-refund span:last-child { color: var(--paper); font-weight: 600; text-align: right; }

.rt-start { border-color: var(--gold); }
.rt-steps { list-style: none; margin: 0 0 6px; padding: 0; counter-reset: step; }
.rt-steps li {
  position: relative; counter-increment: step; padding: 2px 0 16px 40px;
  color: var(--paper-dim); font-size: 14px; line-height: 1.65;
}
.rt-steps li::before {
  content: counter(step); position: absolute; left: 0; top: 0; width: 26px; height: 26px;
  border-radius: 50%; border: 1px solid var(--gold); color: var(--gold);
  display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700;
}
.rt-contact { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 8px; }
.rt-contact .btn {
  display: flex; align-items: center; justify-content: center; min-height: 48px;
  padding: 12px 10px; font-size: 13px; color: var(--ink); text-decoration: none;
}
.rt-handle { text-align: center; color: var(--paper-dim); font-size: 12px; margin: 12px 0 0 !important; }

@media (min-width: 560px) { .rt-title { font-size: 52px; } }
</style>
"""


def returns_page(categories: list, cart_count: int = 0, subcategories: dict | None = None) -> str:
    body = RETURNS_CSS + """
<div class="rt">
  <p class="rt-eyebrow">Loomex support</p>
  <h1 class="rt-title display">Returns &amp; Exchanges</h1>
  <p class="rt-lead">We want you to be happy with your order. If something isn't right,
  here's exactly how returns and exchanges work.</p>

  <div class="rt-glance">
    <div class="rt-stat"><strong>7 days</strong><span>from the day it's delivered</span></div>
    <div class="rt-stat"><strong>As received</strong><span>same condition, ideally boxed</span></div>
    <div class="rt-stat"><strong>Same method</strong><span>refunded how you paid</span></div>
  </div>

  <section class="rt-card">
    <div class="rt-card-head"><span class="rt-num">1</span><h2>Return window</h2></div>
    <p>You have <strong>7 days from the date your order is delivered</strong> to
    request a return or exchange.</p>
  </section>

  <section class="rt-card">
    <div class="rt-card-head"><span class="rt-num">2</span><h2>Condition</h2></div>
    <p>The item must be in <strong>exactly the condition you received it in</strong>,
    and preferably with its original packaging too.</p>
  </section>

  <section class="rt-card">
    <div class="rt-card-head"><span class="rt-num">3</span><h2>Return shipping</h2></div>
    <p>Return shipping is <strong>paid by the customer</strong>.</p>
    <div class="rt-note">
      <strong>The one exception is a defect.</strong> If your item had a defect when you
      received it, you won't pay for return shipping. Send us clear photos of the defect
      as proof on <a href="https://www.instagram.com/loomex_clothing" target="_blank" rel="noopener">Instagram</a>
      or by <a href="mailto:loomex.co@gmail.com">email</a>.
    </div>
  </section>

  <section class="rt-card">
    <div class="rt-card-head"><span class="rt-num">4</span><h2>Refunds</h2></div>
    <div class="rt-refund"><span>You paid with cash</span><span>Refunded in cash</span></div>
    <div class="rt-refund"><span>You paid with InstaPay or wallet</span><span>Refunded by InstaPay or wallet</span></div>
  </section>

  <section class="rt-card rt-start">
    <div class="rt-card-head"><span class="rt-num">&#10003;</span><h2>How to start a return</h2></div>
    <ol class="rt-steps">
      <li>Message us on Instagram, or send us an email.</li>
      <li>Include your order number and the reason for the return, plus photos if the item arrived with a defect.</li>
      <li>We'll reply and walk you through the next steps.</li>
    </ol>
    <div class="rt-contact">
      <a class="btn" href="https://www.instagram.com/loomex_clothing" target="_blank" rel="noopener">Instagram</a>
      <a class="btn" href="mailto:loomex.co@gmail.com">Email us</a>
    </div>
    <p class="rt-handle">@loomex_clothing &nbsp;·&nbsp; loomex.co@gmail.com</p>
  </section>
</div>
"""
    return layout("Returns & Exchanges", body, categories, cart_count, subcategories=subcategories,
                  description="Loomex returns and exchanges: 7-day window, item condition, return shipping, refunds and how to start a return.",
                  path="/returns")