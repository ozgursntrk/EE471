// ---------- Durum (state) ----------
let filterType = "all";     // "all", "book" veya "dvd"
let availableOnly = false;  // "Available Only" kutusu
let editingId = null;       // null = yeni ekleme, sayı = o id'yi düzenleme

// ---------- Sayfadaki elemanlar ----------
const listEl = document.getElementById("item-list");
const emptyEl = document.getElementById("empty");
const errorEl = document.getElementById("error");
const infoEl = document.getElementById("info");
const modal = document.getElementById("modal");
const form = document.getElementById("item-form");
const formError = document.getElementById("form-error");
const formTitle = document.getElementById("form-title");
const fTitle = document.getElementById("f-title");
const fAuthor = document.getElementById("f-author");
const fType = document.getElementById("f-type");
const fNumber = document.getElementById("f-number");
const fNumberLabel = document.getElementById("f-number-label");

// ---------- API ile konuşan tek yardımcı ----------
async function api(method, url, body) {
  const options = { method, headers: {} };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const response = await fetch(url, options);
  if (response.status === 204) return null;            // DELETE: gövde boş
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong");
  return data;
}

function showError(el, message) {
  el.textContent = message;
  el.classList.remove("hidden");
}

function clearError(el) {
  el.textContent = "";
  el.classList.add("hidden");
}

// Kullanıcının yazdığı metni HTML'e güvenli koymak için
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// ---------- Listeyi yükle ve çiz ----------
async function loadItems() {
  clearError(errorEl);
  clearError(infoEl);
  const params = new URLSearchParams();
  if (availableOnly) params.set("available", "true");
  if (filterType !== "all") params.set("type", filterType);
  const query = params.toString();
  try {
    const items = await api("GET", "/api/items" + (query ? "?" + query : ""));
    render(items);
  } catch (err) {
    showError(errorEl, err.message);
  }
}

function render(items) {
  listEl.innerHTML = "";
  emptyEl.classList.toggle("hidden", items.length > 0);

  for (const item of items) {
    const detail = item.type === "book"
      ? `📖 ${item.page_count} pages`
      : `⏱ ${item.duration} mins`;
    const card = document.createElement("div");
    card.className = "card" + (item.is_available ? "" : " out");
    card.innerHTML = `
      <h3>${escapeHtml(item.title)}</h3>
      <p class="author">${escapeHtml(item.author)}</p>
      <span class="badge">${item.type === "book" ? "Book" : "DVD"}</span>
      <div class="meta">
        <span>${detail}</span>
        <span class="status ${item.is_available ? "available" : "checked-out"}">
          ${item.is_available ? "Available" : "Checked out"}
        </span>
      </div>
      <div class="actions">
        <button class="primary" data-action="${item.is_available ? "checkout" : "return"}">
          ${item.is_available ? "Checkout" : "Return"}
        </button>
        <button class="icon" data-action="edit" title="Edit">✏️</button>
        <button class="icon danger" data-action="delete" title="Delete">🗑️</button>
      </div>`;
    card.querySelectorAll("button").forEach(btn =>
      btn.addEventListener("click", () => handleAction(btn.dataset.action, item))
    );
    listEl.appendChild(card);
  }
}

// ---------- Kart butonları ----------
async function handleAction(action, item) {
  clearError(errorEl);
  clearError(infoEl);
  if (action === "edit") {
    openForm(item);
    return;
  }
  try {
    if (action === "checkout") {
      const result = await api("POST", `/api/items/${item.id}/checkout`);
      await loadItems();
      showError(infoEl, result.message);  // ör. DVD: "Handle with care..."
      return;
    }
    if (action === "return") await api("POST", `/api/items/${item.id}/return`);
    if (action === "delete") await api("DELETE", `/api/items/${item.id}`);
    await loadItems();
  } catch (err) {
    showError(errorEl, err.message);  // ör. 409: "Cannot delete a checked-out item"
  }
}

// ---------- Ekle / Düzenle formu ----------
function updateNumberLabel() {
  fNumberLabel.textContent = fType.value === "book" ? "Page Count" : "Duration (min)";
}

function openForm(item = null) {
  clearError(formError);
  editingId = item ? item.id : null;
  formTitle.textContent = item ? "Edit Item" : "Add New Item";
  fTitle.value = item ? item.title : "";
  fAuthor.value = item ? item.author : "";
  fType.value = item ? item.type : "book";
  fType.disabled = item !== null;  // tür değiştirilemez (API kuralı)
  fNumber.value = item ? (item.type === "book" ? item.page_count : item.duration) : "";
  updateNumberLabel();
  modal.classList.remove("hidden");
}

function closeForm() {
  modal.classList.add("hidden");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();  // sayfanın yenilenmesini engelle
  clearError(formError);
  const numberField = fType.value === "book" ? "page_count" : "duration";
  const body = {
    title: fTitle.value,
    author: fAuthor.value,
    [numberField]: fNumber.value === "" ? null : Number(fNumber.value),
  };
  try {
    if (editingId === null) {
      await api("POST", "/api/items", { type: fType.value, ...body });
    } else {
      await api("PUT", `/api/items/${editingId}`, body);
    }
    closeForm();
    await loadItems();
  } catch (err) {
    showError(formError, err.message);  // ör. "'title' must be non-empty text"
  }
});

// ---------- Filtreler ve butonlar ----------
fType.addEventListener("change", updateNumberLabel);
document.getElementById("add-btn").addEventListener("click", () => {
  clearError(errorEl);
  clearError(infoEl);
  openForm();
});
document.getElementById("cancel-btn").addEventListener("click", closeForm);

