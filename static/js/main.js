/* ============================================================
   MAIN — дрібна ініціалізація, що не варта окремого файлу
   ============================================================ */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    // Синхронізація клієнтської мови форм з серверною (cookie Django)
    var langGroup = document.querySelector(".logobar__lang");
    var htmlLang = (document.documentElement.lang || "uk").toLowerCase();
    var serverLang = htmlLang.indexOf("ru") === 0 ? "ru" : "uk";
    var langKey =
      (window.SonyashnykFormValidation && SonyashnykFormValidation.LANG_KEY) || "sonyashnyk_lang";

    try {
      window.localStorage.setItem(langKey, serverLang === "ru" ? "ru" : "ua");
    } catch (e) { /* ignore */ }

    if (langGroup) {
      langGroup.querySelectorAll("button[data-lang]").forEach(function (b) {
        var code = (b.getAttribute("data-lang") || "").toLowerCase();
        var isActive = serverLang === "ru" ? code === "ru" : code === "ua" || code === "uk";
        b.classList.toggle("is-active", isActive);
      });
    }

    if (window.SonyashnykFormValidation) {
      SonyashnykFormValidation.applyStaticI18n(document);
    }

    var searchToggle = document.querySelector("[data-mobile-search-toggle]");
    var searchPanel = document.querySelector("[data-mobile-search]");
    if (searchToggle && searchPanel) {
      function setSearchOpen(open) {
        if (open) {
          searchPanel.removeAttribute("hidden");
          searchToggle.setAttribute("aria-expanded", "true");
        } else {
          searchPanel.setAttribute("hidden", "");
          searchToggle.setAttribute("aria-expanded", "false");
        }
      }

      searchToggle.addEventListener("click", function (e) {
        e.preventDefault();
        var willOpen = searchPanel.hasAttribute("hidden");
        setSearchOpen(willOpen);
        if (!willOpen) return;
        var input = searchPanel.querySelector("input[type='search']");
        if (input) input.focus();
      });

      document.addEventListener("keydown", function (e) {
        if (e.key !== "Escape") return;
        if (searchPanel.hasAttribute("hidden")) return;
        setSearchOpen(false);
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
        var y = window.scrollY || window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
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
