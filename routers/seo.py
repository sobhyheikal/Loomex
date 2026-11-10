"""robots.txt and sitemap.xml, so Google can find every page and product."""
from html import escape

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, Response

from config import CATEGORIES, SITE_URL
from supabase_client import supabase

router = APIRouter()


@router.api_route("/robots.txt", methods=["GET", "HEAD"], include_in_schema=False)
def robots():
    text = ("User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /cart\nDisallow: /checkout\n\n"
            f"Sitemap: {SITE_URL}/sitemap.xml\n")
    return PlainTextResponse(text, headers={"Cache-Control": "public, max-age=3600"})


@router.api_route("/sitemap.xml", methods=["GET", "HEAD"], include_in_schema=False)
def sitemap():
    urls = [(SITE_URL + "/", None), (SITE_URL + "/shop", None),
            (SITE_URL + "/returns", None), (SITE_URL + "/privacy-policy", None)]
    urls += [(f"{SITE_URL}/shop?category={c}", None) for c in CATEGORIES]
    try:
        rows = (supabase.table("products").select("slug,created_at")
                .is_("deleted_at", "null").eq("is_visible", True).execute().data or [])
    except Exception:
        rows = []
    urls += [(f"{SITE_URL}/product/{r['slug']}", (r.get("created_at") or "")[:10]) for r in rows if r.get("slug")]
    body = "".join(
        f"<url><loc>{escape(u)}</loc>{f'<lastmod>{m}</lastmod>' if m else ''}</url>" for u, m in urls)
    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>')
    return Response(xml, media_type="application/xml", headers={"Cache-Control": "public, max-age=3600"})
