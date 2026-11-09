"""Loomex admin panel routes. Everything under /admin needs the admin login."""

import time
from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

import templates_admin as ui
from config import CATEGORIES, SUBCATEGORIES
from services import admin_auth
from services import admin_data as data

public_router = APIRouter()  # login page: reachable without being logged in
router = APIRouter(prefix="/admin", dependencies=[Depends(admin_auth.require_admin)])

MSGS = {
    "created": "Created.", "saved": "Saved.", "updated": "Updated.",
    "deleted": "Moved to Recently Deleted.", "restored": "Restored.",
    "purged": "Deleted permanently.", "profile": "Profile updated.",
}


def _go(path: str, msg: str | None = None, **params):
    if msg:
        params["msg"] = msg
    params = {k: v for k, v in params.items() if v}
    return RedirectResponse(path + ("?" + urlencode(params) if params else ""), status_code=303)


def _kind(kind: str) -> str:
    if kind not in data.KINDS:
        raise HTTPException(404)
    return kind


# ---------------------------------------------------------------- login ----
@public_router.get("/admin/login", response_class=HTMLResponse)
def login_form():
    acct = admin_auth.get_account()
    return ui.login_page(configured=admin_auth.configured(acct), first_time=acct is None)


@public_router.post("/admin/login")
def login(request: Request, password: str = Form("")):
    acct = admin_auth.get_account()
    if not admin_auth.configured(acct):
        return HTMLResponse(ui.login_page(configured=False), status_code=503)
    if not admin_auth.verify_login(password):
        time.sleep(1)  # slows down guessing
        return HTMLResponse(ui.login_page(configured=True, first_time=acct is None,
                                          error="Wrong password."), status_code=401)
    resp = RedirectResponse("/admin/orders", status_code=303)
    admin_auth.set_login_cookie(resp, request, acct)
    return resp


@router.post("/logout")
def logout():
    resp = RedirectResponse("/admin/login", status_code=303)
    resp.delete_cookie(admin_auth.COOKIE)
    return resp


# -------------------------------------------------------------- profile ----
@router.get("/profile", response_class=HTMLResponse)
def profile(msg: str | None = None):
    acct = admin_auth.get_account()
    return ui.profile_page(acct["email"] if acct else "", msg=MSGS.get(msg or ""))


@router.post("/profile")
def profile_save(request: Request, current_password: str = Form(""),
                 new_password: str = Form(""), confirm_password: str = Form("")):
    acct = admin_auth.get_account()
    current_email = acct["email"] if acct else ""

    def fail(error):
        return HTMLResponse(ui.profile_page(current_email, error=error), status_code=400)

    if not admin_auth.verify_current(current_password, acct):
        time.sleep(1)
        return fail("Your current password is wrong.")
    if len(new_password) < admin_auth.MIN_PASSWORD:
        return fail(f"The new password must be at least {admin_auth.MIN_PASSWORD} characters.")
    if new_password != confirm_password:
        return fail("The two new passwords don't match.")
    admin_auth.save_account(admin_auth.hash_password(new_password))
    resp = _go("/admin/profile", "profile")
    admin_auth.set_login_cookie(resp, request, admin_auth.get_account())  # keep this device signed in
    return resp


# ------------------------------------------------------------- products ----
def _product_form(name: str = Form(""), slug: str = Form(""), description: str = Form(""),
                  category: str = Form(""), subcategory: str = Form(""), price: str = Form(""),
                  sizes: str = Form(""), colors: str = Form(""), image_url: str = Form(""),
                  photos: str = Form(""), in_stock: str = Form(""),
                  sold_out: list[str] = Form([]), sold_out_colors: str = Form("")) -> dict:
    return {"name": name, "slug": slug, "description": description, "category": category,
            "subcategory": subcategory, "price": price, "sizes": sizes, "colors": colors,
            "image_url": image_url, "photos": photos, "in_stock": bool(in_stock),
            "sold_out": sold_out, "sold_out_colors": sold_out_colors}


@router.get("/products", response_class=HTMLResponse)
def products(msg: str | None = None):
    return ui.products_page(data.list_products(), msg=MSGS.get(msg or ""))


@router.get("/products/new", response_class=HTMLResponse)
def product_new():
    return ui.product_form_page(data.blank_product_form(), CATEGORIES, SUBCATEGORIES)


