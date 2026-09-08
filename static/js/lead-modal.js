/* ============================================================
   ЛІД-МОДАЛКА — телефон/знижка, «1 клік», callback (§2.11 карти сайту)
   Одна модалка, контент і lead_type підлаштовуються під тригер.
   ============================================================ */
(function () {
  "use strict";

  var AUTO_OPEN_DELAY = 15000; // мс — за замовчуванням; легко змінити тут
  var STORAGE_KEY = "sonyashnyk_lead_modal_shown";

  var COPY = {
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
  };

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

    function applyCopy(leadType) {
      var copy = COPY[leadType] || COPY.phone_modal;
      titleEl.textContent = copy.title;
      leadEl.textContent = copy.lead;
      submitBtn.textContent = copy.cta;
    }

    function open(leadType, productId) {
      typeInput.value = leadType || "phone_modal";
      productInput.value = productId || "";
      applyCopy(typeInput.value);
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

    form.addEventListener("submit", function (e) {
      e.preventDefault();
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
            SonyashnykUtils.showToast("Перевірте, будь ласка, номер телефону.");
          }
        })
        .catch(function () {
          submitBtn.disabled = false;
          SonyashnykUtils.showToast("Сталася помилка. Спробуйте ще раз.");
        });
    });

    // --- Автопоказ один раз за сесію/пристрій, якщо користувач ще не залишав заявку ---
    if (!window.localStorage.getItem(STORAGE_KEY)) {
      window.setTimeout(function () {
        if (!modal.classList.contains("is-open")) open("phone_modal");
      }, AUTO_OPEN_DELAY);
    }
  });
})();
