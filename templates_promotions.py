"""Loomex admin: the Promotions screen (new / edit form and the list of promotions).
Same dark and gold look as the rest of the Loomex admin, laid out like the Moon promotions screen."""

import json
from html import escape

from services.promotions import DISCOUNT_TYPES, VALUE_LABELS, describe, promo_state
from templates_admin import _dt, admin_page

PROMO_CSS = """
<style>
.pm-lead{color:var(--paper-dim);font-size:13px;line-height:1.55;margin:0 0 8px;max-width:62ch;}
.pm-key{font-size:12px;color:var(--paper-dim);margin:0 0 16px;}
.rq{color:#e5806b;font-weight:700;margin-left:3px;}
.pm-opt{color:var(--paper-dim);text-transform:none;letter-spacing:0;font-weight:400;margin-left:6px;}
.pm-bar{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:0 0 12px;}
.pm-bar h2{margin:0;font-family:"Big Shoulders Display",sans-serif;font-size:24px;text-transform:uppercase;}
.pm-count{font-size:12px;color:var(--paper-dim);border:1px solid var(--line);border-radius:999px;padding:5px 12px;white-space:nowrap;}
.pm-tools{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px;}
.pm-pick{display:grid;grid-template-columns:1fr 1fr;gap:8px;max-height:290px;overflow-y:auto;padding:10px;border:1px solid var(--line);background:var(--ink);}
.pm-prod,.pm-type{position:relative;display:flex;align-items:center;gap:10px;padding:11px 12px;border:1px solid var(--line);
  background:var(--ink-raised);cursor:pointer;font-size:13.5px;font-weight:600;line-height:1.3;word-break:break-word;}
.pm-prod input,.pm-type input,.pm-tog input{position:absolute;opacity:0;pointer-events:none;}
.pm-dot{flex:0 0 18px;width:18px;height:18px;border-radius:50%;border:1.5px solid var(--paper-dim);}
.pm-prod input:checked ~ .pm-dot,.pm-type input:checked ~ .pm-dot{border-color:var(--gold);background:radial-gradient(var(--gold) 0 45%,transparent 50%);}
.pm-prod:has(input:checked),.pm-type:has(input:checked){border-color:var(--gold);}
.pm-types{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px;}
.pm-hint{min-height:18px;margin:-4px 0 16px;color:var(--paper-dim);font-size:12.5px;line-height:1.5;}
.pm-dfield[hidden],.pm-hide[hidden]{display:none;}
.pm-tog{position:relative;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 14px;
  border:1px solid var(--line);background:var(--ink);cursor:pointer;}
.pm-tog b{display:block;font-size:14px;}
.pm-tog small{display:block;margin-top:2px;color:var(--paper-dim);font-size:12px;font-weight:400;line-height:1.4;}
.pm-sw{flex:0 0 46px;width:46px;height:26px;border-radius:999px;border:1px solid var(--line);background:rgba(241,236,226,.12);position:relative;transition:background .15s;}
.pm-sw::after{content:"";position:absolute;top:2px;left:2px;width:20px;height:20px;border-radius:50%;background:var(--paper-dim);transition:transform .15s,background .15s;}
.pm-tog input:checked ~ .pm-sw{background:var(--gold);border-color:var(--gold);}
.pm-tog input:checked ~ .pm-sw::after{transform:translateX(20px);background:var(--ink);}
.pm-chips{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:10px 0;}
.pm-chips .k2{font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--paper-dim);margin-right:4px;}
.pm-chip{padding:4px 10px;border:1px solid var(--gold-dim);border-radius:999px;font-size:12px;color:var(--gold);}
.pm-chip.more{border-color:var(--line);color:var(--paper-dim);}
.pm-line{margin:4px 0 0;font-size:12.5px;color:var(--paper-dim);line-height:1.5;}
.pm-line b{color:var(--paper);font-weight:600;}
.pm-foot{display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding:10px 14px;border-top:1px solid var(--line);}
.pm-foot form{margin:0;}
.pm-foot .pm-del{margin-left:auto;}
@media(max-width:560px){.pm-pick,.pm-types{grid-template-columns:1fr;}}
</style>
"""

