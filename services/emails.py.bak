"""Order confirmation emails, sent through Resend."""
import os
from html import escape

import resend

from config import DELIVERY_TIME_TEXT, PAYMENT_METHODS

EMAIL_FROM = "Loomex <orders@loomexclothing.com>"
REPLY_TO = "loomex.co@gmail.com"
SITE = "https://www.loomexclothing.com"
INSTAGRAM = "https://www.instagram.com/loomex_clothing"

BG, CARD, BORDER = "#12100d", "#1e1a16", "#2f2923"
CREAM, MUTED, GOLD = "#f1ece2", "#9b9183", "#c19a57"
HEAD_FONT = "'Arial Narrow', Impact, Arial, Helvetica, sans-serif"
BODY_FONT = "Arial, Helvetica, sans-serif"
MONO_FONT = "'SF Mono', Menlo, Consolas, 'Courier New', monospace"


def _money(x) -> str:
    return f"{float(x or 0):.0f} EGP"


def _label(text: str) -> str:
    return (f'<div style="font-family:{BODY_FONT};font-size:11px;letter-spacing:2.5px;text-transform:uppercase;'
            f'color:{GOLD};font-weight:700;margin:0 0 10px;">{text}</div>')


def _summary(order: dict) -> dict:
    items = order.get("items") or []
    return {
        "items": items,
        "subtotal": sum(float(i.get("unit_price") or 0) * int(i.get("quantity") or 0) for i in items),
        "discount": float(order.get("discount") or 0),
        "shipping": float(order.get("shipping") or 0),
        "total": float(order.get("total") or 0),
        "number": str(order.get("order_number") or ""),
        "pay": PAYMENT_METHODS.get(order.get("payment_method") or "", {}).get("label", "Cash on Delivery"),
    }


