/**
 * TinyMCE для textarea.cms-tinymce в адмінці.
 * Plain-текст → <p> абзаци; Enter додає новий <p>; сумісно з UA/RU.
 */
(function () {
  "use strict";

  var INIT_FLAG = "data-cms-tinymce-ready";
  var HAS_TAG = /<[a-z][\s\S]*>/i;

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function splitSentences(text) {
    var parts = [];
    var re = /[.!?…]["»”']?\)?\s+(?=[A-ZА-ЯЁЇІЄҐA-Z])/g;
    var last = 0;
    var m;
    while ((m = re.exec(text)) !== null) {
      var cut = m.index + 1;
      while (cut < text.length && /["»”')\]]/.test(text.charAt(cut))) {
        cut += 1;
      }
      var chunk = text.slice(last, cut).trim();
      if (chunk) parts.push(chunk);
      last = m.index + m[0].length;
      re.lastIndex = last;
    }
    var tail = text.slice(last).trim();
    if (tail) parts.push(tail);
    return parts.length ? parts : [text];
  }

  /** Звичайний текст → HTML з <p>. Порожні рядки / речення → окремі абзаци. */
  function plainToHtml(raw) {
    var text = String(raw || "")
      .replace(/\r\n/g, "\n")
      .replace(/\r/g, "\n")
      .trim();
    if (!text) return "";
    if (HAS_TAG.test(text)) return text;

    var blocks = text
      .split(/\n\s*\n/)
      .map(function (b) {
        return b.replace(/\n+/g, " ").replace(/\s+/g, " ").trim();
      })
      .filter(Boolean);

    if (!blocks.length) return "";

    if (blocks.length === 1) {
      var sentences = splitSentences(blocks[0]);
      if (sentences.length > 1) blocks = sentences;
    }

    return blocks
      .map(function (b) {
        return "<p>" + escapeHtml(b) + "</p>";
      })
      .join("");
  }

  function prepareTextareas() {
    document.querySelectorAll("textarea.cms-tinymce").forEach(function (ta) {
      if (ta.getAttribute("data-cms-plain-converted") === "1") return;
      ta.value = plainToHtml(ta.value);
      ta.setAttribute("data-cms-plain-converted", "1");
    });
  }

  function baseConfig() {
    return {
      selector: "textarea.cms-tinymce",
      menubar: false,
      branding: false,
      promotion: false,
      height: 420,
      plugins: "lists link code autolink",
      toolbar:
        "undo redo | bold italic underline | bullist numlist | link | removeformat | code",
      valid_elements:
        "p,br,strong/b,em/i,u,ul,ol,li,a[href|target|rel|title],h2,h3,h4,span",
      forced_root_block: "p",
      newline_behavior: "block",
      convert_urls: false,
      relative_urls: false,
      entity_encoding: "raw",
      content_style:
        "body{font-family:system-ui,-apple-system,sans-serif;font-size:15px;line-height:1.55;padding:8px 12px;}" +
        "p{margin:0 0 0.85em;}p:last-child{margin-bottom:0;}",
      paste_preprocess: function (_plugin, args) {
        var content = args.content || "";
        if (!HAS_TAG.test(content)) {
          args.content = plainToHtml(
            content.replace(/<br\s*\/?>/gi, "\n").replace(/&nbsp;/g, " ")
          );
        }
      },
      setup: function (editor) {
        editor.on("init", function () {
          var html = editor.getContent({ format: "html" });
          var text = editor.getContent({ format: "text" });
          if (text && (!html || html === "<p></p>" || !HAS_TAG.test(html.replace(/<\/?p>/gi, "")))) {
            var converted = plainToHtml(text);
            if (converted) editor.setContent(converted);
          } else if (html && !HAS_TAG.test(html.replace(/<\/?p[^>]*>/gi, "").replace(/<br\s*\/?>/gi, ""))) {
            var converted2 = plainToHtml(
              html.replace(/<\/p>\s*<p>/gi, "\n\n").replace(/<[^>]+>/g, "")
            );
            if (converted2) editor.setContent(converted2);
          }
        });
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
    prepareTextareas();
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