PROMO_JS = """
<script>
(function () {
  var TYPES = __TYPES__, LABELS = __LABELS__;
  var form = document.getElementById('pm-form');
  if (!form) return;

  /* products: pick some, or none (= all products) */
  var boxes = form.querySelectorAll('.pm-prod input'), count = document.getElementById('pm-count');
  function upd() {
    var n = 0; boxes.forEach(function (b) { if (b.checked) n++; });
    count.textContent = n + ' of ' + boxes.length + ' selected';
  }
  document.getElementById('pm-all').addEventListener('click', function () {
    var all = Array.prototype.every.call(boxes, function (b) { return b.checked; });
    boxes.forEach(function (b) { b.checked = !all; }); upd();
  });
  boxes.forEach(function (b) { b.addEventListener('change', upd); }); upd();

  /* banner link: custom address box */
  var sel = document.getElementById('pm-link'), custom = document.getElementById('pm-custom');
  function link() {
    var on = sel.value === '__custom';
    custom.hidden = !on; custom.querySelector('input').required = on;
  }
  function autoPick() {
    var v = sel.value, isCat = v.indexOf('/shop?category=') === 0;
    if (v !== '/shop' && !isCat) return;   /* custom / no link: leave the picks alone */
    var cat = isCat ? decodeURIComponent(v.slice(15)) : null;
    boxes.forEach(function (b) {
      b.checked = !cat || b.closest('.pm-prod').dataset.cat === cat;
    });
    upd();
  }
  sel.addEventListener('change', function () { link(); autoPick(); }); link();

  /* discount type: show only the boxes this type needs, mark required / optional */
  var radios = form.querySelectorAll('input[name=discount_type]'), fields = form.querySelectorAll('.pm-dfield');
  function mark(f, req) {
    f.querySelector('.pm-mark').innerHTML = req ? '<span class="rq">*</span>' : '<span class="pm-opt">(optional)</span>';
  }
  function type() {
    var cur = ''; radios.forEach(function (r) { if (r.checked) cur = r.value; });
    var t = TYPES[cur];
    fields.forEach(function (f) {
      var name = f.dataset.field, need = t && t.needs.indexOf(name) >= 0, opt = t && t.optional.indexOf(name) >= 0;
      f.hidden = !(need || opt);
      f.querySelector('input').required = !!need;
      if (need || opt) mark(f, !!need);
      if (name === 'value' && LABELS[cur]) f.querySelector('.pm-lab').textContent = LABELS[cur];
    });
    document.getElementById('pm-hint').textContent = t ? t.hint : 'Pick what this promotion does.';
  }
  radios.forEach(function (r) { r.addEventListener('change', type); }); type();
})();
</script>
"""


def _req():
    return '<span class="rq">*</span>'


def _opt():
    return '<span class="pm-opt">(optional)</span>'


def _link_options(categories: list, current: str) -> str:
    opts = [("/shop", "Shop — all products")]
    opts += [(f"/shop?category={c}", f"Shop — {c.replace('-', ' ').title()}") for c in categories]
    opts += [("__custom", "Custom link…"), ("__none", "No link (not tappable)")]
    return "".join(f'<option value="{escape(v)}"{" selected" if v == current else ""}>{escape(l)}</option>' for v, l in opts)


