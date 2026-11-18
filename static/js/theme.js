// Loaded synchronously in <head> so the saved theme applies before first paint.
(function () {
  var root = document.documentElement;
  root.classList.add("js");

  function preferred() {
    var saved = null;
    try { saved = localStorage.getItem("dd-theme"); } catch (e) {}
    if (saved === "light" || saved === "dark") return saved;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function apply(theme) {
    root.classList.toggle("dark", theme === "dark");
    var btn = document.getElementById("theme-toggle");
    if (btn) {
      var next = theme === "dark" ? "light" : "dark";
      btn.setAttribute("aria-label", "Switch to " + next + " theme");
      btn.setAttribute("data-tooltip", "Switch to " + next + " theme");
      btn.querySelector(".theme-icon-light").hidden = theme === "dark";
      btn.querySelector(".theme-icon-dark").hidden = theme !== "dark";
    }
  }

  apply(preferred());

  window.DDTheme = {
    toggle: function () {
      var next = root.classList.contains("dark") ? "light" : "dark";
      try { localStorage.setItem("dd-theme", next); } catch (e) {}
      apply(next);
      return next;
    },
    sync: function () { apply(preferred()); },
  };

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function () {
    var saved = null;
    try { saved = localStorage.getItem("dd-theme"); } catch (e) {}
    if (!saved) apply(preferred());
  });

  // Replace broken restaurant photos with a neutral placeholder showing the cuisine emoji.
  document.addEventListener("error", function (e) {
    var img = e.target;
    if (!(img instanceof HTMLImageElement) || !img.dataset.fallback || img.dataset.failed) return;
    img.dataset.failed = "1";
    var box = document.createElement("div");
    box.className = "img-fallback";
    box.setAttribute("role", "img");
    box.setAttribute("aria-label", img.alt || "Photo unavailable");
    box.textContent = img.dataset.fallback;
    img.replaceWith(box);
  }, true);
})();
