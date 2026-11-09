from supabase_client import supabase


def _live(query):
    """Only products that are not deleted and are switched ON in the admin panel."""
    return query.is_("deleted_at", "null").eq("is_visible", True)


def get_product_or_404(slug: str):
    result = _live(supabase.table("products").select("*").eq("slug", slug)).maybe_single().execute()
    return result.data if result else None


def list_shop_products(category: str | None, subcategory: str | None,
                        categories: list[str], subcategories_map: dict,
                        search: str | None = None):
    """Query products for the /shop page, optionally filtered by
    category, subcategory, and a free-text search term (matched against
    name/description). Returns (products, normalized_subcategory) —
    subcategory is reset to None if it isn't valid for the given category.
    `category` itself is passed through unchanged either way (same as the
    original inline logic).

    Deleted products and products switched OFF in the admin are never listed.
    Sold-out products are INCLUDED (the page shows them with a "Sold out"
    badge). They are listed after the products that are still available;
    inside each group the newest products come first."""
    query = _live(supabase.table("products").select("*"))
    if category in categories:
        query = query.eq("category", category)
        if subcategory in subcategories_map.get(category, []):
            query = query.eq("subcategory", subcategory)
        else:
            subcategory = None
    else:
        subcategory = None
    search = (search or "").strip()
    if search:
        term = "".join(ch for ch in search if ch not in "%,()")
        query = query.or_(f"name.ilike.%{term}%,description.ilike.%{term}%")
    result = query.order("created_at", desc=True).execute()
    products = list(result.data or [])
    # sorted() is stable, so newest-first order is kept inside each group
    products.sort(key=is_sold_out)
    return products, subcategory


# ----------------------------------------------------------------------
# STOCK HELPERS
#   products.in_stock            -> False means the WHOLE product is sold out
#   products.sold_out_sizes      -> list of sizes that are sold out, e.g. ["M"]
#   products.sold_out_colors     -> list of colors that are sold out
# ----------------------------------------------------------------------
def _norm(size) -> str:
    return str(size).strip().casefold()


def out_of_stock_sizes(product: dict) -> list:
    return list(product.get("sold_out_sizes") or product.get("out_of_stock_sizes") or [])


def is_sold_out(product: dict) -> bool:
    """True when nothing can be bought: the product is switched to out of stock,
    or every size is sold out, or every color is sold out."""
    if not product.get("in_stock"):
        return True
    sizes = product.get("sizes") or []
    out_s = {_norm(s) for s in out_of_stock_sizes(product)}
    if sizes and all(_norm(s) in out_s for s in sizes):
        return True
    colors = product.get("colors") or []
    out_c = {_norm(c) for c in (product.get("sold_out_colors") or [])}
    return bool(colors) and all(_norm(c) in out_c for c in colors)


def available_sizes(product: dict) -> list:
    """Sizes a customer can still buy, in the product's own size order."""
    if is_sold_out(product):
        return []
    out = {_norm(s) for s in out_of_stock_sizes(product)}
    return [s for s in (product.get("sizes") or []) if _norm(s) not in out]


def can_buy(product: dict, size: str) -> bool:
    """Server-side check for add-to-cart and checkout."""
    return _norm(size) in {_norm(s) for s in available_sizes(product)}