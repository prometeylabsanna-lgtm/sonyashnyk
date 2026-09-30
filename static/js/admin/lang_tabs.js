/**
 * Вкладки UA / RU в адмінці.
 * Поля з імʼям *_ru ховаються/показуються; решта завжди видимі.
 *
 * Важливо: у tabular-інлайнах рядок — це TR.form-row з полями обох мов.
 * Ховати треба окремі комірки/поля, а не весь TR (інакше «Додати ще» додає
 * невидимий рядок, а empty-form ламається).
 */
(function () {
  "use strict";

  var STORAGE_KEY = "sonyashnyk_admin_lang";
  var ROOT_ATTR = "data-admin-lang-root";

  function isRuName(name) {
    return typeof name === "string" && (/_ru$/.test(name) || /_ru_/.test(name));
  }

  function ukNameFromRu(name) {
    if (/_ru_/.test(name)) {
      return name.replace(/_ru_/, "_");
    }
    return name.replace(/_ru$/, "");
  }

  function closestRow(el) {
    if (!el || !el.closest) return null;

    // Уже позначений контейнер — лишаємось у ньому.
    var marked = el.closest("[data-admin-lang]");
    if (marked && marked.tagName !== "TR" && marked.tagName !== "TBODY") {
      return marked;
    }

    // CMS-редактор
    var cms = el.closest(".site-content-editor__field");
    if (cms) return cms;

    // Комірка/обгортка поля (tabular: td.field-*, stacked: .field-*)
    var fieldBox = el.closest("[class*='field-']");
    if (fieldBox && fieldBox.tagName !== "TR") {
      return fieldBox;
    }

    // Звичайний stacked form-row (DIV), не TR таблиці
    var formRow = el.closest(".form-row");
    if (formRow && formRow.tagName !== "TR") {
      return formRow;
    }

    // char-kv віджет
    var charKv = el.closest("[data-char-kv]");
    if (charKv) return charKv.closest("[class*='field-']") || charKv.parentElement || charKv;

    return el.parentElement;
  }

  function findControl(root, name) {
    if (!name) return null;
    var escaped = name.replace(/"/g, '\\"');
    return (
      root.querySelector('[name="' + escaped + '"]') ||
      root.querySelector("#id_" + name.replace(/:/g, "\\:"))
    );
  }

  function syncTableHeader(cell, lang) {
    if (!cell || cell.tagName !== "TD") return;
    var tr = cell.parentElement;
    var table = cell.closest("table");
    if (!tr || !table) return;
    var idx = Array.prototype.indexOf.call(tr.children, cell);
    if (idx < 0) return;
    table.querySelectorAll("thead tr").forEach(function (headRow) {
      var th = headRow.children[idx];
      if (!th) return;
      th.setAttribute("data-admin-lang", lang);
    });
  }

  function markPairs(root) {
    // Старий баг: TR інлайну отримував data-admin-lang і ховався цілком
    root.querySelectorAll("tr[data-admin-lang], tbody[data-admin-lang]").forEach(function (node) {
      node.removeAttribute("data-admin-lang");
      node.classList.remove("is-lang-hidden");
    });

    var controls = root.querySelectorAll(
      "input[name], textarea[name], select[name], [data-char-kv-name]"
    );
    var hasRu = false;
    controls.forEach(function (el) {
      var name = el.getAttribute("name") || el.getAttribute("data-char-kv-name") || "";
      if (!isRuName(name)) return;
      if (el.type === "hidden") return;
      // Префікс empty-form теж маркуємо — але лише комірку, не TR.
      hasRu = true;
      var ruRow = closestRow(el);
      if (ruRow && ruRow.tagName !== "TR" && !ruRow.getAttribute("data-admin-lang")) {
        ruRow.setAttribute("data-admin-lang", "ru");
        syncTableHeader(ruRow, "ru");
      }
      var ukName = ukNameFromRu(name);
      var ukEl =
        findControl(root, ukName) ||
        root.querySelector('[data-char-kv-name="' + ukName.replace(/"/g, '\\"') + '"]');
      if (ukEl) {
        var ukRow = closestRow(ukEl);
        if (
          ukRow &&
          ukRow.tagName !== "TR" &&
          ukRow !== ruRow &&
          !ukRow.getAttribute("data-admin-lang")
        ) {
          ukRow.setAttribute("data-admin-lang", "uk");
          syncTableHeader(ukRow, "uk");
        }
      }
    });
    return hasRu;
  }

  function applyLang(root, lang) {
    root.querySelectorAll("[data-admin-lang]").forEach(function (node) {
      // Ніколи не ховаємо цілий рядок tabular-інлайну
      if (node.tagName === "TR" || node.tagName === "TBODY") {
        node.classList.remove("is-lang-hidden");
        return;
      }
      var nodeLang = node.getAttribute("data-admin-lang");
      if (nodeLang === lang) {
        node.classList.remove("is-lang-hidden");
      } else {
        node.classList.add("is-lang-hidden");
      }
    });
    root.querySelectorAll("[data-admin-lang-tab]").forEach(function (btn) {
      var active = btn.getAttribute("data-admin-lang-tab") === lang;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-selected", active ? "true" : "false");
      btn.setAttribute("tabindex", active ? "0" : "-1");
    });
  }

  function buildTabs(root, initial) {
    if (root.querySelector(".admin-lang-tabs")) return;
    var tabs = document.createElement("div");
    tabs.className = "admin-lang-tabs";
    tabs.setAttribute("role", "tablist");
    tabs.setAttribute("aria-label", "Мова текстів");

    ["uk", "ru"].forEach(function (lang) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "admin-lang-tabs__btn" + (lang === initial ? " is-active" : "");
      btn.setAttribute("role", "tab");
      btn.setAttribute("data-admin-lang-tab", lang);
      btn.setAttribute("aria-selected", lang === initial ? "true" : "false");
      btn.textContent = lang === "uk" ? "UA" : "RU";
      btn.addEventListener("click", function () {
        try {
          window.localStorage.setItem(STORAGE_KEY, lang);
        } catch (err) {}
        applyLang(root, lang);
        document.dispatchEvent(
          new CustomEvent("admin-lang-changed", { detail: { lang: lang, root: root } })
        );
      });
      tabs.appendChild(btn);
    });

    var form = root.matches("form") ? root : root.querySelector("form");
    var mount = form || root;
    var anchor =
      mount.querySelector("[name=csrfmiddlewaretoken]") ||
      mount.querySelector(".admin-lang-tabs-anchor") ||
      mount.firstElementChild;
    if (anchor && anchor.parentNode === mount) {
      mount.insertBefore(tabs, anchor.nextSibling);
    } else if (anchor) {
      anchor.parentNode.insertBefore(tabs, anchor);
    } else {
      mount.insertBefore(tabs, mount.firstChild);
    }
  }

  function readLang() {
    try {
      var saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved === "uk" || saved === "ru") return saved;
    } catch (err) {}
    return "uk";
  }

  function initRoot(root) {
    if (!root || root.getAttribute(ROOT_ATTR) === "1") return;
    var hasRu = markPairs(root);
    if (!hasRu && !root.querySelector("[data-admin-lang=ru]")) return;
    root.setAttribute(ROOT_ATTR, "1");
    var lang = readLang();
    buildTabs(root, lang);
    applyLang(root, lang);
  }

  function refreshAfterFormset(row) {
    if (!row) return;
    var form = row.closest("form") || document.querySelector("#content-main form");
    if (!form) return;
    // Зняти помилкові позначки з TR (старий баг)
    if (row.tagName === "TR") {
      row.classList.remove("is-lang-hidden");
      row.removeAttribute("data-admin-lang");
    }
    markPairs(row);
    applyLang(form, readLang());
  }

  function boot() {
    document.querySelectorAll("[data-admin-lang-scope]").forEach(initRoot);
    document.querySelectorAll("#content-main, .site-content-editor").forEach(function (node) {
      var form = node.matches("form") ? node : node.querySelector("form");
      if (form) initRoot(form);
      else initRoot(node);
    });

    // Django admin: новий рядок інлайну
    document.addEventListener("formset:added", function (event) {
      refreshAfterFormset(event.target);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
