/* ============================================================
   ABOUT STEM — ростуче стебло + листочки при скролі туди-назад
   ============================================================ */
(function () {
  "use strict";

  function clamp(n, min, max) {
    return Math.min(max, Math.max(min, n));
  }

  function prefersReducedMotion() {
    return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var root = document.querySelector("[data-about-stem]");
    if (!root) return;

    var nodes = Array.prototype.slice.call(root.querySelectorAll("[data-stem-node]"));
    if (!nodes.length) return;

    if (prefersReducedMotion()) {
      root.style.setProperty("--grow", "1");
      nodes.forEach(function (node) { node.classList.add("is-open"); });
      return;
    }

    var ticking = false;

    function updateGrow() {
      ticking = false;
      var rect = root.getBoundingClientRect();
      var viewH = window.innerHeight || document.documentElement.clientHeight;
      var start = viewH * 0.72;
      var end = viewH * 0.28;
      var progress = (start - rect.top) / (start - end + rect.height);
      root.style.setProperty("--grow", String(clamp(progress, 0, 1)));
    }

    function onScroll() {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(updateGrow);
    }

    updateGrow();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    if (window.visualViewport) {
      window.visualViewport.addEventListener("resize", onScroll, { passive: true });
    }

    if (!("IntersectionObserver" in window)) {
      nodes.forEach(function (node) { node.classList.add("is-open"); });
      return;
    }

    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          entry.target.classList.toggle("is-open", entry.isIntersecting);
        });
      },
      {
        threshold: [0, 0.2, 0.35],
        rootMargin: "-8% 0px -18% 0px",
      }
    );

    nodes.forEach(function (node) { io.observe(node); });
  });
})();
