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