def _form(f: dict, picker: list, categories: list, editing_id: str | None) -> str:
    selected = {str(x) for x in (f.get("product_ids") or [])}
    cur_type = f.get("discount_type") or ""
    products = "".join(
        f'<label class="pm-prod" data-cat="{escape(str(p.get("category") or ""))}"><input type="checkbox" name="product_ids" value="{escape(str(p["id"]))}"'
        f'{" checked" if str(p["id"]) in selected else ""}><span class="pm-dot"></span><span>{escape(p["name"])}</span></label>'
        for p in picker) or '<p class="hint" style="grid-column:1/-1;margin:0">No products yet.</p>'
    types = "".join(
        f'<label class="pm-type"><input type="radio" name="discount_type" value="{k}" required'
        f'{" checked" if cur_type == k else ""}><span class="pm-dot"></span><span>{escape(label)}</span></label>'
        for k, label, _, _, _ in DISCOUNT_TYPES)

    def num(name, step, mn):
        return f'<input type="number" name="{name}" step="{step}" min="{mn}" value="{escape(str(f.get(name) or ""))}" inputmode="decimal">'

    def field(name, label, inner):
        return (f'<div class="fg pm-dfield" data-field="{name}" hidden><label class="f">'
                f'<span class="pm-lab">{label}</span><span class="pm-mark"></span></label>{inner}</div>')

    dfields = (
        field("value", "Value", num("value", "0.01", "0"))
        + field("min_qty", "Number of items (N)", num("min_qty", "1", "1"))
        + field("min_spend", "Minimum spend (EGP)", num("min_spend", "0.01", "0"))
        + field("gift_text", "Free gift", f'<input type="text" name="gift_text" maxlength="120" value="{escape(f.get("gift_text") or "")}" placeholder="e.g. Loomex tote bag">')
    )
    action = f"/admin/promotions/{editing_id}" if editing_id else "/admin/promotions/new"
    verb = "Save changes" if editing_id else "Add promotion"
    return f"""<form method="post" action="{action}" id="pm-form">
<section class="sect"><div class="sect-h"><b>1</b><h2>Basics</h2></div><div class="sect-b">
<div class="fg"><label class="f">Title {_req()}</label>
<input type="text" name="title" maxlength="160" required value="{escape(f.get('title') or '')}" placeholder="Buy 1 Get 1 Free"></div>
<div class="fg"><label class="f">Subtitle {_opt()}</label>
<input type="text" name="subtitle" maxlength="160" value="{escape(f.get('subtitle') or '')}" placeholder="On all hoodies, this week only"></div>
<div class="fg"><label class="f">Banner links to {_opt()}</label>
<select name="link_choice" id="pm-link">{_link_options(categories, f.get('link_choice') or '/shop')}</select>
<div class="pm-hide" id="pm-custom" hidden style="margin-top:8px"><input type="text" name="link_url" value="{escape(f.get('link_url') or '')}" placeholder="/shop?category=pants or https://..."></div></div>
</section>

<section class="sect"><div class="sect-h"><b>2</b><h2>Products</h2></div><div class="sect-b">
<p class="hint" style="margin:0 0 10px">{_opt()} Pick the products this applies to. Pick none and it applies to every product.</p>
<div class="pm-tools"><button type="button" class="btn sm ghost" id="pm-all">+ All products</button><span class="pm-count" id="pm-count">0 of 0 selected</span></div>
<div class="pm-pick">{products}</div>
</div></section>

<section class="sect"><div class="sect-h"><b>3</b><h2>Discount</h2></div><div class="sect-b">
<label class="f">Type {_req()}</label>
<div class="pm-types">{types}</div>
<p class="pm-hint" id="pm-hint"></p>
{dfields}
<p class="hint" style="margin:0">If several promotions match a cart, the customer gets the single biggest money discount (they do not add up). Free shipping and free gifts still apply.</p>
</div></section>

<section class="sect"><div class="sect-h"><b>4</b><h2>Schedule</h2></div><div class="sect-b">
<div class="two"><div class="fg"><label class="f">Starts {_opt()}</label><input type="date" name="starts" value="{escape(f.get('starts') or '')}"></div>
<div class="fg"><label class="f">Ends {_opt()}</label><input type="date" name="ends" value="{escape(f.get('ends') or '')}"></div></div>
<p class="hint" style="margin:-6px 0 16px">Empty Starts = starts now. Empty Ends = runs until you deactivate it. The end date includes that whole day.</p>
<label class="pm-tog"><input type="checkbox" name="show_banner" value="1"{" checked" if f.get("show_banner") else ""}>
<span><b>Show on homepage banner</b><small>Customers can tap it above the site navigation.</small></span><span class="pm-sw"></span></label>
</div></section>
<button class="btn" style="width:100%">{verb}</button>
</form>"""


