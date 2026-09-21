/* ============================================================
   Перемикач обʼєму / ваги / кількості на картці та сторінці товару
   ============================================================ */
(function () {
  "use strict";

  function currency(value) {
    return value ? value + " ₴" : "";
  }

  function applyPack(root, btn) {
    if (!root || !btn) return;

    var variantId = btn.getAttribute("data-variant-id") || "";
    var price = btn.getAttribute("data-price") || "";
    var oldPrice = btn.getAttribute("data-old-price") || "";
    var inStock = btn.getAttribute("data-in-stock") === "1";
    var sku = btn.getAttribute("data-sku") || "";

    root.querySelectorAll("[data-pack-option]").forEach(function (el) {
      var on = el === btn;
      el.classList.toggle("is-active", on);
      el.setAttribute("aria-checked", on ? "true" : "false");
    });

    root.querySelectorAll("[data-add-to-cart]").forEach(function (el) {
      el.setAttribute("data-variant-id", variantId);
      el.disabled = !inStock || !variantId;
    });

    root.querySelectorAll("[data-lead-open]").forEach(function (el) {
      el.disabled = !inStock;
    });

    var priceEl = root.querySelector("[data-pack-price]");
    if (priceEl) priceEl.textContent = currency(price);

    var oldEl = root.querySelector("[data-pack-old-price]");
    if (oldEl) {
      if (oldPrice) {
        oldEl.textContent = currency(oldPrice);
        oldEl.hidden = false;
        oldEl.removeAttribute("hidden");
      } else {
        oldEl.textContent = "";
        oldEl.hidden = true;
      }
    }

    var stockEl = root.querySelector("[data-pack-stock]");
    if (stockEl) {
      var inLabel = root.getAttribute("data-label-in-stock") || "";
      var outLabel = root.getAttribute("data-label-out-of-stock") || "";
      stockEl.textContent = inStock ? inLabel : outLabel;
      stockEl.classList.toggle("is-out", !inStock);
    }

    var skuEl = root.querySelector("[data-pack-sku]");
    if (skuEl && sku) skuEl.textContent = sku;

    root.querySelectorAll("[data-qty-input], [data-qty-decrement], [data-qty-increment]").forEach(function (el) {
      el.disabled = !inStock;
    });

    var qtyWrap = root.querySelector(".product-card__qty");
    if (qtyWrap) {
      if (inStock) qtyWrap.removeAttribute("aria-disabled");
      else qtyWrap.setAttribute("aria-disabled", "true");
    }
  }

  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-pack-option]");
    if (!btn) return;
    e.preventDefault();
    applyPack(btn.closest("[data-pack-root]"), btn);
  });
})();
