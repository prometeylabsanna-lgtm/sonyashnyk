/* ============================================================
   UTILS — спільні хелпери: CSRF, fetch, toast, debounce
   ============================================================ */
(function () {
  "use strict";

  function getCsrfToken() {
    var input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (input) return input.value;
    return (window.SONYASHNYK && window.SONYASHNYK.csrfToken) || "";
  }

  function postForm(url, formData) {
    formData.append("csrfmiddlewaretoken", getCsrfToken());
    return fetch(url, {
      method: "POST",
      headers: { "X-Requested-With": "fetch" },
      body: formData,
      credentials: "same-origin",
    }).then(function (res) {
      return res.json().then(function (data) {
        return { ok: res.ok, status: res.status, data: data };
      });
    });
  }

  function showToast(message, duration) {
    var toast = document.querySelector("[data-toast]");
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("is-visible");
    window.clearTimeout(toast._hideTimer);
    toast._hideTimer = window.setTimeout(function () {
      toast.classList.remove("is-visible");
    }, duration || 2600);
  }

  // Спільний рахунок блокувань скролу — щоб закриття однієї шторки/модалки
  // не розблоковувало скрол, якщо інша ще відкрита (модалка над кошиком тощо).
  var scrollLockCount = 0;
  function lockScroll() {
    scrollLockCount += 1;
    document.body.style.overflow = "hidden";
  }
  function unlockScroll() {
    scrollLockCount = Math.max(0, scrollLockCount - 1);
    if (scrollLockCount === 0) document.body.style.overflow = "";
  }

  function debounce(fn, wait) {
    var timer = null;
    return function () {
      var args = arguments;
      var ctx = this;
      window.clearTimeout(timer);
      timer = window.setTimeout(function () {
        fn.apply(ctx, args);
      }, wait);
    };
  }

  window.SonyashnykUtils = {
    getCsrfToken: getCsrfToken,
    postForm: postForm,
    showToast: showToast,
    debounce: debounce,
    lockScroll: lockScroll,
    unlockScroll: unlockScroll,
  };
})();
