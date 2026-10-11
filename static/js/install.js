/* GMM install-app experience.
 *
 * Why the old prompt only showed "sometimes": it depended 100% on the browser firing
 * `beforeinstallprompt`. That event never fires on iPhone/iPad, Firefox, Samsung
 * Internet, in-app browsers (Facebook/Instagram), when the app is already installed,
 * or after a user dismisses Chrome's own prompt a few times. This script:
 *   1. grabs the native prompt as early as possible (see the tiny inline script in <head>)
 *   2. always shows the banner + a floating pill on phones, even without the native event
 *   3. falls back to a clear step-by-step sheet, written for the visitor's own browser
 *   4. hides everything once the app is installed / opened from the home screen
 *
 * Any element with a  data-install  attribute also triggers the install flow.
 */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var bar = $("insBar"), fab = $("insFab"), cta = $("insCta"), closeBtn = $("insClose"),
      sheet = $("insSheet");
  if (!bar || !fab || !sheet) return;

  var lang = (document.documentElement.lang || "en").slice(0, 2) === "bn" ? "bn" : "en";
  var KEY_SNOOZE = "gmm-ins-hide", KEY_DONE = "gmm-ins-done", SNOOZE_MS = 3 * 864e5; // ask again after 3 days
  var ua = navigator.userAgent || "";

  /* ---------- environment ---------- */
  var isIOS = /iphone|ipad|ipod/i.test(ua) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  var isAndroid = /android/i.test(ua);
  var isMobile = isIOS || isAndroid;
  var inApp = /FBAN|FBAV|FB_IAB|Instagram|Line\/|Snapchat|Twitter|MicroMessenger|; wv\)/i.test(ua) ||
              (isIOS && !/Safari/i.test(ua));
  var isSamsung = /SamsungBrowser/i.test(ua);
  var isFirefox = /Firefox|FxiOS/i.test(ua);
  var isIOSSafari = isIOS && /Safari/i.test(ua) && !/CriOS|FxiOS|EdgiOS|OPiOS/i.test(ua);

  function standalone() {
    try {
      return matchMedia("(display-mode: standalone)").matches || matchMedia("(display-mode: fullscreen)").matches ||
             matchMedia("(display-mode: minimal-ui)").matches || navigator.standalone === true;
    } catch (e) { return navigator.standalone === true; }
  }
  function get(k) { try { return +localStorage.getItem(k) || 0; } catch (e) { return 0; } }
  function set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function del(k) { try { localStorage.removeItem(k); } catch (e) {} }

  /* ---------- state ---------- */
  var dp = window.__gmmDip || null;     // the native install prompt, if the browser gave us one
  var done = !!get(KEY_DONE) || !!window.__gmmInstalled;
  var related = false;                  // Chrome says the app is already installed
  var armed = false;                    // banner delay has passed
  if (dp) { done = false; del(KEY_DONE); } // native prompt proves it is NOT installed (any more)

  function eligible() {
    if (standalone() || related) return false;
    if (dp) return true;                // native prompt available: works everywhere
    if (done) return false;
    return isMobile;                    // phones: show it and guide manually. Desktop without prompt: stay quiet.
  }
  function snoozed() { var t = get(KEY_SNOOZE); return t && Date.now() - t < SNOOZE_MS; }

  var bannerShown = false, compactTimer = null;
  // single place that decides what is on screen: banner first, otherwise the floating pill
  function sync() {
    var ok = eligible();
    if (!ok) bar.hidden = true;
    var showFab = ok && bar.hidden;
    if (showFab && fab.hidden) {
      fab.classList.toggle("compact", bannerShown);   // already saw the banner: keep the pill small
      clearTimeout(compactTimer);
      if (!bannerShown) compactTimer = setTimeout(function () { fab.classList.add("compact"); }, 6500);
    }
    fab.hidden = !showFab;
  }
  function showBar() {
    if (!armed || !eligible() || snoozed() || !bar.hidden) return;
    bar.classList.remove("out", "ok");
    bar.hidden = false; bannerShown = true;
    sync();
  }
  function hideBar() {
    if (bar.hidden) return;
    bar.classList.add("out");
    setTimeout(function () { bar.hidden = true; bar.classList.remove("out"); sync(); }, 260);
  }

  /* ---------- install flow ---------- */
  function installed() {
    if (done && bar.classList.contains("ok")) return;
    var wasShown = !bar.hidden;
    done = true; dp = null; set(KEY_DONE, Date.now());
    closeSheet();
    if (wasShown) {                       // thank the visitor, then tidy away
      bar.classList.add("ok"); fab.hidden = true;
      setTimeout(hideBar, 3000);
    } else sync();
  }

  function install() {
    if (dp) {
      var ev = dp; dp = null; window.__gmmDip = null; // a prompt event can only be used once
      try { ev.prompt(); } catch (e) { openSheet(); return; }
      if (ev.userChoice && ev.userChoice.then) {
        ev.userChoice.then(function (c) {
          if (c && c.outcome === "accepted") installed();
          else { set(KEY_SNOOZE, Date.now()); hideBar(); sync(); }
        });
      }
    } else {
      openSheet();
    }
  }

  /* ---------- "how to install" sheet ---------- */
  var ico = function (n) { return '<span class="insh-ic"><svg class="ic"><use href="#i-' + n + '"/></svg></span>'; };
  var TXT = {
    en: {
      title: "How to install the GMM app", sub: "3 quick steps. Free, and no Play Store needed.", ok: "Got it",
      inappTitle: "Open in your browser first",
      ios: ["Tap the " + ico("share") + " Share button at the bottom of the screen",
            "Scroll down and choose " + ico("addbox") + " <b>Add to Home Screen</b>",
            "Tap <b>Add</b> at the top right. The GMM app is now on your home screen"],
      iosNote: "Tip: this works best in Safari. In another browser, open this page in Safari first.",
      android: ["Tap the " + ico("dots") + " menu at the top right of your browser",
                "Choose <b>Install app</b> (or <b>Add to Home screen</b>)",
                "Tap <b>Install</b>. The GMM icon appears on your home screen"],
      samsung: ["Tap the <b>≡</b> menu at the bottom right",
                "Choose <b>Add page to</b>, then <b>Home screen</b>",
                "Tap <b>Add</b>. The GMM icon appears on your home screen"],
      firefox: ["Tap the " + ico("dots") + " menu in Firefox",
                "Choose <b>Install</b>",
                "Tap <b>Add</b> to confirm"],
      desktop: ["Look for the " + ico("download") + " install icon at the right end of the address bar",
                "Click <b>Install</b>"],
      inapp: ["Tap the " + ico("dots") + " menu at the top right",
              "Choose <b>Open in Chrome</b> or <b>Open in browser</b> (on iPhone: <b>Open in Safari</b>)",
              "On the page that opens, tap <b>Install</b> again"],
      inappNote: "Apps cannot be installed from inside the Facebook, Instagram or WhatsApp browser."
    },
    bn: {
      title: "GMM অ্যাপ ইনস্টল করবেন কীভাবে?", sub: "মাত্র ৩টি ধাপ। বিনামূল্যে, প্লে স্টোর লাগবে না।", ok: "বুঝেছি",
      inappTitle: "আগে আপনার ব্রাউজারে খুলুন",
      ios: ["স্ক্রিনের নিচে " + ico("share") + " শেয়ার বোতামে ট্যাপ করুন",
            "নিচে স্ক্রল করে " + ico("addbox") + " <b>Add to Home Screen</b> বেছে নিন",
            "উপরে ডানদিকে <b>Add</b> ট্যাপ করুন। হোম স্ক্রিনে GMM অ্যাপ চলে আসবে"],
      iosNote: "পরামর্শ: Safari ব্রাউজারে সবচেয়ে ভালো কাজ করে। অন্য ব্রাউজার হলে এই পেজটি আগে Safari-তে খুলুন।",
      android: ["ব্রাউজারের উপরে ডানদিকে " + ico("dots") + " মেনুতে ট্যাপ করুন",
                "<b>Install app</b> (বা <b>Add to Home screen</b>) বেছে নিন",
                "<b>Install</b> ট্যাপ করুন। হোম স্ক্রিনে GMM আইকন চলে আসবে"],
      samsung: ["নিচে ডানদিকে <b>≡</b> মেনুতে ট্যাপ করুন",
                "<b>Add page to</b> এবং তারপর <b>Home screen</b> বেছে নিন",
                "<b>Add</b> ট্যাপ করুন। হোম স্ক্রিনে GMM আইকন চলে আসবে"],
      firefox: ["Firefox-এর " + ico("dots") + " মেনুতে ট্যাপ করুন",
                "<b>Install</b> বেছে নিন",
                "নিশ্চিত করতে <b>Add</b> ট্যাপ করুন"],
      desktop: ["ঠিকানা বারের ডানদিকে " + ico("download") + " ইনস্টল আইকনটি খুঁজুন",
                "<b>Install</b> ক্লিক করুন"],
      inapp: ["উপরে ডানদিকের " + ico("dots") + " মেনুতে ট্যাপ করুন",
              "<b>Open in Chrome</b> বা <b>Open in browser</b> বেছে নিন (আইফোনে: <b>Open in Safari</b>)",
              "যে পেজ খুলবে সেখানে আবার <b>Install</b> ট্যাপ করুন"],
      inappNote: "ফেসবুক, ইনস্টাগ্রাম বা হোয়াটসঅ্যাপের ভেতরের ব্রাউজার থেকে অ্যাপ ইনস্টল করা যায় না।"
    }
  };

  var card = sheet.querySelector(".insh-card"), lastFocus = null;

  function content() {
    var t = TXT[lang], o = { title: t.title, steps: null, note: "" };
    if (inApp) { o.title = t.inappTitle; o.steps = t.inapp; o.note = t.inappNote; }
    else if (isIOS) { o.steps = t.ios; o.note = isIOSSafari ? "" : t.iosNote; }
    else if (isSamsung) o.steps = t.samsung;
    else if (isFirefox && isAndroid) o.steps = t.firefox;
    else if (isAndroid) o.steps = t.android;
    else o.steps = t.desktop;
    return o;
  }

  function openSheet() {
    var t = TXT[lang], c = content();
    $("inshT").textContent = c.title;
    $("inshSub").textContent = t.sub;
    $("inshSteps").innerHTML = "<li><span>" + c.steps.join("</span></li><li><span>") + "</span></li>";
    $("inshNote").textContent = c.note;
    $("inshOk").querySelector("span").textContent = t.ok;
    lastFocus = document.activeElement;
    sheet.hidden = false;
    document.documentElement.classList.add("ins-lock");
    requestAnimationFrame(function () { requestAnimationFrame(function () { sheet.classList.add("on"); card.focus(); }); });
  }
  function closeSheet() {
    if (sheet.hidden) return;
    sheet.classList.remove("on");
    document.documentElement.classList.remove("ins-lock");
    setTimeout(function () { sheet.hidden = true; }, 280);
    if (lastFocus && lastFocus.focus) { try { lastFocus.focus(); } catch (e) {} }
  }

  /* ---------- events ---------- */
  cta.addEventListener("click", install);
  fab.addEventListener("click", install);
  closeBtn.addEventListener("click", function () { set(KEY_SNOOZE, Date.now()); hideBar(); });
  document.addEventListener("click", function (e) {
    var el = e.target.closest && e.target.closest("[data-install]");
    if (el) { e.preventDefault(); install(); }
    else if (e.target.closest && e.target.closest("[data-ins-close]")) closeSheet();
  });
  document.addEventListener("keydown", function (e) {
    if (sheet.hidden) return;
    if (e.key === "Escape") { closeSheet(); return; }
    if (e.key === "Tab") { // keep focus inside the dialog
      var f = card.querySelectorAll("button,[href],[tabindex]:not([tabindex='-1'])");
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && (document.activeElement === first || document.activeElement === card)) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });

  // the browser handed us the native prompt (possibly after the page loaded)
  window.addEventListener("gmm:dip", function () {
    dp = window.__gmmDip; related = false; done = false; del(KEY_DONE);
    sync(); showBar();
  });
  window.addEventListener("appinstalled", installed);
  try { matchMedia("(display-mode: standalone)").addEventListener("change", sync); } catch (e) {}

  // Chrome on Android can tell us the app is already installed
  if (!dp && navigator.getInstalledRelatedApps) {
    navigator.getInstalledRelatedApps().then(function (apps) {
      if (apps && apps.length && !dp) { related = true; sync(); }
    }).catch(function () {});
  }

  /* ---------- go ---------- */
  sync();
  setTimeout(function () { armed = true; showBar(); }, 1200);
})();
