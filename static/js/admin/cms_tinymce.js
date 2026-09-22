/**
 * TinyMCE для textarea.cms-tinymce в адмінці.
 * Сумісно з вкладками UA/RU (hide/show редакторів).
 */
(function () {
  "use strict";

  var INIT_FLAG = "data-cms-tinymce-ready";

  function baseConfig() {
    return {
      selector: "textarea.cms-tinymce",
      menubar: false,
      branding: false,
      promotion: false,
      height: 360,
      plugins: "lists link code autolink",
      toolbar:
        "undo redo | bold italic underline | bullist numlist | link | removeformat | code",
      valid_elements:
        "p,br,strong/b,em/i,u,ul,ol,li,a[href|target|rel|title],h2,h3,h4,span",
      convert_urls: false,
      relative_urls: false,
      entity_encoding: "raw",
      content_style:
        "body{font-family:system-ui,-apple-system,sans-serif;font-size:14px;line-height:1.5;}",
      setup: function (editor) {
        editor.on("change keyup", function () {
          editor.save();
        });
      },
    };
  }

  function syncVisibility() {
    if (!window.tinymce) return;
    window.tinymce.get().forEach(function (editor) {
      var el = editor.getElement();
      if (!el) return;
      var host = el.closest("[data-admin-lang]");
      var hidden = host && host.classList.contains("is-lang-hidden");
      if (hidden) {
        if (typeof editor.hide === "function") editor.hide();
      } else if (typeof editor.show === "function") {
        editor.show();
      }
    });
  }

  function init() {
    if (!window.tinymce) return;
    var nodes = document.querySelectorAll("textarea.cms-tinymce");
    if (!nodes.length) return;
    if (document.documentElement.getAttribute(INIT_FLAG) !== "1") {
      document.documentElement.setAttribute(INIT_FLAG, "1");
      window.tinymce.init(baseConfig());
    }
    window.setTimeout(syncVisibility, 80);
  }

  function beforeSubmit() {
    if (!window.tinymce) return;
    window.tinymce.triggerSave();
  }

  function onReady() {
    init();
    document.querySelectorAll("form").forEach(function (form) {
      form.addEventListener("submit", beforeSubmit);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", onReady);
  } else {
    onReady();
  }

  document.addEventListener("admin-lang-changed", function () {
    window.setTimeout(syncVisibility, 30);
  });
})();
