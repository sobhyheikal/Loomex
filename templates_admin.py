"""Loomex admin panel HTML. Standalone: it does not use the storefront layout."""

import json
from datetime import datetime, timezone
from html import escape

from config import PAYMENT_METHODS
from services.admin_data import ADMIN_TZ, ORDER_STATUSES, ORDER_VIEWS, PAYMENT_STATUSES, parse_photos
from services.promotions import _parse, promo_state
from templates import FONTS

NAV = [("home", "Home"), ("orders", "Orders"), ("products", "Products"), ("customers", "Customers"),
       ("promotions", "Promotions"), ("profile", "Profile")]

ADMIN_CSS = """
<style>
:root{--ink:#201c18;--ink-raised:#2a241e;--stone:#e7e2d6;--paper:#f1ece2;--paper-dim:#b9b2a4;
  --gold:#c79a46;--gold-dim:#8f7239;--teal:#4f6d6a;--line:rgba(241,236,226,.14);}
*{box-sizing:border-box;}
[hidden]{display:none !important;}
html,body{margin:0;background:var(--ink);color:var(--paper);font-family:"Inter",-apple-system,sans-serif;
  -webkit-font-smoothing:antialiased;}
a{color:inherit;text-decoration:none;}
.top{position:sticky;top:0;z-index:10;background:var(--ink);border-bottom:1px solid var(--line);}
.top-in{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;max-width:980px;margin:0 auto;padding:10px 18px;}
.logo{font-family:"Big Shoulders Display",sans-serif;font-weight:700;font-size:22px;letter-spacing:.12em;}
.logo span{color:var(--gold);} .logo small{font-family:Inter,sans-serif;font-size:11px;letter-spacing:.16em;
  color:var(--paper-dim);margin-left:10px;text-transform:uppercase;}
.am-toggle{display:none;}
.am-btn{display:flex;flex-direction:column;justify-content:center;gap:6px;width:24px;padding:10px 8px 10px 0;cursor:pointer;justify-self:start;}
.am-btn span{width:100%;height:1.5px;background:var(--paper);display:block;}
.am-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.5);opacity:0;pointer-events:none;transition:opacity .2s ease;z-index:29;}
.am-drawer{position:fixed;top:0;left:0;bottom:0;width:78%;max-width:300px;background:var(--ink);border-right:1px solid var(--line);
  z-index:30;transform:translateX(-100%);transition:transform .25s ease;padding:20px 22px 24px;overflow-y:auto;display:flex;flex-direction:column;}
.am-close{display:block;text-align:right;font-size:26px;color:var(--paper-dim);padding:4px 4px 14px;cursor:pointer;}
.am-drawer .dl{display:block;width:100%;text-align:left;background:none;border:none;cursor:pointer;
  font-family:"Big Shoulders Display",sans-serif;font-size:22px;text-transform:uppercase;letter-spacing:.03em;color:var(--paper);padding:10px 0;}
.am-drawer .dl.on{color:var(--gold);}
.am-out{margin:auto 0 0;padding-top:18px;border-top:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;}
.am-out form{margin:0;}
.am-out .dl{color:var(--paper-dim);width:auto;}
.trash{display:flex;align-items:center;padding:8px;color:var(--paper-dim);}
.trash:hover,.trash.on{color:var(--gold);}
.trash svg{width:22px;height:22px;display:block;}
.top .trash{justify-self:end;padding:8px 0 8px 8px;}
.am-toggle:checked ~ .am-drawer{transform:translateX(0);}
.am-toggle:checked ~ .am-backdrop{opacity:1;pointer-events:auto;}
.page{max-width:980px;margin:0 auto;padding:22px 18px 70px;}
h1{font-family:"Big Shoulders Display",sans-serif;font-size:34px;text-transform:uppercase;margin:0 0 4px;line-height:1;}
.sub{color:var(--paper-dim);font-size:13px;margin:0 0 20px;}
.head{display:flex;justify-content:space-between;align-items:flex-end;gap:12px;flex-wrap:wrap;margin-bottom:18px;}
.flash{position:fixed;top:68px;left:50%;transform:translateX(-50%);z-index:40;width:calc(100% - 36px);max-width:420px;
  border:1px solid var(--gold);background:#322a1f;box-shadow:0 8px 24px rgba(0,0,0,.45);padding:12px 16px;font-size:13px;
  text-align:center;transition:opacity .3s ease,transform .3s ease;}
.flash.gone{opacity:0;transform:translateX(-50%) translateY(-8px);pointer-events:none;}
.err{border:1px solid var(--gold);background:rgba(199,154,70,.1);padding:10px 14px;font-size:13px;margin-bottom:16px;}
.err strong{color:var(--gold);}
.btn{display:inline-block;padding:10px 16px;background:var(--gold);color:var(--ink);border:none;font:600 12.5px Inter,sans-serif;
  letter-spacing:.04em;text-transform:uppercase;cursor:pointer;text-align:center;}
.btn:hover{background:var(--gold-dim);}
.btn.sm{padding:7px 12px;font-size:11.5px;}
.btn.ghost{background:transparent;color:var(--paper);border:1px solid var(--paper-dim);}
.btn.ghost:hover{border-color:var(--gold);color:var(--gold);}
.link{background:none;border:none;color:var(--paper-dim);font:12px Inter,sans-serif;text-decoration:underline;cursor:pointer;padding:6px 4px;}
.link:hover{color:var(--gold);}
.row{display:flex;align-items:center;gap:12px;flex-wrap:wrap;background:var(--ink-raised);border:1px solid var(--line);padding:12px 14px;margin-bottom:8px;}
.grow{flex:1 1 200px;min-width:0;}
.t{margin:0 0 3px;font-size:14px;font-weight:600;word-break:break-word;} .s{margin:0;font-size:12.5px;color:var(--paper-dim);}
.thumb{width:46px;height:58px;flex:0 0 auto;background:rgba(128,128,128,.12);} .thumb img{width:100%;height:100%;object-fit:contain;display:block;}
.acts{display:flex;align-items:center;gap:6px;} .acts form{margin:0;}
.badge{display:inline-block;padding:3px 9px;border:1px solid var(--line);border-radius:999px;font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:var(--paper-dim);white-space:nowrap;}
.badge.ok{border-color:var(--gold);color:var(--gold);} .badge.good{border-color:var(--teal);color:var(--paper);background:rgba(79,109,106,.35);}
.search{display:flex;gap:8px;margin-bottom:18px;} .search input{flex:1;}
input[type=text],input[type=search],input[type=password],input[type=number],input[type=date],select,textarea{width:100%;padding:11px 13px;background:var(--ink-raised);
  border:1px solid var(--line);color:var(--paper);font:14px Inter,sans-serif;border-radius:0;}
textarea{min-height:90px;resize:vertical;line-height:1.5;} input:focus,select:focus,textarea:focus{outline:none;border-color:var(--gold);}
label.f{display:block;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--paper-dim);margin:0 0 6px;}
.fg{margin-bottom:16px;} .hint{font-size:12px;color:var(--paper-dim);margin:6px 0 0;line-height:1.5;}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px;} .three{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;}
.card{background:var(--ink-raised);border:1px solid var(--line);padding:18px;margin-bottom:18px;}
.check{display:flex;align-items:center;gap:10px;font-size:14px;} .check input{width:auto;accent-color:var(--gold);}
details.order{background:var(--ink-raised);border:1px solid var(--line);margin-bottom:8px;}
details.order summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:13px 14px;}
details.order summary::-webkit-details-marker{display:none;}
details.order[open] summary{border-bottom:1px solid var(--line);}
.ob{padding:16px 14px;display:grid;gap:18px;} .ob h3{margin:0 0 8px;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);font-weight:600;}
.ob p{margin:0 0 4px;font-size:13.5px;line-height:1.55;color:var(--paper);} .ob p span{color:var(--paper-dim);}
.ob a.u{color:var(--gold);text-decoration:underline;}
.items{width:100%;border-collapse:collapse;font-size:13px;} .items td,.items th{padding:8px 4px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;}
.items th{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--paper-dim);font-weight:500;} .items .r{text-align:right;white-space:nowrap;}
.sum{display:flex;justify-content:space-between;font-size:13.5px;padding:6px 0;} .sum.tot{font-weight:700;border-top:1px solid var(--line);margin-top:4px;padding-top:10px;}
.st{display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end;} .st .fg{margin:0;flex:1 1 140px;}
.empty{padding:36px 10px;text-align:center;color:var(--paper-dim);font-size:14px;}
.sec{font-family:"Big Shoulders Display",sans-serif;font-size:22px;text-transform:uppercase;margin:26px 0 10px;} .sec small{font:12px Inter,sans-serif;color:var(--paper-dim);margin-left:8px;}
.login{max-width:360px;margin:12vh auto;padding:0 18px;text-align:center;} .login .card{text-align:left;margin-top:22px;}
.tabs{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:16px;}
.tab{--c:var(--paper-dim);text-align:center;padding:8px 4px;border:1.5px solid var(--c);border-radius:999px;font-size:11.5px;font-weight:600;color:var(--c);white-space:nowrap;}
.tab.active{--c:#6f9a95;} .tab.cancelled{--c:#b86a6a;} .tab.completed{--c:var(--gold);}
.tab.on{background:var(--c);color:var(--ink);}
.sect{background:var(--ink-raised);border:1px solid var(--line);margin-bottom:14px;}
.sect-h{display:flex;align-items:center;gap:10px;padding:11px 16px;background:rgba(241,236,226,.06);border-bottom:1px solid var(--line);}
.sect-h b{display:flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:50%;background:var(--gold);color:var(--ink);font-size:12px;}
.sect-h h2{margin:0;font-family:"Big Shoulders Display",sans-serif;font-size:19px;font-weight:600;text-transform:uppercase;letter-spacing:.04em;}
.sect-b{padding:16px;}
.pc{background:var(--ink-raised);border:1px solid var(--line);margin-bottom:10px;}
.pc-band{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:9px 14px;background:rgba(241,236,226,.06);}
.pc-band .k{font-size:10.5px;letter-spacing:.18em;text-transform:uppercase;font-weight:600;color:var(--paper-dim);}
.pc-body{padding:14px;}
.pc-foot{display:flex;align-items:center;gap:12px;padding:10px 14px;border-top:1px solid var(--line);}
.pc-foot form{margin:0;}
/* promotions page look */
.pc{border-radius:16px;overflow:hidden;margin-bottom:14px;border-left:4px solid var(--c,var(--paper-dim));box-shadow:0 8px 22px rgba(0,0,0,.22);}
.pc.st-live{--c:var(--gold);}
.pc.st-scheduled{--c:#6f9a95;}
.pc.st-ended,.pc.st-off{--c:var(--paper-dim);}
.pc-band{padding:11px 16px;background:linear-gradient(90deg,rgba(241,236,226,.07),rgba(241,236,226,.02));}
.pc.st-live .pc-band{background:linear-gradient(90deg,rgba(199,154,70,.20),rgba(199,154,70,.04));}
.pc.st-scheduled .pc-band{background:linear-gradient(90deg,rgba(111,154,149,.22),rgba(111,154,149,.05));}
.pc-band .k{color:var(--c);letter-spacing:.2em;}
.pc .pc-band .badge{border-color:var(--c);color:var(--c);font-weight:600;}
.pc.st-live .pc-band .badge{background:var(--gold);color:var(--ink);}
.pc-body{padding:16px;}
.pc-body>.t{font-family:"Big Shoulders Display",sans-serif;font-size:27px!important;letter-spacing:.03em;text-transform:uppercase;line-height:1.05;margin:0 0 4px;}
.pc.st-ended .pc-body>.t,.pc.st-off .pc-body>.t{color:var(--paper-dim);}
.pc-body .pm-chips+.pm-line{margin:12px 0 6px;}
.pc-body .pm-chips+.pm-line b{display:inline-block;padding:6px 14px;border-radius:999px;border:1px solid var(--gold-dim);background:rgba(199,154,70,.14);color:var(--gold);font-size:14px;}
.pc-foot{flex-wrap:wrap;gap:8px 10px;padding:12px 16px;background:rgba(0,0,0,.12);}
.pc-foot .btn.sm{border-radius:999px;padding:8px 14px;}
.pc-foot .pm-del{margin-left:auto;}
.pc-foot .link{color:#b86a6a;}
/* promotion form look */
.pm-chip.all{background:var(--gold);border-color:var(--gold);color:var(--ink);font-weight:700;}
#pm-form .sect{border-radius:18px;overflow:hidden;margin-bottom:16px;border:1px solid var(--line);box-shadow:0 10px 26px rgba(0,0,0,.24);}
#pm-form .sect-h{padding:14px 18px;background:linear-gradient(90deg,rgba(199,154,70,.20),rgba(199,154,70,.03));}
#pm-form .sect-h b{width:30px;height:30px;font-size:14px;background:linear-gradient(135deg,#e6c27a,var(--gold) 60%,var(--gold-dim));box-shadow:0 4px 10px rgba(199,154,70,.3);}
#pm-form .sect-h h2{font-size:23px;letter-spacing:.06em;}
#pm-form .sect-b{padding:18px;}
#pm-form input[type=text],#pm-form input[type=number],#pm-form input[type=date],#pm-form select{box-sizing:border-box;max-width:100%;border-radius:14px;padding:14px 16px;background:var(--ink);border:1px solid rgba(241,236,226,.12);box-shadow:inset 0 2px 6px rgba(0,0,0,.25);transition:border-color .15s,box-shadow .15s;}
#pm-form input[type=date]{min-height:50px;-webkit-appearance:none;appearance:none;}
#pm-form input:focus,#pm-form select:focus{border-color:var(--gold);box-shadow:inset 0 2px 6px rgba(0,0,0,.25),0 0 0 3px rgba(199,154,70,.22);}
#pm-form .two>.fg{min-width:0;}
#pm-form .pm-pick{border-radius:16px;padding:12px;background:rgba(0,0,0,.18);}
#pm-form .pm-prod,#pm-form .pm-type{border-radius:14px;padding:13px 14px;background:var(--ink);transition:border-color .15s,background .15s;}
#pm-form .pm-prod:has(input:checked),#pm-form .pm-type:has(input:checked){background:linear-gradient(90deg,rgba(199,154,70,.18),rgba(199,154,70,.04)),var(--ink);border-color:var(--gold);box-shadow:0 0 0 1px rgba(199,154,70,.3);}
#pm-form .pm-count{background:rgba(199,154,70,.12);border-color:var(--gold-dim);color:var(--gold);font-weight:600;}
#pm-form .btn.sm{border-radius:999px;padding:10px 18px;}
#pm-form .pm-tog{border-radius:16px;}
#pm-form > button.btn{display:block;width:100%;border:0;border-radius:999px;padding:17px 18px;font-size:13px;letter-spacing:.16em;color:var(--ink);background:linear-gradient(135deg,#e6c27a,var(--gold) 55%,var(--gold-dim));box-shadow:0 10px 26px rgba(199,154,70,.32);}
details.newp>summary{list-style:none;display:inline-block;margin-bottom:14px;}
details.newp>summary::-webkit-details-marker{display:none;}
.cl{background:var(--ink);border:1px solid var(--line);padding:12px;margin-bottom:10px;display:flex;gap:12px;align-items:flex-start;}
.cl .thumb{width:58px;height:72px;}
.cl-main{flex:1;min-width:0;display:grid;gap:8px;}
.cl-n{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);font-weight:600;}
.cl-top{display:flex;gap:8px;align-items:center;}
.cl-top input{flex:1;min-width:0;}
.cl-price{font-size:12.5px;font-weight:600;color:var(--gold);white-space:nowrap;}
.cl-urls{display:grid;gap:6px;}
.cl-url{display:flex;gap:8px;align-items:center;}
.cl-url span{flex:0 0 46px;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--paper-dim);}
.cl-url input{flex:1;min-width:0;}
details.order .ob{gap:12px;}
details.order{--c:var(--paper-dim);border-left:3px solid var(--c);}
details.order.st-new,details.order.st-confirmed,details.order.st-shipped{--c:#6f9a95;}
details.order.st-delivered{--c:var(--gold);}
details.order.st-cancelled{--c:#b86a6a;}
details.order summary{align-items:center;gap:14px;padding:14px 16px;}
details.order .t{font-size:15px;}
.oside{display:flex;flex-direction:column;align-items:flex-end;gap:7px;}
.obadges{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end;}
.ototal{font-size:16px;white-space:nowrap;}
.badge.st-new,.badge.st-confirmed,.badge.st-shipped{border-color:#6f9a95;color:#6f9a95;background:rgba(111,154,149,.14);}
.badge.st-delivered{border-color:var(--gold);color:var(--gold);background:rgba(199,154,70,.12);}
.badge.st-cancelled{border-color:#b86a6a;color:#b86a6a;background:rgba(184,106,106,.14);}
.badge.promo{border-color:var(--gold);background:var(--gold);color:var(--ink);font-weight:600;}
details.order summary{display:block;padding:14px 16px;}
.oh{display:flex;justify-content:space-between;align-items:baseline;gap:12px;}
.on{font-size:16px;font-weight:700;letter-spacing:.01em;}
.oc{margin:6px 0 0;font-size:14px;color:var(--paper);word-break:break-word;}
.om{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px 10px;margin-top:8px;}
.om .obadges{margin-left:auto;flex:0 0 auto;}
details.order{border-radius:12px;overflow:hidden;margin-bottom:12px;border-left-width:4px;}
details.order summary{display:block;padding:0;}
.oband{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:10px 14px;background:rgba(241,236,226,.05);border-bottom:1px solid var(--line);}
.oband .on{font-size:13px;letter-spacing:.12em;font-weight:700;color:var(--c);}
.obody{padding:14px 14px 4px;}
.obody .oc{margin:0 0 4px;font-size:17px;font-weight:600;}
.ofoot{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:10px 14px 14px;}
.ofoot .ototal{font-size:21px;font-weight:700;}
.ofoot .s{font-size:12px;}
details.order.st-history .oc,details.order.st-history .ototal{color:var(--paper-dim);}
.badge.st-history{background:rgba(185,178,164,.10);}
.op{border:1px solid var(--line);background:var(--ink);padding:14px;margin:0;}
.op h3 small{color:var(--paper-dim);font-weight:500;margin-left:6px;}
.kv{display:flex;justify-content:space-between;align-items:baseline;gap:14px;padding:9px 0;border-top:1px solid var(--line);font-size:13.5px;}
.kv .l{flex:0 0 74px;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--paper-dim);}
.kv b,.kv a,.kv .mut{flex:1;text-align:right;font-weight:500;word-break:break-word;}
.kv a.u{color:var(--gold);text-decoration:underline;}
.mut{color:var(--paper-dim);}
.oi{display:flex;gap:12px;align-items:flex-start;padding:10px 0;border-top:1px solid var(--line);}
.oi-r{display:grid;gap:2px;text-align:right;white-space:nowrap;font-size:13.5px;}
.ot{border-top:1px solid var(--line);padding-top:6px;margin-top:2px;}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
.sz{display:grid;gap:8px;}
.sz-row{display:flex;align-items:center;justify-content:space-between;gap:12px;background:var(--ink);border:1px solid var(--line);padding:10px 12px;}
.sz-row .sz-oos{margin-left:auto;}
.sz-row label{display:flex;align-items:center;gap:10px;cursor:pointer;margin:0;}
.sz-row input[type=checkbox]{width:18px;height:18px;accent-color:var(--gold);margin:0;}
.sz-name{font-weight:600;font-size:14px;min-width:34px;}
.sz-oos{font-size:12.5px;color:var(--paper-dim);}
.sz-row.off .sz-name{color:var(--paper-dim);}
.sz-row.off .sz-oos{opacity:.35;cursor:default;}
.sz-row.sold .sz-name{text-decoration:line-through;color:var(--gold);}
.sz-row.sold .sz-oos{color:var(--gold);}
.sz-rm{background:none;border:none;color:var(--paper-dim);font-size:22px;line-height:1;cursor:pointer;padding:0 2px;} .sz-rm:hover{color:var(--gold);}
.sz-add{display:flex;gap:8px;margin-top:10px;} .sz-add input{flex:1;min-width:0;}
.cl-pics{display:flex;flex-wrap:wrap;gap:8px;}
.cl-pic{position:relative;width:74px;height:94px;background:rgba(128,128,128,.12);border:1px solid var(--line);padding:0;}
.cl-pic img{width:100%;height:100%;object-fit:contain;display:block;}
.cl-pl{position:absolute;left:0;right:0;bottom:0;text-align:center;font-size:10px;letter-spacing:.08em;text-transform:uppercase;background:rgba(32,28,24,.85);color:var(--paper);padding:2px 0;}
.cl-px{position:absolute;top:2px;right:2px;width:22px;height:22px;border-radius:50%;border:none;background:rgba(32,28,24,.9);color:var(--paper);font-size:16px;line-height:1;cursor:pointer;padding:0;}
.cl-px:hover{color:var(--gold);}
.cl-padd{display:flex;align-items:center;justify-content:center;font-size:26px;color:var(--gold);border:1px dashed var(--gold-dim);background:transparent;cursor:pointer;}
.cl-wait{display:flex;align-items:center;justify-content:center;text-align:center;font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--paper-dim);}
.cl-link{display:flex;gap:8px;} .cl-link[hidden]{display:none;} .cl-link input{flex:1;min-width:0;}
.cl-oos{display:flex;align-items:center;gap:8px;font-size:12.5px;color:var(--paper-dim);cursor:pointer;margin:0;}
.cl-oos input{width:18px;height:18px;accent-color:var(--gold);margin:0;}
.cl.sold .cl-n{color:var(--gold);}
.cl.sold .cl-oos{color:var(--gold);}
.cl.sold .cl-top input{text-decoration:line-through;color:var(--paper-dim);}
/* product edit page look v2 */
#product-form{padding-bottom:10px;}
#product-form .card{position:relative;border-radius:20px;padding:22px 18px 20px;margin-bottom:20px;border:1px solid var(--line);border-top:0;overflow:hidden;box-shadow:0 12px 30px rgba(0,0,0,.28);background:linear-gradient(90deg,var(--gold),#e6c27a 50%,var(--gold-dim)) top/100% 4px no-repeat,radial-gradient(120% 60% at 0% 0%,rgba(199,154,70,.12),rgba(199,154,70,0) 60%),var(--ink-raised);}
#product-form > .card::before{display:block;font-family:"Big Shoulders Display",sans-serif;font-size:26px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--paper);margin:4px 0 20px;padding:2px 0 2px 12px;border-left:4px solid var(--gold);}
#product-form > .card:nth-of-type(1)::before{content:"01 · The basics";}
#product-form > .card:nth-of-type(2)::before{content:"02 · Photos & colors";}
#product-form label.f{font-size:10.5px;letter-spacing:.18em;font-weight:600;margin-bottom:8px;}
#product-form input[type=text],#product-form input[type=number],#product-form select,#product-form textarea{border-radius:14px;padding:14px 16px;background:var(--ink);border:1px solid rgba(241,236,226,.12);box-shadow:inset 0 2px 6px rgba(0,0,0,.25);transition:border-color .15s,box-shadow .15s;}
#product-form input:focus,#product-form select:focus,#product-form textarea:focus{border-color:var(--gold);box-shadow:inset 0 2px 6px rgba(0,0,0,.25),0 0 0 3px rgba(199,154,70,.22);}
#product-form input[readonly]{opacity:.6;border-style:dashed;}
#product-form input[name=price]{font-weight:700;font-size:17px;color:var(--gold);}
#product-form .hint{font-size:12px;line-height:1.55;}
#product-form .sz{gap:10px;}
#product-form .sz-row{border-radius:14px;padding:12px 14px;transition:border-color .15s,background .15s;}
#product-form .sz-row:has(.sz-on:checked){border-color:var(--gold-dim);background:linear-gradient(90deg,rgba(199,154,70,.13),rgba(199,154,70,0) 70%),var(--ink);}
#product-form .sz-name{font-family:"Big Shoulders Display",sans-serif;font-size:21px;letter-spacing:.06em;}
#product-form .sz-add{margin-top:12px;}
#product-form .btn.sm{border-radius:999px;padding:10px 18px;}
#product-form .check{gap:14px;padding:14px 16px;border-radius:14px;background:var(--ink);border:1px solid var(--line);font-weight:600;}
#product-form .check input{-webkit-appearance:none;appearance:none;width:46px;height:26px;border-radius:999px;background:rgba(241,236,226,.14);position:relative;flex:0 0 auto;margin:0;cursor:pointer;transition:background .2s;}
#product-form .check input::before{content:"";position:absolute;top:3px;left:3px;width:20px;height:20px;border-radius:50%;background:var(--paper);transition:transform .2s,background .2s;}
#product-form .check input:checked{background:var(--gold);}
#product-form .check input:checked::before{transform:translateX(20px);background:var(--ink);}
#product-form .cl{border-radius:18px;padding:16px;margin-bottom:14px;background:var(--ink);border:1px solid var(--line);border-left:4px solid var(--gold);box-shadow:0 6px 16px rgba(0,0,0,.2);}
#product-form .cl.sold{border-left-color:#b86a6a;}
#product-form .cl-n{justify-self:start;padding:3px 11px;border-radius:999px;background:rgba(199,154,70,.16);letter-spacing:.18em;}
#product-form .cl .thumb{border-radius:12px;overflow:hidden;border:1px solid var(--line);}
#product-form .cl-pic{border-radius:12px;overflow:hidden;transition:transform .15s,border-color .15s;}
#product-form .cl-pic:hover{transform:translateY(-2px);border-color:var(--gold-dim);}
#product-form .cl-padd{border-radius:12px;background:rgba(199,154,70,.05);transition:background .15s;}
#product-form .cl-padd:hover{background:rgba(199,154,70,.14);}
#product-form button.btn:not(.sm){display:block;width:100%;border:0;border-radius:999px;padding:17px 18px;font-size:13px;letter-spacing:.16em;color:var(--ink);background:linear-gradient(135deg,#e6c27a,var(--gold) 55%,var(--gold-dim));box-shadow:0 10px 26px rgba(199,154,70,.32);}
/* end product edit page look v2 */
/* customers page look */
.row.cust{display:grid;grid-template-columns:50px 1fr auto;grid-template-areas:"av info info" "stats stats btn";gap:12px 14px;align-items:center;padding:16px;border-radius:16px;border-left:4px solid var(--gold);margin-bottom:12px;box-shadow:0 8px 22px rgba(0,0,0,.22);background:linear-gradient(90deg,rgba(199,154,70,.08),rgba(199,154,70,0) 55%),var(--ink-raised);}
.row.cust::before{content:attr(data-i);grid-area:av;width:50px;height:50px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:"Big Shoulders Display",sans-serif;font-size:26px;font-weight:700;color:var(--ink);background:linear-gradient(135deg,#e6c27a,var(--gold) 60%,var(--gold-dim));}
.row.cust>.grow{grid-area:info;min-width:0;}
.row.cust .t{font-size:17px;margin:0 0 3px;}
.row.cust>.s{grid-area:stats;line-height:1.55;}
.row.cust>.s::first-line{color:var(--gold);font-weight:700;font-size:15px;}
.row.cust>a.btn{grid-area:btn;border-radius:999px;padding:9px 16px;}
.swf{display:flex;align-items:center;gap:8px;margin:0 0 0 auto;}
.sw-l{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--paper-dim);min-width:68px;}
.sw{position:relative;width:46px;height:26px;border-radius:999px;border:1px solid var(--line);background:rgba(241,236,226,.12);cursor:pointer;padding:0;transition:background .15s;}
.sw .sw-knob{position:absolute;top:2px;left:2px;width:20px;height:20px;border-radius:50%;background:var(--paper-dim);transition:transform .15s,background .15s;}
.sw.on{background:var(--gold);border-color:var(--gold);}
.sw.on .sw-knob{transform:translateX(20px);background:var(--ink);}
.row.is-hidden .thumb,.row.is-hidden .grow{opacity:.5;}
.oi .thumb{width:52px;height:64px;}
.promo-op{border-color:var(--gold);}
@media(max-width:560px){.two,.three{grid-template-columns:1fr;} h1{font-size:30px;}}
</style>
"""


