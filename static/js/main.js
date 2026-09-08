/* ============================================================
   MAIN — дрібна ініціалізація, що не варта окремого файлу
   ============================================================ */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    // Перемикач мови в announce-барі (візуальний стан; повний i18n — наступний етап)
    document.querySelectorAll(".announce__lang button").forEach(function (btn) {
      btn.addEventListener("click", function () {
        btn.parentElement.querySelectorAll("button").forEach(function (b) {
          b.classList.remove("is-active");
        });
        btn.classList.add("is-active");
      });
    });

    // Ховання announce-бару + тінь шапки після прокрутки
    var header = document.getElementById("site-header");
    var announce = header ? header.querySelector(".announce") : null;
    if (header) {
      var scrolled = false;
      var ticking = false;
      var SCROLL_HIDE_AT = 12;

      function syncHeaderScroll() {
        ticking = false;
        var next = window.scrollY > SCROLL_HIDE_AT;
        if (next === scrolled) return;
        scrolled = next;
        header.classList.toggle("is-scrolled", scrolled);
        header.style.boxShadow = scrolled ? "var(--shadow-card)" : "none";
        if (announce) {
          announce.setAttribute("aria-hidden", scrolled ? "true" : "false");
        }
      }

      function onScroll() {
        if (ticking) return;
        ticking = true;
        window.requestAnimationFrame(syncHeaderScroll);
      }

      document.addEventListener("scroll", onScroll, { passive: true });
      syncHeaderScroll();
    }

    // Wishlist UI-only (без бекенду): локальний toggle стану кнопки
    document.addEventListener("click", function (event) {
      var wish = event.target.closest("[data-wishlist-toggle]");
      if (!wish) return;
      event.preventDefault();
      event.stopPropagation();
      var pressed = wish.getAttribute("aria-pressed") === "true";
      wish.setAttribute("aria-pressed", pressed ? "false" : "true");
    });
  });
})();
