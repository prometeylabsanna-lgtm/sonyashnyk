/* ============================================================
   FORM VALIDATION — клієнтські підказки (uk/ru), лише на submit
   ============================================================ */
(function () {
  "use strict";

  var LANG_KEY = "sonyashnyk_lang";
  var NAME_RE = /^[A-Za-zА-Яа-яЁёІіЇїЄєҐґ\s'\u2019\u02BC\u2018\-]+$/;
  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/i;

  var MESSAGES = {
    uk: {
      required: "Це поле обов'язкове",
      name_digits: "В імені не може бути цифр",
      name_invalid: "Лише літери, пробіли, дефіс або апостроф",
      phone_required: "Вкажіть номер телефону",
      phone_short: "Занадто короткий номер телефону",
      phone_long: "Не більше ніж 13 цифр у номері",
      email_required: "Вкажіть email",
      email_invalid: "Введіть коректний email з символом @",
      agree_required: "Потрібна згода на обробку даних",
      city_required: "Вкажіть місто доставки",
      warehouse_required: "Вкажіть відділення або адресу",
    },
    ru: {
      required: "Это поле обязательно",
      name_digits: "В имени не может быть цифр",
      name_invalid: "Только буквы, пробелы, дефис или апостроф",
      phone_required: "Укажите номер телефона",
      phone_short: "Слишком короткий номер телефона",
      phone_long: "Не больше 13 цифр в номере",
      email_required: "Укажите email",
      email_invalid: "Введите корректный email с символом @",
      agree_required: "Нужно согласие на обработку данных",
      city_required: "Укажите город доставки",
      warehouse_required: "Укажите отделение или адрес",
    },
  };

  function normalizeLang(code) {
    if (!code) return "uk";
    code = String(code).toLowerCase();
    if (code === "ru" || code === "rus" || code.indexOf("ru") === 0) return "ru";
    return "uk";
  }

  function getLang() {
    var stored = "";
    try {
      stored = window.localStorage.getItem(LANG_KEY) || "";
    } catch (e) { /* ignore */ }
    if (stored) return normalizeLang(stored);
    var active = document.querySelector(".logobar__lang button.is-active[data-lang]");
    if (active) return normalizeLang(active.getAttribute("data-lang"));
    return normalizeLang(document.documentElement.lang || "uk");
  }

  function t(key) {
    var pack = MESSAGES[getLang()] || MESSAGES.uk;
    return pack[key] || MESSAGES.uk[key] || key;
  }

  function digitsOnly(value) {
    return String(value || "").replace(/\D/g, "");
  }

  function validateName(value, isRequired) {
    var v = String(value || "").trim();
    if (!v) return isRequired ? "required" : null;
    if (/\d/.test(v)) return "name_digits";
    if (!NAME_RE.test(v)) return "name_invalid";
    return null;
  }

  function validatePhone(value, isRequired) {
    var digits = digitsOnly(value);
    if (!digits) return isRequired ? "phone_required" : null;
    if (digits.length < 10) return "phone_short";
    if (digits.length > 13) return "phone_long";
    return null;
  }

  function validateEmail(value, isRequired) {
    var v = String(value || "").trim();
    if (!v) return isRequired ? "email_required" : null;
    if (!EMAIL_RE.test(v)) return "email_invalid";
    return null;
  }

  function fieldWrap(input) {
    return input.closest(".field") || input.parentElement;
  }

  function clearFieldError(input) {
    if (!input) return;
    var wrap = fieldWrap(input);
    if (!wrap) return;
    wrap.classList.remove("field--error");
    wrap.querySelectorAll(".field__error").forEach(function (err) {
      err.remove();
    });
    input.removeAttribute("aria-invalid");
  }

  function setFieldError(input, messageKey) {
    if (!input) return;
    var wrap = fieldWrap(input);
    if (!wrap) return;
    wrap.classList.add("field--error");
    input.setAttribute("aria-invalid", "true");
    var err = wrap.querySelector("[data-field-error]");
    if (!err) {
      err = document.createElement("span");
      err.className = "field__error";
      err.setAttribute("data-field-error", "");
      err.setAttribute("role", "alert");
      wrap.appendChild(err);
    }
    err.textContent = t(messageKey);
    err.setAttribute("data-msg-key", messageKey);
  }

  function isRequired(input) {
    if (!input) return false;
    if (input.hasAttribute("data-validate-optional")) return false;
    return input.required || input.getAttribute("aria-required") === "true"
      || input.hasAttribute("data-validate-required");
  }

  function ruleForInput(input) {
    var explicit = (input.getAttribute("data-validate") || "").trim();
    if (explicit) return explicit;
    var name = (input.getAttribute("name") || "").toLowerCase();
    var type = (input.getAttribute("type") || input.tagName || "").toLowerCase();
    if (name === "name" || name === "full_name") return "name";
    if (name === "phone" || type === "tel") return "phone";
    if (name === "email" || type === "email") return "email";
    if (type === "checkbox") return "checkbox";
    return "text";
  }

  function validateInput(input) {
    if (!input || input.disabled || input.type === "hidden") return null;
    if (input.name === "honeypot") return null;
    if (input.closest(".visually-hidden") && input.name === "honeypot") return null;

    var rule = ruleForInput(input);
    var required = isRequired(input);
    var key = null;

    if (rule === "name") key = validateName(input.value, required);
    else if (rule === "phone") key = validatePhone(input.value, required);
    else if (rule === "email") key = validateEmail(input.value, required);
    else if (rule === "checkbox") {
      if (required && !input.checked) {
        key = input.name === "agreed_to_data_processing" || input.id === "lead-modal-agree"
          ? "agree_required"
          : "required";
      }
    } else if (rule === "city") {
      if (required && !String(input.value || "").trim()) key = "city_required";
    } else if (rule === "warehouse") {
      if (required && !String(input.value || "").trim()) key = "warehouse_required";
    } else if (required && !String(input.value || "").trim()) {
      key = "required";
    }

    return key;
  }

  function refreshVisibleErrors(root) {
    (root || document).querySelectorAll("[data-field-error][data-msg-key]").forEach(function (el) {
      el.textContent = t(el.getAttribute("data-msg-key"));
    });
  }

  function validateForm(form, options) {
    options = options || {};
    var firstInvalid = null;
    var ok = true;
    var inputs = form.querySelectorAll("input, textarea, select");

    inputs.forEach(function (input) {
      if (typeof options.shouldValidate === "function" && !options.shouldValidate(input)) {
        clearFieldError(input);
        return;
      }
      clearFieldError(input);
      var key = validateInput(input);
      if (key) {
        ok = false;
        setFieldError(input, key);
        if (!firstInvalid) firstInvalid = input;
      }
    });

    if (firstInvalid && typeof firstInvalid.focus === "function") {
      try { firstInvalid.focus({ preventScroll: false }); } catch (e) { firstInvalid.focus(); }
    }
    return ok;
  }

  function bindSubmitValidation(form, options) {
    if (!form || form.__sonyashnykValidationBound) return;
    form.__sonyashnykValidationBound = true;
    options = options || {};

    form.addEventListener("input", function (e) {
      var target = e.target;
      if (!target || !target.closest) return;
      if (fieldWrap(target) && fieldWrap(target).classList.contains("field--error")) {
        clearFieldError(target);
      }
    });
    form.addEventListener("change", function (e) {
      var target = e.target;
      if (!target) return;
      if (fieldWrap(target) && fieldWrap(target).classList.contains("field--error")) {
        clearFieldError(target);
      }
    });

    form.addEventListener("submit", function (e) {
      if (!validateForm(form, options)) {
        e.preventDefault();
        e.stopImmediatePropagation();
        if (typeof options.onInvalid === "function") options.onInvalid();
        return false;
      }
      if (typeof options.onValid === "function") {
        // onValid may preventDefault itself (AJAX forms)
      }
    }, true);
  }

  document.addEventListener("sonyashnyk:langchange", function () {
    refreshVisibleErrors(document);
  });

  window.SonyashnykFormValidation = {
    getLang: getLang,
    t: t,
    validateName: validateName,
    validatePhone: validatePhone,
    validateEmail: validateEmail,
    clearFieldError: clearFieldError,
    setFieldError: setFieldError,
    validateForm: validateForm,
    bindSubmitValidation: bindSubmitValidation,
    refreshVisibleErrors: refreshVisibleErrors,
    LANG_KEY: LANG_KEY,
    normalizeLang: normalizeLang,
  };
})();
