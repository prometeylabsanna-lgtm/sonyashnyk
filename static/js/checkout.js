/* ============================================================
   ОФОРМЛЕННЯ ЗАМОВЛЕННЯ — доставка, НП-пошук, підсумок, uk/ru
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

    function tr(key) {
      return window.SonyashnykFormValidation ? SonyashnykFormValidation.t(key) : key;
    }

    function deliveryMeta(value) {
      var map = {
        np_branch: { cityKey: "delivery_city", warehouseKey: "delivery_np_branch", showWh: true, kind: "branch" },
        np_locker: { cityKey: "delivery_city", warehouseKey: "delivery_np_locker", showWh: true, kind: "locker" },
        np_courier: { cityKey: "delivery_city", warehouseKey: "delivery_np_courier", showWh: true, kind: "courier" },
        ukrposhta: { cityKey: "delivery_city", warehouseKey: "delivery_ukrposhta", showWh: true, kind: "manual" },
        pickup: { cityKey: "", warehouseKey: "", showWh: false, kind: "none" },
      };
      return map[value] || map.np_branch;
    }

    var CHOICE_I18N = {
      delivery_method: {
        np_branch: "delivery_choice_np_branch",
        np_locker: "delivery_choice_np_locker",
        np_courier: "delivery_choice_np_courier",
        ukrposhta: "delivery_choice_ukrposhta",
        pickup: "delivery_choice_pickup",
      },
      payment_method: {
        liqpay: "payment_choice_liqpay",
        cod: "payment_choice_cod",
        bank: "payment_choice_bank",
        cash_pickup: "payment_choice_cash",
      },
    };

    function currentDelivery() {
      var checked = document.querySelector('input[name="delivery_method"]:checked');
      return checked ? checked.value : "np_branch";
    }

    function updateChoiceLabels() {
      Object.keys(CHOICE_I18N).forEach(function (fieldName) {
        var keys = CHOICE_I18N[fieldName];
        document.querySelectorAll('input[name="' + fieldName + '"]').forEach(function (input) {
          var key = keys[input.value];
          if (!key) return;
          var label = input.closest("label");
          var textEl = label && label.querySelector(".radio-card__label");
          if (textEl) textEl.textContent = tr(key);
        });
      });
    }

    function updateStaticCheckoutFields() {
      if (!form) return;
      var map = [
        ["full_name", "ph_full_name", "label_full_name"],
        ["phone", "ph_phone", "label_phone"],
        ["email", "ph_email", "label_email"],
        ["city", "ph_city", "label_city"],
        ["comment", "ph_comment", "label_comment"],
        ["promo_code", "ph_promo", "label_promo"],
      ];
      map.forEach(function (row) {
        var input = form.querySelector('[name="' + row[0] + '"]');
        if (input && row[1]) input.setAttribute("placeholder", tr(row[1]));
        if (input && row[2] && input.id) {
          var lab = form.querySelector('label[for="' + input.id + '"]');
          if (lab && !lab.hasAttribute("data-delivery-city-label") && !lab.hasAttribute("data-delivery-warehouse-label")) {
            lab.textContent = tr(row[2]);
          }
        }
      });
      var agree = form.querySelector('[name="agreed_to_data_processing"]');
      if (agree && agree.id) {
        var agreeLab = form.querySelector('label[for="' + agree.id + '"]');
        if (agreeLab) agreeLab.textContent = tr("label_agree");
      }
      updateChoiceLabels();
    }

    function updateDeliveryUI() {
      if (!fieldsBlock) return;
      var value = currentDelivery();
      var meta = deliveryMeta(value);
      var showFields = value !== "pickup";
      fieldsBlock.classList.toggle("is-visible", showFields);
      if (cityLabel && meta.cityKey) cityLabel.textContent = tr(meta.cityKey);
      if (warehouseLabel && meta.warehouseKey) warehouseLabel.textContent = tr(meta.warehouseKey);
      if (warehouseInput) {
        if (meta.kind === "courier") {
          warehouseInput.placeholder = tr("ph_warehouse_courier");
        } else if (npEnabled) {
          warehouseInput.placeholder = tr("ph_warehouse_pick");
        } else {
          warehouseInput.placeholder = tr("ph_warehouse_manual");
        }
      }
      if (cityInput) cityInput.placeholder = tr("ph_city");
      hideList(cityList);
      hideList(warehouseList);
    }

    function applyCheckoutI18n() {
      updateStaticCheckoutFields();
      updateDeliveryUI();
      if (window.SonyashnykFormValidation) {
        SonyashnykFormValidation.applyStaticI18n(form || document);
      }
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
      var meta = deliveryMeta(currentDelivery());
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
    applyCheckoutI18n();

    document.addEventListener("sonyashnyk:langchange", applyCheckoutI18n);

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
          var meta = deliveryMeta(currentDelivery());
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
          var meta = deliveryMeta(currentDelivery());
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
