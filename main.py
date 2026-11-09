"""
Loomex storefront — FastAPI app.

Entrypoint file: Vercel automatically detects a `FastAPI` instance named
`app` in main.py at the project root, so this file needs zero extra
Vercel config to deploy. Kept thin on purpose — routes live in routers/,
business logic + Supabase access live in services/.
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

import templates
from config import CATEGORIES, SUBCATEGORIES
from routers import pages, products, cart, checkout, admin, admin_push
from services.admin_auth import AdminLoginRequired
from fastapi.responses import RedirectResponse
from services.cart import get_cart, cart_item_count

app = FastAPI()

# Serving /static/* — Vercel promotes this to its CDN automatically.
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(pages.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(checkout.router)
app.include_router(admin.public_router)
app.include_router(admin_push.public_router)
app.include_router(admin.router)


@app.exception_handler(AdminLoginRequired)
async def admin_login_required(request: Request, exc: AdminLoginRequired):
    return RedirectResponse("/admin/login", status_code=303)


# Styled error pages instead of FastAPI's bare default — covers both an
# unmatched route (nothing registered for that path) and an explicit
# `raise HTTPException(status_code=404, ...)` from inside a route.
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    cart_count = cart_item_count(get_cart(request))
    message = exc.detail if isinstance(exc.detail, str) and exc.detail != "Not Found" else None
    return HTMLResponse(
        templates.error_page(CATEGORIES, cart_count, subcategories=SUBCATEGORIES,
                              status_code=exc.status_code, message=message),
        status_code=exc.status_code,
    )