document.getElementById("available-only").addEventListener("change", (e) => {
  availableOnly = e.target.checked;
  loadItems();
});

document.querySelectorAll(".filter-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    filterType = btn.dataset.type;
    loadItems();
  });
});

// Sayfa açılınca listeyi getir
loadItems();


// =====================================================================
// Voice librarian
// 1) speech or text  -> /api/voice/command -> which request to send
// 2) send that request to the normal REST endpoint (e.g. POST /api/items/3/checkout)
// 3) status + JSON   -> /api/voice/reply   -> the sentence to say
// 4) sentence        -> /api/voice/speak   -> audio, played in the browser
// =====================================================================
const micBtn = document.getElementById("mic-btn");
const textForm = document.getElementById("text-form");
const textInput = document.getElementById("text-input");
const voiceStatus = document.getElementById("voice-status");
const voiceLog = document.getElementById("voice-log");

let mediaRecorder = null;
let chunks = [];

micBtn.addEventListener("click", async () => {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();  // second click: stop listening
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    chunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((track) => track.stop());  // turn the microphone off
      micBtn.classList.remove("listening");
      const form = new FormData();
      form.append("audio", await toWav16k(new Blob(chunks, { type: mediaRecorder.mimeType })), "command.wav");
      runVoiceCommand({ method: "POST", body: form });
    };
    mediaRecorder.start();
    micBtn.classList.add("listening");
    voiceStatus.textContent = "Listening... say your command, then click the microphone again.";
  } catch (err) {
    voiceStatus.textContent = "Microphone access was denied.";
  }
});

textForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = textInput.value.trim();
  if (!text) return;
  runVoiceCommand({
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
});

async function runVoiceCommand(options) {
  setBusy(true, "Understanding the command...");
  try {
    // 1) What did the user say, and which endpoint does it mean?
    const response = await fetch("/api/voice/command", options);
    const parsed = await response.json();
    if (!response.ok) {
      showVoiceLog(parsed.heard ?? "", "-", "", null, parsed.reply || parsed.error);
      if (parsed.reply) await speak(parsed.reply);
      return;
    }
    const command = parsed.command;

    // 2) Call the real REST endpoint
    voiceStatus.textContent = `Calling ${command.method} ${command.path} ...`;
    const request = { method: command.method, headers: {} };
    if (command.body !== null) {
      request.headers["Content-Type"] = "application/json";
      request.body = JSON.stringify(command.body);
    }
    const apiResponse = await fetch(command.path, request);
    const apiData = apiResponse.status === 204 ? null : await apiResponse.json();

    // 3) Ask the server for the librarian's sentence
    const replyResponse = await fetch("/api/voice/reply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command, status: apiResponse.status, data: apiData }),
    });
    const { reply } = await replyResponse.json();

    const requestText = `${command.method} ${command.path}` +
      (command.body ? " " + JSON.stringify(command.body) : "");
    showVoiceLog(parsed.heard, requestText, apiResponse.status, apiData, reply);
    await loadItems();

    // 4) Say it out loud
    await speak(reply);
  } catch (err) {
    voiceStatus.textContent = "Error: " + err.message;
  } finally {
    setBusy(false);
  }
}

function setBusy(busy, message) {
  micBtn.disabled = busy;
  if (message) voiceStatus.textContent = message;
  if (!busy && voiceStatus.textContent.startsWith("Speaking")) {
    voiceStatus.textContent = "Ready for the next command.";
  }
}

function showVoiceLog(heard, requestText, status, data, reply) {
  document.getElementById("v-heard").textContent = heard ? `"${heard}"` : "(nothing)";
  document.getElementById("v-request").textContent = requestText;
  document.getElementById("v-status").textContent = status === "" ? "-" : status;
  document.getElementById("v-response").textContent =
    status === 204 ? "(204 No Content)" : data === null ? "" : JSON.stringify(data, null, 2);
  document.getElementById("v-reply").textContent = reply;
  voiceLog.classList.remove("hidden");
}

async function speak(text) {
  voiceStatus.textContent = "Speaking...";
  const response = await fetch("/api/voice/speak", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.error);
  }
  const url = URL.createObjectURL(await response.blob());
  const audio = new Audio(url);
  await new Promise((resolve) => {
    audio.onended = audio.onerror = resolve;
    audio.play().catch(resolve);
  });
  URL.revokeObjectURL(url);
}

// ---------- Convert any audio to 16 kHz mono WAV (the format Azure expects) ----------
async function toWav16k(blob) {
  const context = new AudioContext();
  const decoded = await context.decodeAudioData(await blob.arrayBuffer());
  context.close();

  const offline = new OfflineAudioContext(1, Math.ceil(decoded.duration * 16000), 16000);
  const source = offline.createBufferSource();
  source.buffer = decoded;
  source.connect(offline.destination);
  source.start();
  const rendered = await offline.startRendering();
  return encodeWav(rendered.getChannelData(0), 16000);
}

function encodeWav(samples, sampleRate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const writeText = (offset, text) => {
    for (let i = 0; i < text.length; i++) view.setUint8(offset + i, text.charCodeAt(i));
  };

  // 44-byte WAV header
  writeText(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeText(8, "WAVE");
  writeText(12, "fmt ");
  view.setUint32(16, 16, true);              // header chunk size
  view.setUint16(20, 1, true);               // format: PCM
  view.setUint16(22, 1, true);               // channels: 1
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);  // bytes per second
  view.setUint16(32, 2, true);               // bytes per sample
  view.setUint16(34, 16, true);              // bits per sample
  writeText(36, "data");
  view.setUint32(40, samples.length * 2, true);

  // Samples: float (-1..1) -> 16-bit integer
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return new Blob([view], { type: "audio/wav" });
}