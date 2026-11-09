"""Earnings page: each order's real revenue (total - shipping, already after discounts)
and how it is split between me and my partner. Shares are typed by hand."""
from datetime import datetime, timezone
from uuid import UUID

from services.admin_data import ADMIN_TZ
from services.promotions import _parse
from supabase_client import supabase


def month_range(ym: str | None):
    now = datetime.now(ADMIN_TZ)
    try:
        y, m = (int(x) for x in (ym or "").split("-"))
        start = datetime(y, m, 1, tzinfo=ADMIN_TZ)
    except Exception:
        start = datetime(now.year, now.month, 1, tzinfo=ADMIN_TZ)
    end = datetime(start.year + (start.month == 12), start.month % 12 + 1, 1, tzinfo=ADMIN_TZ)
    return f"{start.year}-{start.month:02d}", start, end


def get_month(ym: str | None) -> dict:
    key, start, end = month_range(ym)
    orders = (supabase.table("orders")
              .select("id,order_number,customer_name,total,shipping,status,created_at")
              .is_("deleted_at", "null").neq("status", "cancelled")
              .gte("created_at", start.isoformat()).lt("created_at", end.isoformat())
              .order("created_at").execute().data or [])
    shares = {}
    if orders:
        try:
            rows = (supabase.table("order_shares").select("*")
                    .in_("order_id", [o["id"] for o in orders]).execute().data or [])
            shares = {r["order_id"]: r for r in rows}
        except Exception:
            shares = {}
    out = []
    for o in orders:
        s = shares.get(o["id"]) or {}
        d = _parse(o.get("created_at"))
        out.append({
            "id": o["id"], "number": o["order_number"], "customer": o.get("customer_name") or "",
            "status": o.get("status") or "",
            "date": d.astimezone(ADMIN_TZ).strftime("%d %b") if d else "",
            "revenue": round(float(o.get("total") or 0) - float(o.get("shipping") or 0), 2),
            "my": float(s.get("my_share") or 0), "partner": float(s.get("partner_share") or 0),
        })
    t_rev = round(sum(r["revenue"] for r in out), 2)
    t_my = round(sum(r["my"] for r in out), 2)
    t_pt = round(sum(r["partner"] for r in out), 2)
    return {"month": key, "rows": out, "revenue": t_rev, "my": t_my, "partner": t_pt,
            "unassigned": round(t_rev - t_my - t_pt, 2)}


def _num(x):
    x = str(x or "").strip().replace(",", "")
    if not x:
        return 0.0
    try:
        v = float(x)
    except ValueError:
        return None
    return round(v, 2) if v >= 0 else None


def parse_form(form):
    """Returns (entries, error). entries = [(order_id, my_share, partner_share)]."""
    entries = []
    for key in form.keys():
        if not key.startswith("my_"):
            continue
        oid = key[3:]
        try:
            oid = str(UUID(oid))
        except ValueError:
            continue
        my, pt = _num(form.get(key)), _num(form.get("partner_" + oid))
        if my is None or pt is None:
            return [], "Shares must be numbers that are 0 or more."
        entries.append((oid, my, pt))
    return entries, None


def save(entries):
    if not entries:
        return
    now = datetime.now(timezone.utc).isoformat()
    rows = [{"order_id": o, "my_share": m, "partner_share": p, "updated_at": now} for o, m, p in entries]
    supabase.table("order_shares").upsert(rows, on_conflict="order_id").execute()
