/* ============================================================
   HERO SLIDER — головний банер на головній сторінці
   ============================================================ */
(function () {
  "use strict";

  var AUTOPLAY_MS = 6000;

  document.addEventListener("DOMContentLoaded", function () {
    var hero = document.querySelector("[data-hero]");
    if (!hero) return;

    var slides = Array.prototype.slice.call(hero.querySelectorAll("[data-hero-slide]"));
    var dots = Array.prototype.slice.call(hero.querySelectorAll("[data-hero-dot]"));
    if (slides.length < 2) return;

    var index = 0;
    var timer = null;
    var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function show(newIndex) {
      slides[index].classList.remove("is-active");
      dots[index] && dots[index].classList.remove("is-active");
      index = (newIndex + slides.length) % slides.length;
      slides[index].classList.add("is-active");
      dots[index] && dots[index].classList.add("is-active");
    }

    function next() { show(index + 1); }

    function start() {
      if (reduceMotion) return;
      stop();
      timer = window.setInterval(next, AUTOPLAY_MS);
    }
    function stop() {
      if (timer) window.clearInterval(timer);
      timer = null;
    }

    dots.forEach(function (dot, i) {
      dot.addEventListener("click", function () {
        show(i);
        start();
      });
    });

    hero.addEventListener("mouseenter", stop);
    hero.addEventListener("mouseleave", start);
    hero.addEventListener("focusin", stop);
    hero.addEventListener("focusout", start);

    start();
  });
})();
