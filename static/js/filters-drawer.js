/* ============================================================
   ФІЛЬТРИ КАТАЛОГУ — шторка на мобільному/планшеті, сортування
   ============================================================ */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    var filters = document.querySelector("[data-filters]");
    var openBtn = document.querySelector("[data-filters-toggle]");
    if (filters && openBtn) {
      function open() {
        filters.classList.add("is-open");
        filters.setAttribute("aria-hidden", "false");
        SonyashnykUtils.lockScroll();
      }
      function close() {
        if (!filters.classList.contains("is-open")) return;
        filters.classList.remove("is-open");
        filters.setAttribute("aria-hidden", "true");
        SonyashnykUtils.unlockScroll();
      }
      openBtn.addEventListener("click", open);
      filters.querySelectorAll("[data-filters-close]").forEach(function (el) {
        el.addEventListener("click", close);
      });
    }

    var sortRoot = document.querySelector("[data-sort]");
    if (!sortRoot) return;

    var sortToggle = sortRoot.querySelector("[data-sort-toggle]");
    var sortMenu = sortRoot.querySelector("[data-sort-menu]");
    if (!sortToggle || !sortMenu) return;

    function closeSort() {
      sortRoot.classList.remove("is-open");
      sortMenu.hidden = true;
      sortToggle.setAttribute("aria-expanded", "false");
    }

    function openSort() {
      sortRoot.classList.add("is-open");
      sortMenu.hidden = false;
      sortToggle.setAttribute("aria-expanded", "true");
    }

    sortToggle.addEventListener("click", function (e) {
      e.stopPropagation();
      if (sortRoot.classList.contains("is-open")) {
        closeSort();
      } else {
        openSort();
      }
    });

    sortMenu.addEventListener("click", function (e) {
      var option = e.target.closest("[data-sort-option]");
      if (!option) return;
      var value = option.getAttribute("data-sort-option");
      if (!value) return;
      var url = new URL(window.location.href);
      url.searchParams.set("sort", value);
      url.searchParams.delete("page");
      window.location.href = url.toString();
    });

    document.addEventListener("click", function (e) {
      if (!sortRoot.contains(e.target)) closeSort();
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeSort();
    });
  });
})();
