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

      toast_lead_ok: "Дякуємо! Ваше повідомлення надіслано.",
      toast_lead_fail: "Перевірте поля форми і спробуйте ще раз.",
      toast_network: "Сталася помилка мережі.",
      toast_phone_check: "Перевірте, будь ласка, номер телефону.",
      toast_generic_error: "Сталася помилка. Спробуйте ще раз.",
      toast_cart_added: "Додано в кошик",
      toast_cart_fail: "Не вдалося додати товар.",
      cart_receipt_brand: "чек",
      cart_delivery: "Доставка",
      cart_delivery_free: "безкошт.",
      cart_delivery_tbd: "уточн.",
      cart_discount: "Знижка",
      cart_apply: "Застосувати",
      cart_cancel: "Скасувати",
      cart_total: "Разом",
      cart_checkout: "Оформити замовлення",
      cart_continue: "Продовжити покупки",
      cart_empty_receipt: "Поки що тут порожньо",
      cart_remove: "Видалити",
      footer_credit: "Розробка від команди",

      ph_name: "Ваше ім'я",
      ph_full_name: "Прізвище, ім'я",
      ph_phone: "+380",
      ph_email: "email@example.com",
      ph_city: "Почніть вводити місто",
      ph_warehouse: "Відділення / поштомат / адреса",
      ph_warehouse_courier: "Вулиця, будинок, квартира",
      ph_warehouse_pick: "Почніть вводити або оберіть зі списку",
      ph_warehouse_manual: "Введіть вручну",
      ph_comment: "Коментар до замовлення (необов'язково)",
      ph_promo: "Промокод (якщо є)",
      ph_promo_cart: "Промокод",
      ph_message: "Повідомлення",
      ph_question: "Ваше запитання",
      ph_email_short: "Ваш email",

      label_full_name: "ПІБ отримувача",
      label_phone: "Телефон",
      label_name: "Ім'я",
      label_email: "Email (необов'язково)",
      label_city: "Місто",
      label_warehouse: "Відділення / адреса",
      label_comment: "Коментар до замовлення",
      label_promo: "Промокод",
      label_agree: "Погоджуюсь на обробку персональних даних",

      delivery_city: "Місто",
      delivery_np_branch: "Відділення Нової Пошти",
      delivery_np_locker: "Поштомат Нової Пошти",
      delivery_np_courier: "Адреса доставки",
      delivery_ukrposhta: "№ відділення Укрпошти",
      delivery_choice_np_branch: "Нова Пошта — відділення",
      delivery_choice_np_locker: "Нова Пошта — поштомат",
      delivery_choice_np_courier: "Нова Пошта — курʼєр",
      delivery_choice_ukrposhta: "Укрпошта",
      delivery_choice_pickup: "Самовивіз",
      payment_choice_liqpay: "Оплата карткою (LiqPay)",
      payment_choice_cod: "Оплата при отриманні (накладений платіж)",
      payment_choice_cash: "Оплата при самовивозі",

      checkout_contacts: "Контакти",
      checkout_delivery: "Доставка",
      checkout_payment: "Оплата",
      checkout_extra: "Коментар і промокод",
      checkout_submit: "Підтвердити замовлення",
      checkout_np_hint: "API НП ще не підключено — введіть місто вручну.",
      checkout_summary_items: "Товари",
      checkout_summary_discount: "Знижка",
      checkout_summary_total: "Разом",
      checkout_summary_toggle: "Склад замовлення",
    },
    ru: {
      required: "Это поле обязательно",
      name_digits: "Имя не должно содержать цифры",
      name_invalid: "Только буквы, пробелы, дефис или апостроф",
      phone_required: "Укажите номер телефона",
      phone_short: "Слишком короткий номер телефона",
      phone_long: "В номере не должно быть больше 13 цифр",
      email_required: "Укажите email",
      email_invalid: "Введите корректный email с символом @",
      agree_required: "Необходимо согласие на обработку данных",
      city_required: "Укажите город доставки",
      warehouse_required: "Укажите отделение или адрес",

      toast_lead_ok: "Спасибо! Ваше сообщение отправлено.",
      toast_lead_fail: "Проверьте поля формы и попробуйте ещё раз.",
      toast_network: "Произошла ошибка сети.",
      toast_phone_check: "Проверьте, пожалуйста, номер телефона.",
      toast_generic_error: "Произошла ошибка. Попробуйте ещё раз.",
      toast_cart_added: "Добавлено в корзину",
      toast_cart_fail: "Не удалось добавить товар.",
      cart_receipt_brand: "чек",
      cart_delivery: "Доставка",
      cart_delivery_free: "бесплатно",
      cart_delivery_tbd: "уточн.",
      cart_discount: "Скидка",
      cart_apply: "Применить",
      cart_cancel: "Отменить",
      cart_total: "Итого",
      cart_checkout: "Оформить заказ",
      cart_continue: "Продолжить покупки",
      cart_empty_receipt: "Пока здесь пусто",
      cart_remove: "Удалить",
      footer_credit: "Разработка от команды",

      ph_name: "Ваше имя",
      ph_full_name: "Фамилия, имя",
      ph_phone: "+380",
      ph_email: "email@example.com",
      ph_city: "Начните вводить город",
      ph_warehouse: "Отделение / почтомат / адрес",
      ph_warehouse_courier: "Улица, дом, квартира",
      ph_warehouse_pick: "Начните вводить или выберите из списка",
      ph_warehouse_manual: "Введите вручную",
      ph_comment: "Комментарий к заказу (необязательно)",
      ph_promo: "Промокод (если есть)",
      ph_promo_cart: "Промокод",
      ph_message: "Сообщение",
      ph_question: "Ваш вопрос",
      ph_email_short: "Ваш email",

      label_full_name: "ФИО получателя",
      label_phone: "Телефон",
      label_name: "Имя",
      label_email: "Email (необязательно)",
      label_city: "Город",
      label_warehouse: "Отделение / адрес",
      label_comment: "Комментарий к заказу",
      label_promo: "Промокод",
      label_agree: "Соглашаюсь на обработку персональных данных",

      delivery_city: "Город",
      delivery_np_branch: "Отделение Новой Почты",
      delivery_np_locker: "Почтомат Новой Почты",
      delivery_np_courier: "Адрес доставки",
      delivery_ukrposhta: "№ отделения Укрпочты",
      delivery_choice_np_branch: "Новая Почта — отделение",
      delivery_choice_np_locker: "Новая Почта — почтомат",
      delivery_choice_np_courier: "Новая Почта — курьер",
      delivery_choice_ukrposhta: "Укрпочта",
      delivery_choice_pickup: "Самовывоз",
      payment_choice_liqpay: "Оплата картой (LiqPay)",
      payment_choice_cod: "Оплата при получении (наложенный платёж)",
      payment_choice_cash: "Оплата при самовывозе",

      checkout_contacts: "Контакты",
      checkout_delivery: "Доставка",
      checkout_payment: "Оплата",
      checkout_extra: "Комментарий и промокод",
      checkout_submit: "Подтвердить заказ",
      checkout_np_hint: "API НП ещё не подключено — введите город вручную.",
      checkout_summary_items: "Товары",
      checkout_summary_discount: "Скидка",
      checkout_summary_total: "Итого",
      checkout_summary_toggle: "Состав заказа",
    },
  };

  function normalizeLang(code) {
    if (!code) return "uk";
    code = String(code).toLowerCase();
    if (code === "ru" || code === "rus" || code.indexOf("ru") === 0) return "ru";
    return "uk";
  }

  function getLang() {
    var htmlLang = normalizeLang(document.documentElement.lang || "");
    if (htmlLang === "ru") return "ru";
    var stored = "";
    try {
      stored = window.localStorage.getItem(LANG_KEY) || "";
    } catch (e) { /* ignore */ }
    if (stored) return normalizeLang(stored);
    var active = document.querySelector(".logobar__lang button.is-active[data-lang]");
    if (active) return normalizeLang(active.getAttribute("data-lang"));
    return "uk";
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

  function applyStaticI18n(root) {
    root = root || document;
    root.querySelectorAll("[data-i18n]").forEach(function (el) {
      var key = el.getAttribute("data-i18n");
      if (!key) return;
      var text = t(key);
      if (text) el.textContent = text;
    });
    root.querySelectorAll("[data-i18n-ph]").forEach(function (el) {
      var key = el.getAttribute("data-i18n-ph");
      if (!key) return;
      var text = t(key);
      if (text) el.setAttribute("placeholder", text);
    });
    root.querySelectorAll("[data-i18n-label]").forEach(function (el) {
      var key = el.getAttribute("data-i18n-label");
      if (!key) return;
      var text = t(key);
      if (text) el.textContent = text;
    });
  }

  document.addEventListener("sonyashnyk:langchange", function () {
    refreshVisibleErrors(document);
    applyStaticI18n(document);
  });

  document.addEventListener("DOMContentLoaded", function () {
    applyStaticI18n(document);
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
    applyStaticI18n: applyStaticI18n,
    LANG_KEY: LANG_KEY,
    normalizeLang: normalizeLang,
  };
})();
