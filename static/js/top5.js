// Reorder "My Top 5" with arrow buttons or drag-and-drop; every change autosaves.
(function () {
  "use strict";

  var list = document.getElementById("top5-list");
  if (!list) return;
  var status = document.getElementById("save-status");
  var url = list.dataset.orderUrl;

  function items() { return Array.from(list.querySelectorAll(".top5-item")); }
  function order() { return items().map(function (li) { return Number(li.dataset.id); }); }

  function renumber() {
    var all = items();
    all.forEach(function (li, i) {
      li.querySelector(".rank").textContent = i + 1;
      li.querySelector("[data-rank-label]").textContent = "Rank " + (i + 1) + ": ";
      li.querySelector('[data-move="up"]').disabled = i === 0;
      li.querySelector('[data-move="down"]').disabled = i === all.length - 1;
    });
  }

  function setStatus(text, kind) {
    status.className = "save-status" + (kind ? " " + kind : "");
    status.innerHTML = (kind === "ok" ? DD.iconHTML("check-circle") : kind === "err" ? DD.iconHTML("alert") : "") + "<span></span>";
    status.querySelector("span").textContent = text;
  }

  var lastSaved = order();
  var saveTimer = null;

  async function save() {
    var current = order();
    if (current.join() === lastSaved.join()) return;
    setStatus("Saving…");
    try {
      await DD.api(url, { json: { order: current } });
      lastSaved = current;
      setStatus("Saved", "ok");
      clearTimeout(saveTimer);
      saveTimer = setTimeout(function () { setStatus(""); }, 4000);
    } catch (err) {
      setStatus("Couldn't save. Your last saved order was restored.", "err");
      DD.toast(err.message, { type: "error" });
      restore(lastSaved);
    }
  }

  function restore(ids) {
    var byId = {};
    items().forEach(function (li) { byId[li.dataset.id] = li; });
    ids.forEach(function (id) { if (byId[id]) list.appendChild(byId[id]); });
    renumber();
  }

  // Arrow buttons: progressive enhancement over the no-JS form posts.
  list.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-move]");
    if (!btn) return;
    e.preventDefault();
    var li = btn.closest(".top5-item");
    var direction = btn.dataset.move;
    if (direction === "up" && li.previousElementSibling) list.insertBefore(li, li.previousElementSibling);
    else if (direction === "down" && li.nextElementSibling) list.insertBefore(li.nextElementSibling, li);
    else return;
    renumber();
    var rank = items().indexOf(li) + 1;
    DD.announce("Moved " + li.dataset.name + " to rank " + rank + " of " + items().length);
    // Keep focus on the same control; if it's now disabled (top/bottom), use the other arrow.
    var focusTarget = btn.disabled ? li.querySelector('[data-move="' + (direction === "up" ? "down" : "up") + '"]') : btn;
    if (focusTarget && !focusTarget.disabled) focusTarget.focus();
    save();
  });

  // Drag and drop by the grip handle (mouse users); buttons remain the accessible path.
  var dragged = null;
  list.addEventListener("dragstart", function (e) {
    var handle = e.target.closest(".drag-handle");
    if (!handle) { e.preventDefault(); return; }
    dragged = handle.closest(".top5-item");
    dragged.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", dragged.dataset.id);
    e.dataTransfer.setDragImage(dragged, 24, 24);
  });
  list.addEventListener("dragover", function (e) {
    if (!dragged) return;
    e.preventDefault();
    var target = e.target.closest(".top5-item");
    items().forEach(function (li) { li.classList.toggle("drop-target", li === target && li !== dragged); });
    if (!target || target === dragged) return;
    var rect = target.getBoundingClientRect();
    var after = e.clientY > rect.top + rect.height / 2;
    list.insertBefore(dragged, after ? target.nextElementSibling : target);
  });
  list.addEventListener("drop", function (e) { e.preventDefault(); });
  list.addEventListener("dragend", function () {
    if (!dragged) return;
    dragged.classList.remove("dragging");
    items().forEach(function (li) { li.classList.remove("drop-target"); });
    renumber();
    DD.announce("Moved " + dragged.dataset.name + " to rank " + (items().indexOf(dragged) + 1));
    dragged = null;
    save();
  });
})();
