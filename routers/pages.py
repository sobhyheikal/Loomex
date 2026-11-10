from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

import templates
from config import CATEGORIES, SUBCATEGORIES
from services.cart import get_cart, cart_item_count
from services.products import list_shop_products

router = APIRouter()


# ---------------------------------------------------------------- home ----
@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    cart_count = cart_item_count(get_cart(request))
    try:
        products, _ = list_shop_products(None, None, CATEGORIES, SUBCATEGORIES, search=None)
    except Exception:
        products = []
    return templates.landing_page(CATEGORIES, cart_count, subcategories=SUBCATEGORIES, products=products)


@router.get("/shop", response_class=HTMLResponse)
def shop(request: Request, category: str | None = None, subcategory: str | None = None, q: str | None = None):
    products, subcategory = list_shop_products(category, subcategory, CATEGORIES, SUBCATEGORIES, search=q)
    cart_count = cart_item_count(get_cart(request))
    html = templates.shop_page(
        products, CATEGORIES, category, cart_count,
        subcategories=SUBCATEGORIES, active_subcategory=subcategory, search=q,
    )
    # each category / subcategory gets its own canonical address; searches are kept out of Google
    from config import SITE_URL
    if category in CATEGORIES:
        own = f"{SITE_URL}/shop?category={category}" + (f"&subcategory={subcategory}" if subcategory else "")
        html = html.replace(f'<link rel="canonical" href="{SITE_URL}/shop">',
                            f'<link rel="canonical" href="{own}">', 1)
    if (q or "").strip():
        html = html.replace("</head>", '<meta name="robots" content="noindex, follow"></head>', 1)
    return html


# ----------------------------------------------------------- legal/trust ----
@router.get("/returns", response_class=HTMLResponse)
def returns(request: Request):
    cart_count = cart_item_count(get_cart(request))
    return templates.returns_page(CATEGORIES, cart_count, subcategories=SUBCATEGORIES)


@router.get("/privacy-policy", response_class=HTMLResponse)
def privacy_policy(request: Request):
    cart_count = cart_item_count(get_cart(request))
    return templates.privacy_page(CATEGORIES, cart_count, subcategories=SUBCATEGORIES)