@router.post("/products/new")
def product_create(form: dict = Depends(_product_form)):
    row, error = data.build_product_row(form, creating=True)
    if not error:
        try:
            data.insert_product(row)
        except Exception as e:
            error = data.friendly_db_error(e)
    if error:
        return HTMLResponse(ui.product_form_page(form, CATEGORIES, SUBCATEGORIES, error=error), status_code=400)
    return _go("/admin/products", "created")


@router.get("/products/{pid}", response_class=HTMLResponse)
def product_edit(pid: UUID, msg: str | None = None):
    p = data.get_product(str(pid))
    if not p:
        raise HTTPException(404)
    return ui.product_form_page(data.product_to_form(p), CATEGORIES, SUBCATEGORIES,
                                product_id=str(pid), msg=MSGS.get(msg or ""))


@router.post("/products/{pid}")
def product_save(pid: UUID, form: dict = Depends(_product_form)):
    if not data.get_product(str(pid)):
        raise HTTPException(404)
    row, error = data.build_product_row(form, creating=False)
    if not error:
        try:
            data.update_product(str(pid), row)
        except Exception as e:
            error = data.friendly_db_error(e)
    if error:
        form["slug"] = (data.get_product(str(pid)) or {}).get("slug", "")
        return HTMLResponse(ui.product_form_page(form, CATEGORIES, SUBCATEGORIES,
                                                 error=error, product_id=str(pid)), status_code=400)
    return _go(f"/admin/products/{pid}", "saved")


@router.post("/products/{pid}/visibility")
def product_visibility(pid: UUID, visible: str = Form("")):
    data.set_visible(str(pid), visible == "1")
    return _go("/admin/products", "updated")


@router.post("/products/{pid}/delete")
def product_delete(pid: UUID):
    data.soft_delete("products", str(pid))
    return _go("/admin/products", "deleted")


# ---------------------------------------------------------- photo upload ----
@router.post("/upload")
def upload(file: UploadFile = File(...), folder: str = Form("uploads")):
    try:
        url = data.upload_image(folder, file.filename or "photo", file.file.read(), file.content_type or "")
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": "Upload failed: " + str(e)[:160]}, status_code=500)
    return {"url": url}


@router.post("/upload/delete")
def upload_delete(url: str = Form("")):
    try:
        data.delete_photo_if_unused(url)
    except Exception:
        pass
    return {"ok": True}


# --------------------------------------------------------------- orders ----
@router.get("/orders", response_class=HTMLResponse)
def orders(q: str | None = None, view: str | None = None, msg: str | None = None):
    if view not in [k for k, _ in data.ORDER_VIEWS]:
        view = "all" if q else "active"  # a search from Customers looks in every tab
    return ui.orders_page(data.filter_orders(data.list_orders(q), view), q or "",
                          msg=MSGS.get(msg or ""), view=view)


@router.post("/orders/{oid}/status")
def order_status(oid: UUID, status: str = Form(...), payment_status: str = Form(""),
                 q: str = Form(""), view: str = Form("")):
    data.update_order_status(str(oid), status, payment_status)
    return _go("/admin/orders", "updated", q=q, view=view)


@router.post("/orders/{oid}/delete")
def order_delete(oid: UUID, q: str = Form(""), view: str = Form("")):
    data.soft_delete("orders", str(oid))
    return _go("/admin/orders", "deleted", q=q, view=view)


# ------------------------------------------------------------ customers ----
@router.get("/customers", response_class=HTMLResponse)
def customers(q: str | None = None):
    return ui.customers_page(data.list_customers(q), q or "")





# ------------------------------------------------------ recently deleted ----
@router.get("/deleted", response_class=HTMLResponse)
def deleted(msg: str | None = None):
    try:
        data.purge_expired()  # anything older than the retention window goes for good
    except Exception:
        pass
    return ui.deleted_page(data.list_deleted(), data.RETENTION_DAYS, msg=MSGS.get(msg or ""))


@router.post("/deleted/{kind}/{rid}/restore")
def deleted_restore(kind: str, rid: UUID):
    data.restore(_kind(kind), str(rid))
    return _go("/admin/deleted", "restored")


@router.post("/deleted/{kind}/{rid}/purge")
def deleted_purge(kind: str, rid: UUID):
    data.purge(_kind(kind), str(rid))
    return _go("/admin/deleted", "purged")
from routers import admin_promotions  # noqa: E402
router.include_router(admin_promotions.router)
from routers import admin_earnings  # noqa: E402
router.include_router(admin_earnings.router)