def build_confirmation_html(order: dict) -> str:
    s = _summary(order)
    first = escape((order.get("customer_name") or "").split(" ")[0] or "there")
    number = escape(s["number"])

    # items
    rows = ""
    for i in s["items"]:
        variant = " · ".join(v for v in [i.get("size"), i.get("color")] if v)
        qty = int(i.get("quantity") or 0)
        sub = (variant + " · " if variant else "") + f"Qty {qty}"
        name = escape(str(i.get("product_name") or ""))
        price = _money(float(i.get("unit_price") or 0) * qty)
        rows += (f'<tr><td style="padding:14px 0;border-bottom:1px solid {BORDER};">'
                 f'<div style="font-family:{BODY_FONT};font-size:15px;font-weight:700;color:{CREAM};">{name}</div>'
                 f'<div style="font-family:{BODY_FONT};font-size:12px;color:{MUTED};margin-top:3px;">{escape(sub)}</div></td>'
                 f'<td align="right" style="padding:14px 0;border-bottom:1px solid {BORDER};'
                 f'font-family:{BODY_FONT};font-size:15px;color:{CREAM};white-space:nowrap;">{price}</td></tr>')

    def line(label, value, color=MUTED):
        return (f'<tr><td style="padding:5px 0;font-family:{BODY_FONT};font-size:14px;color:{color};">{label}</td>'
                f'<td align="right" style="padding:5px 0;font-family:{BODY_FONT};font-size:14px;color:{CREAM};">{value}</td></tr>')

    totals = line("Subtotal", _money(s["subtotal"]))
    if s["discount"] > 0:
        totals += line("Discount", "&minus;" + _money(s["discount"]), GOLD)
    totals += line("Shipping", "Free" if s["shipping"] == 0 else _money(s["shipping"]))

    delivery = ""
    if (DELIVERY_TIME_TEXT or "").strip():
        delivery = (f'<table width="100%" cellpadding="0" cellspacing="0" style="margin-top:22px;"><tr>'
                    f'<td style="border:1px solid {GOLD};border-radius:12px;padding:14px 16px;'
                    f'font-family:{BODY_FONT};font-size:14px;font-weight:700;color:{GOLD};">'
                    f'{escape(DELIVERY_TIME_TEXT.strip())}</td></tr></table>')

    notes = ""
    if order.get("delivery_notes"):
        notes = (f'<div style="font-family:{BODY_FONT};font-size:13px;color:{MUTED};margin-top:10px;">'
                 f'Notes: <span style="color:{CREAM};">{escape(order["delivery_notes"])}</span></div>')

    address = "<br>".join(escape(str(x)) for x in [
        order.get("customer_name") or "", order.get("address") or "",
        (order.get("city") or "") + ", Egypt", order.get("phone") or ""] if x)

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light only"><meta name="supported-color-schemes" content="light only">
<style>:root {{ color-scheme: light only; supported-color-schemes: light only; }}</style>
<title>Your Loomex order {number}</title></head>
<body bgcolor="#ffffff" style="margin:0;padding:0;background:#ffffff;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:#ffffff;">We received your order {number}. Total {_money(s["total"])}.</div>
<table width="100%" cellpadding="0" cellspacing="0" bgcolor="#ffffff" style="background:#ffffff;background-image:linear-gradient(#ffffff,#ffffff);"><tr><td align="center" style="padding:20px 12px;">
<table width="100%" cellpadding="0" cellspacing="0" bgcolor="{BG}" style="max-width:560px;background:{BG};background-image:linear-gradient({BG},{BG});border-radius:24px;">

  <tr><td align="center" style="padding:38px 0 24px;">
    <div style="font-family:{HEAD_FONT};font-size:34px;font-weight:700;letter-spacing:10px;color:{CREAM};">LOOM<span style="color:{GOLD};">EX</span></div>
    <div style="width:44px;height:2px;background:{GOLD};margin:12px auto 0;font-size:0;line-height:0;">&nbsp;</div>
  </td></tr>

  <tr><td style="padding:0 14px;"><table width="100%" cellpadding="0" cellspacing="0"><tr><td bgcolor="{CARD}" style="background:{CARD};background-image:linear-gradient({CARD},{CARD});border:1px solid {BORDER};border-radius:18px;padding:34px 26px;">

    <div style="font-family:{BODY_FONT};font-size:11px;letter-spacing:3px;text-transform:uppercase;color:{GOLD};font-weight:700;">Order received</div>
    <div style="font-family:{HEAD_FONT};font-size:40px;line-height:1.05;font-weight:700;text-transform:uppercase;color:{CREAM};margin:10px 0 12px;">Thank you,<br>{first}.</div>
    <div style="font-family:{BODY_FONT};font-size:14px;line-height:1.6;color:{MUTED};">We've got your order and we're getting it ready for you.</div>

    <table width="100%" cellpadding="0" cellspacing="0" style="margin:26px 0;"><tr>
      <td align="center" style="border:1px dashed {GOLD};border-radius:14px;padding:18px 10px;">
        <div style="font-family:{BODY_FONT};font-size:10px;letter-spacing:3px;text-transform:uppercase;color:{MUTED};">Order number</div>
        <div style="font-family:{MONO_FONT};font-size:26px;font-weight:700;letter-spacing:3px;color:{GOLD};margin-top:6px;">{number}</div>
      </td></tr></table>

    {_label("Your items")}
    <table width="100%" cellpadding="0" cellspacing="0">{rows}</table>
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:10px;">{totals}
      <tr><td style="padding:14px 0 0;border-top:1px solid {GOLD};font-family:{HEAD_FONT};font-size:20px;letter-spacing:2px;text-transform:uppercase;font-weight:700;color:{CREAM};">Total</td>
          <td align="right" style="padding:14px 0 0;border-top:1px solid {GOLD};font-family:{HEAD_FONT};font-size:24px;font-weight:700;color:{GOLD};">{_money(s["total"])}</td></tr>
    </table>

    <div style="height:30px;font-size:0;line-height:0;">&nbsp;</div>
    {_label("Delivering to")}
    <div style="font-family:{BODY_FONT};font-size:14px;line-height:1.7;color:{CREAM};">{address}</div>
    {notes}

    <div style="height:22px;font-size:0;line-height:0;">&nbsp;</div>
    {_label("Payment")}
    <div style="font-family:{BODY_FONT};font-size:14px;color:{CREAM};">{escape(s["pay"])}</div>
    {delivery}

    <table cellpadding="0" cellspacing="0" style="margin:30px auto 0;"><tr>
      <td bgcolor="{GOLD}" style="background:{GOLD};border-radius:999px;">
        <a href="{SITE}/shop" style="display:inline-block;padding:14px 34px;font-family:{BODY_FONT};font-size:13px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#201c18;text-decoration:none;">Keep shopping</a>
      </td></tr></table>
  </td></tr></table></td></tr>

  <tr><td align="center" style="padding:26px 10px 38px;">
    <div style="font-family:{HEAD_FONT};font-size:18px;letter-spacing:4px;text-transform:uppercase;color:{CREAM};">Thank you for choosing Loomex.</div>
    <div style="font-family:{BODY_FONT};font-size:12px;line-height:1.7;color:{MUTED};margin-top:12px;">
      Questions about your order? Message us on <a href="{INSTAGRAM}" style="color:{GOLD};text-decoration:none;">Instagram @loomex_clothing</a>.</div>
  </td></tr>
</table></td></tr></table></body></html>"""


def build_confirmation_text(order: dict) -> str:
    s = _summary(order)
    lines = [f"Thank you for your Loomex order!", f"Order number: {s['number']}", ""]
    for i in s["items"]:
        variant = " / ".join(v for v in [i.get("size"), i.get("color")] if v)
        qty = int(i.get("quantity") or 0)
        lines.append(f"- {i.get('product_name')} ({variant}) x{qty}: {_money(float(i.get('unit_price') or 0) * qty)}")
    lines += ["", f"Shipping: {'Free' if s['shipping'] == 0 else _money(s['shipping'])}",
              f"Total: {_money(s['total'])}", f"Payment: {s['pay']}", "",
              f"Delivering to: {order.get('address')}, {order.get('city')}", "",
              "Questions? Message us on Instagram @loomex_clothing"]
    return "\n".join(lines)


def send_order_confirmation(order: dict) -> bool:
    """Returns True if Resend accepted the email. Never raises."""
    key = os.environ.get("RESEND_API_KEY")
    to = (order.get("email") or "").strip()
    if not key or not to:
        return False
    try:
        resend.api_key = key
        resend.Emails.send({
            "from": EMAIL_FROM,
            "reply_to": REPLY_TO,
            "to": [to],
            "subject": f"We received your order {order.get('order_number', '')}",
            "html": build_confirmation_html(order),
            "text": build_confirmation_text(order),
        })
        return True
    except Exception as e:
        print("Order email failed:", e)
        return False
