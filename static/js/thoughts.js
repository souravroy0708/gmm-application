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
  var warnEl = d.getElementById("thWarn"), warnBtn = d.getElementById("thWarnBtn");
  var btnDl = d.getElementById("thDownload"), btnShare = d.getElementById("thShare"), btnCap = d.getElementById("thCaption");

  var FQ = '"Anek Bangla","Hind Siliguri","Noto Sans Bengali","Segoe UI",sans-serif';   // thought text
  var FB = '"Hind Siliguri","Noto Sans Bengali","Segoe UI",sans-serif';                   // name, role, footer
  var SIZES = { square: [1080, 1080], portrait: [1080, 1350], story: [1080, 1920] };
  var THEMES = {
    leaf:    { bg: ["#0F2F1E", "#1F6B3A"], text: "#FFFFFF", accent: "#F2C14E", sub: "rgba(255,255,255,.78)", line: "rgba(255,255,255,.22)", deco: 0.07, plate: "#FFFFFF", glow: "rgba(255,255,255,.10)", panel: "rgba(255,255,255,.09)", panelLine: "rgba(255,255,255,.18)", onAccent: "#0F2F1E" },
    harvest: { bg: ["#F9D84A", "#E3A800"], text: "#2A1B00", accent: "#1F6B3A", sub: "rgba(42,27,0,.75)",     line: "rgba(42,27,0,.2)",     deco: 0.12, plate: "#FFFFFF", glow: "rgba(255,255,255,.28)", panel: "rgba(255,255,255,.42)", panelLine: "rgba(42,27,0,.14)",    onAccent: "#FFFFFF" },
    paper:   { bg: ["#FFFFFF", "#EFEBDB"], text: "#1B2A20", accent: "#1F6B3A", sub: "rgba(27,42,32,.7)",     line: "rgba(27,42,32,.15)",   deco: 0.06, plate: "#FFFFFF", glow: "rgba(242,193,78,.16)",  panel: "rgba(31,107,58,.07)",   panelLine: "rgba(31,107,58,.16)",  onAccent: "#FFFFFF" },
    earth:   { bg: ["#6B4423", "#34200F"], text: "#FFF4E0", accent: "#F2C14E", sub: "rgba(255,244,224,.78)", line: "rgba(255,244,224,.22)", deco: 0.08, plate: "#FFFFFF", glow: "rgba(255,255,255,.09)", panel: "rgba(255,255,255,.08)", panelLine: "rgba(255,244,224,.18)", onAccent: "#34200F" }
  };
  var state = { theme: "leaf", size: "square", foot: "dir" };

  // remembered between visits (name / role / look) - optional, never required
  function store(k, v) { try { localStorage.setItem("gmm-th-" + k, v); } catch (e) {} }
  function recall(k) { try { return localStorage.getItem("gmm-th-" + k); } catch (e) { return null; } }

  var logo = new Image();
  logo.onload = function () { schedule(); };
  logo.src = cfg.logo;
  var dirImg = new Image();                      // director's photo for the footer (same origin, so the canvas stays exportable)
  dirImg.onload = function () { schedule(); };
  if (cfg.dirPhoto) dirImg.src = cfg.dirPhoto;

  /* ---------- helpers ---------- */
  function clean(s) { return (s || "").replace(/\s+/g, " ").trim(); }

  function rrect(x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
  }

  // a single leaf, pointing along +x from (0,0)
  function leaf(len) {
    ctx.beginPath(); ctx.moveTo(0, 0);
    ctx.quadraticCurveTo(len * 0.45, -len * 0.38, len, 0);
    ctx.quadraticCurveTo(len * 0.45, len * 0.38, 0, 0); ctx.fill();
  }

  // a small curved sprig with paired leaves, grown upward from (x, y)
  function sprig(x, y, s, color, alpha) {
    ctx.save(); ctx.translate(x, y); ctx.globalAlpha = alpha; ctx.fillStyle = color; ctx.strokeStyle = color;
    ctx.lineWidth = Math.max(2, s * 0.03); ctx.lineCap = "round";
    ctx.beginPath(); ctx.moveTo(0, 0); ctx.quadraticCurveTo(-s * 0.12, -s * 0.5, s * 0.05, -s); ctx.stroke();
    [[0.28, -1], [0.28, 1], [0.52, -1], [0.52, 1], [0.76, -1], [0.76, 1]].forEach(function (p, i) {
      var t = p[0], side = p[1], px = -s * 0.12 * (1 - Math.abs(2 * t - 1)) * 0.5 + s * 0.05 * t * 0.4, py = -s * t;
      ctx.save(); ctx.translate(px, py); ctx.rotate(side < 0 ? -Math.PI * 0.72 : -Math.PI * 0.28); leaf(s * (0.36 - i * 0.025)); ctx.restore();
    });
    ctx.save(); ctx.translate(s * 0.05, -s); ctx.rotate(-Math.PI / 2); leaf(s * 0.26); ctx.restore();
    ctx.restore();
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

  /* ---------- footer ---------- */
  // Logo + brand on the left; director photo, name, role and phone on the right.
  // Everything is measured first and scaled down together so it always fits the card width.
  function footer(t, W, H, pad, maxW) {
    var showDir = state.foot === "dir" && cfg.dirName;
    var ph = Math.round(W * (showDir ? 0.19 : 0.15)), py = H - Math.round(W * 0.06) - ph, ip = Math.round(ph * 0.14);
    var innerW = maxW - ip * 2, cy = py + ph / 2, k = 1, m;

    function sizes(k) {
      return {
        logo: W * (showDir ? 0.085 : 0.1) * k, brand: W * (showDir ? 0.03 : 0.036) * k, tag: W * (showDir ? 0.021 : 0.025) * k, gapL: W * 0.017 * k,
        photo: W * 0.125 * k, name: W * 0.028 * k, role: W * 0.02 * k, pill: W * 0.026 * k, gapR: W * 0.019 * k
      };
    }
    function measure(z) {
      ctx.font = "700 " + z.brand + "px " + FB; var bw = ctx.measureText(cfg.brand).width;
      ctx.font = "500 " + z.tag + "px " + FB;   var tw = ctx.measureText(cfg.tag).width;
      var left = z.logo + z.gapL + Math.max(bw, tw), right = 0, nw = 0, rw = 0, pw = 0;
      if (showDir) {
        ctx.font = "700 " + z.name + "px " + FB; nw = ctx.measureText(cfg.dirName).width;
        ctx.font = "500 " + z.role + "px " + FB; rw = ctx.measureText(cfg.dirRole).width;
        ctx.font = "700 " + z.pill + "px " + FB; pw = ctx.measureText(cfg.dirPhone).width + z.pill * 1.4;
        right = z.photo + z.gapR + Math.max(nw, rw, pw);
      }
      return { left: left, right: right, pillW: pw };
    }
    var z = sizes(1);
    for (k = 1; k >= 0.58; k -= 0.02) { z = sizes(k); m = measure(z); if (m.left + m.right + W * 0.03 <= innerW) break; }
    m = measure(z);

    // glass panel
    rrect(pad, py, maxW, ph, ph * 0.2); ctx.fillStyle = t.panel; ctx.fill();
    ctx.lineWidth = 2; ctx.strokeStyle = t.panelLine; ctx.stroke();

    // left: logo plate + brand + tagline
    var lx = pad + ip, ly = cy - z.logo / 2;
    ctx.save(); rrect(lx, ly, z.logo, z.logo, z.logo * 0.22); ctx.fillStyle = t.plate; ctx.fill(); ctx.clip();
    if (logo.complete && logo.naturalWidth) { var mg = z.logo * 0.06; ctx.drawImage(logo, lx + mg, ly + mg, z.logo - mg * 2, z.logo - mg * 2); }
    ctx.restore();
    var tx = lx + z.logo + z.gapL;
    ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
    ctx.fillStyle = t.text; ctx.font = "700 " + z.brand + "px " + FB; ctx.fillText(cfg.brand, tx, cy - z.logo * 0.04);
    ctx.fillStyle = t.sub;  ctx.font = "500 " + z.tag + "px " + FB;   ctx.fillText(cfg.tag, tx, cy + z.logo * 0.38);

    if (!showDir) return py;

    // right: round photo with a ring, then name / role / phone pill (right-aligned to the panel padding)
    var rx = pad + maxW - ip - m.right, pr = z.photo / 2, pcx = rx + pr;
    ctx.save(); ctx.beginPath(); ctx.arc(pcx, cy, pr, 0, Math.PI * 2); ctx.closePath(); ctx.fillStyle = t.plate; ctx.fill(); ctx.clip();
    if (dirImg.complete && dirImg.naturalWidth) { var iw = dirImg.naturalWidth, ih = dirImg.naturalHeight, sw = Math.min(iw, ih) * 0.9; ctx.drawImage(dirImg, (iw - sw) / 2, 0, sw, sw, pcx - pr, cy - pr, z.photo, z.photo); }
    ctx.restore();
    ctx.beginPath(); ctx.arc(pcx, cy, pr + 3, 0, Math.PI * 2); ctx.lineWidth = Math.max(4, z.photo * 0.04); ctx.strokeStyle = t.accent; ctx.stroke();

    var dx = rx + z.photo + z.gapR;
    var groupH = z.name * 1.05 + z.role * 1.45 + z.role * 0.5 + z.pill * 1.55, y0 = cy - groupH / 2;
    var nameBase = y0 + z.name * 1.05, roleBase = nameBase + z.role * 1.45, pillTop = roleBase + z.role * 0.5, pillH = z.pill * 1.55;
    ctx.fillStyle = t.text; ctx.font = "700 " + z.name + "px " + FB; ctx.fillText(cfg.dirName, dx, nameBase);
    ctx.fillStyle = t.sub;  ctx.font = "500 " + z.role + "px " + FB; ctx.fillText(cfg.dirRole, dx, roleBase);
    rrect(dx, pillTop, m.pillW, pillH, pillH / 2); ctx.fillStyle = t.accent; ctx.fill();
    ctx.fillStyle = t.onAccent; ctx.font = "700 " + z.pill + "px " + FB; ctx.fillText(cfg.dirPhone, dx + z.pill * 0.7, pillTop + pillH / 2 + z.pill * 0.34);
    return py;
  }

  /* ---------- drawing ---------- */
  function draw() {
    var t = THEMES[state.theme], dim = SIZES[state.size], W = dim[0], H = dim[1], story = state.size === "story";
    var text = clean(ta.value) || cfg.sample, name = clean(nameEl.value), role = clean(roleEl.value);
    if (cv.width !== W || cv.height !== H) { cv.width = W; cv.height = H; }

    // background: gradient, soft light, large circles
    var g = ctx.createLinearGradient(0, 0, W, H);
    g.addColorStop(0, t.bg[0]); g.addColorStop(1, t.bg[1]);
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    var rg = ctx.createRadialGradient(W * 0.12, H * 0.06, 0, W * 0.12, H * 0.06, W * 0.85);
    rg.addColorStop(0, t.glow); rg.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = rg; ctx.fillRect(0, 0, W, H);
    ctx.save(); ctx.globalAlpha = t.deco; ctx.fillStyle = t.accent;
    ctx.beginPath(); ctx.arc(W * 0.98, H * 0.04, W * 0.36, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.arc(W * 0.0, H * 0.8, W * 0.22, 0, Math.PI * 2); ctx.fill();
    ctx.restore();

    var pad = Math.round(W * 0.085), maxW = W - pad * 2;

    // thin inset frame and a sprig of leaves in the top-right corner
    var fm = Math.round(W * 0.028);
    rrect(fm, fm, W - fm * 2, H - fm * 2, W * 0.03); ctx.lineWidth = 2; ctx.strokeStyle = t.accent; ctx.globalAlpha = 0.35; ctx.stroke(); ctx.globalAlpha = 1;
    var topY = Math.round(story ? H * 0.1 : H * 0.06);
    sprig(W - pad - W * 0.015, topY + W * 0.19, W * 0.15, t.accent, 0.5);

    // footer: logo + brand, director photo + phone
    ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
    var panelTop = footer(t, W, H, pad, maxW), contentBottom = panelTop - Math.round(W * 0.04);

    // author block (accent bar, name, role)
    var authH = name ? (role ? W * 0.15 : W * 0.115) : 0, authTop = contentBottom - authH;
    if (name) {
      ctx.fillStyle = t.accent; ctx.fillRect(pad, authTop, Math.round(W * 0.11), 6);
      ctx.fillStyle = t.text; ctx.font = "700 " + Math.round(W * 0.042) + "px " + FB;
      ctx.fillText("\u2014 " + name, pad, authTop + W * 0.07);
      if (role) { ctx.fillStyle = t.sub; ctx.font = "500 " + Math.round(W * 0.03) + "px " + FB; ctx.fillText(role, pad, authTop + W * 0.115); }
    }

    // big opening quote mark
    ctx.fillStyle = t.accent; ctx.font = "700 " + Math.round(W * 0.17) + "px Georgia, 'Times New Roman', serif";
    ctx.fillText("\u201C", pad, topY + W * 0.13);

    // the thought: shrink-to-fit, vertically centred in the free space
    var boxTop = topY + W * 0.14, boxBottom = (name ? authTop : contentBottom) - W * 0.04, boxH = boxBottom - boxTop;
    var f = fit(text, maxW, boxH, Math.round(W * (story ? 0.095 : 0.085)), Math.round(W * 0.024));
    ctx.font = "700 " + f.px + "px " + FQ; ctx.fillStyle = t.text; ctx.textBaseline = "alphabetic";
    var y = boxTop + Math.max(0, (boxH - f.lines.length * f.lh) / 2) + f.px;
    f.lines.forEach(function (ln) { ctx.fillText(ln, pad, y); y += f.lh; });

    // very long text on a short card: offer a taller size so the letters stay readable
    var next = state.size === "square" ? "portrait" : "story";
    warnEl.hidden = !(f.px < W * 0.036 && state.size !== "story");
    if (!warnEl.hidden) { warnBtn.dataset.size = next; warnBtn.textContent = next === "portrait" ? cfg.mPortrait : cfg.mStory; }

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
      var sample = (ta.value || cfg.sample) + (nameEl.value || "") + (roleEl.value || "") + cfg.brand + cfg.tag + (cfg.dirName || "") + (cfg.dirRole || "") + (cfg.dirPhone || "");
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
  var themeChips = pick("thThemes", "data-theme", "theme"), sizeChips = pick("thSizes", "data-size", "size"), footChips = pick("thFoot", "data-foot", "foot");
  function restoreChip(chips, attr, key, valid) {
    var v = recall(key); if (!v || !valid[v]) return;
    state[key] = v; chips.forEach(function (c) { c.setAttribute("aria-pressed", c.getAttribute(attr) === v ? "true" : "false"); });
  }
  restoreChip(themeChips, "data-theme", "theme", THEMES);
  restoreChip(sizeChips, "data-size", "size", SIZES);
  restoreChip(footChips, "data-foot", "foot", { dir: 1, brand: 1 });

  var savedName = recall("name"), savedRole = recall("role");
  if (!nameEl.value && savedName) nameEl.value = savedName;
  if (savedRole) roleEl.value = savedRole;

  warnBtn.addEventListener("click", function () {
    var chip = d.querySelector('#thSizes .th-chip[data-size="' + warnBtn.dataset.size + '"]');
    if (chip) chip.click();
  });

  ta.addEventListener("input", schedule);
  nameEl.addEventListener("input", function () { store("name", nameEl.value); schedule(); });
  roleEl.addEventListener("input", function () { store("role", roleEl.value); schedule(); });

  schedule();
})();
