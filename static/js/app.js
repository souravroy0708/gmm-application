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