def _dt(iso) -> str:
    d = _parse(iso)
    return d.astimezone(ADMIN_TZ).strftime("%d %b %Y, %I:%M %p") if d else ""


def _money(n) -> str:
    return f"{float(n or 0):,.0f} EGP"


def _first_image(p: dict) -> str:
    for v in (p.get("color_images") or {}).values():
        if isinstance(v, list) and v:
            return v[0]
        if isinstance(v, str) and v:
            return v
    return p.get("image_url") or ""


TRASH_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" '
              'stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M8 6V4h8v2"/>'
              '<path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/></svg>')


def admin_page(title: str, body: str, active: str = "", msg: str | None = None) -> str:
    links = "".join(f'<a href="/admin/{k}" class="dl{" on" if k == active else ""}">{label}</a>' for k, label in NAV)
    flash = f'<div class="flash" id="flash" role="status">{escape(msg)}</div>' if msg else ""
    on = " on" if active == "deleted" else ""
    trash = f'<a href="/admin/deleted" class="trash{on}" aria-label="Recently Deleted" title="Recently Deleted">{TRASH_ICON}</a>'
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow"><title>{escape(title)} · Loomex Admin</title>
<link rel="manifest" href="/admin/manifest.webmanifest"><meta name="theme-color" content="#201c18">
<meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="LX Admin">
<link rel="apple-touch-icon" href="/static/admin-icon.png">
{FONTS}<link rel="icon" type="image/png" href="/static/loomex-icon-v5.png"><link rel="apple-touch-icon" href="/static/loomex-icon-v5.png">{ADMIN_CSS}</head>
<body>
<input type="checkbox" id="am" class="am-toggle">
<label for="am" class="am-backdrop"></label>
<nav class="am-drawer"><label for="am" class="am-close">&times;</label>{links}
<div class="am-out"><form method="post" action="/admin/logout"><button class="dl">Log out</button></form>{trash}</div></nav>
<header class="top"><div class="top-in">
  <label for="am" class="am-btn" aria-label="Open menu"><span></span><span></span><span></span></label>
  <a href="/admin/home" class="logo">LOOM<span>EX</span><small>Admin</small></a>{trash}
