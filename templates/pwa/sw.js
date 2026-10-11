{% load static %}/* GMM service worker. Pages are always fetched from the network (orders, cart and
   invoices are private and must never be served from a stale cache). Only static
   assets and public product photos are cached. */
const VERSION = "gmm-v2";
const OFFLINE = "{% url 'pages:offline' %}";
const CORE = [OFFLINE,
  "{% static 'css/app.css' %}", "{% static 'css/premium.css' %}?v=2",
  "{% static 'css/pages.css' %}", "{% static 'css/theme.css' %}",
  "{% static 'css/install.css' %}?v=2", "{% static 'js/install.js' %}?v=2",
  "{% static 'images/logo.jpg' %}", "{% static 'pwa/icon-192.png' %}"];

self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(VERSION).then(function (c) {
    return Promise.all(CORE.map(function (u) { return c.add(u).catch(function () {}); }));
  }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener("activate", function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== VERSION; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener("fetch", function (e) {
  var r = e.request;
  if (r.method !== "GET") return;
  var u = new URL(r.url);
  if (u.origin !== location.origin) return;

  if (r.mode === "navigate") {
    e.respondWith(fetch(r).catch(function () { return caches.match(OFFLINE); }));
    return;
  }
  var isStatic = u.pathname.indexOf("/static/") === 0;
  var isPhoto = u.pathname.indexOf("/media/products/") === 0;
  if (isStatic || isPhoto) {
    e.respondWith(caches.open(VERSION).then(function (c) {
      return c.match(r).then(function (hit) {
        var net = fetch(r).then(function (res) {
          if (res && res.status === 200) c.put(r, res.clone());
          return res;
        }).catch(function () { return hit; });
        return hit || net;
      });
    }));
  }
});
