// Favorite (heart) toggles without a page reload, with Undo on removal.
(function () {
  "use strict";

  function buttonsFor(id) {
    return document.querySelectorAll('[data-favorite][data-id="' + id + '"]');
  }

  function setState(id, favorited) {
    buttonsFor(id).forEach(function (btn) {
      var name = btn.dataset.name;
      btn.setAttribute("aria-pressed", String(favorited));
      btn.setAttribute("aria-label", favorited ? "Remove " + name + " from favorites" : "Save " + name + " to favorites");
      var hidden = btn.form.querySelector('input[name="favorite"]');
      if (hidden) hidden.value = favorited ? "0" : "1";
    });
  }

  async function send(btn, favorited) {
    var res = await DD.api(btn.form.action, { data: { favorite: favorited ? "1" : "0" } });
    setState(btn.dataset.id, res.favorited);
    return res;
  }

  // On the favorites page, removing hides the card and offers Undo.
  function updateFavoritesPage() {
    var list = document.querySelector("[data-favorites-list]");
    if (!list) return;
    var visible = list.querySelectorAll("li:not([hidden])").length;
    var count = document.querySelector("[data-favorites-count]");
    if (count) count.textContent = visible + " saved restaurant" + (visible === 1 ? "" : "s");
    document.querySelector("[data-favorites-empty]").hidden = visible > 0;
    list.hidden = visible === 0;
  }

  document.addEventListener("click", async function (e) {
    var btn = e.target.closest("[data-favorite]");
    if (!btn) return;
    e.preventDefault();
    var next = btn.getAttribute("aria-pressed") !== "true";
    var name = btn.dataset.name;
    try {
      var res = await send(btn, next);
      var item = document.querySelector("[data-favorites-list]") && btn.closest("[data-favorites-list] > li");

      if (item && !res.favorited) {
        var sibling = item.nextElementSibling || item.previousElementSibling;
        item.hidden = true;
        updateFavoritesPage();
        var focusTarget = sibling && !sibling.hidden && sibling.querySelector(".r-title a");
        if (!focusTarget) {
          focusTarget = document.querySelector("h1");
          focusTarget.setAttribute("tabindex", "-1");
        }
        focusTarget.focus();
        DD.toast(res.message, {
          action: {
            label: "Undo",
            onClick: async function () {
              try {
                await send(btn, true);
                item.hidden = false;
                updateFavoritesPage();
                btn.focus();
                DD.toast("Restored " + name + " to favorites.");
              } catch (err) { DD.toast(err.message, { type: "error" }); }
            },
          },
        });
        return;
      }

      DD.toast(res.message, {
        action: {
          label: "Undo",
          onClick: async function () {
            try {
              var undo = await send(btn, !res.favorited);
              DD.toast(undo.message, { type: "info" });
            } catch (err) { DD.toast(err.message, { type: "error" }); }
          },
        },
      });
    } catch (err) {
      DD.toast(err.message, { type: "error" });
    }
  });
})();
