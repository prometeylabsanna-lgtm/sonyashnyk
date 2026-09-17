/* ============================================================
   MAIN — дрібна ініціалізація, що не варта окремого файлу
   ============================================================ */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    // Перемикач мови в logobar (зберігає ua/ru для клієнтських підказок форм)
    var langGroup = document.querySelector(".logobar__lang");
    if (langGroup) {
      var storedLang = "";
      try {
        storedLang = window.localStorage.getItem(
          (window.SonyashnykFormValidation && SonyashnykFormValidation.LANG_KEY) || "sonyashnyk_lang"
        ) || "";
      } catch (e) { /* ignore */ }

      if (storedLang) {
        var normalized = window.SonyashnykFormValidation
          ? SonyashnykFormValidation.normalizeLang(storedLang)
          : (storedLang === "ru" ? "ru" : "uk");
        langGroup.querySelectorAll("button[data-lang]").forEach(function (b) {
          var code = (b.getAttribute("data-lang") || "").toLowerCase();
          var isActive = normalized === "ru" ? code === "ru" : code === "ua" || code === "uk";
          b.classList.toggle("is-active", isActive);
        });
        document.documentElement.lang = normalized === "ru" ? "ru" : "uk";
      }

      langGroup.querySelectorAll("button[data-lang]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          langGroup.querySelectorAll("button").forEach(function (b) {
            b.classList.remove("is-active");
          });
          btn.classList.add("is-active");
          var raw = btn.getAttribute("data-lang") || "ua";
          var lang = window.SonyashnykFormValidation
            ? SonyashnykFormValidation.normalizeLang(raw)
            : (raw === "ru" ? "ru" : "uk");
          try {
            window.localStorage.setItem(
              (window.SonyashnykFormValidation && SonyashnykFormValidation.LANG_KEY) || "sonyashnyk_lang",
              lang === "ru" ? "ru" : "ua"
            );
          } catch (e) { /* ignore */ }
          document.documentElement.lang = lang === "ru" ? "ru" : "uk";
          document.dispatchEvent(new CustomEvent("sonyashnyk:langchange", { detail: { lang: lang } }));
        });
      });
    }

    // Тінь sticky-шапки (announce не стискається — лише від’їжджає)
    var header = document.getElementById("site-header");
    if (header) {
      var scrolled = false;
      var ticking = false;
      var HIDE_AT = 24;
      var SHOW_AT = 8;

      function syncHeaderScroll() {
        ticking = false;
        var y = window.scrollY || window.pageYOffset || 0;
        var next = scrolled ? y > SHOW_AT : y > HIDE_AT;
        if (next === scrolled) return;
        scrolled = next;
        header.classList.toggle("is-scrolled", scrolled);
      }

      function onScroll() {
        if (ticking) return;
        ticking = true;
        window.requestAnimationFrame(syncHeaderScroll);
      }

      document.addEventListener("scroll", onScroll, { passive: true });
      syncHeaderScroll();
    }
  });
})();
