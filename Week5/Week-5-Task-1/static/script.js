const recordBtn = document.getElementById("record-btn");
const stopBtn = document.getElementById("stop-btn");
const fileInput = document.getElementById("file-input");
const languageSelect = document.getElementById("language");
const preview = document.getElementById("preview");
const transcribeBtn = document.getElementById("transcribe-btn");
const clearBtn = document.getElementById("clear-btn");
const statusBox = document.getElementById("status");
const resultBox = document.getElementById("result");
const transcriptEl = document.getElementById("transcript");
const copyBtn = document.getElementById("copy-btn");

let mediaRecorder = null;
let chunks = [];
let audioBlob = null;  // the audio to transcribe (recorded or uploaded)

function showStatus(message, type) {
  statusBox.textContent = message;
  statusBox.className = `status ${type}`;
}

function setAudio(blob) {
  audioBlob = blob;
  preview.src = URL.createObjectURL(blob);
  preview.classList.remove("hidden");
  transcribeBtn.disabled = false;
}

// ---------- Recording from the microphone ----------
recordBtn.addEventListener("click", async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    chunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
    mediaRecorder.onstop = () => {
      stream.getTracks().forEach((track) => track.stop());  // turn the microphone off
      setAudio(new Blob(chunks, { type: mediaRecorder.mimeType }));
      showStatus("Recording finished. Click 'Transcribe Audio'.", "success");
    };
    mediaRecorder.start();
    recordBtn.disabled = true;
    stopBtn.disabled = false;
    fileInput.value = "";
    showStatus("● Recording...", "recording");
  } catch (err) {
    showStatus("Microphone access was denied.", "error");
  }
});

stopBtn.addEventListener("click", () => {
  mediaRecorder.stop();
  recordBtn.disabled = false;
  stopBtn.disabled = true;
});

// ---------- Uploading a file ----------
fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    setAudio(fileInput.files[0]);
    showStatus(`File selected: ${fileInput.files[0].name}`, "success");
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
transcribeBtn.addEventListener("click", async () => {
  if (!audioBlob) return;
  transcribeBtn.disabled = true;
  showStatus("Transcribing...", "loading");

  try {
    const wav = await toWav16k(audioBlob);
    const form = new FormData();
    form.append("audio", wav, "audio.wav");
    form.append("language", languageSelect.value);

    const response = await fetch("/api/stt", { method: "POST", body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);

    transcriptEl.textContent = data.text;
    resultBox.classList.remove("hidden");
    showStatus("✓ Audio transcribed successfully!", "success");
  } catch (err) {
    showStatus(err.message, "error");
  } finally {
    transcribeBtn.disabled = false;
  }
});

copyBtn.addEventListener("click", async () => {
  await navigator.clipboard.writeText(transcriptEl.textContent);
  showStatus("Text copied to clipboard.", "success");
});

clearBtn.addEventListener("click", () => {
  audioBlob = null;
  fileInput.value = "";
  preview.removeAttribute("src");
  preview.classList.add("hidden");
  transcribeBtn.disabled = true;
  resultBox.classList.add("hidden");
  statusBox.className = "status hidden";
});