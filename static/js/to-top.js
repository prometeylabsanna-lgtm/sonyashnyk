(function () {
  "use strict";

  var btn = document.querySelector("[data-to-top]");
  if (!btn) return;

  var ticking = false;

  function scrollY() {
    return window.scrollY || window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
  }

  function showAt() {
    return window.matchMedia("(max-width: 899.98px)").matches ? 220 : 480;
  }

  function sync() {
    ticking = false;
    btn.hidden = scrollY() <= showAt();
  }

  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(sync);
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  document.addEventListener("scroll", onScroll, { passive: true });
  if (window.visualViewport) {
    window.visualViewport.addEventListener("scroll", onScroll, { passive: true });
    window.visualViewport.addEventListener("resize", onScroll, { passive: true });
  }

  btn.addEventListener("click", function () {
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
  });

  sync();
})();
