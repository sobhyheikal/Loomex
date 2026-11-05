from supabase_client import supabase


def get_product_or_404(slug: str):
    result = supabase.table("products").select("*").eq("slug", slug).maybe_single().execute()
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

    Sold-out products are INCLUDED (the page shows them with a "Sold out"
    badge). They are listed after the products that are still available;
    inside each group the newest products come first."""
    query = supabase.table("products").select("*")
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
#   products.out_of_stock_sizes  -> list of sizes that are sold out, e.g. ["M"]
# ----------------------------------------------------------------------
def _norm(size) -> str:
    return str(size).strip().casefold()


def is_sold_out(product: dict) -> bool:
    """True when the whole product is sold out. A missing/NULL in_stock counts
    as sold out, because the old shop query (in_stock = true) hid those too."""
    return not product.get("in_stock")


def out_of_stock_sizes(product: dict) -> list:
    return list(product.get("out_of_stock_sizes") or [])


def available_sizes(product: dict) -> list:
    """Sizes a customer can still buy, in the product's own size order."""
    if is_sold_out(product):
        return []
    out = {_norm(s) for s in out_of_stock_sizes(product)}
    return [s for s in (product.get("sizes") or []) if _norm(s) not in out]


def can_buy(product: dict, size: str) -> bool:
    """Server-side check for add-to-cart and checkout."""
    return _norm(size) in {_norm(s) for s in available_sizes(product)}