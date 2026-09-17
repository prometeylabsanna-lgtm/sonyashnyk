/* ============================================================
   ІНЛАЙН-ЛІД-ФОРМИ — підписка на email (K) та форма "Контакти"
   Будь-яка форма з [data-lead-form-inline] надсилається сюди через AJAX.
   ============================================================ */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-lead-form-inline]").forEach(initInlineLeadForm);
  });

  function toast(uk, ru) {
    var isRu = window.SonyashnykFormValidation && SonyashnykFormValidation.getLang() === "ru";
    SonyashnykUtils.showToast(isRu ? ru : uk);
  }

  function initInlineLeadForm(form) {
    if (window.SonyashnykFormValidation) {
      SonyashnykFormValidation.bindSubmitValidation(form);
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (window.SonyashnykFormValidation && !SonyashnykFormValidation.validateForm(form)) {
        return;
      }
      var button = form.querySelector('button[type="submit"]');
      button.disabled = true;
      var formData = new FormData(form);
      SonyashnykUtils.postForm(window.SONYASHNYK.leadUrl, formData)
        .then(function (result) {
          button.disabled = false;
          if (result.data && result.data.ok) {
            toast("Дякуємо! Ваше повідомлення надіслано.", "Спасибо! Ваше сообщение отправлено.");
            form.reset();
          } else {
            toast("Перевірте поля форми і спробуйте ще раз.", "Проверьте поля формы и попробуйте ещё раз.");
          }
        })
        .catch(function () {
          button.disabled = false;
          toast("Сталася помилка мережі.", "Произошла сетевая ошибка.");
        });
    });
  }
})();
