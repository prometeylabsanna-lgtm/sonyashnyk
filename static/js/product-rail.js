/* ============================================================
   PRODUCT RAIL — горизонтальна галерея товарів зі стрілками
   ============================================================ */
(function () {
  "use strict";

  function initRail(rail) {
    var track = rail.querySelector("[data-rail-track]");
    var prev = rail.querySelector("[data-rail-prev]");
    var next = rail.querySelector("[data-rail-next]");
    if (!track || !prev || !next) return;

    var items = track.querySelectorAll(".product-rail__item");
    if (items.length < 2) {
      prev.hidden = true;
      next.hidden = true;
      return;
    }

    function stepSize() {
      var first = items[0];
      if (!first) return track.clientWidth * 0.8;
      var styles = window.getComputedStyle(track);
      var gap = parseFloat(styles.columnGap || styles.gap) || 14;
      return first.getBoundingClientRect().width + gap;
    }

    function maxScroll() {
      return Math.max(0, track.scrollWidth - track.clientWidth);
    }

    function updateNav() {
      var left = track.scrollLeft;
      var max = maxScroll();
      var eps = 2;
      prev.disabled = left <= eps;
      next.disabled = left >= max - eps;
      var canScroll = max > eps;
      prev.hidden = !canScroll;
      next.hidden = !canScroll;
    }

    function scrollByDir(dir) {
      track.scrollBy({ left: dir * stepSize(), behavior: "smooth" });
    }

    prev.addEventListener("click", function () { scrollByDir(-1); });
    next.addEventListener("click", function () { scrollByDir(1); });
    track.addEventListener("scroll", updateNav, { passive: true });
    window.addEventListener("resize", updateNav);

    updateNav();
  }

  document.addEventListener("DOMContentLoaded", function () {
    var rails = document.querySelectorAll("[data-product-rail]");
    for (var i = 0; i < rails.length; i++) initRail(rails[i]);
  });
})();