def _card(p: dict, names: dict) -> str:
    state = promo_state(p)
    badge = {"live": ("Active", "ok"), "scheduled": ("Scheduled", ""), "ended": ("Ended", ""), "off": ("Inactive", "")}[state]
    type_label = next((t[1] for t in DISCOUNT_TYPES if t[0] == p.get("discount_type")), "Banner only")
    ids = [str(i) for i in (p.get("product_ids") or [])]
    shown = [names[i] for i in ids if i in names]
    if names and len(shown) >= len(names):
        shown = []  # covers every product: show 'All products' instead of the list
    if shown:
        chips = "".join(f'<span class="pm-chip">{escape(n)}</span>' for n in shown[:3])
        if len(shown) > 3:
            chips += f'<span class="pm-chip more">+{len(shown) - 3} more</span>'
    else:
        chips = '<span class="pm-chip all">All products</span>'
    dates = " → ".join(x for x in [
        _dt(p.get("starts_at")).split(",")[0] if p.get("starts_at") else "",
        _dt(p.get("ends_at")).split(",")[0] if p.get("ends_at") else ""] if x)
    code = f'<p class="pm-line">Code: <b>{escape(p["code"])}</b></p>' if p.get("code") else ""
    sub = f'<p class="s" style="margin-top:2px">{escape(p["subtitle"])}</p>' if p.get("subtitle") else ""
    on_banner = p.get("show_banner") is not False
    banner = "On homepage banner" if on_banner else "Not on homepage banner"
    pid = p["id"]
    return f"""<div class="pc st-{state}"><div class="pc-band"><span class="k">{escape(type_label)}</span><span class="badge {badge[1]}">{badge[0]}</span></div>
<div class="pc-body"><p class="t" style="font-size:17px">{escape(p['message'])}</p>{sub}
<div class="pm-chips"><span class="k2">Applies to</span>{chips}</div>
<p class="pm-line"><b>{escape(describe(p))}</b></p>{code}
<p class="pm-line">{escape(dates) or 'No dates set'}</p><p class="pm-line">{banner}</p></div>
<div class="pm-foot">
<a class="btn sm ghost" href="/admin/promotions/{pid}/edit">Edit</a>
<form method="post" action="/admin/promotions/{pid}/toggle"><button class="btn sm ghost">{"Deactivate" if p.get("is_active") else "Activate"}</button></form>
<form method="post" action="/admin/promotions/{pid}/banner"><button class="btn sm ghost">{"Hide from banner" if on_banner else "Show on banner"}</button></form>
<form method="post" action="/admin/promotions/{pid}/delete" class="pm-del" onsubmit="return confirm('Move this promotion to Recently Deleted?')"><button class="link">Delete</button></form>
</div></div>"""


def promotions_page(promos: list, picker: list, categories: list, msg: str | None = None,
                    error: str | None = None, form: dict | None = None,
                    editing_id: str | None = None, show_form: bool = False) -> str:
    names = {str(p["id"]): p["name"] for p in picker}
    err = f'<div class="err"><strong>{escape(error)}</strong></div>' if error else ""
    if show_form:
        top = '<a class="btn sm ghost" href="/admin/promotions">Cancel</a>'
        heading = f'<div class="pm-bar"><h2>{"Edit promotion" if editing_id else "New promotion"}</h2></div>'
        form_html = heading + err + _form(form or {}, picker, categories, editing_id)
    else:
        top = '<a class="btn" href="/admin/promotions?new=1">+ New promotion</a>'
        form_html = err
    cards = "".join(_card(p, names) for p in promos) or '<div class="empty">No promotions yet.</div>'
    types_json = json.dumps({k: {"needs": list(n), "optional": list(o), "hint": h} for k, _, n, o, h in DISCOUNT_TYPES})
    js = PROMO_JS.replace("__TYPES__", types_json).replace("__LABELS__", json.dumps(VALUE_LABELS)) if show_form else ""
    body = f"""{PROMO_CSS}<div class="head"><div><h1>Promotions</h1></div>{top}</div>
<p class="pm-lead">Active promotions marked "Show on homepage banner" appear as a banner customers can tap, above the site navigation.
If you pick products, their discounted price also shows directly on the shop page.</p>
<p class="pm-key">{_req()} Required</p>
{form_html}
{'<h2 class="sec">Your promotions<small>' + str(len(promos)) + '</small></h2>' if show_form else ''}{cards}{js}"""
    return admin_page("Promotions", body, "promotions", msg)