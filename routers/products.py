from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

import templates
from config import CATEGORIES, SUBCATEGORIES
from services.cart import get_cart, cart_item_count
from services.products import get_product_or_404

router = APIRouter()


# ------------------------------------------------------------- product ----
@router.get("/product/{slug}", response_class=HTMLResponse)
def product_detail(request: Request, slug: str):
    p = get_product_or_404(slug)
    if not p:
        raise HTTPException(status_code=404, detail="We couldn't find that product — it may no longer be available.")
    cart_count = cart_item_count(get_cart(request))
    return templates.product_page(p, CATEGORIES, cart_count, subcategories=SUBCATEGORIES)
