/* ============================================================
   ОФОРМЛЕННЯ ЗАМОВЛЕННЯ — доставка, НП-пошук, підсумок
   ============================================================ */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    var form = document.querySelector(".checkout-form");
    var radios = document.querySelectorAll('input[name="delivery_method"]');
    var fieldsBlock = document.querySelector("[data-delivery-fields]");
    var cityLabel = document.querySelector("[data-delivery-city-label]");
    var warehouseLabel = document.querySelector("[data-delivery-warehouse-label]");
    var cityInput = document.querySelector("[data-np-city-input]");
    var warehouseInput = document.querySelector("[data-np-warehouse-input]");
    var cityRef = document.querySelector("[data-np-city-ref]");
    var warehouseRef = document.querySelector("[data-np-warehouse-ref]");
    var cityList = document.querySelector('[data-search-select="city"] [data-search-list]');
    var warehouseList = document.querySelector('[data-search-select="warehouse"] [data-search-list]');

    var npEnabled = form && form.getAttribute("data-np-enabled") === "1";
    var citiesUrl = form && form.getAttribute("data-np-cities-url");
    var warehousesUrl = form && form.getAttribute("data-np-warehouses-url");
    var debounce = (window.SonyashnykUtils && window.SonyashnykUtils.debounce) || function (fn, wait) {
      var t;
      return function () {
        var args = arguments;
        var ctx = this;
        clearTimeout(t);
        t = setTimeout(function () { fn.apply(ctx, args); }, wait);
      };
    };

    var LABELS = {
      np_branch: { city: "Місто", warehouse: "Відділення Нової Пошти", showWh: true, kind: "branch" },
      np_locker: { city: "Місто", warehouse: "Поштомат Нової Пошти", showWh: true, kind: "locker" },
      np_courier: { city: "Місто", warehouse: "Адреса доставки", showWh: true, kind: "courier" },
      ukrposhta: { city: "Місто", warehouse: "№ відділення Укрпошти", showWh: true, kind: "manual" },
      pickup: { city: "", warehouse: "", showWh: false, kind: "none" },
    };

    function currentDelivery() {
      var checked = document.querySelector('input[name="delivery_method"]:checked');
      return checked ? checked.value : "np_branch";
    }

    function updateDeliveryUI() {
      if (!fieldsBlock) return;
      var value = currentDelivery();
      var labels = LABELS[value] || LABELS.np_branch;
      var showFields = value !== "pickup";
      fieldsBlock.classList.toggle("is-visible", showFields);
      if (cityLabel) cityLabel.textContent = labels.city;
      if (warehouseLabel) warehouseLabel.textContent = labels.warehouse;
      if (warehouseInput) {
        warehouseInput.placeholder = labels.kind === "courier"
          ? "Вулиця, будинок, квартира"
          : (npEnabled ? "Почніть вводити або оберіть зі списку" : "Введіть вручну");
      }
      hideList(cityList);
      hideList(warehouseList);
    }

    function hideList(list) {
      if (!list) return;
      list.hidden = true;
      list.innerHTML = "";
    }

    function renderList(list, items, onPick) {
      if (!list) return;
      list.innerHTML = "";
      if (!items.length) {
        list.hidden = true;
        return;
      }
      items.forEach(function (item) {
        var li = document.createElement("li");
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "search-select__option";
        btn.textContent = item.name;
        btn.addEventListener("click", function () {
          onPick(item);
          hideList(list);
        });
        li.appendChild(btn);
        list.appendChild(li);
      });
      list.hidden = false;
    }

    function fetchJson(url) {
      return fetch(url, { credentials: "same-origin", headers: { "X-Requested-With": "fetch" } })
        .then(function (res) { return res.json(); });
    }

    function searchCities(query) {
      if (!npEnabled || !citiesUrl || query.length < 2) {
        hideList(cityList);
        return;
      }
      fetchJson(citiesUrl + "?q=" + encodeURIComponent(query)).then(function (data) {
        if (data.fallback) {
          hideList(cityList);
          return;
        }
        renderList(cityList, data.items || [], function (item) {
          if (cityInput) cityInput.value = item.name;
          if (cityRef) cityRef.value = item.ref;
          if (warehouseInput) warehouseInput.value = "";
          if (warehouseRef) warehouseRef.value = "";
        });
      }).catch(function () { hideList(cityList); });
    }

    function searchWarehouses(query) {
      var meta = LABELS[currentDelivery()] || LABELS.np_branch;
      if (!npEnabled || !warehousesUrl || meta.kind === "courier" || meta.kind === "manual") {
        hideList(warehouseList);
        return;
      }
      if (!cityRef || !cityRef.value) {
        hideList(warehouseList);
        return;
      }
      var url = warehousesUrl
        + "?city_ref=" + encodeURIComponent(cityRef.value)
        + "&kind=" + encodeURIComponent(meta.kind)
        + "&q=" + encodeURIComponent(query || "");
      fetchJson(url).then(function (data) {
        if (data.fallback) {
          hideList(warehouseList);
          return;
        }
        renderList(warehouseList, data.items || [], function (item) {
          if (warehouseInput) warehouseInput.value = item.name;
          if (warehouseRef) warehouseRef.value = item.ref;
        });
      }).catch(function () { hideList(warehouseList); });
    }

    radios.forEach(function (radio) {
      radio.addEventListener("change", function () {
        if (cityRef) cityRef.value = "";
        if (warehouseRef) warehouseRef.value = "";
        if (cityInput) cityInput.value = "";
        if (warehouseInput) warehouseInput.value = "";
        updateDeliveryUI();
      });
      if (radio.checked) updateDeliveryUI();
    });
    updateDeliveryUI();

    if (cityInput) {
      cityInput.addEventListener("input", debounce(function () {
        if (cityRef) cityRef.value = "";
        if (warehouseRef) warehouseRef.value = "";
        if (warehouseInput) warehouseInput.value = "";
        searchCities(cityInput.value.trim());
      }, 280));
      cityInput.addEventListener("focus", function () {
        if (npEnabled && cityInput.value.trim().length >= 2) searchCities(cityInput.value.trim());
      });
    }

    if (warehouseInput) {
      warehouseInput.addEventListener("input", debounce(function () {
        if (warehouseRef) warehouseRef.value = "";
        searchWarehouses(warehouseInput.value.trim());
      }, 280));
      warehouseInput.addEventListener("focus", function () {
        searchWarehouses(warehouseInput.value.trim());
      });
    }

    document.addEventListener("click", function (e) {
      if (!e.target.closest("[data-search-select]")) {
        hideList(cityList);
        hideList(warehouseList);
      }
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

    if (form && window.SonyashnykFormValidation) {
      function shouldValidateCheckoutField(input) {
        var name = input.getAttribute("name") || "";
        if (name === "city") {
          return currentDelivery() !== "pickup";
        }
        if (name === "warehouse") {
          var meta = LABELS[currentDelivery()] || LABELS.np_branch;
          return !!meta.showWh;
        }
        return true;
      }

      var cityField = form.querySelector('[name="city"]');
      var warehouseField = form.querySelector('[name="warehouse"]');
      var fullNameField = form.querySelector('[name="full_name"]');
      var phoneField = form.querySelector('[name="phone"]');
      var emailField = form.querySelector('[name="email"]');
      var agreeField = form.querySelector('[name="agreed_to_data_processing"]');

      if (fullNameField) {
        fullNameField.setAttribute("data-validate", "name");
        fullNameField.setAttribute("data-validate-required", "");
      }
      if (phoneField) {
        phoneField.setAttribute("data-validate", "phone");
        phoneField.setAttribute("data-validate-required", "");
      }
      if (emailField) {
        emailField.setAttribute("data-validate", "email");
        emailField.setAttribute("data-validate-optional", "");
      }
      if (cityField) cityField.setAttribute("data-validate", "city");
      if (warehouseField) warehouseField.setAttribute("data-validate", "warehouse");
      if (agreeField) agreeField.setAttribute("data-validate-required", "");

      form.addEventListener("submit", function (e) {
        if (cityField) {
          if (currentDelivery() !== "pickup") cityField.setAttribute("data-validate-required", "");
          else cityField.removeAttribute("data-validate-required");
        }
        if (warehouseField) {
          var meta = LABELS[currentDelivery()] || LABELS.np_branch;
          if (meta.showWh) warehouseField.setAttribute("data-validate-required", "");
          else warehouseField.removeAttribute("data-validate-required");
        }

        if (!SonyashnykFormValidation.validateForm(form, { shouldValidate: shouldValidateCheckoutField })) {
          e.preventDefault();
        }
      }, true);
    }
  });
})();
