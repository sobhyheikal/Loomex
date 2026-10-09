"""
Loomex storefront — FastAPI app.

Entrypoint file: Vercel automatically detects a `FastAPI` instance named
`app` in main.py at the project root, so this file needs zero extra
Vercel config to deploy. Kept thin on purpose — routes live in routers/,
business logic + Supabase access live in services/.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from routers import pages, products, cart, checkout

app = FastAPI()

# Serving /static/* — Vercel promotes this to its CDN automatically.
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(pages.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(checkout.router)