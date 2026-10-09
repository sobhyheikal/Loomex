from supabase_client import supabase


def get_product_or_404(slug: str):
    result = supabase.table("products").select("*").eq("slug", slug).single().execute()
    return result.data


def list_shop_products(category: str | None, subcategory: str | None,
                        categories: list[str], subcategories_map: dict):
    """Query in-stock products for the /shop page, optionally filtered by
    category and subcategory. Returns (products, normalized_subcategory) —
    subcategory is reset to None if it isn't valid for the given category.
    `category` itself is passed through unchanged either way (same as the
    original inline logic)."""
    query = supabase.table("products").select("*").eq("in_stock", True)
    if category in categories:
        query = query.eq("category", category)
        if subcategory in subcategories_map.get(category, []):
            query = query.eq("subcategory", subcategory)
        else:
            subcategory = None
    else:
        subcategory = None
    result = query.order("created_at", desc=True).execute()
    return result.data, subcategory
