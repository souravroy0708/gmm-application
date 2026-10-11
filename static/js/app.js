// + / - quantity buttons; auto-save in the cart; stop double taps on forms.
document.addEventListener("click", function (e) {
  var b = e.target.closest("[data-step]");
  if (!b) return;
  var i = b.parentNode.querySelector("input");
  var v = (parseInt(i.value, 10) || 0) + parseInt(b.dataset.step, 10);
  i.value = Math.max(parseInt(i.min, 10) || 0, Math.min(parseInt(i.max, 10) || 999, v));
  var f = b.closest("form[data-auto]");
  if (f) { clearTimeout(f._t); f._t = setTimeout(function () { f.submit(); }, 700); }
});
document.addEventListener("submit", function (e) {
  var f = e.target;
  if (f.hasAttribute("data-once")) {
    var s = f.querySelector("button[type=submit]");
    if (s) { s.disabled = true; s.textContent = "Please wait…"; }
  }
});

// ---- homepage: header on scroll, pack stock, add to cart without reload ----
(function () {
  var hdr = document.querySelector("header.top"), home = document.body.classList.contains("home");
  function sc() { hdr.classList.toggle("scrolled", !home || window.scrollY > 24); }
  sc(); window.addEventListener("scroll", sc, { passive: true });

  document.addEventListener("change", function (e) {
    var r = e.target;
    if (!r.matches || !r.matches(".packs input")) return;
    var q = r.form.querySelector("input.q");
    q.max = r.dataset.stock;
    if (+q.value > +q.max) q.value = q.max;
  });

  var toast = document.getElementById("toast"), tt;
  function say(t, warn) {
    toast.textContent = t; toast.className = "toast show" + (warn ? " warn" : "");
    clearTimeout(tt); tt = setTimeout(function () { toast.classList.remove("show"); }, 2600);
  }
  document.addEventListener("submit", function (e) {
    var f = e.target;
    if (!f.matches || !f.matches("form[data-add]") || !window.fetch || !window.DOMParser) return;
    e.preventDefault();
    var b = f.querySelector("button[type=submit]"); b.disabled = true;
    fetch(f.action, { method: "POST", body: new FormData(f), credentials: "same-origin" })
      .then(function (r) { if (!r.ok) throw 0; return r.text(); })
      .then(function (h) {
        var d = new DOMParser().parseFromString(h, "text/html"),
            nav = d.querySelector("nav.tabs"), bar = d.querySelector(".cartbar"), msg = d.querySelector("main .msg");
        if (!nav) throw 0;
        var cur = document.querySelector("nav.tabs"); cur.innerHTML = nav.innerHTML;
        var old = document.querySelector(".cartbar");
        if (bar) { if (old) old.replaceWith(bar); else cur.before(bar); }
        var bd = cur.querySelector(".badge"); if (bd) bd.classList.add("bump");
        say(msg ? msg.textContent.trim() : "✓", msg && msg.classList.contains("warning"));
        b.classList.add("done"); setTimeout(function () { b.classList.remove("done"); }, 1400);
      })
      .catch(function () { HTMLFormElement.prototype.submit.call(f); })
      .then(function () { b.disabled = false; });
  });
})();

// pause the bubbles while the hero is off screen (saves battery on cheap phones)
(function () {
  var h = document.querySelector(".hero2");
  if (h && "IntersectionObserver" in window)
    new IntersectionObserver(function (e) { h.classList.toggle("off", !e[0].isIntersecting); }).observe(h);
})();
