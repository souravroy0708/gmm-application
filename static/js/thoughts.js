/* GMM thought-card maker. Draws the card on an HTML canvas in the browser, so Bengali text is
   shaped by the browser's own font engine and nothing is uploaded or stored on the server. */
(function () {
  "use strict";
  var d = document, root = d.getElementById("thApp");
  if (!root) return;

  var cfg = root.dataset;
  var cv = d.getElementById("thCanvas"), ctx = cv.getContext("2d");
  var ta = d.getElementById("thText"), nameEl = d.getElementById("thName"), roleEl = d.getElementById("thRole");
  var countEl = d.getElementById("thCount"), noteEl = d.getElementById("thNote");
  var btnDl = d.getElementById("thDownload"), btnShare = d.getElementById("thShare"), btnCap = d.getElementById("thCaption");

  var FQ = '"Anek Bangla","Hind Siliguri","Noto Sans Bengali","Segoe UI",sans-serif';   // thought text
  var FB = '"Hind Siliguri","Noto Sans Bengali","Segoe UI",sans-serif';                   // name, role, footer
  var SIZES = { square: [1080, 1080], story: [1080, 1920] };
  var THEMES = {
    leaf:    { bg: ["#0F2F1E", "#1F6B3A"], text: "#FFFFFF", accent: "#F2C14E", sub: "rgba(255,255,255,.78)", line: "rgba(255,255,255,.22)", deco: 0.07, plate: "#FFFFFF" },
    harvest: { bg: ["#F9D84A", "#E3A800"], text: "#2A1B00", accent: "#1F6B3A", sub: "rgba(42,27,0,.75)",     line: "rgba(42,27,0,.2)",     deco: 0.12, plate: "#FFFFFF" },
    paper:   { bg: ["#FFFFFF", "#EFEBDB"], text: "#1B2A20", accent: "#1F6B3A", sub: "rgba(27,42,32,.7)",     line: "rgba(27,42,32,.15)",   deco: 0.06, plate: "#FFFFFF" },
    earth:   { bg: ["#6B4423", "#34200F"], text: "#FFF4E0", accent: "#F2C14E", sub: "rgba(255,244,224,.78)", line: "rgba(255,244,224,.22)", deco: 0.08, plate: "#FFFFFF" }
  };
  var state = { theme: "leaf", size: "square" };

  // remembered between visits (name / role / look) - optional, never required
  function store(k, v) { try { localStorage.setItem("gmm-th-" + k, v); } catch (e) {} }
  function recall(k) { try { return localStorage.getItem("gmm-th-" + k); } catch (e) { return null; } }

  var logo = new Image();
  logo.onload = function () { schedule(); };
  logo.src = cfg.logo;

  /* ---------- helpers ---------- */
  function clean(s) { return (s || "").replace(/\s+/g, " ").trim(); }

  function rrect(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
  }

  function wrap(text, maxW) {
    var words = text.split(" "), lines = [], cur = "";
    words.forEach(function (w) {
      var test = cur ? cur + " " + w : w;
      if (ctx.measureText(test).width <= maxW) { cur = test; return; }
      if (cur) lines.push(cur);
      if (ctx.measureText(w).width <= maxW) { cur = w; return; }
      // a single very long word: break it by characters
      cur = "";
      Array.from(w).forEach(function (ch) {
        if (ctx.measureText(cur + ch).width > maxW && cur) { lines.push(cur); cur = ch; } else cur += ch;
      });
    });
    if (cur) lines.push(cur);
    return lines;
  }

  function fit(text, maxW, maxH, maxPx, minPx) {
    var px, lines, lh;
    for (px = maxPx; px >= minPx; px -= 2) {
      ctx.font = "700 " + px + "px " + FQ;
      lines = wrap(text, maxW); lh = px * 1.4;
      if (lines.length * lh <= maxH) return { px: px, lines: lines, lh: lh };
    }
    // last resort at the smallest size: squeeze the line spacing so nothing spills into the footer
    lines = wrap(text, maxW);
    return { px: minPx, lines: lines, lh: Math.max(minPx * 1.15, Math.min(minPx * 1.4, maxH / lines.length)) };
  }

  /* ---------- drawing ---------- */
  function draw() {
    var t = THEMES[state.theme], dim = SIZES[state.size], W = dim[0], H = dim[1], story = state.size === "story";
    var text = clean(ta.value) || cfg.sample, name = clean(nameEl.value), role = clean(roleEl.value);
    if (cv.width !== W || cv.height !== H) { cv.width = W; cv.height = H; }

    // background + soft decoration
    var g = ctx.createLinearGradient(0, 0, W, H);
    g.addColorStop(0, t.bg[0]); g.addColorStop(1, t.bg[1]);
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    ctx.save(); ctx.globalAlpha = t.deco; ctx.fillStyle = t.accent;
    ctx.beginPath(); ctx.arc(W * 0.98, H * 0.04, W * 0.36, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.arc(W * 0.0, H * 0.8, W * 0.22, 0, Math.PI * 2); ctx.fill();
    ctx.restore();

    var pad = Math.round(W * 0.085), maxW = W - pad * 2;

    // footer: logo + brand on the left, site on the right
    var ls = Math.round(W * 0.115), footTop = H - pad - ls;
    ctx.fillStyle = t.line; ctx.fillRect(pad, footTop - Math.round(W * 0.035), maxW, 2);
    ctx.save(); rrect(pad, footTop, ls, ls, ls * 0.22); ctx.fillStyle = t.plate; ctx.fill(); ctx.clip();
    if (logo.complete && logo.naturalWidth) { var m = ls * 0.06; ctx.drawImage(logo, pad + m, footTop + m, ls - m * 2, ls - m * 2); }
    ctx.restore();
    var tx = pad + ls + Math.round(W * 0.025);
    ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
    ctx.fillStyle = t.text; ctx.font = "700 " + Math.round(W * 0.036) + "px " + FB;
    ctx.fillText(cfg.brand, tx, footTop + ls * 0.47);
    ctx.fillStyle = t.sub; ctx.font = "500 " + Math.round(W * 0.025) + "px " + FB;
    ctx.fillText(cfg.tag, tx, footTop + ls * 0.84);
    ctx.textAlign = "right"; ctx.fillStyle = t.accent; ctx.font = "700 " + Math.round(W * 0.026) + "px " + FB;
    ctx.fillText(cfg.site, W - pad, footTop + ls * 0.62);
    ctx.textAlign = "left";

    // author block (accent bar, name, role)
    var authH = name ? (role ? W * 0.15 : W * 0.115) : 0, authTop = footTop - Math.round(W * 0.035) - authH - Math.round(W * 0.03);
    if (name) {
      ctx.fillStyle = t.accent; ctx.fillRect(pad, authTop, Math.round(W * 0.11), 6);
      ctx.fillStyle = t.text; ctx.font = "700 " + Math.round(W * 0.042) + "px " + FB;
      ctx.fillText("— " + name, pad, authTop + W * 0.07);
      if (role) { ctx.fillStyle = t.sub; ctx.font = "500 " + Math.round(W * 0.03) + "px " + FB; ctx.fillText(role, pad, authTop + W * 0.115); }
    }

    // big opening quote mark
    var topY = Math.round(story ? H * 0.1 : H * 0.06);
    ctx.fillStyle = t.accent; ctx.font = "700 " + Math.round(W * 0.17) + "px Georgia, 'Times New Roman', serif";
    ctx.fillText("\u201C", pad, topY + W * 0.13);

    // the thought: shrink-to-fit, vertically centred in the free space
    var boxTop = topY + W * 0.14, boxBottom = (name ? authTop : footTop - W * 0.035) - W * 0.04, boxH = boxBottom - boxTop;
    var f = fit(text, maxW, boxH, Math.round(W * (story ? 0.095 : 0.085)), Math.round(W * 0.034));
    ctx.font = "700 " + f.px + "px " + FQ; ctx.fillStyle = t.text; ctx.textBaseline = "alphabetic";
    var y = boxTop + Math.max(0, (boxH - f.lines.length * f.lh) / 2) + f.px;
    f.lines.forEach(function (ln) { ctx.fillText(ln, pad, y); y += f.lh; });

    // buttons only make sense once the person has typed something
    var has = clean(ta.value).length > 0;
    btnDl.disabled = btnShare.disabled = btnCap.disabled = !has;
    countEl.textContent = ta.value.length;
  }

  // wait for the web fonts (Bengali glyph subsets load lazily) before painting
  var pending = false;
  function schedule() {
    if (pending) return; pending = true;
    requestAnimationFrame(function () {
      pending = false;
      var sample = (ta.value || cfg.sample) + (nameEl.value || "") + (roleEl.value || "") + cfg.brand + cfg.tag;
      var loaders = [];
      if (d.fonts && d.fonts.load) {
        ["700 48px \"Anek Bangla\"", "700 32px \"Hind Siliguri\"", "500 32px \"Hind Siliguri\""].forEach(function (f) {
          loaders.push(d.fonts.load(f, sample).catch(function () {}));
        });
      }
      Promise.all(loaders).then(draw, draw);
    });
  }

  /* ---------- actions ---------- */
  function note(msg) { noteEl.textContent = msg; clearTimeout(note.t); note.t = setTimeout(function () { noteEl.textContent = ""; }, 3500); }

  function fileName() {
    var n = new Date(), p = function (x) { return (x < 10 ? "0" : "") + x; };
    return "gmm-thought-" + n.getFullYear() + p(n.getMonth() + 1) + p(n.getDate()) + "-" + p(n.getHours()) + p(n.getMinutes()) + ".png";
  }

  function caption() {
    var name = clean(nameEl.value);
    return "\u201C" + clean(ta.value) + "\u201D" + (name ? "\n— " + name : "") + "\n\n" + cfg.brand + "\n" + (location.protocol + "//" + cfg.site);
  }

  function blob() { draw(); return new Promise(function (res) { cv.toBlob(res, "image/png"); }); }

  function download(b) {
    var a = d.createElement("a"), url = URL.createObjectURL(b);
    a.href = url; a.download = fileName(); d.body.appendChild(a); a.click(); d.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
  }

  btnDl.addEventListener("click", function () {
    blob().then(function (b) { if (!b) throw new Error("blob"); download(b); note(cfg.mSaved); }).catch(function () { note(cfg.mFail); });
  });

  btnShare.addEventListener("click", function () {
    blob().then(function (b) {
      if (!b) throw new Error("blob");
      var file = new File([b], fileName(), { type: "image/png" });
      if (navigator.canShare && navigator.canShare({ files: [file] })) return navigator.share({ files: [file], text: caption() });
      download(b); note(cfg.mSaved);
    }).catch(function (e) { if (e && e.name === "AbortError") return; note(cfg.mFail); });
  });

  btnCap.addEventListener("click", function () {
    var c = caption(), ok = function () { note(cfg.mCopied); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(c).then(ok, function () { window.prompt("Copy:", c); });
    else { var t = d.createElement("textarea"); t.value = c; d.body.appendChild(t); t.select(); try { d.execCommand("copy"); ok(); } catch (e) { window.prompt("Copy:", c); } d.body.removeChild(t); }
  });

  // native share sheet with an image file (Android / iOS); hidden where unsupported
  try {
    var probe = new File([new Blob(["x"])], "x.png", { type: "image/png" });
    if (navigator.share && navigator.canShare && navigator.canShare({ files: [probe] })) btnShare.hidden = false;
  } catch (e) {}

  function pick(groupId, attr, key) {
    var chips = Array.prototype.slice.call(d.querySelectorAll("#" + groupId + " .th-chip"));
    chips.forEach(function (c) {
      c.addEventListener("click", function () {
        state[key] = c.getAttribute(attr); store(key, state[key]);
        chips.forEach(function (x) { x.setAttribute("aria-pressed", x === c ? "true" : "false"); });
        schedule();
      });
    });
    return chips;
  }
  var themeChips = pick("thThemes", "data-theme", "theme"), sizeChips = pick("thSizes", "data-size", "size");
  function restoreChip(chips, attr, key, valid) {
    var v = recall(key); if (!v || !valid[v]) return;
    state[key] = v; chips.forEach(function (c) { c.setAttribute("aria-pressed", c.getAttribute(attr) === v ? "true" : "false"); });
  }
  restoreChip(themeChips, "data-theme", "theme", THEMES);
  restoreChip(sizeChips, "data-size", "size", SIZES);

  var savedName = recall("name"), savedRole = recall("role");
  if (!nameEl.value && savedName) nameEl.value = savedName;
  if (savedRole) roleEl.value = savedRole;

  ta.addEventListener("input", schedule);
  nameEl.addEventListener("input", function () { store("name", nameEl.value); schedule(); });
  roleEl.addEventListener("input", function () { store("role", roleEl.value); schedule(); });

  schedule();
})();
