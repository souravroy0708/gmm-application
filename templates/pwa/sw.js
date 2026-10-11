{% load static %}/* GMM service worker - built for very slow / no internet.
   - The thought-card page + all its files (JS, CSS, logo, director photo, Bengali fonts) are saved
     on the phone at install time, so the card maker works fully offline.
   - Public pages (home, shop list, advisory, contact...) open instantly from the saved copy and
     refresh quietly in the background when the network allows.
   - Private pages (cart, checkout, orders, invoices, login, admin) are NEVER cached. */
const VERSION = "gmm-v4";
const FONT_CSS = "{% static 'css/fonts.css' %}";
const OFFLINE = "{% url 'pages:offline' %}";
const THOUGHTS = "{% url 'thoughts:create' %}";
const PAGES = [THOUGHTS, "/", "{% url 'pages:contact' %}", "{% url 'pages:leadership' %}",
  "{% url 'pages:vision_mission' %}", "{% url 'advisory:index' %}"];
const PUBLIC_PREFIX = ["/thoughts/", "/contact/", "/leadership/", "/vision-mission/", "/krishi-paramarsha/"];
const STATIC = [OFFLINE,
  "{% static 'css/app.css' %}", "{% static 'css/premium.css' %}?v=2", "{% static 'css/pages.css' %}",
  "{% static 'css/theme.css' %}", "{% static 'css/krishi.css' %}", "{% static 'css/install.css' %}?v=2",
  "{% static 'css/thoughts.css' %}", "{% static 'css/thoughts-nav.css' %}?v=1",
  "{% static 'js/install.js' %}?v=2", "{% static 'js/app.js' %}", "{% static 'js/thoughts.js' %}",
  "{% static 'images/logo.jpg' %}", "{% static 'images/chikur-kumar-ray.jpg' %}",
  "{% static 'pwa/icon-192.png' %}", "{% static 'pwa/icon-512.png' %}", "{% static 'pwa/apple-touch-icon.png' %}",
  "{% static 'images/krishi/paddy.svg' %}", "{% static 'images/krishi/potato.svg' %}",
  "{% static 'images/krishi/jute.svg' %}", "{% static 'images/krishi/mustard.svg' %}",
  "{% static 'images/krishi/brinjal.svg' %}"];

function isPublicPage(p) { return p === "/" || PUBLIC_PREFIX.some(function (x) { return p.indexOf(x) === 0; }); }
function safe(fn) { return fn.catch(function () {}); }

// Save the local font CSS and every font file it points to (Bengali + Latin), so text renders offline.
function cacheFonts(c) {
  return fetch(FONT_CSS).then(function (r) { return r.ok ? r : Promise.reject(); }).then(function (r) {
    return c.put(FONT_CSS, r.clone()).then(function () { return r.text(); });
  }).then(function (css) {
    var urls = (css.match(/url\(([^)]+)\)/g) || []).map(function (x) { return new URL(x.slice(4, -1).replace(/['"]/g, ""), new URL(FONT_CSS, location.origin)).pathname; });
    return Promise.all(urls.map(function (u) { return safe(c.add(u)); }));
  });
}

// Save every photo a page uses (product images etc.) so shop pages look complete offline.
function cacheImagesFrom(c, res) {
  return res.clone().text().then(function (html) {
    var urls = {}, re = /(?:src|data-src)=["'](\/(?:media|static)\/[^"']+\.(?:webp|jpe?g|png|svg))["']/g, m;
    while ((m = re.exec(html))) urls[m[1]] = 1;
    return Promise.all(Object.keys(urls).map(function (u) { return safe(c.match(u).then(function (h) { return h || c.add(u); })); }));
  }).catch(function () {});
}

self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(VERSION).then(function (c) {
    var jobs = STATIC.map(function (u) { return safe(c.add(u)); })
      .concat(PAGES.map(function (u) {
        return safe(fetch(u, { credentials: "same-origin" }).then(function (res) {
          if (res.status !== 200) return; c.put(u, res.clone()); return cacheImagesFrom(c, res);
        }));
      }))
      .concat([safe(cacheFonts(c))]);
    return Promise.all(jobs);
  }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener("activate", function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== VERSION; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

// cached copy first, refresh in the background (instant on slow networks)
function staleWhileRevalidate(r, ignoreSearch) {
  return caches.open(VERSION).then(function (c) {
    return c.match(r, { ignoreSearch: !!ignoreSearch }).then(function (hit) {
      var net = fetch(r).then(function (res) {
        if (res && (res.status === 200 || res.type === "opaque")) c.put(r, res.clone());
        return res;
      }).catch(function () { return hit; });
      return hit || net;
    });
  });
}

// network, but give up after `ms` and use the saved copy
function networkFirst(r, ms) {
  return caches.open(VERSION).then(function (c) {
    return new Promise(function (resolve) {
      var done = false;
      function fallback() {
        if (done) return; done = true;
        c.match(r, { ignoreSearch: true }).then(function (hit) { resolve(hit || c.match(OFFLINE)); });
      }
      var t = setTimeout(fallback, ms);
      fetch(r).then(function (res) {
        clearTimeout(t);
        if (res && res.status === 200 && res.type === "basic") { c.put(r, res.clone()); cacheImagesFrom(c, res); }
        if (!done) { done = true; resolve(res); }
      }).catch(function () { clearTimeout(t); fallback(); });
    });
  });
}

self.addEventListener("fetch", function (e) {
  var r = e.request;
  if (r.method !== "GET") return;
  var u = new URL(r.url);

  if (u.origin !== location.origin) return;

  if (r.mode === "navigate") {
    if (u.pathname === THOUGHTS) { e.respondWith(staleWhileRevalidate(r, true)); return; }   // card maker: always instant
    if (isPublicPage(u.pathname)) { e.respondWith(networkFirst(r, 4000)); return; }          // public pages: 4s then saved copy
    e.respondWith(fetch(r).catch(function () { return caches.match(OFFLINE); }));            // private pages: network only
    return;
  }
  if (u.pathname.indexOf("/static/") === 0 || u.pathname.indexOf("/media/products/") === 0) {
    e.respondWith(staleWhileRevalidate(r));
  }
});
