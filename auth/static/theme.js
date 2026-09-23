(() => {
  const root = document.documentElement;
  const saved = localStorage.getItem("byteon-theme");
  root.dataset.theme = saved || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  addEventListener("DOMContentLoaded", () => document.querySelectorAll("[data-theme-toggle]").forEach(button => {
    const update = () => { button.textContent = root.dataset.theme === "dark" ? "☀" : "☾"; button.setAttribute("aria-label", `Use ${root.dataset.theme === "dark" ? "light" : "dark"} mode`); };
    button.onclick = () => { root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark"; localStorage.setItem("byteon-theme", root.dataset.theme); update(); };
    update();
  }));
})();
