"""Admin panel: push notification setup (manifest, service worker, subscribe / unsubscribe)."""
import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response

from services import admin_auth, push

# no login needed: the browser fetches these files before it can send the admin cookie
public_router = APIRouter()
# under /admin, needs the admin login (included into routers/admin.py)
router = APIRouter(dependencies=[Depends(admin_auth.require_admin)])

MANIFEST = {
    "name": "Loomex Admin",
    "short_name": "LX Admin",
    "start_url": "/admin/orders",
    "scope": "/admin/",
    "display": "standalone",
    "background_color": "#201c18",
    "theme_color": "#201c18",
    "icons": [{"src": "/static/admin-icon.png", "sizes": "180x180", "type": "image/png", "purpose": "any"}],
}

SW_JS = r"""
self.addEventListener('install', function () { self.skipWaiting(); });
self.addEventListener('activate', function (e) { e.waitUntil(self.clients.claim()); });
self.addEventListener('push', function (e) {
  var d = {};
  try { d = e.data.json(); } catch (err) {}
  e.waitUntil(self.registration.showNotification(d.title || 'Loomex', {
    body: d.body || '',
    icon: '/static/admin-icon.png',
    badge: '/static/admin-icon.png',
    tag: d.tag || 'loomex',
    data: { url: d.url || '/admin/orders' }
  }));
});
self.addEventListener('notificationclick', function (e) {
  e.notification.close();
  var url = (e.notification.data && e.notification.data.url) || '/admin/orders';
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (list) {
    for (var i = 0; i < list.length; i++) {
      if (list[i].url.indexOf('/admin') !== -1 && 'focus' in list[i]) {
        if ('navigate' in list[i]) { list[i].navigate(url); }
        return list[i].focus();
      }
    }
    return self.clients.openWindow(url);
  }));
});
"""


@public_router.get("/admin/sw.js")
def service_worker():
    return Response(SW_JS, media_type="application/javascript",
                    headers={"Service-Worker-Allowed": "/admin/", "Cache-Control": "no-cache"})


@public_router.get("/admin/manifest.webmanifest")
def manifest():
    return Response(json.dumps(MANIFEST), media_type="application/manifest+json",
                    headers={"Cache-Control": "no-cache"})


@router.get("/push/key")
def push_key():
    return {"key": push.public_key(), "configured": push.configured()}


@router.post("/push/subscribe")
async def push_subscribe(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"ok": False}, status_code=400)
    try:
        ok = push.save_subscription(data)
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)[:160]}, status_code=500)
    return JSONResponse({"ok": ok}, status_code=200 if ok else 400)


@router.post("/push/unsubscribe")
async def push_unsubscribe(request: Request):
    try:
        data = await request.json()
        push.remove_subscription(data.get("endpoint", ""))
    except Exception:
        pass
    return {"ok": True}


@router.post("/push/test")
def push_test():
    sent = push.send_push("Notifications are on", "You will get an alert here for every new Loomex order.",
                          "/admin/orders", tag="test")
    return {"sent": sent}
