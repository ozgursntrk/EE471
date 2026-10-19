const display = document.getElementById("display");
let firstNumber = null;  // ilk sayı, ör. "8"
let operation = null;    // işlem adı, ör. "divide"
let opSymbol = "";       // ekranda görünecek işaret, ör. "÷"
let current = "0";       // şu an yazılan sayı
let startNew = true;     // bir sonraki rakam yeni sayı mı başlatacak?

// Ekranı güncelleyen fonksiyon
function render() {
  if (operation === null) {
    display.textContent = current;
  } else {
    display.textContent = `${firstNumber} ${opSymbol} ${startNew ? "" : current}`;
  }
}

// Rakam ve nokta butonları
document.querySelectorAll(".digit").forEach(btn => {
  btn.addEventListener("click", () => {
    const char = btn.textContent;
    if (startNew) {
      current = char === "." ? "0." : char;
      startNew = false;
    } else {
      if (char === "." && current.includes(".")) return;
      current += char;
    }
    render();
  });
});

// İşlem butonları (+ − × ÷)
document.querySelectorAll(".op").forEach(btn => {
  btn.addEventListener("click", () => {
    if (operation === null || !startNew) {
      firstNumber = current;
    }
    operation = btn.dataset.op;
    opSymbol = btn.textContent;
    startNew = true;
    render();
  });
});

// Eşittir: hesabı Flask'a gönder
document.getElementById("equals").addEventListener("click", async () => {
  if (operation === null || startNew) return;  // ikinci sayı yoksa bekle

  const response = await fetch("/api/calculate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      a: Number(firstNumber),
      b: Number(current),
      operation: operation
    })
  });
  const data = await response.json();

  operation = null;
  startNew = true;
  if (response.ok) {
    current = String(data.result);
    render();
  } else {
    current = "0";
    display.textContent = data.error;  // ör. "Division by zero"
  }
});

// Ekrana tıklayınca sıfırla
display.addEventListener("click", () => {
  firstNumber = null;
  operation = null;
  opSymbol = "";
  current = "0";
  startNew = true;
  render();
});