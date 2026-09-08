/* ============================================================
   MAIN — дрібна ініціалізація, що не варта окремого файлу
   ============================================================ */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    // Перемикач мови в logobar (візуальний стан; повний i18n — наступний етап)
    document.querySelectorAll(".logobar__lang button").forEach(function (btn) {
      btn.addEventListener("click", function () {
        btn.parentElement.querySelectorAll("button").forEach(function (b) {
          b.classList.remove("is-active");
        });
        btn.classList.add("is-active");
      });
    });

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
