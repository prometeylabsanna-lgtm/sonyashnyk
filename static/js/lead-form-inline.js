/* ============================================================
   ІНЛАЙН-ЛІД-ФОРМИ — підписка на email (K) та форма "Контакти"
   Будь-яка форма з [data-lead-form-inline] надсилається сюди через AJAX.
   ============================================================ */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-lead-form-inline]").forEach(initInlineLeadForm);
  });

  function initInlineLeadForm(form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var button = form.querySelector('button[type="submit"]');
      button.disabled = true;
      var formData = new FormData(form);
      SonyashnykUtils.postForm(window.SONYASHNYK.leadUrl, formData)
        .then(function (result) {
          button.disabled = false;
          if (result.data && result.data.ok) {
            SonyashnykUtils.showToast("Дякуємо! Ваше повідомлення надіслано.");
            form.reset();
          } else {
            SonyashnykUtils.showToast("Перевірте поля форми і спробуйте ще раз.");
          }
        })
        .catch(function () {
          button.disabled = false;
          SonyashnykUtils.showToast("Сталася помилка мережі.");
        });
    });
  }
})();