</div></header>
<main class="page">{flash}{body}</main>
{LIVE_SEARCH_JS}{FLASH_JS if msg else ""}
</body></html>"""


FLASH_JS = """<script>
/* The notice shows for 2 seconds, then fades away. The ?msg= part is removed from the address
   so reloading the page does not show it again. */
(function () {
  var f = document.getElementById('flash');
  if (!f) return;
  try {
    var u = new URL(location.href);
    if (u.searchParams.has('msg')) { u.searchParams.delete('msg'); history.replaceState(null, '', u.pathname + u.search + u.hash); }
  } catch (e) {}
  setTimeout(function () { f.classList.add('gone'); setTimeout(function () { f.remove(); }, 350); }, 2000);
})();
</script>"""

LIVE_SEARCH_JS = """<script>
/* Search boxes marked data-live update the results as you type, no button needed */
document.querySelectorAll('input[data-live]').forEach(function (inp) {
  var form = inp.form, timer = null, seq = 0;
  function run() {
    var params = new URLSearchParams(new FormData(form));
    if (!inp.value.trim()) params.delete('q');
    var qs = params.toString();
    var url = form.getAttribute('action') + (qs ? '?' + qs : '');
    var mine = ++seq;
    fetch(url, { credentials: 'same-origin' }).then(function (r) { return r.text(); }).then(function (html) {
      if (mine !== seq) return;
      var doc = new DOMParser().parseFromString(html, 'text/html');
      var fresh = doc.getElementById('results'), cur = document.getElementById('results');
      if (fresh && cur) cur.innerHTML = fresh.innerHTML;
      history.replaceState(null, '', url);
    }).catch(function () {});
  }
  inp.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(run, 200); });
});
</script>"""


_LOGIN_CSS = """<style>
.lg{min-height:100vh;min-height:100dvh;display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding:32px 18px;position:relative;overflow:hidden;
  background:repeating-linear-gradient(45deg,rgba(199,154,70,.05) 0 1px,transparent 1px 9px),
  radial-gradient(520px 320px at 50% 28%,rgba(199,154,70,.16),transparent 70%),var(--ink);}
.lg-in{width:100%;max-width:380px;position:relative;}
.lg-brand{text-align:center;margin-bottom:28px;}
.lg-logo{font-family:"Big Shoulders Display",sans-serif;font-weight:700;font-size:56px;letter-spacing:.14em;line-height:1;}
.lg-logo span{color:var(--gold);}
.lg-rule{width:46px;height:3px;background:var(--gold);margin:16px auto 13px;}
.lg-tag{margin:0;font-size:11px;letter-spacing:.3em;text-transform:uppercase;color:var(--paper-dim);}
.lg-card{position:relative;padding:28px 22px 22px;border:1px solid var(--line);
  background:linear-gradient(135deg,rgba(199,154,70,.10),rgba(199,154,70,.02) 60%),var(--ink-raised);
  box-shadow:0 18px 40px rgba(0,0,0,.35);}
.lg-card::before{content:"";position:absolute;inset:6px;border:1px dashed rgba(199,154,70,.32);pointer-events:none;}
.lg-card>*{position:relative;}
label.f.lg-label{display:flex;align-items:center;gap:8px;}
.lg-label svg{width:14px;height:14px;color:var(--gold);flex:0 0 auto;}
.lg-pw{position:relative;}
.lg-pw input{padding:14px 74px 14px 14px;font-size:16px;}
.lg-t{position:absolute;right:0;top:0;bottom:0;padding:0 14px;background:none;border:none;color:var(--paper-dim);
  font:600 11px Inter,sans-serif;letter-spacing:.1em;text-transform:uppercase;cursor:pointer;}
.lg-t:hover{color:var(--gold);}
.lg-btn{width:100%;padding:15px 16px;font-size:13px;margin-top:6px;}
.lg-hint{margin:0 0 16px;padding:10px 12px;border-left:3px solid var(--gold);background:rgba(199,154,70,.08);
  font-size:12.5px;line-height:1.5;color:var(--paper-dim);}
.lg-foot{margin-top:24px;text-align:center;font-size:10.5px;letter-spacing:.22em;text-transform:uppercase;
  color:var(--paper-dim);opacity:.7;}
