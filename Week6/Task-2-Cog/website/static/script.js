const fileInput = document.getElementById("file");
const drop = document.getElementById("drop");
const preview = document.getElementById("preview");
const hint = document.getElementById("hint");
const button = document.getElementById("classify");
const statusText = document.getElementById("status");
const result = document.getElementById("result");

let selectedFile = null;

// Show the chosen image as a preview
function useFile(file) {
  if (!file) return;
  selectedFile = file;
  preview.src = URL.createObjectURL(file);
  preview.hidden = false;
  hint.hidden = true;
  result.hidden = true;
  statusText.textContent = file.name;
  button.disabled = false;
}

fileInput.addEventListener("change", () => useFile(fileInput.files[0]));

// Drag & drop support
drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
drop.addEventListener("dragleave", () => drop.classList.remove("over"));
drop.addEventListener("drop", (e) => {
  e.preventDefault();
  drop.classList.remove("over");
  useFile(e.dataTransfer.files[0]);
});

// Send the image to our Flask server, which forwards it to the Cog model
button.addEventListener("click", async () => {
  const form = new FormData();
  form.append("image", selectedFile);

  button.disabled = true;
  statusText.textContent = "Classifying…";
  result.hidden = true;

  try {
    const response = await fetch("/api/classify", { method: "POST", body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Something went wrong.");
    showResult(data);
    statusText.textContent = "";
  } catch (error) {
    statusText.textContent = "⚠️ " + error.message;
  } finally {
    button.disabled = false;
  }
});

function showResult(data) {
  const percent = (x) => (x * 100).toFixed(1) + "%";

  document.getElementById("prediction").textContent = data.is_cat
    ? `${data.prediction} (${percent(data.confidence)})`
    : "This does not look like a cat 🤔";

  document.getElementById("summary").textContent =
    `Cat probability: ${percent(data.cat_probability)} · ` +
    `Model's top ImageNet label: "${data.top_imagenet_label}"`;

  const bars = document.getElementById("bars");
  bars.innerHTML = "";
  // highest probability first
  const kinds = Object.entries(data.all_kinds).sort((a, b) => b[1] - a[1]);
  for (const [kind, p] of kinds) {
    const row = document.createElement("div");
    row.className = "bar-row";
    row.innerHTML = `
      <span class="bar-label">${kind}</span>
      <span class="bar"><span class="fill" style="width:${p * 100}%"></span></span>
      <span class="bar-value">${percent(p)}</span>`;
    bars.appendChild(row);
  }
  result.hidden = false;
}