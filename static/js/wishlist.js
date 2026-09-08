/* ============================================================
   WISHLIST — localStorage + sync кнопок / бейджа / сторінки
   ============================================================ */
(function () {
  "use strict";

  var STORAGE_KEY = "sonyashnyk_wishlist";
  var MAX_ITEMS = 60;

  function getIds() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      var parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) return [];
      return parsed
        .map(function (id) { return parseInt(id, 10); })
        .filter(function (id) { return id > 0; })
        .slice(0, MAX_ITEMS);
    } catch (e) {
      return [];
    }
  }

  function setIds(ids) {
    var unique = [];
    var seen = {};
    ids.forEach(function (id) {
      var n = parseInt(id, 10);
      if (!n || seen[n]) return;
      seen[n] = true;
      unique.push(n);
    });
    unique = unique.slice(0, MAX_ITEMS);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(unique));
    } catch (e) { /* ignore quota */ }
    syncUi(unique);
    return unique;
  }

  function hasId(ids, id) {
    return ids.indexOf(id) !== -1;
  }

  function toggleId(id) {
    var ids = getIds();
    var idx = ids.indexOf(id);
    if (idx === -1) ids.push(id);
    else ids.splice(idx, 1);
    return setIds(ids);
  }

  function syncButtons(ids) {
    document.querySelectorAll("[data-wishlist-toggle][data-product-id]").forEach(function (btn) {
      var id = parseInt(btn.getAttribute("data-product-id"), 10);
      if (!id) return;
      var on = hasId(ids, id);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
      var label = btn.getAttribute("data-label-on") || "В обраному";
      var labelOff = btn.getAttribute("data-label-off") || "В обране";
      var textEl = btn.querySelector("[data-wishlist-label]");
      if (textEl) textEl.textContent = on ? label : labelOff;
      if (!textEl) {
        btn.setAttribute("aria-label", on ? label : labelOff);
      }
    });
  }

  function syncBadges(ids) {
    var count = ids.length;
    document.querySelectorAll("[data-wishlist-count]").forEach(function (el) {
      el.textContent = String(count);
      el.hidden = count === 0;
      el.setAttribute("data-empty", count === 0 ? "1" : "0");
    });
  }

  function syncUi(ids) {
    ids = ids || getIds();
    syncButtons(ids);
    syncBadges(ids);
  }

  function loadWishlistPage() {
    var root = document.querySelector("[data-wishlist-page]");
    if (!root) return;

    var grid = root.querySelector("[data-wishlist-grid]");
    var empty = root.querySelector("[data-wishlist-empty]");
    var loading = root.querySelector("[data-wishlist-loading]");
    var ids = getIds();

    if (!ids.length) {
      if (loading) loading.hidden = true;
      if (grid) {
        grid.innerHTML = "";
        grid.hidden = true;
      }
      if (empty) empty.hidden = false;
      return;
    }

    var cfg = window.SONYASHNYK || {};
    var base = cfg.wishlistFragmentUrl;
    if (!base || !grid) return;

    if (loading) loading.hidden = false;
    if (empty) empty.hidden = true;
    grid.hidden = true;

    var url = base + (base.indexOf("?") === -1 ? "?" : "&") + "ids=" + encodeURIComponent(ids.join(","));

    fetch(url, {
      headers: { "X-Requested-With": "fetch", Accept: "text/html" },
      credentials: "same-origin",
    })
      .then(function (res) {
        if (!res.ok) throw new Error("wishlist fetch failed");
        return res.text();
      })
      .then(function (html) {
        grid.innerHTML = html;
        // Картки приходять після DOMContentLoaded — data-reveal інакше лишає opacity:0
        grid.querySelectorAll("[data-reveal]").forEach(function (el) {
          el.classList.add("is-visible");
        });
        var hasCards = !!grid.querySelector(".product-card");
        grid.hidden = !hasCards;
        if (empty) empty.hidden = hasCards;
        if (loading) loading.hidden = true;
        if (hasCards) {
          var shownIds = Array.prototype.map.call(
            grid.querySelectorAll("[data-wishlist-toggle][data-product-id]"),
            function (btn) { return parseInt(btn.getAttribute("data-product-id"), 10); }
          ).filter(function (id) { return id > 0; });
          // Прибираємо з localStorage id, яких уже немає в каталозі
          if (shownIds.length !== ids.length) setIds(shownIds);
          else syncUi();
        } else {
          setIds([]);
        }
      })
      .catch(function () {
        if (loading) loading.hidden = true;
        if (empty) empty.hidden = false;
        if (grid) {
          grid.innerHTML = "";
          grid.hidden = true;
        }
      });
  }

  document.addEventListener("DOMContentLoaded", function () {
    syncUi();
    loadWishlistPage();
  });

  document.addEventListener("click", function (event) {
    var wish = event.target.closest("[data-wishlist-toggle]");
    if (!wish) return;
    event.preventDefault();
    event.stopPropagation();

    var id = parseInt(wish.getAttribute("data-product-id"), 10);
    if (!id) return;

    var ids = toggleId(id);

    // Якщо зняли зі списку на сторінці обраного — прибираємо картку
    var page = document.querySelector("[data-wishlist-page]");
    if (page && !hasId(ids, id)) {
      var card = wish.closest(".product-card");
      if (card) card.remove();
      var grid = page.querySelector("[data-wishlist-grid]");
      var empty = page.querySelector("[data-wishlist-empty]");
      if (grid && !grid.querySelector(".product-card")) {
        grid.hidden = true;
        if (empty) empty.hidden = false;
      }
    }
  });

  window.SonyashnykWishlist = {
    getIds: getIds,
    syncUi: syncUi,
  };
})();
