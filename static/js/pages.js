/* ============================================================
   ІНФОСТОРІНКИ — FAQ-акордеон (Доставка і оплата) + фільтр сертифікатів
   ============================================================ */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-faq-toggle]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        btn.closest(".faq-item").classList.toggle("is-open");
      });
    });

    var filterBtns = Array.prototype.slice.call(document.querySelectorAll("[data-cert-filter]"));
    var cards = Array.prototype.slice.call(document.querySelectorAll("[data-cert-card]"));
    if (filterBtns.length && cards.length) {
      filterBtns.forEach(function (btn) {
        btn.addEventListener("click", function () {
          var series = btn.getAttribute("data-cert-filter");
          filterBtns.forEach(function (b) { b.classList.remove("is-active"); });
          btn.classList.add("is-active");
          cards.forEach(function (card) {
            var show = series === "all" || card.getAttribute("data-series") === series;
            card.style.display = show ? "" : "none";
          });
        });
      });
    }
  });
})();
