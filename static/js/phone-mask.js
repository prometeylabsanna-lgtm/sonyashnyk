/* ============================================================
   PHONE MASK — простий формат +380 (XX) XXX-XX-XX без залежностей
   ============================================================ */
(function () {
  "use strict";

  function formatPhone(digits) {
    // digits — лише цифри, без коду країни (максимум 9 після 380)
    var d = digits.slice(0, 9);
    var out = "+380";
    if (d.length > 0) out += " (" + d.slice(0, 2);
    if (d.length >= 2) out += ")";
    if (d.length > 2) out += " " + d.slice(2, 5);
    if (d.length > 5) out += "-" + d.slice(5, 7);
    if (d.length > 7) out += "-" + d.slice(7, 9);
    return out;
  }

  function toDigitsAfterCountryCode(value) {
    var digits = value.replace(/\D/g, "");
    if (digits.startsWith("380")) digits = digits.slice(3);
    else if (digits.startsWith("0")) digits = digits.slice(1);
    return digits;
  }

  function attach(input) {
    input.addEventListener("focus", function () {
      if (!input.value) input.value = "+380 (";
    });
    input.addEventListener("input", function () {
      var digits = toDigitsAfterCountryCode(input.value);
      input.value = formatPhone(digits);
    });
    input.addEventListener("blur", function () {
      if (input.value === "+380 (") input.value = "";
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-phone-mask]").forEach(attach);
  });
})();
