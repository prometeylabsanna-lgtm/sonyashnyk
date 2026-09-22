/**
 * Вкладки UA / RU в адмінці.
 * Поля з імʼям *_ru ховаються/показуються; решта завжди видимі.
 */
(function () {
  "use strict";

  var STORAGE_KEY = "sonyashnyk_admin_lang";
  var ROOT_ATTR = "data-admin-lang-root";

  function isRuName(name) {
    return typeof name === "string" && /_ru$/.test(name);
  }

  function ukNameFromRu(name) {
    return name.replace(/_ru$/, "");
  }

  function closestRow(el) {
    return (
      el.closest("[data-admin-lang]") ||
      el.closest(".form-row") ||
      el.closest(".site-content-editor__field") ||
      el.closest("[class*='field-']") ||
      el.parentElement
    );
  }

  function findControl(root, name) {
    if (!name) return null;
    var escaped = name.replace(/"/g, '\\"');
    return (
      root.querySelector('[name="' + escaped + '"]') ||
      root.querySelector("#id_" + name.replace(/:/g, "\\:"))
    );
  }

  function markPairs(root) {
    var controls = root.querySelectorAll("input[name], textarea[name], select[name]");
    var hasRu = false;
    controls.forEach(function (el) {
      var name = el.getAttribute("name") || "";
      if (!isRuName(name)) return;
      if (el.type === "hidden") return;
      hasRu = true;
      var ruRow = closestRow(el);
      if (ruRow && !ruRow.getAttribute("data-admin-lang")) {
        ruRow.setAttribute("data-admin-lang", "ru");
      }
      var ukName = ukNameFromRu(name);
      var ukEl = findControl(root, ukName);
      if (ukEl) {
        var ukRow = closestRow(ukEl);
        if (ukRow && ukRow !== ruRow && !ukRow.getAttribute("data-admin-lang")) {
          ukRow.setAttribute("data-admin-lang", "uk");
        }
      }
    });
    return hasRu;
  }

  function applyLang(root, lang) {
    root.querySelectorAll("[data-admin-lang]").forEach(function (node) {
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

  function boot() {
    document.querySelectorAll("[data-admin-lang-scope]").forEach(initRoot);
    document.querySelectorAll("#content-main, .site-content-editor").forEach(function (node) {
      var form = node.matches("form") ? node : node.querySelector("form");
      if (form) initRoot(form);
      else initRoot(node);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
