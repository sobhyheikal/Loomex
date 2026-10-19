/* Loomex shop: live search + keep the category chips where they were */
document.addEventListener('DOMContentLoaded', function () {
  var KEY = 'loomex_chip_scroll';

  function getPos() {
    var c = document.querySelector('.chips');
    var s = document.querySelector('.subtabs');
    return { c: c ? c.scrollLeft : 0, s: s ? s.scrollLeft : 0 };
  }
  function setPos(p) {
    var c = document.querySelector('.chips');
    var s = document.querySelector('.subtabs');
    if (c) c.scrollLeft = p.c;
    if (s) s.scrollLeft = p.s;
  }
  function revealActive(sel) {
    var bar = document.querySelector(sel);
    var el = bar && bar.querySelector('.active');
    if (!bar || !el) return;
    var b = bar.getBoundingClientRect();
    var e = el.getBoundingClientRect();
    if (e.left < b.left || e.right > b.right) {
      bar.scrollLeft += (e.left - b.left) - (bar.clientWidth - e.width) / 2;
    }
  }

  // Remember the row's scroll position when a chip or sub-tab is tapped
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.chips a, .subtabs a')) return;
    try { sessionStorage.setItem(KEY, JSON.stringify(getPos())); } catch (err) {}
  });

  // Restore it on the new page, then make sure the selected chip is visible
  try {
    var saved = JSON.parse(sessionStorage.getItem(KEY) || 'null');
    if (saved) setPos(saved);
    sessionStorage.removeItem(KEY);
  } catch (err) {}
  revealActive('.chips');
  revealActive('.subtabs');

  // ---- live search ----
  var input = document.getElementById('shop-search');
  if (!input) return;
  var form = input.form;
  var timer = null;
  var seq = 0;

  function run() {
    var params = new URLSearchParams(new FormData(form));
    if (!input.value.trim()) params.delete('q');
    var qs = params.toString();
    var url = '/shop' + (qs ? '?' + qs : '');
    var mine = ++seq;

    fetch(url, { credentials: 'same-origin' })
      .then(function (r) { return r.text(); })
      .then(function (html) {
        if (mine !== seq) return; // a newer keystroke already started
        var pos = getPos();
        var doc = new DOMParser().parseFromString(html, 'text/html');
        ['shop-filters', 'shop-results'].forEach(function (id) {
          var fresh = doc.getElementById(id);
          var cur = document.getElementById(id);
          if (fresh && cur) cur.innerHTML = fresh.innerHTML;
        });
        setPos(pos); // the chips were rebuilt, so put the scroll back
        var clear = document.getElementById('shop-clear');
        if (clear) clear.hidden = !input.value.trim();
        history.replaceState(null, '', url);
      })
      .catch(function () {});
  }

  input.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(run, 150);
  });
});