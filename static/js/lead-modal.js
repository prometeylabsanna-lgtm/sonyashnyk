/* ============================================================
   ЛІД-МОДАЛКА — телефон/знижка, «1 клік», callback
   ============================================================ */
(function () {
  "use strict";

  var AUTO_OPEN_DELAY = 15000;
  var STORAGE_KEY = "sonyashnyk_lead_modal_shown";

  var COPY = {
    uk: {
      phone_modal: {
        title: "Не йдіть без подарунка!",
        lead: "Залиште номер телефону — передзвонимо і підкажемо знижку та найкращі товари під ваш запит.",
        cta: "Отримати знижку",
      },
      buy_one_click: {
        title: "Купити в 1 клік",
        lead: "Залиште ім'я й телефон — наш менеджер зателефонує для підтвердження замовлення.",
        cta: "Купити в 1 клік",
      },
      callback: {
        title: "Передзвоніть мені",
        lead: "Залиште номер — зателефонуємо протягом робочого дня.",
        cta: "Передзвоніть мені",
      },
      close: "Закрити",
    },
    ru: {
      phone_modal: {
        title: "Не уходите без подарка!",
        lead: "Оставьте номер телефона — перезвоним и подскажем скидку и лучшие товары под ваш запрос.",
        cta: "Получить скидку",
      },
      buy_one_click: {
        title: "Купить в 1 клик",
        lead: "Оставьте имя и телефон — наш менеджер позвонит для подтверждения заказа.",
        cta: "Купить в 1 клик",
      },
      callback: {
        title: "Перезвоните мне",
        lead: "Оставьте номер — позвоним в течение рабочего дня.",
        cta: "Перезвоните мне",
      },
      close: "Закрыть",
    },
  };

  function lang() {
    if (window.SonyashnykFormValidation) {
      return SonyashnykFormValidation.getLang() === "ru" ? "ru" : "uk";
    }
    var code = (document.documentElement.lang || "uk").toLowerCase();
    return code.indexOf("ru") === 0 ? "ru" : "uk";
  }

  document.addEventListener("DOMContentLoaded", function () {
    var modal = document.querySelector("[data-lead-modal]");
    if (!modal) return;

    var form = modal.querySelector("[data-lead-form]");
    var successBox = modal.querySelector("[data-lead-success]");
    var submitBtn = form.querySelector('button[type="submit"]');
    var typeInput = form.querySelector("[data-lead-type-input]");
    var productInput = form.querySelector("[data-lead-product-input]");
    var titleEl = modal.querySelector("[data-lead-title]");
    var leadEl = modal.querySelector("[data-lead-lead]");
    var closeLabel = modal.querySelector("[data-lead-close-label]");

    function pack() {
      return COPY[lang()] || COPY.uk;
    }

    function applyCopy(leadType) {
      var p = pack();
      var copy = p[leadType] || p.phone_modal;
      titleEl.textContent = copy.title;
      leadEl.textContent = copy.lead;
      submitBtn.textContent = copy.cta;
      if (closeLabel) closeLabel.textContent = p.close;
    }

    function open(leadType, productId) {
      typeInput.value = leadType || "phone_modal";
      productInput.value = productId || "";
      applyCopy(typeInput.value);
      modal.classList.toggle("modal--arch", typeInput.value === "phone_modal");
      form.classList.remove("is-hidden");
      successBox.classList.remove("is-visible");
      modal.classList.add("is-open");
      modal.setAttribute("aria-hidden", "false");
      SonyashnykUtils.lockScroll();
      window.setTimeout(function () {
        var firstField = form.querySelector('input[name="name"], input[name="phone"]');
        if (firstField) firstField.focus();
      }, 250);
    }

    function close() {
      if (!modal.classList.contains("is-open")) return;
      modal.classList.remove("is-open");
      modal.classList.remove("modal--arch");
      modal.setAttribute("aria-hidden", "true");
      SonyashnykUtils.unlockScroll();
    }

    window.SonyashnykLeadModal = { open: open, close: close };

    modal.querySelectorAll("[data-modal-close]").forEach(function (el) {
      el.addEventListener("click", close);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && modal.classList.contains("is-open")) close();
    });

    document.querySelectorAll("[data-lead-open]").forEach(function (trigger) {
      trigger.addEventListener("click", function () {
        open(trigger.getAttribute("data-lead-type"), trigger.getAttribute("data-product-id"));
      });
    });

    if (window.SonyashnykFormValidation) {
      SonyashnykFormValidation.bindSubmitValidation(form);
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (window.SonyashnykFormValidation && !SonyashnykFormValidation.validateForm(form)) {
        return;
      }
      submitBtn.disabled = true;
      var formData = new FormData(form);
      SonyashnykUtils.postForm(window.SONYASHNYK.leadUrl, formData)
        .then(function (result) {
          submitBtn.disabled = false;
          if (result.data && result.data.ok) {
            form.classList.add("is-hidden");
            successBox.classList.add("is-visible");
            window.localStorage.setItem(STORAGE_KEY, "1");
            window.setTimeout(close, 2200);
          } else {
            SonyashnykUtils.showToast(
              window.SonyashnykFormValidation
                ? SonyashnykFormValidation.t("toast_phone_check")
                : "Перевірте, будь ласка, номер телефону."
            );
          }
        })
        .catch(function () {
          submitBtn.disabled = false;
          SonyashnykUtils.showToast(
            window.SonyashnykFormValidation
              ? SonyashnykFormValidation.t("toast_generic_error")
              : "Сталася помилка. Спробуйте ще раз."
          );
        });
    });

    if (!window.localStorage.getItem(STORAGE_KEY)) {
      window.setTimeout(function () {
        if (!modal.classList.contains("is-open")) open("phone_modal");
      }, AUTO_OPEN_DELAY);
    }
  });
})();
