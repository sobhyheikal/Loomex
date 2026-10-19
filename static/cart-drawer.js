/* Loomex cart drawer: slides in from the right, data comes from /cart/drawer */
(function () {
  var drawer = document.getElementById('cart-drawer');
  var backdrop = document.getElementById('cart-backdrop');
  var body = document.getElementById('cart-drawer-body');
  var foot = document.getElementById('cart-drawer-foot');
  if (!drawer || !backdrop || !body || !foot) return;

  var AJAX = { 'X-Requested-With': 'fetch' };
  var busy = false;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function egp(n) { return Math.round(n) + ' EGP'; }

  function setBadge(count) {
    var link = document.querySelector('.cart-link');
    if (!link) return;
    var badge = link.querySelector('.cart-badge');
    if (!count) { if (badge) badge.remove(); return; }
    if (!badge) {
      badge = document.createElement('span');
      badge.className = 'cart-badge';
      link.appendChild(badge);
    }
    badge.textContent = count;
  }

  function openDrawer() {
    drawer.classList.add('open');
    backdrop.classList.add('open');
    drawer.setAttribute('aria-hidden', 'false');
    document.body.classList.add('cart-open');
  }
  function closeDrawer() {
    drawer.classList.remove('open');
    backdrop.classList.remove('open');
    drawer.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('cart-open');
  }

  function render(data) {
    setBadge(data.count);
    if (!data.lines.length) {
      body.innerHTML = '<p class="cd-empty">Your cart is empty.</p>';
      foot.innerHTML = '<button type="button" class="btn" data-act="close">Continue Shopping</button>';
      return;
    }
    body.innerHTML = data.lines.map(function (l) {
      return '<div class="cd-line">' +
        '<img class="cd-img" src="' + esc(l.image_url) + '" alt="' + esc(l.name) + '">' +
        '<div class="cd-info">' +
          '<p class="cd-name">' + esc(l.name) + '</p>' +
          '<p class="cd-variant">' + esc(l.variant) + '</p>' +
          '<div class="cd-qty">' +
            '<button type="button" data-act="dec" data-index="' + l.index + '" data-qty="' + l.qty + '"' +
              (l.qty <= 1 ? ' disabled' : '') + ' aria-label="Decrease quantity">&minus;</button>' +
            '<span>' + l.qty + '</span>' +
            '<button type="button" data-act="inc" data-index="' + l.index + '" data-qty="' + l.qty + '"' +
              (l.qty >= 10 ? ' disabled' : '') + ' aria-label="Increase quantity">+</button>' +
          '</div>' +
        '</div>' +
        '<div class="cd-side">' +
          '<p class="cd-total">' + egp(l.line_total) + '</p>' +
          '<button type="button" class="cd-remove" data-act="remove" data-index="' + l.index + '">Remove</button>' +
        '</div>' +
      '</div>';
    }).join('');
    foot.innerHTML =
      '<div class="cd-subtotal"><span>Subtotal</span><span>' + egp(data.subtotal) + '</span></div>' +
      '<p class="cd-note">Shipping is calculated at checkout.</p>' +
      '<a href="/checkout" class="btn">Checkout</a>' +
      '<a href="/cart" class="cd-viewcart">View full cart</a>';
  }

  function post(url, fields) {
    var fd = new FormData();
    Object.keys(fields).forEach(function (k) { fd.append(k, fields[k]); });
    return fetch(url, { method: 'POST', body: fd, headers: AJAX, credentials: 'same-origin' })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); });
  }

  function load() {
    if (!body.innerHTML) body.innerHTML = '<p class="cd-empty">Loading…</p>';
    return fetch('/cart/drawer', { headers: AJAX, credentials: 'same-origin' })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(render)
      .catch(function () { window.location.href = '/cart'; });
  }

  function send(url, fields) {
    if (busy) return;
    busy = true;
    post(url, fields)
      .then(render)
      .catch(function () { window.location.href = '/cart'; })
      .finally(function () { busy = false; });
  }

  // Buttons inside the drawer (close, quantity, remove)
  drawer.addEventListener('click', function (e) {
    var t = e.target.closest('[data-act]');
    if (!t || t.disabled) return;
    var act = t.getAttribute('data-act');
    if (act === 'close') return closeDrawer();
    var index = t.getAttribute('data-index');
    if (act === 'remove') return send('/cart/remove', { index: index });
    var qty = Number(t.getAttribute('data-qty')) + (act === 'inc' ? 1 : -1);
    send('/cart/update', { index: index, qty: qty });
  });

  backdrop.addEventListener('click', closeDrawer);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeDrawer(); });
  window.addEventListener('pageshow', function (e) { if (e.persisted) closeDrawer(); });

  // Top-bar cart icon opens the drawer (the /cart page itself is left alone)
  document.addEventListener('click', function (e) {
    var a = e.target.closest('[data-cart-open]');
    if (!a || e.metaKey || e.ctrlKey || window.location.pathname === '/cart') return;
    e.preventDefault();
    openDrawer();
    load();
  });

  // Add to Cart: submit in the background, then open the drawer
  document.addEventListener('submit', function (e) {
    var f = e.target;
    if (!f || f.getAttribute('action') !== '/cart/add') return;
    e.preventDefault();
    var btn = f.querySelector('button[type=submit]');
    if (btn) btn.disabled = true;
    fetch('/cart/add', { method: 'POST', body: new FormData(f), headers: AJAX, credentials: 'same-origin' })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (data) { render(data); openDrawer(); })
      .catch(function () { f.submit(); })
      .finally(function () { if (btn) btn.disabled = false; });
  });
})();