/* ============================================================
   ІНЛАЙН-ЛІД-ФОРМИ — підписка на email (K) та форма "Контакти"
   Будь-яка форма з [data-lead-form-inline] надсилається сюди через AJAX.
   ============================================================ */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-lead-form-inline]").forEach(initInlineLeadForm);
  });

  function toast(key) {
    var msg = window.SonyashnykFormValidation
      ? SonyashnykFormValidation.t(key)
      : key;
    SonyashnykUtils.showToast(msg);
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
            toast("toast_lead_ok");
            form.reset();
          } else {
            toast("toast_lead_fail");
          }
        })
        .catch(function () {
          button.disabled = false;
          toast("toast_network");
        });
    });
  }
})();
