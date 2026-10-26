const textInput = document.getElementById("text");
const voiceSelect = document.getElementById("voice");
const synthBtn = document.getElementById("synth-btn");
const clearBtn = document.getElementById("clear-btn");
const statusBox = document.getElementById("status");
const resultBox = document.getElementById("result");
const player = document.getElementById("player");
const downloadLink = document.getElementById("download");

let audioUrl = null;  // the last generated audio (kept in browser memory)

function showStatus(message, type) {
  statusBox.textContent = message;
  statusBox.className = `status ${type}`;
}

synthBtn.addEventListener("click", async () => {
  const text = textInput.value.trim();
  if (!text) {
    showStatus("Please enter some text.", "error");
    return;
  }

  synthBtn.disabled = true;
  showStatus("Synthesizing...", "loading");

  try {
    const response = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text, voice: voiceSelect.value }),
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error);
    }

    const blob = await response.blob();          // WAV bytes from Flask
    if (audioUrl) URL.revokeObjectURL(audioUrl); // free the old audio
    audioUrl = URL.createObjectURL(blob);

    player.src = audioUrl;
    downloadLink.href = audioUrl;
    resultBox.classList.remove("hidden");
    showStatus("✓ Speech synthesized successfully!", "success");
    player.play();
  } catch (err) {
    showStatus(err.message, "error");
  } finally {
    synthBtn.disabled = false;
  }
});

clearBtn.addEventListener("click", () => {
  textInput.value = "";
  statusBox.className = "status hidden";
  resultBox.classList.add("hidden");
  player.removeAttribute("src");
});