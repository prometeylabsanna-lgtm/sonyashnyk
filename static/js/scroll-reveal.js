/* ============================================================
   SCROLL REVEAL — легка появи блоків при скролі (IntersectionObserver)
   ============================================================ */
(function () {
  "use strict";

  var observer = null;

  function revealNow(el) {
    el.classList.add("is-visible");
  }

  function observe(root) {
    var scope = root && root.querySelectorAll ? root : document;
    var items = scope.querySelectorAll("[data-reveal]:not(.is-visible)");
    if (!items.length) return;

    if (!("IntersectionObserver" in window)) {
      items.forEach(revealNow);
      return;
    }

    if (!observer) {
      observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            revealNow(entry.target);
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.15, rootMargin: "0px 0px -40px 0px" });
    }

    items.forEach(function (el) { observer.observe(el); });
  }

  document.addEventListener("DOMContentLoaded", function () {
    observe(document);
  });

  window.SonyashnykReveal = { observe: observe, revealNow: revealNow };
})();
