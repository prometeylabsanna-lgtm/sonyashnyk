(() => {
  const rowHtml = (name) =>
    `<div class="char-kv__row" data-char-kv-row>` +
    `<input type="text" name="${name}_key" value="" ` +
    `placeholder="Назва (напр. Тип)" autocomplete="off" class="char-kv__input">` +
    `<span class="char-kv__arrow" aria-hidden="true">→</span>` +
    `<input type="text" name="${name}_value" value="" ` +
    `placeholder="Значення (напр. овочеве)" autocomplete="off" class="char-kv__input">` +
    `<button type="button" class="char-kv__remove" data-char-kv-remove ` +
    `aria-label="Видалити рядок">×</button>` +
    `</div>`;

  const bind = (root) => {
    const name = root.getAttribute("data-char-kv-name");
    const rows = root.querySelector("[data-char-kv-rows]");
    const addBtn = root.querySelector("[data-char-kv-add]");
    if (!name || !rows || !addBtn) return;

    addBtn.addEventListener("click", () => {
      rows.insertAdjacentHTML("beforeend", rowHtml(name));
      const last = rows.querySelector("[data-char-kv-row]:last-child input");
      if (last) last.focus();
    });

    root.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-char-kv-remove]");
      if (!btn || !root.contains(btn)) return;
      const row = btn.closest("[data-char-kv-row]");
      if (!row) return;
      const all = rows.querySelectorAll("[data-char-kv-row]");
      if (all.length <= 1) {
        row.querySelectorAll("input").forEach((input) => {
          input.value = "";
        });
        return;
      }
      row.remove();
    });
  };

  document.querySelectorAll("[data-char-kv]").forEach(bind);
})();
