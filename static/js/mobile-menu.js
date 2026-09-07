/* ============================================================
   МОБІЛЬНЕ МЕНЮ — drawer з категоріями + акордеон підкатегорій
   ============================================================ */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    var menu = document.querySelector("[data-mobile-menu]");
    var openBtn = document.querySelector("[data-mobile-menu-toggle]");
    if (!menu || !openBtn) return;

    function open() {
      menu.classList.add("is-open");
      menu.setAttribute("aria-hidden", "false");
      SonyashnykUtils.lockScroll();
    }
    function close() {
      if (!menu.classList.contains("is-open")) return;
      menu.classList.remove("is-open");
      menu.setAttribute("aria-hidden", "true");
      SonyashnykUtils.unlockScroll();
    }

    openBtn.addEventListener("click", open);
    menu.querySelectorAll("[data-mobile-menu-close]").forEach(function (el) {
      el.addEventListener("click", close);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") close();
    });

    menu.querySelectorAll("[data-accordion-toggle]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var item = btn.closest(".mobile-menu__item");
        item.classList.toggle("is-expanded");
      });
    });
  });
})();
