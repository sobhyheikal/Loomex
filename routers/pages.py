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
    return templates.landing_page(CATEGORIES, cart_count, subcategories=SUBCATEGORIES)


@router.get("/shop", response_class=HTMLResponse)
def shop(request: Request, category: str | None = None, subcategory: str | None = None, q: str | None = None):
    products, subcategory = list_shop_products(category, subcategory, CATEGORIES, SUBCATEGORIES, search=q)
    cart_count = cart_item_count(get_cart(request))
    return templates.shop_page(
        products, CATEGORIES, category, cart_count,
        subcategories=SUBCATEGORIES, active_subcategory=subcategory, search=q,
    )


# ----------------------------------------------------------- legal/trust ----
@router.get("/returns", response_class=HTMLResponse)
def returns(request: Request):
    cart_count = cart_item_count(get_cart(request))
    return templates.returns_page(CATEGORIES, cart_count, subcategories=SUBCATEGORIES)


@router.get("/privacy-policy", response_class=HTMLResponse)
def privacy_policy(request: Request):
    cart_count = cart_item_count(get_cart(request))
    return templates.privacy_page(CATEGORIES, cart_count, subcategories=SUBCATEGORIES)