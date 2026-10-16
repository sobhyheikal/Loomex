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

# ----------------------------------------------------------------------
# SHIPPING RATES — EGP, by city/zone (your real courier rate sheet).
# Shown live at checkout and stored on the order. The dropdown at
# checkout is built from this dict's keys, in this order.
# ----------------------------------------------------------------------
SHIPPING_RATES = {
    "Alexandria": 60,
    "Burj Al Arab": 85,
    "Al-Amriya": 85,
    "Abdel Qader": 85,
    "Cairo": 95,
    "New Cairo": 95,
    "Giza": 95,
    "10th of Ramadan": 105,
    "Obour City": 105,
    "Badr City": 105,
    "Ajmi": 80,
    "Sadat City": 105,
    "Ismailia": 105,
    "Suez": 105,
    "Port Said": 105,
    "Dakahlia": 105,
    "Qalyubia": 105,
    "Menoufia": 105,
    "Sharkia": 105,
    "Gharbia": 105,
    "Beheira": 105,
    "Kafr El Sheikh": 105,
    "Damietta": 105,
    "Beni Suef": 120,
    "Fayoum": 120,
    "Minya": 120,
    "Assiut": 120,
    "Qena": 120,
    "Luxor": 120,
    "Aswan": 120,
    "Red Sea": 130,
    "Sohag": 120,
    "Matruh": 140,
    "North Coast": 140,
    "New Valley": 150,
    "South Sinai": 150,
    "Ajmi To Alex": 80,
    "Ajmi To Ajmi": 60,
}
