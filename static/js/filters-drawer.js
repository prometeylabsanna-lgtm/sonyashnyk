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

    var sortSelect = document.querySelector("[data-sort-select]");
    if (sortSelect) {
      sortSelect.addEventListener("change", function () {
        var url = new URL(window.location.href);
        url.searchParams.set("sort", sortSelect.value);
        url.searchParams.delete("page");
        window.location.href = url.toString();
      });
    }
  });
})();