</style>"""

_LOGIN_JS = """<script>
(function(){
  var t=document.querySelector('.lg-t'), i=document.getElementById('pw');
  if(!t||!i)return;
  t.addEventListener('click',function(){
    var show=i.type==='password';
    i.type=show?'text':'password';
    t.textContent=show?'Hide':'Show';
    i.focus();
  });
})();
</script>"""

_LOCK = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
         'stroke-linejoin="round"><rect x="4" y="11" width="16" height="10" rx="1.5"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>')


def login_page(configured: bool = True, error: str | None = None, first_time: bool = False) -> str:
    if not configured:
        inner = ('<div class="lg-card"><p class="s">Admin login isn\'t set up yet. Add <b>ADMIN_PASSWORD</b> and '
                 '<b>ADMIN_SECRET</b> to your .env file (and to Vercel) and restart.</p></div>')
    else:
        err = f'<div class="err"><strong>{escape(error)}</strong></div>' if error else ""
        note = ('<p class="lg-hint">First time? Use the password from your .env file, '
                'then set your own password in Profile.</p>' if first_time else "")
        inner = f"""<div class="lg-card"><form method="post" action="/admin/login">{err}{note}
<div class="fg"><label class="f lg-label" for="pw">{_LOCK}Password</label>
<div class="lg-pw"><input type="password" id="pw" name="password" autocomplete="current-password" autofocus required>
<button type="button" class="lg-t">Show</button></div></div>
<button class="btn lg-btn">Log in</button></form></div>"""
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"><meta name="robots" content="noindex, nofollow">
<title>Admin login · Loomex</title>{FONTS}<link rel="icon" type="image/png" href="/static/loomex-icon-v5.png"><link rel="apple-touch-icon" href="/static/loomex-icon-v5.png">{ADMIN_CSS}{_LOGIN_CSS}</head>
<body><div class="lg"><div class="lg-in">
<div class="lg-brand"><div class="lg-logo">LOOM<span>EX</span></div><div class="lg-rule"></div><p class="lg-tag">Admin panel</p></div>
{inner}
<p class="lg-foot">Loomex &middot; Owners only</p>
</div></div>{_LOGIN_JS}</body></html>"""


PUSH_CARD = """
<div class="card" id="push-card">
<h3 style="margin:0 0 6px;font:600 11px Inter,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--gold)">Order notifications</h3>
<p class="hint" style="margin:0 0 14px">Get an alert on this device for every new order.</p>
<p class="s" id="push-status" style="margin:0 0 12px"></p>
<div style="display:flex;gap:8px;flex-wrap:wrap">
<button type="button" class="btn" id="push-on">Enable notifications</button>
<button type="button" class="btn ghost" id="push-off" hidden>Turn off</button>
</div>
</div>
<script>
(function () {
  var st = document.getElementById('push-status');
  var on = document.getElementById('push-on'), off = document.getElementById('push-off');
  if (!st) return;
  function say(t) { st.textContent = t; }
  function ui(enabled) { on.hidden = enabled; off.hidden = !enabled; }
  var ios = /iphone|ipad|ipod/i.test(navigator.userAgent);
  var standalone = window.navigator.standalone === true || (window.matchMedia && matchMedia('(display-mode: standalone)').matches);
  var ok = ('serviceWorker' in navigator) && ('PushManager' in window) && ('Notification' in window);
  if (!ok) { var card = document.getElementById('push-card'); if (card) card.remove(); return; }
  function keyBytes(b64) {
    var pad = '='.repeat((4 - b64.length % 4) % 4);
    var raw = atob((b64 + pad).replace(/-/g, '+').replace(/_/g, '/'));
    var out = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
    return out;
  }
  function post(url, body) {
    return fetch(url, {method: 'POST', credentials: 'same-origin',
      headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body || {})});
  }
  function registration() {
    return navigator.serviceWorker.register('/admin/sw.js', {scope: '/admin/'})
      .then(function () { return navigator.serviceWorker.ready; });
  }
  function refresh() {
    return navigator.serviceWorker.getRegistration('/admin/').then(function (reg) {
      return reg ? reg.pushManager.getSubscription() : null;
    }).then(function (sub) {
      var enabled = !!sub && Notification.permission === 'granted';
      ui(enabled);
      if (enabled) say('Notifications are ON for this device.');
      else if (Notification.permission === 'denied') say('Notifications are blocked. Allow them in your browser or phone settings, then try again.');
      else say('Notifications are off.');
    }).catch(function () { say('Notifications are off.'); });
  }
  on.addEventListener('click', function () {
    on.disabled = true; say('Setting up...');
    var reg;
    registration().then(function (r) {
      reg = r;
      return Notification.requestPermission();
    }).then(function (perm) {
      if (perm !== 'granted') throw new Error('Permission was not given.');
      return fetch('/admin/push/key', {credentials: 'same-origin'}).then(function (r) { return r.json(); });
    }).then(function (k) {
      if (!k.configured || !k.key) throw new Error('Push is not set up on the server yet (the VAPID keys are missing in Vercel).');
      return reg.pushManager.getSubscription().then(function (existing) {
        return existing || reg.pushManager.subscribe({userVisibleOnly: true, applicationServerKey: keyBytes(k.key)});
      });
    }).then(function (sub) {
      return post('/admin/push/subscribe', sub.toJSON()).then(function (r) {
        if (!r.ok) throw new Error('The server could not save this device.');
      });
    }).then(function () { return refresh(); }).catch(function (e) {
      say((e && e.message) || 'Something went wrong. Try again.');
    }).then(function () { on.disabled = false; });
  });
  off.addEventListener('click', function () {
    navigator.serviceWorker.getRegistration('/admin/').then(function (reg) {
      return reg ? reg.pushManager.getSubscription() : null;
    }).then(function (sub) {
      if (!sub) return;
      return post('/admin/push/unsubscribe', {endpoint: sub.endpoint}).then(function () { return sub.unsubscribe(); });
    }).then(function () { return refresh(); });
  });
  refresh();
})();
</script>
"""


_PAGES_CSS = """<style>
.pf-head{display:flex;align-items:center;gap:14px;background:var(--ink-raised);border:1px solid var(--line);
  border-left:4px solid var(--gold);padding:16px 18px;margin-bottom:14px;}
.pf-av{width:52px;height:52px;flex:0 0 auto;border-radius:50%;background:var(--gold);color:var(--ink);
  font-family:"Big Shoulders Display",sans-serif;font-size:28px;font-weight:700;display:flex;align-items:center;justify-content:center;}
.pf-role{margin:0 0 2px;font-size:10.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--gold);font-weight:600;}
.pf-mail{margin:0;font-size:14px;word-break:break-all;}
.pf-card{padding:0;overflow:hidden;}
.pf-card-h{padding:12px 18px;background:rgba(241,236,226,.06);border-bottom:1px solid var(--line);
  font-family:"Big Shoulders Display",sans-serif;font-size:19px;text-transform:uppercase;letter-spacing:.04em;}
.pf-card-b{padding:18px;}
.pw{position:relative;}
.pw input{padding-right:70px;}
.pw-t{position:absolute;right:0;top:0;bottom:0;padding:0 14px;background:none;border:none;color:var(--paper-dim);
  font:600 11px Inter,sans-serif;letter-spacing:.1em;text-transform:uppercase;cursor:pointer;}
.pw-t:hover{color:var(--gold);}
.meter{display:grid;grid-template-columns:repeat(4,1fr);gap:4px;margin-top:9px;}
.meter i{display:block;height:3px;background:var(--line);}
.meter.s1 i:nth-child(-n+1),.meter.s2 i:nth-child(-n+2){background:var(--gold-dim);}
.meter.s3 i:nth-child(-n+3),.meter.s4 i{background:var(--gold);}
.mt{font-size:12px;color:var(--paper-dim);margin:6px 0 0;min-height:16px;}
.mt.ok{color:var(--gold);}
.pf-btn{width:100%;padding:13px 16px;font-size:13px;}
.pf-note{display:flex;gap:12px;align-items:flex-start;background:var(--ink-raised);border:1px solid var(--line);
  padding:14px 16px;margin-bottom:18px;font-size:12.5px;color:var(--paper-dim);line-height:1.55;}
.pf-note svg{width:20px;height:20px;flex:0 0 auto;color:var(--gold);margin-top:1px;}
.pf-note b{color:var(--paper);font-weight:600;}
.dl-tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:6px;}
.dl-tile{background:var(--ink-raised);border:1px solid var(--line);padding:14px 10px;text-align:center;}
.dl-tile b{display:block;font-family:"Big Shoulders Display",sans-serif;font-size:32px;line-height:1;margin:8px 0 4px;color:var(--paper);}
.dl-tile small{font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--paper-dim);}
.dl-ico{display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:50%;
  background:rgba(199,154,70,.12);color:var(--gold);flex:0 0 auto;}
.dl-ico svg{width:18px;height:18px;display:block;}
.dl-sec{display:flex;align-items:center;gap:10px;margin:26px 0 10px;}
.dl-sec h2{margin:0;font-family:"Big Shoulders Display",sans-serif;font-size:22px;text-transform:uppercase;}
.dl-sec span{margin-left:auto;font-size:12px;color:var(--paper-dim);}
.dl-card{background:var(--ink-raised);border:1px solid var(--line);border-left:4px solid var(--gold-dim);padding:14px 16px;margin-bottom:10px;}
.dl-card.soon{border-left-color:var(--gold);box-shadow:0 0 0 1px rgba(199,154,70,.25) inset;}
.dl-top{display:flex;align-items:center;gap:12px;}
.dl-top .grow{flex:1 1 auto;min-width:0;}
.dl-bar{height:4px;background:var(--line);margin:14px 0 8px;overflow:hidden;border-radius:2px;}
.dl-bar i{display:block;height:100%;background:var(--gold-dim);border-radius:2px;}
.dl-card.soon .dl-bar i{background:var(--gold);}
.dl-when{margin:0 0 12px;font-size:12px;color:var(--paper-dim);}
.dl-card.soon .dl-when{color:var(--gold);}
.dl-acts{display:flex;align-items:center;gap:14px;}
.dl-acts form{margin:0;}
.dl-empty{text-align:center;padding:46px 20px;background:var(--ink-raised);border:1px dashed var(--line);margin-top:8px;}
.dl-empty .dl-ico{width:56px;height:56px;margin-bottom:12px;}
.dl-empty .dl-ico svg{width:26px;height:26px;}
.dl-empty p{margin:0;font-size:14px;color:var(--paper-dim);}
.dl-empty b{display:block;font-family:"Big Shoulders Display",sans-serif;font-size:22px;text-transform:uppercase;color:var(--paper);margin-bottom:4px;}
</style>"""

_PROFILE_JS = """<script>
(function(){
  document.querySelectorAll('.pw-t').forEach(function(b){
    b.addEventListener('click',function(){
      var i=b.parentNode.querySelector('input'), show=i.type==='password';
      i.type=show?'text':'password'; b.textContent=show?'Hide':'Show';
    });
  });
  var np=document.getElementById('pf-new'), cf=document.getElementById('pf-conf'),
      meter=document.getElementById('pf-meter'), st=document.getElementById('pf-strength'),
      cm=document.getElementById('pf-match');
  if(!np||!cf)return;
  var labels=['','Too short','Okay','Good','Strong'];
  function score(v){
    if(!v)return 0;
    if(v.length<8)return 1;
    var s=2, kinds=[/[a-z]/,/[A-Z]/,/\\d/,/[^A-Za-z0-9]/].filter(function(r){return r.test(v);}).length;
    if(v.length>=12)s++;
    if(kinds>=3)s++;
    return Math.min(s,4);
  }
  function upd(){
    var s=score(np.value);
    meter.className='meter'+(s?' s'+s:'');
    st.textContent=labels[s];
    st.className='mt'+(s>=3?' ok':'');
    if(!cf.value){cm.textContent='';cm.className='mt';return;}
    var ok=cf.value===np.value;
    cm.textContent=ok?'Passwords match':"Passwords don't match";
    cm.className='mt'+(ok?' ok':'');
  }
  np.addEventListener('input',upd);
  cf.addEventListener('input',upd);
})();
</script>"""

