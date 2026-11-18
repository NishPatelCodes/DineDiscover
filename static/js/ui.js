// Shared UI behaviour: fetch helper, toasts, live announcements, dialogs/sheets,
// dropdown menu, tabs, tooltips, confirm dialogs and small enhancements.
(function () {
  "use strict";

  var csrf = document.querySelector('meta[name="csrf-token"]').content;

  function iconHTML(name) {
    var tpl = document.getElementById("icon-templates");
    var el = tpl && tpl.content.querySelector('[data-icon="' + name + '"]');
    return el ? el.innerHTML : "";
  }

  // ---------- Fetch helper ----------
  async function api(url, opts) {
    opts = opts || {};
    var headers = { "X-Requested-With": "fetch", "X-CSRFToken": csrf, Accept: "application/json" };
    var body;
    if (opts.json !== undefined) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(opts.json);
    } else if (opts.data) {
      body = opts.data instanceof FormData ? opts.data : new URLSearchParams(opts.data);
    }
    var res;
    try {
      res = await fetch(url, { method: opts.method || "POST", headers: headers, body: body, credentials: "same-origin" });
    } catch (e) {
      throw new Error("Can't reach DineDiscover. Check your connection and try again.");
    }
    var payload = {};
    try { payload = await res.json(); } catch (e) {}
    if (res.status === 401 && payload.login_url) {
      window.location.href = payload.login_url;
      throw new Error("Please log in first.");
    }
    if (!res.ok) {
      var err = new Error(payload.error || "Something went wrong. Please try again.");
      err.payload = payload;
      err.status = res.status;
      throw err;
    }
    return payload;
  }

  // ---------- Live region announcements ----------
  function announce(message) {
    var el = document.getElementById("sr-announcer");
    if (!el) return;
    el.textContent = "";
    setTimeout(function () { el.textContent = message; }, 60);
  }

  // ---------- Toasts ----------
  var TOAST_ICONS = { success: "check-circle", error: "alert", info: "info" };

  function toast(message, opts) {
    opts = opts || {};
    var type = opts.type || "success";
    var list = document.getElementById("toaster");
    if (!list) return;

    var li = document.createElement("li");
    li.className = "toast toast-" + type;
    li.innerHTML = iconHTML(TOAST_ICONS[type] || "info") + '<p class="toast-message"></p>';
    li.querySelector(".toast-message").textContent = message;

    if (opts.action) {
      var action = document.createElement("button");
      action.type = "button";
      action.className = "btn btn-outline btn-sm";
      action.textContent = opts.action.label;
      action.addEventListener("click", function () {
        dismiss();
        opts.action.onClick();
      });
      li.appendChild(action);
    }
    var close = document.createElement("button");
    close.type = "button";
    close.className = "btn btn-ghost btn-icon btn-sm";
    close.setAttribute("aria-label", "Dismiss notification");
    close.innerHTML = iconHTML("x");
    close.addEventListener("click", dismiss);
    li.appendChild(close);

    list.appendChild(li);
    while (list.children.length > 3) list.firstElementChild.remove();

    // Errors and toasts with actions stay longer; timers pause while hovered or focused (WCAG 2.2.1).
    var duration = opts.duration || (opts.action || type === "error" ? 8000 : 5000);
    var timer = setTimeout(dismiss, duration);
    function pause() { clearTimeout(timer); }
    function resume() { clearTimeout(timer); timer = setTimeout(dismiss, 2500); }
    li.addEventListener("mouseenter", pause);
    li.addEventListener("focusin", pause);
    li.addEventListener("mouseleave", resume);
    li.addEventListener("focusout", function (e) { if (!li.contains(e.relatedTarget)) resume(); });

    function dismiss() {
      clearTimeout(timer);
      if (!li.isConnected) return;
      var hadFocus = li.contains(document.activeElement);
      li.classList.add("toast-leaving");
      setTimeout(function () { li.remove(); }, 160);
      if (hadFocus) document.getElementById("main").focus();
    }
    return { dismiss: dismiss };
  }

  // ---------- Dialogs & sheets (native <dialog>) ----------
  var openers = new WeakMap();

  function openDialog(dialog, opener) {
    if (!dialog || dialog.open) return;
    openers.set(dialog, opener || document.activeElement);
    dialog.showModal();
    document.dispatchEvent(new CustomEvent("dd:dialog-open", { detail: dialog }));
  }

  document.addEventListener("click", function (e) {
    var openBtn = e.target.closest("[data-dialog-open]");
    if (openBtn) {
      openDialog(document.getElementById(openBtn.dataset.dialogOpen), openBtn);
      return;
    }
    var closeBtn = e.target.closest("[data-dialog-close]");
    if (closeBtn) {
      closeBtn.closest("dialog").close();
      return;
    }
    // Clicking the backdrop (the dialog element itself, outside its content) closes it.
    if (e.target instanceof HTMLDialogElement && e.target.open) {
      var rect = e.target.getBoundingClientRect();
      var inside = e.clientX >= rect.left && e.clientX <= rect.right && e.clientY >= rect.top && e.clientY <= rect.bottom;
      if (!inside) e.target.close();
    }
  });

  document.querySelectorAll("dialog").forEach(function (dialog) {
    dialog.addEventListener("close", function () {
      document.dispatchEvent(new CustomEvent("dd:dialog-close", { detail: dialog }));
      var opener = openers.get(dialog);
      if (opener && opener.isConnected && typeof opener.focus === "function") opener.focus();
    });
  });

  // Close the mobile sheet when the viewport grows past the breakpoint.
  window.matchMedia("(min-width: 900px)").addEventListener("change", function (mq) {
    var nav = document.getElementById("mobile-nav");
    if (mq.matches && nav && nav.open) nav.close();
  });

  // ---------- Confirm before destructive form submits ----------
  var pendingForm = null;
  document.addEventListener("submit", function (e) {
    var form = e.target;
    if (!form.matches("[data-confirm]") || form.dataset.confirmed) return;
    e.preventDefault();
    pendingForm = form;
    var dialog = document.getElementById("confirm-dialog");
    document.getElementById("confirm-title").textContent = form.dataset.confirmTitle || "Are you sure?";
    document.getElementById("confirm-message").textContent = form.dataset.confirm;
    document.getElementById("confirm-ok").textContent = form.dataset.confirmLabel || "Confirm";
    openDialog(dialog, e.submitter || document.activeElement);
  });
  var confirmOk = document.getElementById("confirm-ok");
  if (confirmOk) {
    confirmOk.addEventListener("click", function () {
      if (!pendingForm) return;
      pendingForm.dataset.confirmed = "1";
      document.getElementById("confirm-dialog").close();
      pendingForm.submit();
    });
  }

  // ---------- Dropdown menu (WAI-ARIA menu button pattern) ----------
  document.querySelectorAll("[data-dropdown]").forEach(function (wrap) {
    var button = wrap.querySelector('[aria-haspopup="menu"]');
    var menu = wrap.querySelector('[role="menu"]');
    var items = function () { return Array.from(menu.querySelectorAll('[role="menuitem"]')); };

    function open(focusIndex) {
      menu.hidden = false;
      button.setAttribute("aria-expanded", "true");
      var list = items();
      var i = focusIndex < 0 ? list.length - 1 : focusIndex;
      if (list[i]) list[i].focus();
    }
    function close(returnFocus) {
      menu.hidden = true;
      button.setAttribute("aria-expanded", "false");
      if (returnFocus) button.focus();
    }

    button.addEventListener("click", function () { menu.hidden ? open(0) : close(false); });
    button.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ") { e.preventDefault(); open(0); }
      if (e.key === "ArrowUp") { e.preventDefault(); open(-1); }
    });
    menu.addEventListener("keydown", function (e) {
      var list = items();
      var i = list.indexOf(document.activeElement);
      if (e.key === "ArrowDown") { e.preventDefault(); list[(i + 1) % list.length].focus(); }
      else if (e.key === "ArrowUp") { e.preventDefault(); list[(i - 1 + list.length) % list.length].focus(); }
      else if (e.key === "Home") { e.preventDefault(); list[0].focus(); }
      else if (e.key === "End") { e.preventDefault(); list[list.length - 1].focus(); }
      else if (e.key === "Escape") { e.preventDefault(); close(true); }
      else if (e.key === "Tab") { close(false); }
    });
    document.addEventListener("click", function (e) { if (!wrap.contains(e.target) && !menu.hidden) close(false); });
  });

  // ---------- Tabs (WAI-ARIA tabs pattern, automatic activation) ----------
  document.querySelectorAll('[role="tablist"]').forEach(function (list) {
    var tabs = Array.from(list.querySelectorAll('[role="tab"]'));
    function select(tab, focus) {
      tabs.forEach(function (t) {
        var selected = t === tab;
        t.setAttribute("aria-selected", String(selected));
        t.tabIndex = selected ? 0 : -1;
        var panel = document.getElementById(t.getAttribute("aria-controls"));
        if (panel) panel.hidden = !selected;
      });
      if (focus) tab.focus();
      if (list.dataset.syncParam) {
        var url = new URL(window.location);
        url.searchParams.set(list.dataset.syncParam, tab.dataset.value);
        history.replaceState(null, "", url);
      }
    }
    tabs.forEach(function (tab, i) {
      tab.addEventListener("click", function (e) {
        // Keep in-page tab switching when JS works; real links still work without JS.
        if (tab.tagName === "A") e.preventDefault();
        select(tab, false);
      });
      tab.addEventListener("keydown", function (e) {
        var next = null;
        if (e.key === "ArrowRight") next = tabs[(i + 1) % tabs.length];
        else if (e.key === "ArrowLeft") next = tabs[(i - 1 + tabs.length) % tabs.length];
        else if (e.key === "Home") next = tabs[0];
        else if (e.key === "End") next = tabs[tabs.length - 1];
        if (next) { e.preventDefault(); select(next, true); }
      });
    });
  });

  // ---------- Tooltips: Escape dismisses (WCAG 1.4.13) ----------
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    document.querySelectorAll("[data-tooltip]:hover, [data-tooltip]:focus-visible").forEach(function (el) {
      el.classList.add("tooltip-dismissed");
    });
  });
  ["mouseleave", "blur"].forEach(function (type) {
    document.addEventListener(type, function (e) {
      if (e.target instanceof Element && e.target.matches("[data-tooltip]")) e.target.classList.remove("tooltip-dismissed");
    }, true);
  });

  // ---------- Theme toggle ----------
  var themeBtn = document.getElementById("theme-toggle");
  if (themeBtn && window.DDTheme) {
    window.DDTheme.sync();
    themeBtn.addEventListener("click", function () {
      var theme = window.DDTheme.toggle();
      announce((theme === "dark" ? "Dark" : "Light") + " theme on");
    });
  }

  // ---------- "/" focuses the search box ----------
  document.addEventListener("keydown", function (e) {
    if (e.key !== "/" || e.ctrlKey || e.metaKey || e.altKey) return;
    var t = e.target;
    if (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)) return;
    var search = document.querySelector("[data-search-shortcut]");
    if (search) { e.preventDefault(); search.focus(); search.select(); }
  });

  // ---------- Auto-submit selects (with a visible button fallback when JS is off) ----------
  document.addEventListener("change", function (e) {
    if (e.target.matches("[data-autosubmit]")) e.target.form.requestSubmit();
  });

  // ---------- Star rating inputs: show the chosen value next to the stars ----------
  document.querySelectorAll("[data-star-input]").forEach(function (group) {
    var out = group.parentElement.querySelector("[data-star-value]");
    group.addEventListener("change", function (e) {
      if (out) out.textContent = e.target.value + " of 5";
    });
  });

  // ---------- Character counters ----------
  document.querySelectorAll("[data-char-count]").forEach(function (field) {
    var out = document.getElementById(field.dataset.charCount);
    var max = Number(field.getAttribute("maxlength")) || 0;
    function update() { out.textContent = field.value.length + (max ? " / " + max : "") + " characters"; }
    field.addEventListener("input", update);
    update();
  });

  // ---------- Move focus to error summaries so problems are announced first ----------
  var summary = document.querySelector(".error-summary");
  if (summary) summary.focus();

  // ---------- Server flash messages become toasts (announced via the live region) ----------
  var flashData = document.getElementById("flash-data");
  if (flashData) {
    var messages = [];
    try { messages = JSON.parse(flashData.textContent); } catch (e) {}
    setTimeout(function () {
      messages.forEach(function (m) { toast(m[1], { type: m[0] === "message" ? "info" : m[0] }); });
    }, 250);
  }

  window.DD = { api: api, toast: toast, announce: announce, openDialog: openDialog, iconHTML: iconHTML, csrf: csrf };
})();
