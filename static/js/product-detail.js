/* ============================================================
   КАРТКА ТОВАРУ — галерея (мініатюри + свайп)
   ============================================================ */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    initGallery();
  });

  function initGallery() {
    var main = document.querySelector("[data-gallery-main]");
    var thumbs = Array.prototype.slice.call(document.querySelectorAll("[data-gallery-thumb]"));
    if (!main || !thumbs.length) return;

    var slides = Array.prototype.slice.call(main.querySelectorAll("[data-gallery-slide]"));

    thumbs.forEach(function (thumb, i) {
      thumb.addEventListener("click", function () {
        var slide = slides[i];
        if (!slide) return;
        var left = slide.offsetLeft;
        if (typeof main.scrollTo === "function") {
          main.scrollTo({ left: left, behavior: "smooth" });
        } else {
          main.scrollLeft = left;
        }
        setActiveThumb(thumbs, i);
      });
    });

    if ("IntersectionObserver" in window) {
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var idx = slides.indexOf(entry.target);
          if (idx >= 0) setActiveThumb(thumbs, idx);
        });
      }, { root: main, threshold: 0.55 });
      slides.forEach(function (s) { observer.observe(s); });
    }
  }

  function setActiveThumb(thumbs, idx) {
    thumbs.forEach(function (t, i) {
      t.classList.toggle("is-active", i === idx);
    });
  }
})();