_SHIELD = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
           'stroke-linejoin="round"><path d="M12 3l8 3v6c0 4.5-3.2 8-8 9-4.8-1-8-4.5-8-9V6l8-3z"/><path d="M9 12l2 2 4-4"/></svg>')

_ICONS = {
    "products": ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
                 'stroke-linejoin="round"><path d="M20.6 13.4l-7.2 7.2a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8z"/>'
                 '<circle cx="7.5" cy="7.5" r="1.2"/></svg>'),
    "orders": ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
               'stroke-linejoin="round"><path d="M6 7h12l1 13H5L6 7z"/><path d="M9 7a3 3 0 0 1 6 0"/></svg>'),
    "promotions": ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
                   'stroke-linejoin="round"><path d="M19 5L5 19"/><circle cx="7" cy="7" r="2.2"/><circle cx="17" cy="17" r="2.2"/></svg>'),
    "trash": TRASH_ICON,
}


def profile_page(email: str, msg: str | None = None, error: str | None = None, form_email: str = "") -> str:
    err = f'<div class="err"><strong>{escape(error)}</strong></div>' if error else ""
    shown = email or form_email or "Admin"
    initial = escape((shown[:1] or "A").upper())
    body = f"""{_PAGES_CSS}
<div class="head"><div><h1>Profile</h1>
<p class="sub">Manage the login both owners share.</p></div></div>{err}
<div class="pf-note">{_SHIELD}<div><b>Changing your password logs out your other devices.</b><br>
Use at least 8 characters. A longer password with numbers and symbols is stronger.</div></div>
<form method="post" action="/admin/profile" class="card pf-card">
<div class="pf-card-h">Change password</div>
<div class="pf-card-b">
<div class="fg"><label class="f" for="pf-cur">Current password</label>
<div class="pw"><input type="password" id="pf-cur" name="current_password" autocomplete="current-password" required>
<button type="button" class="pw-t">Show</button></div></div>
<div class="fg"><label class="f" for="pf-new">New password</label>
<div class="pw"><input type="password" id="pf-new" name="new_password" autocomplete="new-password" required>
<button type="button" class="pw-t">Show</button></div>
<div class="meter" id="pf-meter"><i></i><i></i><i></i><i></i></div>
<p class="mt" id="pf-strength"></p></div>
<div class="fg"><label class="f" for="pf-conf">Confirm new password</label>
<div class="pw"><input type="password" id="pf-conf" name="confirm_password" autocomplete="new-password" required>
<button type="button" class="pw-t">Show</button></div>
<p class="mt" id="pf-match"></p></div>
<button class="btn pf-btn">Change password</button>
</div></form>
{PUSH_CARD}{_PROFILE_JS}"""
    return admin_page("Profile", body, "profile", msg)


# ------------------------------------------------------------- products ----
def products_page(products: list, msg: str | None = None) -> str:
    rows = []
    for p in products:
        img = _first_image(p)
        thumb = f'<img src="{escape(img)}" alt="" loading="lazy">' if img else ""
        sub = f" · {escape(p['subcategory'].replace('-', ' ').title())}" if p.get("subcategory") else ""
        stock = '<span class="badge ok">In stock</span>' if p.get("in_stock") else '<span class="badge">Out of stock</span>'
        visible = p.get("is_visible", True) is not False
        switch = (f'<form method="post" action="/admin/products/{p["id"]}/visibility" class="swf">'
                  f'<input type="hidden" name="visible" value="{"" if visible else "1"}">'
                  f'<button class="sw{" on" if visible else ""}" type="submit" role="switch" aria-checked="{"true" if visible else "false"}" '
                  f'title="{"Shown on the website. Tap to hide it." if visible else "Hidden from the website. Tap to show it."}">'
                  f'<span class="sw-knob"></span></button>'
                  f'<span class="sw-l">{"On website" if visible else "Hidden"}</span></form>')
        rows.append(f"""<div class="row{"" if visible else " is-hidden"}"><div class="thumb">{thumb}</div>
<div class="grow"><p class="t">{escape(p['name'])}</p>
<p class="s">{escape(p['category'].replace('-', ' ').title())}{sub} · {_money(p['price'])}</p></div>{stock}
<div class="acts"><a class="btn sm ghost" href="/admin/products/{p['id']}">Edit</a>
<form method="post" action="/admin/products/{p['id']}/delete" onsubmit="return confirm('Move this product to Recently Deleted? It will also disappear from the website.')">
<button class="link">Delete</button></form></div>{switch}</div>""")
    listing = "".join(rows) or '<div class="empty">No products yet.</div>'
    body = f"""<div class="head"><div><h1>Products</h1><p class="sub">{len(products)} on the site</p></div>
<a class="btn" href="/admin/products/new">+ Add product</a></div>{listing}"""
    return admin_page("Products", body, "products", msg)


def _color_rows(v: dict) -> list[dict]:
    """The product's colors and photo links, as rows for the colors editor."""
    photos = parse_photos(v.get("photos", ""))
    names = [c.strip() for c in (v.get("colors") or "").split(",") if c.strip()]
    seen = {n.lower() for n in names}
    names += [c for c in photos if c.lower() not in seen]
    by_name = {c.lower(): urls for c, urls in photos.items()}
    sc = v.get("sold_out_colors") or []
    if isinstance(sc, str):
        sc = [x.strip() for x in sc.split(",") if x.strip()]
    sold = {c.lower() for c in sc}
    rows = []
    for n in names:
        urls = list(by_name.get(n.lower(), []))
        rows.append({"name": n, "urls": urls + [""] * max(0, 2 - len(urls)), "out": n.lower() in sold})
    return rows


COLOR_EDITOR_JS = r"""<script>
/* Colors & photos editor: fills the same "Color = url | url" text the server already reads */
(function () {
  var list = document.getElementById('cl-list');
  if (!list) return;
  var form = list.closest('form');
  var colorsField = document.getElementById('cl-colors');
  var photosField = document.getElementById('cl-photos');
  var soldField = document.getElementById('cl-sold');
  var addBtn = document.getElementById('cl-add');
  var priceInput = form.querySelector('input[name=price]');
  var LABELS = ['Front', 'Back'];
  var rows = [];
  try { rows = JSON.parse(list.dataset.rows || '[]'); } catch (e) {}
  if (!rows.length) rows = [{name: '', urls: ['', '']}];

  function clean(s) { return (s || '').replace(/[,=|\n\r]+/g, ' ').trim(); }
  function priceText() {
    var n = parseFloat(priceInput ? priceInput.value : '');
    return isNaN(n) ? '' : n.toLocaleString(undefined, {maximumFractionDigits: 2}) + ' EGP';
  }
  function firstUrl(row) {
    return row.urls.map(function (u) { return u.trim(); }).filter(Boolean)[0] || '';
  }
  function setThumb(thumb, url) {
    thumb.innerHTML = '';
    if (!url) return;
    var img = document.createElement('img');
    img.alt = '';
    img.onerror = function () { img.remove(); };
    img.src = url;
    thumb.appendChild(img);
  }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text) e.textContent = text;
    return e;
  }

  /* ---- adding photos from the gallery: they are uploaded into the storage bucket ---- */
  /* tell the server a photo was removed, so its file can be deleted from the bucket */
  function discard(url) {
    if (!url) return;
    var fd = new FormData();
    fd.append('url', url);
    fetch('/admin/upload/delete', {method: 'POST', body: fd, credentials: 'same-origin'}).catch(function () {});
  }
  function folder() {
    var s = form.querySelector('input[name=slug]');
    var n = form.querySelector('input[name=name]');
    var v = (s && s.value) || list.dataset.slug || (n && n.value) || 'uploads';
    return v.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'uploads';
  }
  /* phone photos are big: shrink large ones first so the upload always fits */
  function shrink(file) {
    return new Promise(function (resolve) {
      if (file.size <= 3500000 || !/^image\/(png|jpeg|webp)$/.test(file.type)) return resolve(file);
      var img = new Image(), u = URL.createObjectURL(file);
      img.onload = function () {
        var k = Math.min(1, 1800 / Math.max(img.width, img.height));
        var c = document.createElement('canvas');
        c.width = Math.round(img.width * k); c.height = Math.round(img.height * k);
        c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
        URL.revokeObjectURL(u);
        c.toBlob(function (b) { resolve(b || file); }, file.type, 0.88);
      };
      img.onerror = function () { URL.revokeObjectURL(u); resolve(file); };
      img.src = u;
    });
  }
  function uploadFile(file) {
    return shrink(file).then(function (blob) {
      var fd = new FormData();
      fd.append('file', blob, file.name || 'photo.jpg');
      fd.append('folder', folder());
      return fetch('/admin/upload', {method: 'POST', body: fd, credentials: 'same-origin'});
    }).then(function (r) {
      return r.json().catch(function () { return {error: 'Upload failed (the image may be too large).'}; });
    }).then(function (j) {
      if (!j.url) throw new Error(j.error || 'Upload failed.');
      return j.url;
    });
  }
  function addFiles(row, fileList) {
    var queue = Array.prototype.slice.call(fileList);
    row.pending = (row.pending || 0) + queue.length;
    render();
    queue.reduce(function (chain, f) {
      return chain.then(function () {
        return uploadFile(f).then(function (url) {
          row.urls.push(url);
        }).catch(function (e) {
          alert((e && e.message) || 'Upload failed. Check your connection and try again.');
        }).then(function () {
          row.pending--; render(); sync();
        });
      });
    }, Promise.resolve());
  }

  function sync() {
    var names = [], lines = [], sold = [];
    rows.forEach(function (row) {
      var n = clean(row.name);
      if (!n) return;
      names.push(n);
      if (row.out) sold.push(n);
      var urls = row.urls.map(function (u) { return u.trim(); }).filter(Boolean);
      if (urls.length) lines.push(n + ' = ' + urls.join(' | '));
    });
    colorsField.value = names.join(', ');
    photosField.value = lines.join('\n');
    if (soldField) soldField.value = sold.join(', ');
  }
  function render() {
    list.innerHTML = '';
    rows.forEach(function (row, ri) {
      var card = el('div', 'cl');
      var thumb = el('div', 'thumb');
      setThumb(thumb, firstUrl(row));

      var main = el('div', 'cl-main');
      var num = el('div', 'cl-n', 'Color ' + (ri + 1));
      var top = el('div', 'cl-top');
      var name = document.createElement('input');
      name.type = 'text'; name.placeholder = 'Color name (e.g. Black)'; name.value = row.name;
      name.addEventListener('input', function () { row.name = name.value; sync(); });
      var price = el('span', 'cl-price', priceText());
      price.setAttribute('data-price', '1');
      var rm = el('button', 'link', 'remove'); rm.type = 'button';
      rm.addEventListener('click', function () { var gone = rows.splice(ri, 1)[0]; render(); sync(); gone.urls.forEach(discard); });
      top.appendChild(name); top.appendChild(price); top.appendChild(rm);

      var oos = el('label', 'cl-oos');
      var oosBox = document.createElement('input'); oosBox.type = 'checkbox'; oosBox.checked = !!row.out;
      oosBox.addEventListener('change', function () { row.out = oosBox.checked; card.classList.toggle('sold', row.out); sync(); });
      oos.appendChild(oosBox); oos.appendChild(document.createTextNode(' Out of stock (this color only)'));
      card.classList.toggle('sold', !!row.out);

      row.urls = row.urls.filter(function (u) { return u.trim(); });
      var pics = el('div', 'cl-pics');
      row.urls.forEach(function (u, ui) {
        var tile = el('div', 'cl-pic');
        var img = document.createElement('img');
        img.alt = ''; img.src = u;
        var lab = el('span', 'cl-pl', LABELS[ui] || 'Photo ' + (ui + 1));
        var x = el('button', 'cl-px', '×'); x.type = 'button';
        x.setAttribute('aria-label', 'Remove photo');
        x.addEventListener('click', function () { var gone = row.urls.splice(ui, 1)[0]; render(); sync(); discard(gone); });
        tile.appendChild(img); tile.appendChild(lab); tile.appendChild(x);
        pics.appendChild(tile);
      });
      for (var p = 0; p < (row.pending || 0); p++) pics.appendChild(el('div', 'cl-pic cl-wait', 'Uploading...'));

      /* the + tile opens the phone's gallery (several photos can be picked at once) */
      var pick = document.createElement('input');
      pick.type = 'file'; pick.accept = 'image/*'; pick.multiple = true; pick.style.display = 'none';
      var addTile = el('button', 'cl-pic cl-padd', '+'); addTile.type = 'button';
      addTile.setAttribute('aria-label', 'Add photos from your gallery');
      addTile.addEventListener('click', function () { pick.click(); });
      pick.addEventListener('change', function () {
        if (pick.files && pick.files.length) addFiles(row, pick.files);
      });
      pics.appendChild(pick); pics.appendChild(addTile);

      /* pasting a link still works, tucked under the photos */
      var linkBox = el('div', 'cl-link'); linkBox.hidden = true;
      var linkIn = document.createElement('input');
      linkIn.type = 'text'; linkIn.placeholder = 'Paste the photo link';
      var linkOk = el('button', 'btn sm', 'Add'); linkOk.type = 'button';
      function commit() {
        var u = linkIn.value.trim();
        if (!u) return;
        row.urls.push(u); render(); sync();
      }
      linkOk.addEventListener('click', commit);
      linkIn.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); commit(); } });
      linkBox.appendChild(linkIn); linkBox.appendChild(linkOk);
      var linkToggle = el('button', 'link', 'or paste a link'); linkToggle.type = 'button';
      linkToggle.style.justifySelf = 'start'; linkToggle.style.paddingLeft = '0';
      linkToggle.addEventListener('click', function () { linkBox.hidden = !linkBox.hidden; if (!linkBox.hidden) linkIn.focus(); });
      main.appendChild(num); main.appendChild(top); main.appendChild(oos); main.appendChild(pics);
      main.appendChild(linkToggle); main.appendChild(linkBox);
      card.appendChild(thumb); card.appendChild(main);
      list.appendChild(card);
    });
    addBtn.textContent = '+ Add color ' + (rows.length + 1);
  }

  addBtn.addEventListener('click', function () {
    rows.push({name: '', urls: ['', '']});
    render(); sync();
    var inputs = list.querySelectorAll('.cl-top input');
    if (inputs.length) inputs[inputs.length - 1].focus();
  });
  if (priceInput) priceInput.addEventListener('input', function () {
    var t = priceText();
    list.querySelectorAll('[data-price]').forEach(function (s) { s.textContent = t; });
  });
  form.addEventListener('submit', function (e) {
    if (rows.some(function (r) { return r.pending > 0; })) {
      e.preventDefault();
      alert('Photos are still uploading. Wait a moment, then save.');
      return;
    }
    sync();
  });
  render(); sync();
})();
</script>"""


