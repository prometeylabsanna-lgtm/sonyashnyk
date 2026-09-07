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

    // Легка тінь у шапці після прокрутки
    var header = document.getElementById("site-header");
    if (header) {
      var onScroll = SonyashnykUtils.debounce(function () {
        header.style.boxShadow = window.scrollY > 8 ? "var(--shadow-card)" : "none";
      }, 30);
      document.addEventListener("scroll", onScroll, { passive: true });
    }
  });
})();
