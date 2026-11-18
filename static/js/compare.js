// "Compare" toggles and the floating compare tray.
(function () {
  "use strict";

  var tray = document.getElementById("compare-tray");

  function setState(id, inCompare) {
    document.querySelectorAll('[data-compare][data-id="' + id + '"]').forEach(function (btn) {
      if (btn.closest("#compare-tray")) return;
      btn.setAttribute("aria-pressed", String(inCompare));
      var hidden = btn.form.querySelector('input[name="compare"]');
      if (hidden) hidden.value = inCompare ? "0" : "1";
    });
  }

  function renderTray(items) {
    document.querySelectorAll("[data-compare-count]").forEach(function (el) {
      el.hidden = items.length === 0;
      el.firstChild.textContent = String(items.length);
    });
    if (!tray) return;
    var list = tray.querySelector("[data-compare-tray-list]");
    list.innerHTML = "";
    items.forEach(function (item) {
      var li = document.createElement("li");
      li.appendChild(document.createTextNode(item.name));
      var form = document.createElement("form");
      form.method = "post";
      form.action = "/compare/" + item.id;
      form.innerHTML =
        '<input type="hidden" name="csrf_token"><input type="hidden" name="compare" value="0">' +
        '<button type="submit" class="btn btn-ghost btn-icon" data-compare aria-pressed="true"></button>';
      form.querySelector('[name="csrf_token"]').value = DD.csrf;
      var btn = form.querySelector("button");
      btn.dataset.id = item.id;
      btn.dataset.name = item.name;
      btn.setAttribute("aria-label", "Remove " + item.name + " from compare");
      btn.innerHTML = DD.iconHTML("x");
      li.appendChild(form);
      list.appendChild(li);
    });
    tray.querySelector("[data-compare-tray-count]").textContent = "(" + items.length + "/3)";
    tray.hidden = items.length === 0;
    document.body.classList.toggle("has-tray", items.length > 0);
  }

  document.addEventListener("click", async function (e) {
    var btn = e.target.closest("[data-compare]");
    if (!btn) return;
    e.preventDefault();
    var fromTray = !!btn.closest("#compare-tray");
    var add = !fromTray && btn.getAttribute("aria-pressed") !== "true";
    var id = btn.dataset.id;
    try {
      var res = await DD.api(btn.form.action, { data: { compare: add ? "1" : "0" } });
      setState(id, res.in_compare);
      renderTray(res.items);
      if (fromTray) {
        var next = tray.querySelector("[data-compare]") || tray.querySelector("a") ;
        if (next && !tray.hidden) next.focus(); else document.getElementById("main").focus();
      }
      DD.toast(res.message, { type: res.in_compare ? "success" : "info" });
    } catch (err) {
      if (err.payload && err.payload.items) renderTray(err.payload.items);
      DD.toast(err.message, { type: "error" });
    }
  });
})();