def _size_rows(v: dict) -> str:
    """One row per size: tick = sold in this size, 'Out of stock' tick = this size is sold out."""
    chosen = [s.strip() for s in (v.get("sizes") or "").split(",") if s.strip()]
    sold = set(v.get("sold_out") or [])
    names = list(dict.fromkeys(chosen))  # only this product's own sizes
    rows = []
    for n in names:
        on, out = n in chosen, n in sold and n in chosen
        cls = ("" if on else " off") + (" sold" if out else "")
        rows.append(
            f'<div class="sz-row{cls}" data-size="{escape(n)}">'
            f'<label><input type="checkbox" class="sz-on" value="{escape(n)}"{" checked" if on else ""}>'
            f'<span class="sz-name">{escape(n)}</span></label>'
            f'<label class="sz-oos"><input type="checkbox" class="sz-out" name="sold_out" value="{escape(n)}"'
            f'{" checked" if out else ""}{"" if on else " disabled"}> Out of stock</label>'
            f'<button type="button" class="sz-rm" aria-label="Remove size {escape(n)}">&times;</button></div>')
    return "".join(rows)


SIZE_JS = r"""<script>
/* Sizes: ticking a size sells it; "Out of stock" marks just that size sold out */
(function () {
  var box = document.getElementById('sz-list');
  if (!box) return;
  var field = document.getElementById('sz-field');
  function sync() {
    var on = [];
    box.querySelectorAll('.sz-row').forEach(function (row) {
      var a = row.querySelector('.sz-on'), b = row.querySelector('.sz-out');
      if (a.checked) on.push(a.value);
      b.disabled = !a.checked;
      if (!a.checked) b.checked = false;
      row.classList.toggle('off', !a.checked);
      row.classList.toggle('sold', a.checked && b.checked);
    });
    field.value = on.join(', ');
  }
  box.addEventListener('change', sync);
  box.addEventListener('click', function (e) {
    var b = e.target.closest('.sz-rm');
    if (b) { b.closest('.sz-row').remove(); sync(); }
  });
  function addSize() {
    var inp = document.getElementById('sz-new');
    var n = inp.value.replace(/[,|=]+/g, ' ').trim().toUpperCase();
    if (!n) return;
    var exists = false;
    box.querySelectorAll('.sz-on').forEach(function (c) { if (c.value === n) { c.checked = true; exists = true; } });
    if (!exists) {
      var row = document.createElement('div');
      row.className = 'sz-row'; row.setAttribute('data-size', n);
      row.innerHTML = '<label><input type="checkbox" class="sz-on" checked><span class="sz-name"></span></label>' +
        '<label class="sz-oos"><input type="checkbox" class="sz-out" name="sold_out"> Out of stock</label>' +
        '<button type="button" class="sz-rm" aria-label="Remove size">&times;</button>';
      row.querySelector('.sz-on').value = n;
      row.querySelector('.sz-out').value = n;
      row.querySelector('.sz-name').textContent = n;
      box.appendChild(row);
    }
    inp.value = ''; sync();
  }
  document.getElementById('sz-add').addEventListener('click', addSize);
  document.getElementById('sz-new').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') { e.preventDefault(); addSize(); }
  });
  box.closest('form').addEventListener('submit', sync);
  sync();
})();
</script>"""


SUBCAT_JS = r"""<script>
/* Block saving when the chosen category has sub-categories but none is picked */
(function () {
  var form = document.getElementById('product-form');
  if (!form) return;
  var subs = {};
  try { subs = JSON.parse(form.dataset.subs || '{}'); } catch (e) {}
  var cat = form.querySelector('select[name=category]');
  var sub = form.querySelector('select[name=subcategory]');
  var box = document.getElementById('sub-err');
  function pretty(s) { return s.replace(/-/g, ' ').replace(/\b\w/g, function (c) { return c.toUpperCase(); }); }
  function hide() { if (box) box.hidden = true; sub.style.borderColor = ''; }
  cat.addEventListener('change', hide);
  sub.addEventListener('change', hide);
  form.addEventListener('submit', function (e) {
    if ((subs[cat.value] || []).length && !sub.value) {
      e.preventDefault();
      box.querySelector('strong').textContent = 'Choose a sub-category for ' + pretty(cat.value) + ' first.';
      box.hidden = false;
      sub.style.borderColor = 'var(--gold)';
      box.scrollIntoView({behavior: 'smooth', block: 'center'});
    }
  });
})();
</script>"""


def product_form_page(v: dict, categories: list, subcategories: dict, error: str | None = None,
                      product_id: str | None = None, msg: str | None = None) -> str:
    def opt(val, label, current):
        return f'<option value="{escape(val)}"{" selected" if val == current else ""}>{escape(label)}</option>'

    cats = "".join(opt(c, c.replace("-", " ").title(), v.get("category")) for c in categories)
    groups = "".join(
        f'<optgroup label="{escape(c.replace("-", " ").title())}">'
        + "".join(opt(s, s.replace("-", " ").title(), v.get("subcategory")) for s in subs) + "</optgroup>"
        for c, subs in subcategories.items() if subs)
    subs = opt("", "None", v.get("subcategory") or "") + groups
    err = f'<div class="err"><strong>{escape(error)}</strong></div>' if error else ""
    editing = bool(product_id)
    slug_field = (f'<input type="text" value="{escape(v.get("slug", ""))}" readonly>'
                  '<p class="hint">The slug is the product\'s web address and stays fixed, so carts and links never break.</p>'
                  if editing else
                  f'<input type="text" name="slug" value="{escape(v.get("slug", ""))}" placeholder="made from the name if left empty">')
    action = f"/admin/products/{product_id}" if editing else "/admin/products/new"
    rows_json = escape(json.dumps(_color_rows(v)))
    body = f"""<div class="head"><div><h1>{"Edit product" if editing else "New product"}</h1>
<p class="sub"><a href="/admin/products" class="link" style="padding:0">&larr; Back to products</a></p></div></div>
{err}
<div class="err" id="sub-err" hidden><strong></strong></div>
<form method="post" action="{action}" id="product-form" data-subs="{escape(json.dumps({k: v for k, v in subcategories.items() if v}))}">
<div class="card">
<div class="fg"><label class="f">Name</label><input type="text" name="name" value="{escape(v.get('name', ''))}" required></div>
<div class="fg"><label class="f">Slug</label>{slug_field}</div>
<div class="fg"><label class="f">Description</label><textarea name="description">{escape(v.get('description', ''))}</textarea></div>
<div class="three">
<div class="fg"><label class="f">Category</label><select name="category">{cats}</select></div>
<div class="fg"><label class="f">Sub-category</label><select name="subcategory">{subs}</select></div>
<div class="fg"><label class="f">Price (EGP)</label><input type="number" name="price" min="0" step="0.01" value="{escape(v.get('price', ''))}" required></div>
</div>
<div class="fg"><label class="f">Sizes</label>
<div class="sz" id="sz-list">{_size_rows(v)}</div>
<input type="hidden" name="sizes" id="sz-field" value="{escape(v.get('sizes', ''))}">
<div class="sz-add"><input type="text" id="sz-new" placeholder="Other size (e.g. 3XL, 32)" autocomplete="off"><button type="button" class="btn sm ghost" id="sz-add">+ Add size</button></div>
<p class="hint">Use × to remove a size. Tick "Out of stock" on a size to hide just that size from buyers.</p></div>
<label class="check"><input type="checkbox" name="in_stock" value="1"{" checked" if v.get("in_stock") else ""}> In stock</label>
<p class="hint">Untick to mark the whole product out of stock.</p>
</div>
<div class="card">
<div class="fg"><label class="f">Main photo URL</label><input type="text" name="image_url" value="{escape(v.get('image_url', ''))}">
<p class="hint">Used for social sharing and as the fallback. If you leave it empty, the first color photo is used.</p></div>
<div class="fg" style="margin-bottom:0"><label class="f">Colors &amp; photos</label>
<div id="cl-list" data-rows="{rows_json}" data-slug="{escape(v.get('slug', ''))}"></div>
<button type="button" class="btn sm ghost" id="cl-add">+ Add color</button>
<input type="hidden" name="colors" id="cl-colors" value="{escape(v.get('colors', ''))}">
<input type="hidden" name="sold_out_colors" id="cl-sold" value="">
<textarea name="photos" id="cl-photos" style="display:none">{escape(v.get('photos', ''))}</textarea>
<p class="hint">One card per color. Photos show as Front, Back, then Photo 3 and so on. Tap + to add photos from your gallery (you can pick several at once), or paste a link. Tap × to remove one.
The price on each color is the product price above.</p></div>
</div>
<button class="btn" style="width:100%">{"Save changes" if editing else "Add product"}</button>
</form>
{SIZE_JS}{COLOR_EDITOR_JS}{SUBCAT_JS}"""
    return admin_page("Edit product" if editing else "New product", body, "products", msg)


