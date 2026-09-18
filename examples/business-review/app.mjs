import { appendReview, exportReviews } from "./review-state.mjs";
const $ = (id) => document.getElementById(id);
let cases = [],
  selected = null,
  history = [];
const key = "alder-synthetic-review-v1";
function status(message) {
  $("status").textContent = message;
}
function renderHistory() {
  $("history").replaceChildren(
    ...history.map((row) => {
      const li = document.createElement("li");
      li.textContent = `${row.revision}. ${row.case_id}: ${row.decision} — ${row.evidence}`;
      return li;
    }),
  );
}
function queue() {
  const query = $("search").value.toLowerCase();
  const matches = cases.filter((item) =>
    (item.title + " " + item.kind).toLowerCase().includes(query),
  );
  $("queue").replaceChildren(
    ...matches.map((item) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = item.title;
      button.setAttribute("aria-current", String(selected?.id === item.id));
      button.addEventListener("click", () => select(item));
      return button;
    }),
  );
  if (!matches.length) {
    const p = document.createElement("p");
    p.textContent = "No matching cases.";
    $("queue").append(p);
  }
}
function select(item) {
  selected = item;
  $("case-title").textContent = item.title;
  $("prompt").textContent = item.prompt;
  $("findings").textContent = JSON.stringify(item.result, null, 2);
  $("links").replaceChildren(
    ...Object.entries(item.evidence).map(([label, url]) => {
      const a = document.createElement("a");
      a.textContent = label;
      a.href = url;
      return a;
    }),
  );
  $("previews").replaceChildren(
    ...item.previews.map((url, index) => {
      const figure = document.createElement("figure");
      const img = document.createElement("img");
      img.src = url;
      img.alt = `${item.title}, rendered artifact ${index + 1}`;
      const caption = document.createElement("figcaption");
      caption.textContent = url;
      figure.append(img, caption);
      return figure;
    }),
  );
  $("review").reset();
  queue();
  status("Review the source and artifacts before saving a judgment.");
  $("case-title").focus();
}
$("search").addEventListener("input", queue);
$("review").addEventListener("submit", (event) => {
  event.preventDefault();
  try {
    const next = appendReview(
      history,
      {
        case_id: selected?.id,
        decision: $("decision").value,
        evidence: $("evidence").value,
      },
      cases.map((item) => item.id),
      new Date().toISOString(),
    );
    localStorage.setItem(key, JSON.stringify(next));
    history = next;
    renderHistory();
    status("Review revision saved locally.");
    $("evidence").focus();
  } catch (error) {
    status(error.message);
  }
});
$("export").addEventListener("click", () => {
  const url =
    "data:application/json;charset=utf-8," +
    encodeURIComponent(JSON.stringify(exportReviews(history), null, 2));
  const link = document.createElement("a");
  link.href = url;
  link.download = "alder-review-history.json";
  document.body.append(link);
  link.click();
  link.remove();
});
try {
  const saved = JSON.parse(localStorage.getItem(key) || "[]");
  if (Array.isArray(saved)) history = saved;
} catch {
  status("Stored review history could not be loaded.");
}
renderHistory();
try {
  const response = await fetch("review-data.json");
  if (!response.ok) throw new Error("Case file could not be loaded.");
  cases = (await response.json()).cases;
  queue();
  select(cases[0]);
} catch (error) {
  status(error.message);
  $("review")
    .querySelectorAll("input,select,textarea,button")
    .forEach((control) => (control.disabled = true));
}
