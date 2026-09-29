/* ============================================================
   Poll статусу оплати на thank-you (LiqPay pending)
   ============================================================ */
(function () {
  "use strict";

  var INTERVAL_MS = 4000;
  var MAX_MS = 120000;

  document.addEventListener("DOMContentLoaded", function () {
    var root = document.querySelector("[data-payment-poll]");
    if (!root) return;
    var url = root.getAttribute("data-payment-status-url");
    if (!url) return;

    var started = Date.now();
    var timer = window.setInterval(function () {
      if (Date.now() - started > MAX_MS) {
        window.clearInterval(timer);
        return;
      }
      fetch(url, { credentials: "same-origin", headers: { Accept: "application/json" } })
        .then(function (res) {
          if (!res.ok) return null;
          return res.json();
        })
        .then(function (data) {
          if (!data || !data.payment_status) return;
          if (data.payment_status === "paid" || data.payment_status === "failed") {
            window.clearInterval(timer);
            window.location.reload();
          }
        })
        .catch(function () { /* тихо: мережа може бути нестабільною */ });
    }, INTERVAL_MS);
  });
})();