# --------------------------------------------------------------- orders ----
def _order_card(o: dict, q: str, view: str = "active") -> str:
    items = o.get("order_items") or []
    subtotal = sum(float(i["unit_price"]) * int(i["quantity"]) for i in items)
    pay = PAYMENT_METHODS.get(o.get("payment_method"), {}).get("label") or (o.get("payment_method") or "")
    status = o.get("status") or "new"
    pstatus = o.get("payment_status") or "pending"
    st = "history" if view == "history" else (status if status in ("new", "confirmed", "shipped", "delivered", "cancelled") else "other")
    cls = f"st-{st}"
    pcls = "good" if pstatus == "paid" else ""
    discount = float(o.get("discount") or 0)
    code = (o.get("discount_code") or "").strip()
    note = (o.get("promotion_note") or "").strip()
    has_promo = bool(discount > 0 or code or note)
    promo_badge = '<span class="badge promo">Promotion</span>' if has_promo else ""
    foot_left = promo_badge or '<span class="s">Tap for details</span>'
    promo_box = ""
    if has_promo:
        bits = []
        if note:
            bits.append(f'<div class="kv"><span class="l">Promotion</span><b>{escape(note)}</b></div>')
        if code:
            bits.append(f'<div class="kv"><span class="l">Code</span><b>{escape(code)}</b></div>')
        if discount > 0:
            bits.append(f'<div class="kv"><span class="l">Saved</span><b>{_money(discount)}</b></div>')
        promo_box = f'<section class="op promo-op"><h3>Promotion used</h3>{"".join(bits)}</section>'
    discount_line = (f'<div class="sum"><span>Discount{f" ({escape(code)})" if code else ""}</span>'
                     f'<span>-{_money(discount)}</span></div>') if discount > 0 else ""
    item_rows = "".join(
        f"""<div class="oi"><div class="thumb">{f'<img src="{escape(i["image"])}" alt="" loading="lazy">' if i.get("image") else ""}</div>
<div class="grow"><p class="t">{escape(i['product_name'])}</p>
<p class="s">{escape(' / '.join(x for x in [i.get('size'), i.get('color')] if x))}</p></div>
<div class="oi-r"><span class="s">{int(i['quantity'])} × {_money(i['unit_price'])}</span>
<strong>{_money(float(i['unit_price']) * int(i['quantity']))}</strong></div></div>""" for i in items)
    email = (f'<a class="u" href="mailto:{escape(o["email"])}">{escape(o["email"])}</a>'
             if o.get("email") else '<span class="mut">Not given</span>')
    proof = (f'<div class="kv"><span class="l">Proof</span><a class="u" href="{escape(o["payment_proof_url"])}" target="_blank" rel="noopener">View payment proof</a></div>'
             if o.get("payment_proof_url") else "")

    def sel(name, values, current):
        vals = values + ([current] if current not in values else [])
        return f'<select name="{name}">' + "".join(
            f'<option value="{escape(x)}"{" selected" if x == current else ""}>{escape(x.title())}</option>' for x in vals) + "</select>"

    # a cancelled order has no payment: show and edit only its status, so it can be brought back
    cancelled = status == "cancelled"
    pay_status = "" if cancelled else (
        f'<div class="kv"><span class="l">Status</span><span class="badge {pcls}">{escape(pstatus)}</span></div>')
    status_field = f'<div><label class="f">Order status</label>{sel("status", ORDER_STATUSES, status)}</div>'
    payment_field = f'<div><label class="f">Payment</label>{sel("payment_status", PAYMENT_STATUSES, pstatus)}</div>'
    update_fields = (
        status_field + '<p class="hint">Cancelled orders have no payment. Change the status to bring this order back.</p>'
        if cancelled else f'<div class="pair">{status_field}{payment_field}</div>')

    return f"""<details class="order st-{st}"><summary>
<div class="oband"><span class="on">#{escape(o['order_number'])}</span><span class="badge {cls}">{escape(status)}</span></div>
<div class="obody"><p class="oc">{escape(o['customer_name'])}</p>
<p class="s">{_dt(o.get('created_at'))} · {len(items)} item{'s' if len(items) != 1 else ''}</p></div>
<div class="ofoot">{foot_left}<strong class="ototal">{_money(o['total'])}</strong></div></summary>
<div class="ob">
<section class="op"><h3>Customer</h3>
<div class="kv"><span class="l">Name</span><b>{escape(o['customer_name'])}</b></div>
<div class="kv"><span class="l">Phone</span><a class="u" href="tel:{escape(o['phone'])}">{escape(o['phone'])}</a></div>
<div class="kv"><span class="l">Email</span>{email}</div>
<div class="kv"><span class="l">Address</span><b>{escape(o['address'])}, {escape(o['city'])}</b></div></section>
<section class="op"><h3>Items<small>{len(items)}</small></h3>{item_rows}
<div class="ot"><div class="sum"><span>Subtotal</span><span>{_money(subtotal)}</span></div>
{discount_line}
<div class="sum"><span>Shipping ({escape(o['city'])})</span><span>{_money(o.get('shipping'))}</span></div>
<div class="sum tot"><span>Total</span><span>{_money(o['total'])}</span></div></div></section>
{promo_box}
<section class="op"><h3>Payment</h3>
<div class="kv"><span class="l">Method</span><b>{escape(pay)}</b></div>
{pay_status}{proof}</section>
<form method="post" action="/admin/orders/{o['id']}/status" class="op"><h3>Update</h3>
<input type="hidden" name="q" value="{escape(q)}"><input type="hidden" name="view" value="{escape(view)}">
{update_fields}
<button class="btn" style="width:100%;margin-top:12px">Save</button></form>
<form method="post" action="/admin/orders/{o['id']}/delete" style="margin:0" onsubmit="return confirm('Move this order to Recently Deleted?')">
<input type="hidden" name="q" value="{escape(q)}"><input type="hidden" name="view" value="{escape(view)}"><button class="link" style="padding-left:0">Delete order</button></form>
</div></details>"""


ORDER_SYNC_JS = """<script>
/* Delivered and Paid go together: picking one picks the other */
document.addEventListener('change', function (e) {
  var el = e.target;
  if (!el || el.tagName !== 'SELECT') return;
  var form = el.form;
  if (!form) return;
  var status = form.querySelector('select[name=status]');
  var pay = form.querySelector('select[name=payment_status]');
  if (!status || !pay) return;
  if (el === status && status.value === 'delivered') pay.value = 'paid';
  if (el === status && status.value !== 'delivered' && status.value !== 'cancelled' && pay.value === 'paid') pay.value = 'pending';
  if (el === pay && pay.value === 'paid') status.value = 'delivered';
});
</script>"""


def orders_page(orders: list, q: str, msg: str | None = None, view: str = "active") -> str:
    cards = "".join(_order_card(o, q, view) for o in orders)
    if not cards:
        cards = f'<div class="empty">{"No orders match that search." if q else "No orders in this tab."}</div>'
    tabs = "".join(
        f'<a href="/admin/orders?view={k}" class="tab {k}{" on" if k == view else ""}">{label}</a>'
        for k, label in ORDER_VIEWS)
    body = f"""<div class="head"><div><h1>Orders</h1><p class="sub">Newest first · tap an order for the full details</p></div></div>
<div class="tabs">{tabs}</div>
<form class="search" method="get" action="/admin/orders"><input type="hidden" name="view" value="{escape(view)}"><input type="search" name="q" value="{escape(q)}" data-live autocomplete="off"
placeholder="Search order number, name, phone or email"></form><div id="results">{cards}</div>{ORDER_SYNC_JS}"""
    return admin_page("Orders", body, "orders", msg)


# ------------------------------------------------------------ customers ----
def customers_page(customers: list, q: str) -> str:
    rows = []
    for c in customers:
        email = escape(c["email"]) if c["email"] else "No email"
        ini = escape((c["name"] or "?").strip()[:1].upper() or "?")
        rows.append(f"""<div class="row cust" data-i="{ini}"><div class="grow"><p class="t">{escape(c['name'])}</p>
<p class="s">{escape(c['phone'])} · {email}</p></div>
<div class="s">{c['orders']} order{'s' if c['orders'] != 1 else ''} · {_money(c['spent'])}<br>Last: {_dt(c['last'])}</div>
<a class="btn sm ghost" href="/admin/orders?q={escape(c['phone'] or c['name'])}">View orders</a></div>""")
    listing = "".join(rows) or f'<div class="empty">{"No customers match that search." if q else "No customers yet."}</div>'
    body = f"""<div class="head"><div><h1>Customers</h1><p class="sub">Built from orders · {len(customers)} shown</p></div></div>
<form class="search" method="get" action="/admin/customers"><input type="search" name="q" value="{escape(q)}" data-live autocomplete="off"
placeholder="Search by name, phone or email"></form><div id="results">{listing}</div>"""
    return admin_page("Customers", body, "customers")


