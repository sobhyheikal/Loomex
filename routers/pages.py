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
def shop(request: Request, category: str | None = None, subcategory: str | None = None):
    products, subcategory = list_shop_products(category, subcategory, CATEGORIES, SUBCATEGORIES)
    cart_count = cart_item_count(get_cart(request))
    return templates.shop_page(
        products, CATEGORIES, category, cart_count,
        subcategories=SUBCATEGORIES, active_subcategory=subcategory,
    )
