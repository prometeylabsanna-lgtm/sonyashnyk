/* ============================================================
   КОШИК — випадаюча панель під іконкою (AJAX)
   ============================================================ */
(function () {
  "use strict";

  var lastToggle = null;
  var GAP = 8;
  var EDGE = 8;

  function getDrawer() { return document.getElementById("cart-drawer"); }

  function getPanel(drawer) {
    return drawer ? drawer.querySelector(".cart-drawer__panel") : null;
  }

  function visibleToggle() {
    var toggles = document.querySelectorAll("[data-cart-toggle]");
    for (var i = 0; i < toggles.length; i++) {
      var el = toggles[i];
      if (el.offsetParent !== null || el.getClientRects().length) {
        var style = window.getComputedStyle(el);
        if (style.display !== "none" && style.visibility !== "hidden") {
          return el;
        }
      }
    }
    return toggles[0] || null;
  }

  function positionPanel(toggle) {
    var drawer = getDrawer();
    var panel = getPanel(drawer);
    if (!panel) return;
    var btn = toggle || lastToggle || visibleToggle();
    if (!btn) return;
    lastToggle = btn;

    var rect = btn.getBoundingClientRect();
    var panelWidth = Math.min(window.innerWidth - EDGE * 2, 360);
    var right = Math.max(EDGE, window.innerWidth - rect.right);
    if (right + panelWidth > window.innerWidth - EDGE) {
      right = EDGE;
    }

    var top = rect.bottom + GAP;
    var maxH = Math.min(window.innerHeight * 0.7, 520);
    if (top + Math.min(maxH, 200) > window.innerHeight - EDGE) {
      top = Math.max(EDGE, rect.top - GAP - Math.min(maxH, window.innerHeight * 0.55));
    }

    panel.style.top = top + "px";
    panel.style.right = right + "px";
    panel.style.left = "auto";
    panel.style.width = panelWidth + "px";
  }

  function setCartCount(count) {
    document.querySelectorAll("[data-cart-count]").forEach(function (el) {
      el.textContent = count;
      el.setAttribute("data-bump", "0");
      window.requestAnimationFrame(function () {
        el.setAttribute("data-bump", "1");
      });
    });
  }

  function openDrawer(toggle) {
    var drawer = getDrawer();
    if (!drawer) return;
    lastToggle = toggle || lastToggle || visibleToggle();
    positionPanel(lastToggle);
    drawer.classList.add("is-open");
    drawer.setAttribute("aria-hidden", "false");
    if (lastToggle) lastToggle.setAttribute("aria-expanded", "true");
  }

  function closeDrawer() {
    var drawer = getDrawer();
    if (!drawer || !drawer.classList.contains("is-open")) return;
    drawer.classList.remove("is-open");
    drawer.setAttribute("aria-hidden", "true");
    document.querySelectorAll("[data-cart-toggle]").forEach(function (el) {
      el.setAttribute("aria-expanded", "false");
    });
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
        var wasOpen = keepOpen || current.classList.contains("is-open");
        if (wasOpen) {
          fresh.classList.add("is-open");
          fresh.setAttribute("aria-hidden", "false");
        }
        current.replaceWith(fresh);
        if (wasOpen) positionPanel(lastToggle);
      });
  }

  function addToCart(button) {
    var variantId = button.getAttribute("data-variant-id");
    if (!variantId) return;
    var wrapper = button.closest("[data-pdp-actions], .product-card");
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
    if (toggle) {
      e.preventDefault();
      var drawer = getDrawer();
      if (drawer && drawer.classList.contains("is-open")) {
        closeDrawer();
      } else {
        openDrawer(toggle);
      }
      return;
    }

    var close = e.target.closest("[data-cart-close]");
    if (close) { closeDrawer(); return; }

    var add = e.target.closest("[data-add-to-cart]");
    if (add) { addToCart(add); return; }

    var remove = e.target.closest("[data-cart-remove]");
    if (remove) { removeFromCart(remove.getAttribute("data-variant-id")); return; }

    var inc = e.target.closest("[data-qty-increment]");
    if (inc) {
      var incInput = inc.parentElement.querySelector("[data-qty-input]");
      if (incInput) {
        adjustQtyInput(incInput, 1);
        submitCartQtyForm(inc);
      }
      return;
    }
    var dec = e.target.closest("[data-qty-decrement]");
    if (dec) {
      var decInput = dec.parentElement.querySelector("[data-qty-input]");
      if (decInput) {
        adjustQtyInput(decInput, -1);
        submitCartQtyForm(dec);
      }
      return;
    }
  });

  function submitCartQtyForm(fromEl) {
    var form = fromEl.closest("[data-cart-qty-form]");
    if (!form) return;
    form.submit();
  }

  document.addEventListener("change", function (e) {
    var input = e.target.closest("[data-cart-qty-form] [data-qty-input]");
    if (input) submitCartQtyForm(input);
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeDrawer();
  });

  window.addEventListener("resize", function () {
    var drawer = getDrawer();
    if (drawer && drawer.classList.contains("is-open")) positionPanel(lastToggle);
  });

  window.addEventListener("scroll", function () {
    var drawer = getDrawer();
    if (drawer && drawer.classList.contains("is-open")) positionPanel(lastToggle);
  }, { passive: true });
})();
