/* ============================================================
   КОШИК — шторка (AJAX), кнопки "До кошика", степер кількості
   Делегування подій на document, щоб переживати заміну DOM шторки.
   ============================================================ */
(function () {
  "use strict";

  function getDrawer() { return document.getElementById("cart-drawer"); }

  function setCartCount(count) {
    document.querySelectorAll("[data-cart-count]").forEach(function (el) {
      el.textContent = count;
      el.setAttribute("data-bump", "0");
      window.requestAnimationFrame(function () {
        el.setAttribute("data-bump", "1");
      });
    });
  }

  function openDrawer() {
    var drawer = getDrawer();
    if (!drawer) return;
    drawer.classList.add("is-open");
    drawer.setAttribute("aria-hidden", "false");
    SonyashnykUtils.lockScroll();
  }

  function closeDrawer() {
    var drawer = getDrawer();
    if (!drawer || !drawer.classList.contains("is-open")) return;
    drawer.classList.remove("is-open");
    drawer.setAttribute("aria-hidden", "true");
    SonyashnykUtils.unlockScroll();
  }

  function refreshDrawer(keepOpen) {
    fetch(window.SONYASHNYK.cartDrawerUrl, { credentials: "same-origin" })
      .then(function (res) { return res.text(); })
      .then(function (html) {
        var wrapper = document.createElement("div");
        wrapper.innerHTML = html.trim();
        var fresh = wrapper.firstElementChild;
        var current = getDrawer();
        if (!fresh || !current) return;
        if (keepOpen || current.classList.contains("is-open")) {
          fresh.classList.add("is-open");
          fresh.setAttribute("aria-hidden", "false");
        }
        current.replaceWith(fresh);
      });
  }

  function addToCart(button) {
    var variantId = button.getAttribute("data-variant-id");
    if (!variantId) return;
    var wrapper = button.closest("[data-pdp-actions], .product-card__body");
    var qtyInput = wrapper ? wrapper.querySelector("[data-qty-input]") : null;
    var quantity = qtyInput ? parseInt(qtyInput.value, 10) || 1 : 1;

    var formData = new FormData();
    formData.append("variant_id", variantId);
    formData.append("quantity", quantity);

    button.disabled = true;
    SonyashnykUtils.postForm(window.SONYASHNYK.cartAddUrl, formData)
      .then(function (result) {
        button.disabled = false;
        if (result.data && result.data.ok) {
          setCartCount(result.data.cart_count);
          button.setAttribute("data-added", "1");
          window.setTimeout(function () { button.removeAttribute("data-added"); }, 1600);
          SonyashnykUtils.showToast("Додано в кошик");
          refreshDrawer(false);
        } else {
          SonyashnykUtils.showToast("Не вдалося додати товар.");
        }
      })
      .catch(function () {
        button.disabled = false;
        SonyashnykUtils.showToast("Сталася помилка мережі.");
      });
  }

  function removeFromCart(variantId) {
    var formData = new FormData();
    var url = window.SONYASHNYK.cartRemoveUrlBase + variantId + "/";
    SonyashnykUtils.postForm(url, formData).then(function (result) {
      if (result.data && result.data.ok) {
        setCartCount(result.data.cart_count);
        refreshDrawer(true);
      }
    });
  }

  function adjustQtyInput(input, delta) {
    var min = parseInt(input.getAttribute("min") || "1", 10);
    var max = parseInt(input.getAttribute("max") || "99", 10);
    var value = (parseInt(input.value, 10) || min) + delta;
    input.value = Math.min(max, Math.max(min, value));
  }

  document.addEventListener("click", function (e) {
    var toggle = e.target.closest("[data-cart-toggle]");
    if (toggle) { openDrawer(); return; }

    var close = e.target.closest("[data-cart-close]");
    if (close) { closeDrawer(); return; }

    var add = e.target.closest("[data-add-to-cart]");
    if (add) { addToCart(add); return; }

    var remove = e.target.closest("[data-cart-remove]");
    if (remove) { removeFromCart(remove.getAttribute("data-variant-id")); return; }

    var inc = e.target.closest("[data-qty-increment]");
    if (inc) {
      var incInput = inc.parentElement.querySelector("[data-qty-input]");
      if (incInput) adjustQtyInput(incInput, 1);
      return;
    }
    var dec = e.target.closest("[data-qty-decrement]");
    if (dec) {
      var decInput = dec.parentElement.querySelector("[data-qty-input]");
      if (decInput) adjustQtyInput(decInput, -1);
      return;
    }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeDrawer();
  });
})();
