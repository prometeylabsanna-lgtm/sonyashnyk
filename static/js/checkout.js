/* ============================================================
   ОФОРМЛЕННЯ ЗАМОВЛЕННЯ — показ полів доставки, згорнутий підсумок
   ============================================================ */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    var radios = document.querySelectorAll('input[name="delivery_method"]');
    var fieldsBlock = document.querySelector("[data-delivery-fields]");
    var cityLabel = document.querySelector("[data-delivery-city-label]");
    var warehouseLabel = document.querySelector("[data-delivery-warehouse-label]");

    var LABELS = {
      np_branch: { city: "Місто", warehouse: "№ відділення Нової Пошти" },
      np_locker: { city: "Місто", warehouse: "№ поштомату Нової Пошти" },
      np_courier: { city: "Місто", warehouse: "Адреса доставки" },
      ukrposhta: { city: "Місто", warehouse: "№ відділення Укрпошти" },
      pickup: { city: "", warehouse: "" },
    };

    function update(value) {
      if (!fieldsBlock) return;
      var showFields = value !== "pickup";
      fieldsBlock.classList.toggle("is-visible", showFields);
      var labels = LABELS[value] || LABELS.np_branch;
      if (cityLabel) cityLabel.textContent = labels.city;
      if (warehouseLabel) warehouseLabel.textContent = labels.warehouse;
    }

    radios.forEach(function (radio) {
      radio.addEventListener("change", function () { update(radio.value); });
      if (radio.checked) update(radio.value);
    });

    var toggleBtn = document.querySelector("[data-summary-toggle]");
    var summaryBody = document.querySelector("[data-summary-body]");
    if (toggleBtn && summaryBody) {
      toggleBtn.addEventListener("click", function () {
        var isOpen = summaryBody.style.display !== "none";
        summaryBody.style.display = isOpen ? "none" : "";
        toggleBtn.setAttribute("aria-expanded", String(!isOpen));
      });
    }
  });
})();
