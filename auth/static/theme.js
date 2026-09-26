(() => {
  const root = document.documentElement;
  const palettes = { ocean: "Ocean", violet: "Violet", forest: "Forest", sunset: "Sunset", mono: "Mono" };
  root.dataset.theme = localStorage.getItem("byteon-theme") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  root.dataset.palette = localStorage.getItem("byteon-palette") || "ocean";
  addEventListener("DOMContentLoaded", () => {
    document.body.dataset.theme = root.dataset.theme;
    document.body.dataset.palette = root.dataset.palette;
    if (!document.querySelector("[data-theme-controls]")) {
      const controls = document.createElement("div"); controls.className = "theme-controls theme-floating"; controls.dataset.themeControls = ""; document.body.append(controls);
    }
    document.querySelectorAll("[data-theme-controls]").forEach(host => {
      if (/^\/(coding-challenges|conversion-game|logic-gate-quiz|flashcards|wordsearch_app|trace-tables)(\/|$)/.test(location.pathname) && !host.querySelector('[data-achievements-link]')) {
        const link = document.createElement('a'); link.href = '/achievements'; link.textContent = '★ Achievements'; link.className = 'button'; link.dataset.achievementsLink = ''; host.append(link);
      }
      if (!host.querySelector("[data-palette-select]")) {
        const label = document.createElement("label"); label.className = "palette-control";
        label.innerHTML = `<span>Colour</span><select data-palette-select aria-label="Colour scheme">${Object.entries(palettes).map(([value, name]) => `<option value="${value}">${name}</option>`).join("")}</select>`; host.prepend(label);
      }
      if (!host.querySelector("[data-theme-toggle]")) { const button = document.createElement("button"); button.type = "button"; button.dataset.themeToggle = ""; host.append(button); }
    });
    document.querySelectorAll("[data-palette-select]").forEach(select => {
      select.value = root.dataset.palette;
      select.onchange = () => { root.dataset.palette = select.value; document.body.dataset.palette = select.value; localStorage.setItem("byteon-palette", select.value); document.querySelectorAll("[data-palette-select]").forEach(other => other.value = select.value); };
    });
    document.querySelectorAll("[data-theme-toggle]").forEach(button => {
      const update = () => { button.textContent = root.dataset.theme === "dark" ? "☀ Light" : "☾ Dark"; button.setAttribute("aria-label", `Use ${root.dataset.theme === "dark" ? "light" : "dark"} mode`); };
      button.onclick = () => { root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark"; document.body.dataset.theme = root.dataset.theme; localStorage.setItem("byteon-theme", root.dataset.theme); update(); }; update();
    });
  });
})();
