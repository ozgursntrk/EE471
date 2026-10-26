// ================= Shared helpers =================
function showStatus(box, message, type) {
  box.textContent = message;
  box.className = `status ${type}`;
}

function hideStatus(box) {
  box.className = "status hidden";
}

// ================= Tabs =================
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.add("hidden"));
    tab.classList.add("active");
    document.getElementById(tab.dataset.tab).classList.remove("hidden");
  });
});

// ================= Text to Speech =================
const ttsText = document.getElementById("tts-text");
const ttsVoice = document.getElementById("tts-voice");
const ttsSynthBtn = document.getElementById("tts-synth-btn");
const ttsClearBtn = document.getElementById("tts-clear-btn");
const ttsStatus = document.getElementById("tts-status");
const ttsResult = document.getElementById("tts-result");
const ttsPlayer = document.getElementById("tts-player");
const ttsDownload = document.getElementById("tts-download");

let ttsAudioUrl = null;  // the last generated audio (kept in browser memory)

ttsSynthBtn.addEventListener("click", async () => {
  const text = ttsText.value.trim();
  if (!text) {
    showStatus(ttsStatus, "Please enter some text.", "error");
    return;
  }

  ttsSynthBtn.disabled = true;
  showStatus(ttsStatus, "Synthesizing...", "loading");

  try {
    const response = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text, voice: ttsVoice.value }),
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error);
    }

    const blob = await response.blob();               // WAV bytes from Flask
    if (ttsAudioUrl) URL.revokeObjectURL(ttsAudioUrl); // free the old audio
    ttsAudioUrl = URL.createObjectURL(blob);

    ttsPlayer.src = ttsAudioUrl;
    ttsDownload.href = ttsAudioUrl;
    ttsResult.classList.remove("hidden");
    showStatus(ttsStatus, "✓ Speech synthesized successfully!", "success");
    ttsPlayer.play();
  } catch (err) {
    showStatus(ttsStatus, err.message, "error");
  } finally {
    ttsSynthBtn.disabled = false;
  }
});

ttsClearBtn.addEventListener("click", () => {
  ttsText.value = "";
  hideStatus(ttsStatus);
  ttsResult.classList.add("hidden");
  ttsPlayer.removeAttribute("src");
});

// ================= Speech to Text =================
const sttRecordBtn = document.getElementById("stt-record-btn");
const sttStopBtn = document.getElementById("stt-stop-btn");
const sttFile = document.getElementById("stt-file");
const sttLanguage = document.getElementById("stt-language");
const sttPreview = document.getElementById("stt-preview");
const sttTranscribeBtn = document.getElementById("stt-transcribe-btn");
const sttClearBtn = document.getElementById("stt-clear-btn");
const sttStatus = document.getElementById("stt-status");
const sttResult = document.getElementById("stt-result");
const sttTranscript = document.getElementById("stt-transcript");
const sttCopyBtn = document.getElementById("stt-copy-btn");

let mediaRecorder = null;
let chunks = [];
let sttAudioBlob = null;  // the audio to transcribe (recorded or uploaded)

function setSttAudio(blob) {
  sttAudioBlob = blob;
  sttPreview.src = URL.createObjectURL(blob);
  sttPreview.classList.remove("hidden");
  sttTranscribeBtn.disabled = false;
}

// ---------- Recording from the microphone ----------
sttRecordBtn.addEventListener("click", async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    chunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
    mediaRecorder.onstop = () => {
      stream.getTracks().forEach((track) => track.stop());  // turn the microphone off
      setSttAudio(new Blob(chunks, { type: mediaRecorder.mimeType }));
      showStatus(sttStatus, "Recording finished. Click 'Transcribe Audio'.", "success");
    };
    mediaRecorder.start();
    sttRecordBtn.disabled = true;
    sttStopBtn.disabled = false;
    sttFile.value = "";
    showStatus(sttStatus, "● Recording...", "recording");
  } catch (err) {
    showStatus(sttStatus, "Microphone access was denied.", "error");
  }
});

sttStopBtn.addEventListener("click", () => {
  mediaRecorder.stop();
  sttRecordBtn.disabled = false;
  sttStopBtn.disabled = true;
});

// ---------- Uploading a file ----------
sttFile.addEventListener("change", () => {
  if (sttFile.files.length > 0) {
    setSttAudio(sttFile.files[0]);
    showStatus(sttStatus, `File selected: ${sttFile.files[0].name}`, "success");
  }
});

// ---------- Convert any audio to 16 kHz mono WAV (the format Azure expects) ----------
async function toWav16k(blob) {
  const context = new AudioContext();
  const decoded = await context.decodeAudioData(await blob.arrayBuffer());
  context.close();

  // Re-render the audio at 16 kHz with 1 channel (mono)
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

// ---------- Sending the audio to Flask ----------
sttTranscribeBtn.addEventListener("click", async () => {
  if (!sttAudioBlob) return;
  sttTranscribeBtn.disabled = true;
  showStatus(sttStatus, "Transcribing...", "loading");

  try {
    const wav = await toWav16k(sttAudioBlob);
    const form = new FormData();
    form.append("audio", wav, "audio.wav");
    form.append("language", sttLanguage.value);

    const response = await fetch("/api/stt", { method: "POST", body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);

    sttTranscript.textContent = data.text;
    sttResult.classList.remove("hidden");
    showStatus(sttStatus, "✓ Audio transcribed successfully!", "success");
  } catch (err) {
    showStatus(sttStatus, err.message, "error");
  } finally {
    sttTranscribeBtn.disabled = false;
  }
});

sttCopyBtn.addEventListener("click", async () => {
  await navigator.clipboard.writeText(sttTranscript.textContent);
  showStatus(sttStatus, "Text copied to clipboard.", "success");
});

sttClearBtn.addEventListener("click", () => {
  sttAudioBlob = null;
  sttFile.value = "";
  sttPreview.removeAttribute("src");
  sttPreview.classList.add("hidden");
  sttTranscribeBtn.disabled = true;
  sttResult.classList.add("hidden");
  hideStatus(sttStatus);
});