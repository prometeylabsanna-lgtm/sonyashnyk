/* ============================================================
   SCROLL REVEAL — легка поява блоків при скролі (без бібліотек)
   ============================================================ */
(function () {
  "use strict";

  var STAGGER_STEP = 55;
  var STAGGER_MAX = 8;
  var MOBILE_MQ = "(max-width: 767px)";
  var REDUCE_MQ = "(prefers-reduced-motion: reduce)";

  var observer = null;
  var reduced = false;
  var mobileLite = false;

  var AUTO_SELECTORS = [
    "main .pdp > .gallery",
    "main .pdp > .pdp-info",
    "main .about-intro",
    "main .about-produce",
    "main .contacts-stores",
    "main .contacts-form-block",
    "main .cart-page-section > .container",
    "main .checkout-block",
    "main .checkout-summary",
    "main .thank-you",
    "main .error-404",
    "main .empty-state",
    ".site-footer .footer-cta",
    ".site-footer .footer-panel",
    "main .section__head",
    "main .about-why__title",
    "main .catalog-toolbar",
    "main .cert-filter",
    "main .h1",
    "main .page-content > h1",
    "main .page-content > h2",
    "main .page-content > p",
    "main .page-content > table",
    "main .page-content > ul",
    "main .page-content > .faq-list",
    "main .page-content > .delivery-table"
  ];

  var STAGGER_SELECTORS = [
    "main .grid--cats",
    "main .grid--products",
    "main .trust-bar",
    "main .story-band",
    "main .ticket-grid",
    "main .about-stats",
    "main .subcats",
    "main .product-rail__track",
    "[data-reveal-stagger]"
  ];

  function skip(el) {
    if (!el || el.nodeType !== 1) return true;
    if (el.hasAttribute("data-reveal-skip")) return true;
    if (el.closest("[data-reveal-skip]")) return true;
    if (el.closest(".hero")) return true;
    if (el.closest("[data-about-stem]")) return true;
    if (el.closest(".cart-drawer, .lead-modal, .mobile-menu, #site-header")) return true;
    return false;
  }

  function inViewport(el) {
    var rect = el.getBoundingClientRect();
    var vh = window.innerHeight || document.documentElement.clientHeight;
    return rect.top < vh * 0.92 && rect.bottom > 0;
  }

  function revealNow(el) {
    el.classList.add("is-visible");
  }

  function markReveal(el, delayMs) {
    if (skip(el)) return null;
    if (
      !el.hasAttribute("data-reveal") &&
      el.parentElement &&
      el.parentElement.closest("[data-reveal]")
    ) {
      return null;
    }
    if (!el.hasAttribute("data-reveal")) {
      if (inViewport(el) || reduced) {
        el.classList.add("is-visible");
      }
      el.setAttribute("data-reveal", "");
    }
    if (typeof delayMs === "number" && delayMs > 0 && !mobileLite) {
      el.style.setProperty("--reveal-delay", delayMs + "ms");
    }
    return el;
  }

  function applyStagger(root) {
    var scope = root && root.querySelectorAll ? root : document;
    var parents = [];

    STAGGER_SELECTORS.forEach(function (sel) {
      scope.querySelectorAll(sel).forEach(function (node) {
        parents.push(node);
      });
    });

    parents.forEach(function (parent) {
      var kids = parent.children;
      var count = 0;
      for (var i = 0; i < kids.length; i++) {
        var child = kids[i];
        if (skip(child)) continue;
        if (child.matches && child.matches(".product-rail__nav")) continue;
        var target = child.hasAttribute("data-reveal")
          ? child
          : (child.querySelector("[data-reveal]") || child);
        var delay = mobileLite ? 0 : Math.min(count, STAGGER_MAX) * STAGGER_STEP;
        markReveal(target, delay);
        count += 1;
      }
    });
  }

  function autoMark(root) {
    var scope = root && root.querySelectorAll ? root : document;

    AUTO_SELECTORS.forEach(function (sel) {
      scope.querySelectorAll(sel).forEach(function (el) {
        markReveal(el, 0);
      });
    });

    applyStagger(scope);
  }

  function observe(root) {
    var scope = root && root.querySelectorAll ? root : document;

    autoMark(scope);

    var items = scope.querySelectorAll("[data-reveal]:not(.is-visible)");
    if (!items.length) return;

    if (reduced || !("IntersectionObserver" in window)) {
      items.forEach(revealNow);
      return;
    }

    if (!observer) {
      observer = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (!entry.isIntersecting) return;
            revealNow(entry.target);
            observer.unobserve(entry.target);
          });
        },
        {
          threshold: mobileLite ? 0.06 : 0.12,
          rootMargin: mobileLite ? "0px 0px -12px 0px" : "0px 0px -36px 0px"
        }
      );
    }

    items.forEach(function (el) {
      if (inViewport(el)) {
        revealNow(el);
        return;
      }
      observer.observe(el);
    });
  }

  function syncMotionFlags() {
    reduced = window.matchMedia(REDUCE_MQ).matches;
    mobileLite = window.matchMedia(MOBILE_MQ).matches;
    document.documentElement.classList.toggle("is-motion-lite", mobileLite && !reduced);
    document.documentElement.classList.toggle("is-motion-off", reduced);
  }

  function boot() {
    syncMotionFlags();
    observe(document);

    if (window.matchMedia) {
      var mqMobile = window.matchMedia(MOBILE_MQ);
      var mqReduce = window.matchMedia(REDUCE_MQ);
      var onChange = function () {
        syncMotionFlags();
      };
      if (mqMobile.addEventListener) mqMobile.addEventListener("change", onChange);
      else if (mqMobile.addListener) mqMobile.addListener(onChange);
      if (mqReduce.addEventListener) mqReduce.addEventListener("change", onChange);
      else if (mqReduce.addListener) mqReduce.addListener(onChange);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }

  window.SonyashnykReveal = {
    observe: observe,
    revealNow: revealNow,
    markReveal: markReveal
  };
})();
