const fileInput = document.getElementById("file");
const drop = document.getElementById("drop");
const preview = document.getElementById("preview");
const hint = document.getElementById("hint");
const button = document.getElementById("classify");
const statusText = document.getElementById("status");

let selectedFile = null;

// Show the chosen image as a preview
function useFile(file) {
  if (!file) return;
  selectedFile = file;
  preview.src = URL.createObjectURL(file);
  preview.hidden = false;
  hint.hidden = true;
  statusText.textContent = file.name;
  button.disabled = false;
  document.querySelectorAll(".result").forEach((el) => (el.innerHTML = ""));
}

fileInput.addEventListener("change", () => useFile(fileInput.files[0]));
drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
drop.addEventListener("dragleave", () => drop.classList.remove("over"));
drop.addEventListener("drop", (e) => {
  e.preventDefault();
  drop.classList.remove("over");
  useFile(e.dataTransfer.files[0]);
});

// Send the image to Flask, which asks both Cog models
button.addEventListener("click", async () => {
  const form = new FormData();
  form.append("image", selectedFile);
  button.disabled = true;
  statusText.textContent = "Classifying…";

  try {
    const response = await fetch("/api/classify", { method: "POST", body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Something went wrong.");
    showResult("baseline", data.baseline);
    showResult("optimized", data.optimized);
    if (data.baseline.error || data.optimized.error) {
      statusText.textContent = "⚠️ A model returned an error.";
    } else {
      statusText.textContent = data.baseline.prediction === data.optimized.prediction
        ? "Both models agree."
        : "The models disagree!";
    }
  } catch (error) {
    statusText.textContent = "⚠️ " + error.message;
  } finally {
    button.disabled = false;
  }
});

function showResult(name, data) {
  const box = document.querySelector(`#${name} .result`);
  if (data.error) {
    box.innerHTML = `<p class="error">${data.error}</p>`;
    return;
  }
  const percent = (x) => (x * 100).toFixed(1) + "%";
  const bars = data.top3.map((item) => `
    <div class="bar-row">
      <span class="bar-label">${item.label}</span>
      <span class="bar"><span class="fill" style="width:${item.probability * 100}%"></span></span>
      <span class="bar-value">${percent(item.probability)}</span>
    </div>`).join("");
  box.innerHTML = `
    <p class="prediction">${data.prediction}</p>
    <p class="confidence">${percent(data.confidence)} confident</p>
    ${bars}
    <p class="accuracy">Test accuracy: <b>${percent(data.test_accuracy)}</b></p>`;
}