"""Loomex admin: the Earnings screen."""
from html import escape

from templates_admin import admin_page

CSS = """
<style>
.er-bar{display:flex;gap:10px;align-items:center;margin:0 0 14px;flex-wrap:wrap;}
.er-bar input[type=month]{background:var(--ink-raised);color:var(--paper);border:1px solid var(--line);padding:10px 12px;font:inherit;}
.er-sum{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:0 0 16px;}
.er-box{border:1px solid var(--line);background:var(--ink-raised);padding:12px 14px;}
.er-box small{display:block;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--paper-dim);}
.er-box b{display:block;margin-top:4px;font-size:20px;}
.er-box.gold b{color:var(--gold);}
.er-row{border:1px solid var(--line);background:var(--ink-raised);padding:12px 14px;margin:0 0 8px;}
.er-top{display:flex;justify-content:space-between;gap:10px;font-size:13.5px;font-weight:600;}
.er-top span{color:var(--paper-dim);font-weight:400;}
.er-in{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px;}
.er-in label{font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--paper-dim);}
.er-in input{width:100%;margin-top:4px;background:var(--ink);color:var(--paper);border:1px solid var(--line);padding:10px;font:inherit;}
.er-left{margin-top:8px;font-size:12px;color:var(--paper-dim);}
.neg{color:#e5806b;}
</style>
"""

JS = """
<script>
(function () {
  var form = document.getElementById('er-form');
  if (!form) return;
  function n(v) { v = parseFloat(String(v).replace(/,/g, '')); return isNaN(v) ? 0 : v; }
  function fmt(x) { return (Math.round(x * 100) / 100).toLocaleString('en-US', {maximumFractionDigits: 2}); }
  function calc() {
    var my = 0, pt = 0, rev = 0;
    form.querySelectorAll('.er-row').forEach(function (r) {
      var rv = n(r.dataset.rev), a = n(r.querySelector('.my').value), b = n(r.querySelector('.pt').value);
      my += a; pt += b; rev += rv;
      var left = rv - a - b, el = r.querySelector('.er-left b');
      el.textContent = fmt(left) + ' EGP'; el.className = left < -0.005 ? 'neg' : '';
    });
    document.getElementById('t-my').textContent = fmt(my) + ' EGP';
    document.getElementById('t-pt').textContent = fmt(pt) + ' EGP';
    var un = rev - my - pt, u = document.getElementById('t-un');
    u.textContent = fmt(un) + ' EGP'; u.className = un < -0.005 ? 'neg' : '';
  }
  form.addEventListener('input', calc); calc();
})();
</script>
"""


def _m(x: float) -> str:
    s = f"{x:,.2f}"
    return (s.rstrip("0").rstrip(".") if "." in s else s) + " EGP"


def _row(r: dict) -> str:
    oid = escape(r["id"])
    my = f"{r['my']:g}" if r["my"] else ""
    pt = f"{r['partner']:g}" if r["partner"] else ""
    return f"""<div class="er-row" data-rev="{r['revenue']}">
<div class="er-top"><div>{escape(r['number'])} <span>· {escape(r['customer'])} · {escape(r['date'])}</span></div><div>{_m(r['revenue'])}</div></div>
<div class="er-in">
<div><label>My share</label><input class="my" type="number" step="0.01" min="0" inputmode="decimal" name="my_{oid}" value="{my}" placeholder="0"></div>
<div><label>Partner share</label><input class="pt" type="number" step="0.01" min="0" inputmode="decimal" name="partner_{oid}" value="{pt}" placeholder="0"></div>
</div>
<div class="er-left">Not assigned: <b></b></div></div>"""


def earnings_page(d: dict, msg: str | None = None, error: str | None = None) -> str:
    err = f'<div class="err"><strong>{escape(error)}</strong></div>' if error else ""
    month = escape(d["month"])
    rows = "".join(_row(r) for r in d["rows"])
    if rows:
        listing = (f'<form method="post" action="/admin/earnings" id="er-form">'
                   f'<input type="hidden" name="month" value="{month}">{rows}'
                   f'<button class="btn" style="width:100%">Save shares</button></form>')
    else:
        listing = '<div class="empty">No orders in this month.</div>'
    body = f"""{CSS}<div class="head"><div><h1>Earnings</h1></div></div>
<p class="hint">Amounts are each order's total after discounts, without shipping. Cancelled and deleted orders are left out.</p>
<form method="get" action="/admin/earnings" class="er-bar">
<input type="month" name="month" value="{month}" onchange="this.form.submit()">
<button class="btn sm ghost">Show</button></form>
{err}
<div class="er-sum">
<div class="er-box"><small>From orders</small><b>{_m(d['revenue'])}</b></div>
<div class="er-box gold"><small>My total</small><b id="t-my">{_m(d['my'])}</b></div>
<div class="er-box"><small>Partner total</small><b id="t-pt">{_m(d['partner'])}</b></div>
<div class="er-box"><small>Not assigned</small><b id="t-un">{_m(d['unassigned'])}</b></div>
</div>
{listing}{JS if rows else ""}"""
    return admin_page("Earnings", body, "earnings", msg)
