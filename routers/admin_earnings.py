"""Loomex admin: Earnings routes. Included into routers/admin.py, so URLs are under /admin."""
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

import templates_earnings as ui
from services import admin_auth, earnings as earn

router = APIRouter(dependencies=[Depends(admin_auth.require_admin)])


@router.get("/earnings", response_class=HTMLResponse)
def earnings(month: str | None = None, msg: str | None = None):
    try:
        d = earn.get_month(month)
    except Exception as e:
        d = earn.get_month.__globals__["month_range"](month)
        d = {"month": d[0], "rows": [], "revenue": 0, "my": 0, "partner": 0, "unassigned": 0}
        return HTMLResponse(ui.earnings_page(d, error="Couldn't load: " + str(e)[:160]))
    return HTMLResponse(ui.earnings_page(d, msg="Saved." if msg == "saved" else None))


@router.post("/earnings")
async def earnings_save(request: Request):
    form = await request.form()
    month = str(form.get("month") or "")
    entries, error = earn.parse_form(form)
    if not error:
        try:
            earn.save(entries)
        except Exception as e:
            s = str(e)
            error = ("The order_shares table is missing. Run the SQL from Step 9 in Supabase first."
                     if "order_shares" in s else "Couldn't save: " + s[:160])
    if error:
        return HTMLResponse(ui.earnings_page(earn.get_month(month), error=error), status_code=400)
    return RedirectResponse("/admin/earnings?" + urlencode({"month": month, "msg": "saved"}), status_code=303)
