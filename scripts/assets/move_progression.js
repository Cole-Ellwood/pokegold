    const DATA = window.REPORT_DATA;
    const cards = Array.from(document.querySelectorAll("[data-card]"));
    const rows = Array.from(document.querySelectorAll("[data-row]"));
    const search = document.querySelector("#search");
    const typeFilter = document.querySelector("#typeFilter");
    const buttons = Array.from(document.querySelectorAll("[data-filter]"));
    const visibleCount = document.querySelector("#visibleCount");
    const empty = document.querySelector("#empty");
    let activeFilter = "issue";

    function matches(item, query, type, mode) {
      const haystack = [
        item.family,
        item.laterSpecies,
        item.earlierSpecies,
        item.later.name,
        item.earlier.name,
        item.reason,
        item.suggestion,
        item.severity,
      ].join(" ").toLowerCase();
      const classOk = mode === "all" || item.classification === mode;
      const typeOk = type === "all" || item.later.rawType === type;
      const queryOk = !query || haystack.includes(query);
      return classOk && typeOk && queryOk;
    }

    function applyFilters() {
      const query = search.value.trim().toLowerCase();
      const type = typeFilter.value;
      let count = 0;
      cards.forEach((card) => {
        const item = DATA.findings[Number(card.dataset.card)];
        const show = matches(item, query, type, activeFilter);
        card.classList.toggle("hidden", !show);
        if (show) count += 1;
      });
      rows.forEach((row) => {
        const item = DATA.findings[Number(row.dataset.row)];
        row.hidden = !matches(item, query, type, activeFilter);
      });
      visibleCount.textContent = count;
      empty.style.display = count === 0 ? "block" : "none";
    }

    buttons.forEach((button) => {
      button.addEventListener("click", () => {
        buttons.forEach((other) => other.classList.remove("active"));
        button.classList.add("active");
        activeFilter = button.dataset.filter;
        applyFilters();
      });
    });
    search.addEventListener("input", applyFilters);
    typeFilter.addEventListener("change", applyFilters);
    applyFilters();
