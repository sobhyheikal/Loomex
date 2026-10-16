from supabase_client import supabase


def get_product_or_404(slug: str):
    result = supabase.table("products").select("*").eq("slug", slug).maybe_single().execute()
    return result.data if result else None


def list_shop_products(category: str | None, subcategory: str | None,
                        categories: list[str], subcategories_map: dict,
                        search: str | None = None):
    """Query in-stock products for the /shop page, optionally filtered by
    category, subcategory, and a free-text search term (matched against
    name/description). Returns (products, normalized_subcategory) —
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
    search = (search or "").strip()
    if search:
        term = "".join(ch for ch in search if ch not in "%,()")
        query = query.or_(f"name.ilike.%{term}%,description.ilike.%{term}%")
    result = query.order("created_at", desc=True).execute()
    return result.data, subcategory