# ----------------------------------------------------------- promotions ----
def promotions_page(promos: list, msg: str | None = None, error: str | None = None, form: dict | None = None) -> str:
    f = form or {}
    err = f'<div class="err"><strong>{escape(error)}</strong></div>' if error else ""
    labels = {"live": ("Live on site", "ok"), "scheduled": ("Scheduled", ""), "ended": ("Ended", ""), "off": ("Off", "")}
    rows = []
    for p in promos:
        text, cls = labels[promo_state(p)]
        dates = " → ".join(x for x in [
            _dt(p.get("starts_at")).split(",")[0] if p.get("starts_at") else "",
            _dt(p.get("ends_at")).split(",")[0] if p.get("ends_at") else ""] if x)
        link = f" · {escape(p['link_text'] or '')} → {escape(p['link_url'])}" if p.get("link_url") else ""
        flip = "Turn off" if p.get("is_active") else "Turn on"
        rows.append(f"""<div class="pc"><div class="pc-band"><span class="k">Banner</span><span class="badge {cls}">{text}</span></div>
<div class="pc-body"><p class="t" style="font-size:16px">{escape(p['message'])}</p>
<p class="s">{escape(dates) or 'No dates set'}{link}</p></div>
<div class="pc-foot"><form method="post" action="/admin/promotions/{p['id']}/toggle"><button class="btn sm ghost">{flip}</button></form>
<form method="post" action="/admin/promotions/{p['id']}/delete" style="margin-left:auto" onsubmit="return confirm('Move this promotion to Recently Deleted?')">
<button class="link">Delete</button></form></div></div>""")
    listing = "".join(rows) or '<div class="empty">No promotions yet.</div>'
    body = f"""<div class="head"><div><h1>Promotions</h1>
<p class="sub">Live promotions appear in a gold bar at the top of the website (changes show within a minute).</p></div></div>{err}
<details class="newp"{" open" if error else ""}><summary class="btn">+ New promotion</summary>
<form method="post" action="/admin/promotions/new">
<section class="sect"><div class="sect-h"><b>1</b><h2>Promotion</h2></div><div class="sect-b">
<div class="fg"><label class="f">Promotion text</label><input type="text" name="message" maxlength="160" value="{escape(f.get('message', ''))}"
placeholder="e.g. Free shipping on orders over 1500 EGP" required></div>
<div class="two"><div class="fg" style="margin-bottom:0"><label class="f">Button text (optional)</label><input type="text" name="link_text" value="{escape(f.get('link_text', ''))}" placeholder="Shop now"></div>
<div class="fg" style="margin-bottom:0"><label class="f">Link (optional)</label><input type="text" name="link_url" value="{escape(f.get('link_url', ''))}" placeholder="/shop?category=pants"></div></div>
</div></section>
<section class="sect"><div class="sect-h"><b>2</b><h2>Schedule</h2></div><div class="sect-b">
<div class="two"><div class="fg" style="margin-bottom:0"><label class="f">Starts (optional)</label><input type="date" name="starts" value="{escape(f.get('starts', ''))}"></div>
<div class="fg" style="margin-bottom:0"><label class="f">Ends (optional)</label><input type="date" name="ends" value="{escape(f.get('ends', ''))}"></div></div>
</div></section>
<button class="btn" style="width:100%">Add promotion</button></form></details>{listing}"""
    return admin_page("Promotions", body, "promotions", msg)


# ------------------------------------------------------ recently deleted ----
def deleted_page(groups: dict, days: int, msg: str | None = None) -> str:
    titles = {"products": "Products", "orders": "Orders", "promotions": "Promotions"}
    total = sum(len(v) for v in groups.values())

    def card(kind: str, i: dict) -> str:
        left = int(i["days_left"])
        pct = max(4, min(100, round(left / max(days, 1) * 100)))
        soon = " soon" if left <= 7 else ""
        plural = "" if left == 1 else "s"
        return f"""<div class="dl-card{soon}">
<div class="dl-top"><span class="dl-ico">{_ICONS[kind]}</span>
<div class="grow"><p class="t">{escape(i['label'])}</p><p class="s">{escape(i['detail'])}</p></div>
<span class="badge{' ok' if soon else ''}">{left} day{plural} left</span></div>
<div class="dl-bar"><i style="width:{pct}%"></i></div>
<p class="dl-when">Deleted {_dt(i['deleted_at'])}</p>
<div class="dl-acts">
<form method="post" action="/admin/deleted/{kind}/{i['id']}/restore"><button class="btn sm">Restore</button></form>
<form method="post" action="/admin/deleted/{kind}/{i['id']}/purge" onsubmit="return confirm('Delete this forever? This cannot be undone.')">
<button class="link">Delete forever</button></form></div></div>"""

    tiles = "".join(
        f'<div class="dl-tile"><span class="dl-ico">{_ICONS[k]}</span><b>{len(groups.get(k, []))}</b><small>{titles[k]}</small></div>'
        for k in titles
    )
    sections = "".join(
        f'<div class="dl-sec"><h2>{titles[k]}</h2><span>{len(groups[k])} item{"" if len(groups[k]) == 1 else "s"}</span></div>'
        + "".join(card(k, i) for i in groups[k])
        for k in titles if groups.get(k)
    )
    empty = (f'<div class="dl-empty"><span class="dl-ico">{_ICONS["trash"]}</span><b>Nothing deleted</b>'
             f'<p>Anything you delete shows up here for {days} days, so you can bring it back.</p></div>')
    body = f"""{_PAGES_CSS}
<div class="head"><div><h1>Recently deleted</h1>
<p class="sub">Deleted items stay here for {days} days, then are removed for good.</p></div></div>
<div class="dl-tiles">{tiles}</div>
{sections if total else empty}"""
    return admin_page("Recently deleted", body, "deleted", msg)


# ------------------------------------------------------------ dashboard ----
ADMIN_NAME = "Sobhy"

_HOME_CSS = """<style>
.hm-hero{position:relative;overflow:hidden;padding:34px 28px 30px;margin-bottom:14px;border:1px solid var(--line);
  background:repeating-linear-gradient(45deg,rgba(199,154,70,.07) 0 1px,transparent 1px 9px),
  linear-gradient(135deg,rgba(199,154,70,.20),rgba(199,154,70,.02) 65%),var(--ink-raised);}
.hm-stitch{position:absolute;inset:8px;border:1px dashed rgba(199,154,70,.38);pointer-events:none;}
.hm-hero h1{position:relative;font-size:68px;line-height:.95;margin:0 0 18px;letter-spacing:.01em;}
.hm-hero h1 em{font-style:normal;color:var(--gold);}
.hm-rule{position:relative;width:46px;height:3px;background:var(--gold);margin:0 0 14px;}
.hm-date{position:relative;display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin:0;
  font-size:13px;letter-spacing:.2em;text-transform:uppercase;color:var(--paper-dim);}
.hm-date b{color:var(--paper);font-weight:600;}
.hm-tiles{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px;}
.hm-tile{background:var(--ink-raised);border:1px solid var(--line);padding:16px;}
.hm-tile.hot{border-color:var(--gold);background:linear-gradient(135deg,rgba(199,154,70,.16),rgba(199,154,70,.03));}
.hm-k{margin:0 0 8px;font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--paper-dim);font-weight:600;}
.hm-tile.hot .hm-k{color:var(--gold);}
.hm-v{margin:0;font-family:"Big Shoulders Display",sans-serif;font-size:32px;line-height:1;}
.hm-n{margin:7px 0 0;font-size:12px;color:var(--paper-dim);}
.hm-card{background:var(--ink-raised);border:1px solid var(--line);margin-bottom:14px;overflow:hidden;}
.hm-card-h{display:flex;align-items:baseline;justify-content:space-between;gap:10px;padding:12px 16px;
  background:rgba(241,236,226,.06);border-bottom:1px solid var(--line);}
.hm-card-h h2{margin:0;font-family:"Big Shoulders Display",sans-serif;font-size:19px;text-transform:uppercase;letter-spacing:.04em;}
.hm-card-h span,.hm-card-h a{font-size:12px;color:var(--paper-dim);}
.hm-card-h a{text-decoration:underline;}
.hm-card-h a:hover{color:var(--gold);}
.hm-chart{display:flex;align-items:flex-end;gap:8px;height:150px;padding:18px 16px 0;}
.hm-col{flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;height:100%;min-width:0;}
.hm-bar{width:100%;background:var(--gold-dim);border-radius:2px 2px 0 0;min-height:2px;}
.hm-col.now .hm-bar{background:var(--gold);}
.hm-lbl{display:flex;gap:8px;padding:8px 16px 14px;}
.hm-lbl span{flex:1;text-align:center;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--paper-dim);}
.hm-lbl span.now{color:var(--gold);}
.hm-ord{display:flex;align-items:center;gap:12px;padding:12px 16px;border-bottom:1px solid var(--line);}
.hm-ord:last-child{border-bottom:none;}
.hm-ord:hover{background:rgba(241,236,226,.04);}
.hm-ord .grow{flex:1 1 auto;min-width:0;}
.hm-amt{font-size:13.5px;font-weight:600;white-space:nowrap;}
.hm-empty{padding:26px 16px;text-align:center;color:var(--paper-dim);font-size:13.5px;}
.hm-health{display:grid;grid-template-columns:repeat(3,1fr);}
.hm-health div{padding:14px 10px;text-align:center;border-right:1px solid var(--line);}
.hm-health div:last-child{border-right:none;}
.hm-health b{display:block;font-family:"Big Shoulders Display",sans-serif;font-size:26px;line-height:1;margin-bottom:5px;}
.hm-health b.warn{color:var(--gold);}
.hm-health small{font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--paper-dim);}
.hm-links{display:grid;grid-template-columns:1fr 1fr;gap:8px;}
.hm-link{display:block;padding:14px 16px;background:var(--ink-raised);border:1px solid var(--line);
  font-family:"Big Shoulders Display",sans-serif;font-size:19px;text-transform:uppercase;letter-spacing:.04em;}
.hm-link:hover{border-color:var(--gold);color:var(--gold);}
@media (min-width:700px){.hm-tiles{grid-template-columns:repeat(4,1fr);}.hm-links{grid-template-columns:repeat(4,1fr);}}
</style>"""


def dashboard_page(d: dict, msg: str | None = None) -> str:
    h = d["hour"]
    hello = "Good morning" if h < 12 else "Good afternoon" if h < 18 else "Good evening"
    plural = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
    open_n = d["open_orders"]
    tiles = [
        ("Today's sales", _money(d["today_sales"]), plural(d["today_orders"], "order") + " today", False),
        ("Last 30 days", _money(d["month_sales"]), plural(d["month_orders"], "order"), False),
        ("Open orders", str(open_n), "Waiting on you" if open_n else "All caught up", open_n > 0),
        ("Live promotions", str(d["live_promos"]), "Running right now" if d["live_promos"] else "None running", False),
    ]
    tiles_html = "".join(
        f'<div class="hm-tile{" hot" if hot else ""}"><p class="hm-k">{k}</p><p class="hm-v">{v}</p><p class="hm-n">{n}</p></div>'
        for k, v, n, hot in tiles
    )

    peak = max((x["sales"] for x in d["week"]), default=0) or 1
    cols = "".join(
        f'<div class="hm-col{" now" if x["today"] else ""}" title="{escape(_money(x["sales"]))}">'
        f'<div class="hm-bar" style="height:{max(2, round(x["sales"] / peak * 100)) if x["sales"] else 2}%"></div></div>'
        for x in d["week"]
    )
    labels = "".join(f'<span class="{"now" if x["today"] else ""}">{x["label"]}</span>' for x in d["week"])

    if d["recent"]:
        recent = "".join(
            f'<a class="hm-ord" href="/admin/orders?q={escape(str(o.get("order_number") or ""))}">'
            f'<div class="grow"><p class="t">Order {escape(str(o.get("order_number") or ""))}</p>'
            f'<p class="s">{escape(str(o.get("customer_name") or ""))} · {_dt(o.get("created_at"))}</p></div>'
            f'<span class="badge">{escape(str(o.get("status") or "new"))}</span>'
            f'<span class="hm-amt">{_money(o.get("total"))}</span></a>'
            for o in d["recent"]
        )
    else:
        recent = '<div class="hm-empty">No orders yet. They will show up here as they come in.</div>'

    so = d["sold_out"]
    wd, _, rest = d["weekday"].partition(" ")
    body = f"""{_HOME_CSS}
<div class="hm-hero"><div class="hm-stitch"></div>
<h1>Hi <em>{escape(ADMIN_NAME)}</em></h1>
<div class="hm-rule"></div>
<p class="hm-date"><b>{escape(wd)}</b><span>{escape(rest)}</span></p></div>
<div class="hm-tiles">{tiles_html}</div>
<div class="hm-card"><div class="hm-card-h"><h2>Sales, last 7 days</h2><span>{_money(sum(x["sales"] for x in d["week"]))}</span></div>
<div class="hm-chart">{cols}</div><div class="hm-lbl">{labels}</div></div>
<div class="hm-card"><div class="hm-card-h"><h2>Latest orders</h2><a href="/admin/orders">View all</a></div>{recent}</div>"""
    return admin_page("Home", body, "home", msg)
