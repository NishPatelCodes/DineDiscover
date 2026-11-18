// Live filtering on the results page. The form still works as a normal GET form without JS.
(function () {
  "use strict";

  var form = document.getElementById("filters-form");
  if (!form) return;
  var results = document.getElementById("results");
  var home = document.getElementById("filters-home");
  var sheet = document.getElementById("filters-sheet");
  var slot = sheet.querySelector("[data-filters-slot]");
  var openBtn = document.querySelector('[data-dialog-open="filters-sheet"]');
  var slider = document.getElementById("f-max-km");
  var sliderOut = document.getElementById("f-max-km-out");
  var cuisineSelect = document.getElementById("f-cuisine");
  var title = document.querySelector(".page-title");
  var nearSelect = document.getElementById("f-near");

  openBtn.hidden = false;

  // On small screens the same form moves into the slide-over sheet while it's open.
  document.addEventListener("dd:dialog-open", function (e) { if (e.detail === sheet) slot.appendChild(form); });
  document.addEventListener("dd:dialog-close", function (e) { if (e.detail === sheet) home.appendChild(form); });

  function updateSliderText() {
    var any = slider.value === slider.dataset.any;
    sliderOut.textContent = any ? "Any" : slider.value + " km";
    slider.setAttribute("aria-valuetext", any ? "Any distance" : "Within " + slider.value + " kilometres");
  }

  function paramsFromForm() {
    var params = new URLSearchParams();
    new FormData(form).forEach(function (value, key) {
      if (value === "") return;
      if (key === "max_km" && value === slider.dataset.any) return;
      if (key === "sort" && value === "rating") return;
      params.append(key, value);
    });
    return params;
  }

  function syncForm(params) {
    Array.from(form.elements).forEach(function (el) {
      if (!el.name) return;
      if (el.type === "checkbox") el.checked = params.getAll(el.name).indexOf(el.value) !== -1;
      else if (el.type === "radio") el.checked = el.value === (params.get(el.name) || "");
      else if (el === slider) el.value = params.get("max_km") || slider.dataset.any;
      else if (el.tagName === "SELECT") el.value = params.get(el.name) || (el.name === "sort" ? "rating" : el.name === "near" ? el.value : "");
      else if (el.type === "search" || el.type === "text") el.value = params.get(el.name) || "";
    });
    updateSliderText();
  }

  function showSkeletons() {
    var grid = results.querySelector(".card-grid");
    if (!grid) return;
    var html = "";
    for (var i = 0; i < Math.min(grid.children.length || 3, 6); i++) {
      html += '<li aria-hidden="true"><div class="card r-card"><div class="r-media skeleton" style="border-radius:0"></div>' +
        '<div class="r-body"><div class="skeleton" style="height:1.25rem;width:70%"></div>' +
        '<div class="skeleton" style="height:1rem;width:45%"></div><div class="skeleton" style="height:1rem;width:60%"></div></div></div></li>';
    }
    grid.innerHTML = html;
  }

  var controller = null;
  var skeletonTimer = null;

  async function refresh(params, opts) {
    opts = opts || {};
    if (controller) controller.abort();
    controller = new AbortController();
    var url = form.action + (params.toString() ? "?" + params.toString() : "");
    var fetchParams = new URLSearchParams(params);
    fetchParams.set("partial", "1");

    results.setAttribute("aria-busy", "true");
    clearTimeout(skeletonTimer);
    skeletonTimer = setTimeout(showSkeletons, 300);
    try {
      var res = await fetch(form.action + "?" + fetchParams.toString(), {
        signal: controller.signal,
        headers: { "X-Requested-With": "fetch" },
        credentials: "same-origin",
      });
      if (!res.ok) throw new Error("bad status");
      results.innerHTML = await res.text();
      history.replaceState(null, "", url);

      var countEl = document.getElementById("results-count");
      var count = Number(countEl.dataset.count);
      DD.announce(count + " restaurant" + (count === 1 ? "" : "s") + " found");
      sheet.querySelector("[data-sheet-count]").textContent = count;

      var chipCount = results.querySelectorAll(".chip").length;
      var badge = openBtn.querySelector(".nav-count");
      if (chipCount && !badge) {
        badge = document.createElement("span");
        badge.className = "nav-count";
        openBtn.appendChild(badge);
      }
      if (badge) { badge.textContent = chipCount; badge.hidden = !chipCount; }

      var cuisineName = cuisineSelect.value ? cuisineSelect.selectedOptions[0].text : "";
      title.textContent = cuisineName ? cuisineName + " restaurants" : "Discover restaurants";
      document.title = title.textContent + " near " + nearSelect.selectedOptions[0].text + " · DineDiscover";

      if (opts.focusCount) {
        countEl.setAttribute("tabindex", "-1");
        countEl.focus();
      }
    } catch (err) {
      if (err.name !== "AbortError") DD.toast("Couldn't update the results. Check your connection and try again.", { type: "error" });
    } finally {
      clearTimeout(skeletonTimer);
      results.removeAttribute("aria-busy");
    }
  }

  var debounce = null;
  form.addEventListener("input", function (e) {
    if (e.target === slider) { updateSliderText(); return; }
    if (e.target.type === "search") {
      clearTimeout(debounce);
      debounce = setTimeout(function () { refresh(paramsFromForm()); }, 350);
    }
  });
  form.addEventListener("change", function (e) {
    if (e.target.type === "search") return;
    refresh(paramsFromForm());
  });
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    clearTimeout(debounce);
    refresh(paramsFromForm(), { focusCount: true });
    if (sheet.open) sheet.close();
  });

  // Chip removal / "Clear all" links update in place instead of reloading.
  results.addEventListener("click", function (e) {
    var link = e.target.closest("a[data-chip]");
    if (!link) return;
    e.preventDefault();
    var params = new URL(link.href).searchParams;
    syncForm(params);
    refresh(paramsFromForm(), { focusCount: true });
  });

  updateSliderText();
})();
