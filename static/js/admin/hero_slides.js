(() => {
  const root = document.querySelector("[data-hero-slides]");
  if (!root) return;

  const list = root.querySelector("[data-hero-list]");
  const addBtn = root.querySelector("[data-hero-add]");
  const emptyTpl = root.querySelector("[data-hero-empty]");
  const totalInput = root.querySelector('input[name$="-TOTAL_FORMS"]');
  if (!list || !addBtn || !emptyTpl || !totalInput) return;

  const reindex = () => {
    const rows = [...list.querySelectorAll("[data-hero-row]")];
    rows.forEach((row, index) => {
      row.querySelectorAll("input, textarea, select, label").forEach((el) => {
        ["name", "id", "for"].forEach((attr) => {
          const val = el.getAttribute(attr);
          if (!val) return;
          el.setAttribute(attr, val.replace(/hero_slides-\d+-/, `hero_slides-${index}-`));
        });
      });
      const order = row.querySelector('input[name$="-order"]');
      if (order) order.value = String(index);
    });
    totalInput.value = String(rows.length);
  };

  addBtn.addEventListener("click", () => {
    const html = emptyTpl.innerHTML.replace(/__prefix__/g, totalInput.value);
    const wrap = document.createElement("div");
    wrap.innerHTML = html.trim();
    const row = wrap.firstElementChild;
    if (!row) return;
    list.appendChild(row);
    reindex();
  });

  let dragRow = null;
  list.addEventListener("dragstart", (e) => {
    const handle = e.target.closest("[data-hero-handle]");
    if (!handle || !list.contains(handle)) return;
    dragRow = handle.closest("[data-hero-row]");
    if (!dragRow) return;
    dragRow.classList.add("is-dragging");
    if (e.dataTransfer) {
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", "slide");
    }
  });
  list.addEventListener("dragend", () => {
    if (dragRow) dragRow.classList.remove("is-dragging");
    dragRow = null;
    reindex();
  });
  list.addEventListener("dragover", (e) => {
    e.preventDefault();
    const row = e.target.closest("[data-hero-row]");
    if (!row || !dragRow || row === dragRow) return;
    const rect = row.getBoundingClientRect();
    const after = e.clientY > rect.top + rect.height / 2;
    list.insertBefore(dragRow, after ? row.nextSibling : row);
  });
})();
