(function () {
  var d = document, de = d.documentElement; de.classList.add("kp-js");
  var $ = function (s, r) { return (r || d).querySelector(s); }, $$ = function (s, r) { return Array.prototype.slice.call((r || d).querySelectorAll(s)); };

  // reading progress
  var bar = d.createElement("div"); bar.id = "kpProg"; d.body.appendChild(bar);
  function prog() { var h = de.scrollHeight - innerHeight; bar.style.width = (h > 0 ? Math.min(100, scrollY / h * 100) : 0) + "%"; }
  addEventListener("scroll", prog, { passive: true }); prog();

  // reveal on scroll
  var rv = $$(".kp-rv");
  if ("IntersectionObserver" in window && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
    var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }); }, { rootMargin: "0px 0px -8% 0px" });
    rv.forEach(function (el) { io.observe(el); });
  } else rv.forEach(function (el) { el.classList.add("in"); });

  // scroll-spy for the sticky section nav
  var links = $$(".kp-nav a");
  if (links.length && "IntersectionObserver" in window) {
    var map = {}; links.forEach(function (a) { map[a.getAttribute("href").slice(1)] = a; });
    var spy = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { links.forEach(function (a) { a.classList.remove("on"); }); var a = map[e.target.id]; if (a) { a.classList.add("on"); a.scrollIntoView({ block: "nearest", inline: "center" }); } } }); }, { rootMargin: "-30% 0px -60% 0px" });
    Object.keys(map).forEach(function (id) { var el = d.getElementById(id); if (el) spy.observe(el); });
  }

  // season filter on the index
  var chips = $$(".kp-chip"), cards = $$("#kpGrid .kp-card");
  chips.forEach(function (c) { c.addEventListener("click", function () {
    var f = c.dataset.f; chips.forEach(function (x) { x.setAttribute("aria-pressed", x === c ? "true" : "false"); });
    cards.forEach(function (k) { k.hidden = !(f === "all" || (" " + k.dataset.seasons + " ").indexOf(" " + f + " ") > -1); });
  }); });

  // share: native sheet (mobile) + copy link
  $$("[data-share]").forEach(function (b) { if (navigator.share) b.hidden = false; b.addEventListener("click", function () {
    navigator.share({ title: b.dataset.title, text: b.dataset.text, url: b.dataset.url }).catch(function () {}); }); });
  $$("[data-copy]").forEach(function (b) { b.addEventListener("click", function () {
    var u = b.dataset.copy, note = $(".kp-copied"), ok = function () { if (note) { note.textContent = "✓ লিংক কপি হয়েছে"; setTimeout(function () { note.textContent = ""; }, 2500); } };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(u).then(ok, function () { prompt("লিংক কপি করুন:", u); });
    else { var t = d.createElement("textarea"); t.value = u; d.body.appendChild(t); t.select(); try { d.execCommand("copy"); ok(); } catch (e) { prompt("লিংক কপি করুন:", u); } d.body.removeChild(t); }
  }); });
})();
