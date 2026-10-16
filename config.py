"""
Shared app configuration/constants, used by routers and services.
"""

CATEGORIES = ["tops", "tank-tops", "pants", "pullovers", "quarter-zips", "jackets"]
SUBCATEGORIES = {"pants": ["joggers", "checkered-pants"]}
CART_COOKIE = "loomex_cart"

# Your live domain once deployed, e.g. "https://loomex.vercel.app" or
# "https://loomex.com" — no trailing slash. Used to build absolute
# Open Graph (og:url) tags for social-sharing previews. Leave blank until
# you have one; og:url is just omitted until then.
SITE_URL = ""

# Ad pixels — from Meta Events Manager / TikTok Ads Manager -> "Set up
# pixel" -> "Add code manually". Leave either blank to keep that pixel
# fully disabled (nothing loads, no cookies, no tracking).
META_PIXEL_ID = "1069351069434655"
TIKTOK_PIXEL_ID = "DB9884RC77UACVVNC4F0"
