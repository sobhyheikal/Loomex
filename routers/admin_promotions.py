

"""Loomex admin: promotion routes (list, create, edit, activate, banner on/off, delete).
Included into routers/admin.py, so every URL here is under /admin and needs the admin login."""

from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

import templates_promotions as ui
from config import CATEGORIES
from services import admin_auth, promo_admin
from services import admin_data as data

router = APIRouter(dependencies=[Depends(admin_auth.require_admin)])

MSGS = {"created": "Promotion added.", "saved": "Saved.", "updated": "Updated.",
        "deleted": "Moved to Recently Deleted."}


def _go(path: str, msg: str | None = None):
    return RedirectResponse(path + ("?" + urlencode({"msg": msg}) if msg else ""), status_code=303)


def _page(msg=None, error=None, form=None, editing=None, show_form=False, status=200):
    html = ui.promotions_page(promo_admin.list_promotions(), promo_admin.products_for_picker(), CATEGORIES,
                              msg=msg, error=error, form=form, editing_id=editing, show_form=show_form)
    return HTMLResponse(html, status_code=status)


def _promo_form(title: str = Form(""), subtitle: str = Form(""), link_choice: str = Form("/shop"),
                link_url: str = Form(""), code: str = Form(""), product_ids: list[str] = Form([]),
                discount_type: str = Form(""), value: str = Form(""), min_qty: str = Form(""),
                min_spend: str = Form(""), same_product: str = Form(""), starts: str = Form(""),
                ends: str = Form(""), show_banner: str = Form("")) -> dict:
    return {"title": title, "subtitle": subtitle, "link_choice": link_choice, "link_url": link_url,
            "code": code, "product_ids": product_ids, "discount_type": discount_type, "value": value,
            "min_qty": min_qty, "min_spend": min_spend, "same_product": same_product, "starts": starts,
            "ends": ends, "show_banner": show_banner}


@router.get("/promotions", response_class=HTMLResponse)
def promotions(msg: str | None = None, new: str | None = None):
    return _page(msg=MSGS.get(msg or ""), form=promo_admin.blank_form() if new else None, show_form=bool(new))


@router.post("/promotions/new")
def promotion_create(form: dict = Depends(_promo_form)):
    row, error = promo_admin.build_row(form)
    if not error:
        row["is_active"] = True
        try:
            promo_admin.add(row)
        except Exception as e:
            error = promo_admin.friendly_error(e)
    if error:
        return _page(error=error, form=form, show_form=True, status=400)
    return _go("/admin/promotions", "created")


@router.get("/promotions/{pid}/edit", response_class=HTMLResponse)
def promotion_edit(pid: UUID):
    p = promo_admin.get_promotion(str(pid))
    if not p:
        raise HTTPException(404)
    return _page(form=promo_admin.row_to_form(p), editing=str(pid), show_form=True)


@router.post("/promotions/{pid}")
def promotion_save(pid: UUID, form: dict = Depends(_promo_form)):
    if not promo_admin.get_promotion(str(pid)):
        raise HTTPException(404)
    row, error = promo_admin.build_row(form)
    if not error:
        try:
            promo_admin.update(str(pid), row)
        except Exception as e:
            error = promo_admin.friendly_error(e)
    if error:
        return _page(error=error, form=form, editing=str(pid), show_form=True, status=400)
    return _go("/admin/promotions", "saved")


@router.post("/promotions/{pid}/toggle")
def promotion_toggle(pid: UUID):
    promo_admin.toggle_active(str(pid))
    return _go("/admin/promotions", "updated")


@router.post("/promotions/{pid}/banner")
def promotion_banner(pid: UUID):
    promo_admin.toggle_banner(str(pid))
    return _go("/admin/promotions", "updated")


@router.post("/promotions/{pid}/delete")
def promotion_delete(pid: UUID):
    data.soft_delete("promotions", str(pid))
    return _go("/admin/promotions", "deleted")