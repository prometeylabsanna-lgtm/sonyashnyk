/* ============================================================
   КАРТКА ТОВАРУ — галерея (свайп), вибір об'єму, таби, "1 клік"
   ============================================================ */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    initGallery();
    initTabs();
    initVariants();
  });

  function initGallery() {
    var main = document.querySelector("[data-gallery-main]");
    var thumbs = Array.prototype.slice.call(document.querySelectorAll("[data-gallery-thumb]"));
    if (!main || !thumbs.length) return;
    var slides = Array.prototype.slice.call(main.querySelectorAll("[data-gallery-slide]"));

    thumbs.forEach(function (thumb, i) {
      thumb.addEventListener("click", function () {
        slides[i].scrollIntoView({ behavior: "smooth", inline: "start", block: "nearest" });
      });
    });

    if ("IntersectionObserver" in window) {
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var idx = slides.indexOf(entry.target);
            thumbs.forEach(function (t) { t.classList.remove("is-active"); });
            if (thumbs[idx]) thumbs[idx].classList.add("is-active");
          }
        });
      }, { root: main, threshold: 0.6 });
      slides.forEach(function (s) { observer.observe(s); });
    }
  }

  function initTabs() {
    var nav = document.querySelector("[data-pdp-tabs-nav]");
    if (!nav) return;
    var buttons = Array.prototype.slice.call(nav.querySelectorAll("[data-pdp-tab-btn]"));
    var panels = Array.prototype.slice.call(document.querySelectorAll("[data-pdp-tab-panel]"));

    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var target = btn.getAttribute("data-pdp-tab-btn");
        buttons.forEach(function (b) { b.classList.remove("is-active"); });
        panels.forEach(function (p) { p.classList.remove("is-active"); });
        btn.classList.add("is-active");
        var panel = document.querySelector('[data-pdp-tab-panel="' + target + '"]');
        if (panel) panel.classList.add("is-active");
      });
    });
  }

  function initVariants() {
    var chips = Array.prototype.slice.call(document.querySelectorAll("[data-variant-chip]"));
    if (!chips.length) return;
    var priceEl = document.querySelector("[data-pdp-price]");
    var oldPriceEl = document.querySelector("[data-pdp-old-price]");
    var stockEl = document.querySelector("[data-pdp-stock]");
    var cartBtn = document.querySelector("[data-add-to-cart]");
    var buyOneClickBtn = document.querySelector("[data-lead-open][data-lead-type='buy_one_click']");

    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        if (chip.disabled) return;
        chips.forEach(function (c) { c.classList.remove("is-active"); });
        chip.classList.add("is-active");

        var price = chip.getAttribute("data-price");
        var oldPrice = chip.getAttribute("data-old-price");
        var inStock = chip.getAttribute("data-in-stock") === "1";
        var variantId = chip.getAttribute("data-variant-id");

        if (priceEl) priceEl.textContent = price + " ₴";
        if (oldPriceEl) {
          if (oldPrice) { oldPriceEl.textContent = oldPrice + " ₴"; oldPriceEl.style.display = ""; }
          else { oldPriceEl.style.display = "none"; }
        }
        if (stockEl) {
          stockEl.textContent = inStock ? "В наявності" : "Немає в наявності";
          stockEl.classList.toggle("is-out", !inStock);
        }
        if (cartBtn) {
          cartBtn.setAttribute("data-variant-id", variantId);
          cartBtn.disabled = !inStock;
        }
        if (buyOneClickBtn) buyOneClickBtn.disabled = !inStock;
      });
    });
  }
})();
