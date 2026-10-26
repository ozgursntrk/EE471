// ================= Shared helpers =================
function showStatus(box, message, type) {
  box.textContent = message;
  box.className = `status ${type}`;
}

function hideStatus(box) {
  box.className = "status hidden";
}

const $ = (id) => document.getElementById(id);

// ================= Tabs =================
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.add("hidden"));
    tab.classList.add("active");
    $(tab.dataset.tab).classList.remove("hidden");
  });
});

// ================= Audio input (record or upload) =================
// The same record/stop/upload/preview block is used in 4 tabs.
// createAudioInput wires up one block and returns an object to read or reset it.
function createAudioInput(prefix) {
  const recordBtn = $(`${prefix}-record-btn`);
  const stopBtn = $(`${prefix}-stop-btn`);
  const fileInput = $(`${prefix}-file`);
  const preview = $(`${prefix}-preview`);
  const runBtn = $(`${prefix}-run-btn`);
  const status = $(`${prefix}-status`);

  let mediaRecorder = null;
  let chunks = [];
  let audioBlob = null;

  function setAudio(blob) {
    audioBlob = blob;
    preview.src = URL.createObjectURL(blob);
    preview.classList.remove("hidden");
    runBtn.disabled = false;
  }

  recordBtn.addEventListener("click", async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunks = [];
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
      mediaRecorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());  // turn the microphone off
        setAudio(new Blob(chunks, { type: mediaRecorder.mimeType }));
        showStatus(status, "Recording finished. Click the button below.", "success");
      };
      mediaRecorder.start();
      recordBtn.disabled = true;
      stopBtn.disabled = false;
      fileInput.value = "";
      showStatus(status, "● Recording...", "recording");
    } catch (err) {
      showStatus(status, "Microphone access was denied.", "error");
    }
  });

  stopBtn.addEventListener("click", () => {
    mediaRecorder.stop();
    recordBtn.disabled = false;
    stopBtn.disabled = true;
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      setAudio(fileInput.files[0]);
      showStatus(status, `File selected: ${fileInput.files[0].name}`, "success");
    }
  });

  return {
    getBlob: () => audioBlob,
    reset() {
      audioBlob = null;
      fileInput.value = "";
      preview.removeAttribute("src");
      preview.classList.add("hidden");
      runBtn.disabled = true;
      hideStatus(status);
    },
  };
}

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

// ---------- Send audio + extra form fields to a Flask endpoint ----------
async function postAudio(url, blob, fields) {
  const form = new FormData();
  form.append("audio", await toWav16k(blob), "audio.wav");
  for (const [name, value] of Object.entries(fields)) form.append(name, value);

  const response = await fetch(url, { method: "POST", body: form });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error);
  return data;
}

// Runs an action with a loading message and shows any error in the status box
async function runAction(button, status, loadingText, action) {
  button.disabled = true;
  showStatus(status, loadingText, "loading");
  try {
    await action();
  } catch (err) {
    showStatus(status, err.message, "error");
  } finally {
    button.disabled = false;
  }
}

// ================= 1) Text to Speech =================
let ttsAudioUrl = null;  // the last generated audio (kept in browser memory)

$("tts-synth-btn").addEventListener("click", () => {
  const status = $("tts-status");
  const text = $("tts-text").value.trim();
  if (!text) {
    showStatus(status, "Please enter some text.", "error");
    return;
  }

  runAction($("tts-synth-btn"), status, "Synthesizing...", async () => {
    const response = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text, voice: $("tts-voice").value }),
    });
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error);
    }

    const blob = await response.blob();               // WAV bytes from Flask
    if (ttsAudioUrl) URL.revokeObjectURL(ttsAudioUrl); // free the old audio
    ttsAudioUrl = URL.createObjectURL(blob);

    $("tts-player").src = ttsAudioUrl;
    $("tts-download").href = ttsAudioUrl;
    $("tts-result").classList.remove("hidden");
    showStatus(status, "✓ Speech synthesized successfully!", "success");
    $("tts-player").play();
  });
});

$("tts-clear-btn").addEventListener("click", () => {
  $("tts-text").value = "";
  hideStatus($("tts-status"));
  $("tts-result").classList.add("hidden");
  $("tts-player").removeAttribute("src");
});

// ================= 2) Speech to Text =================
const sttInput = createAudioInput("stt");

$("stt-run-btn").addEventListener("click", () => {
  const status = $("stt-status");
  runAction($("stt-run-btn"), status, "Transcribing...", async () => {
    const data = await postAudio("/api/stt", sttInput.getBlob(), {
      language: $("stt-language").value,
    });
    $("stt-transcript").textContent = data.text;
    $("stt-result").classList.remove("hidden");
    showStatus(status, "✓ Audio transcribed successfully!", "success");
  });
});

$("stt-copy-btn").addEventListener("click", async () => {
  await navigator.clipboard.writeText($("stt-transcript").textContent);
  showStatus($("stt-status"), "Text copied to clipboard.", "success");
});

$("stt-clear-btn").addEventListener("click", () => {
  sttInput.reset();
  $("stt-result").classList.add("hidden");
});

// ================= 3) Diarization =================
const diaInput = createAudioInput("dia");

$("dia-run-btn").addEventListener("click", () => {
  const status = $("dia-status");
  runAction($("dia-run-btn"), status, "Identifying speakers...", async () => {
    const data = await postAudio("/api/diarize", diaInput.getBlob(), {
      language: $("dia-language").value,
    });

    // Give every speaker their own color
    const colors = {};
    const list = $("dia-segments");
    list.innerHTML = "";
    for (const segment of data.segments) {
      if (!(segment.speaker in colors)) colors[segment.speaker] = Object.keys(colors).length % 4;

      const row = document.createElement("div");
      row.className = "segment";
      const badge = document.createElement("span");
      badge.className = `speaker speaker-${colors[segment.speaker]}`;
      badge.textContent = segment.speaker;
      const text = document.createElement("span");
      text.textContent = segment.text;
      row.append(badge, text);
      list.append(row);
    }

    $("dia-result").classList.remove("hidden");
    const speakerCount = Object.keys(colors).length;
    showStatus(status, `✓ Found ${speakerCount} speaker(s).`, "success");
  });
});

$("dia-clear-btn").addEventListener("click", () => {
  diaInput.reset();
  $("dia-result").classList.add("hidden");
});

// ================= 4) Translation =================
const trInput = createAudioInput("tr");

$("tr-run-btn").addEventListener("click", () => {
  const status = $("tr-status");
  runAction($("tr-run-btn"), status, "Translating...", async () => {
    const data = await postAudio("/api/translate", trInput.getBlob(), {
      source: $("tr-source").value,
      target: $("tr-target").value,
    });
    $("tr-original").textContent = data.original;
    $("tr-translation").textContent = data.translation;
    $("tr-result").classList.remove("hidden");
    showStatus(status, "✓ Speech translated successfully!", "success");
  });
});

$("tr-clear-btn").addEventListener("click", () => {
  trInput.reset();
  $("tr-result").classList.add("hidden");
});

// ================= 5) Pronunciation assessment =================
const paInput = createAudioInput("pa");

function wordClass(word) {
  if (word.error === "Omission") return "omission";   // the word was skipped
  if (word.error !== "None") return "bad";            // mispronounced or extra word
  if (word.accuracy >= 80) return "good";
  if (word.accuracy >= 60) return "ok";
  return "bad";
}

$("pa-run-btn").addEventListener("click", () => {
  const status = $("pa-status");
  const referenceText = $("pa-reference").value.trim();
  if (!referenceText) {
    showStatus(status, "Please enter the sentence you will read.", "error");
    return;
  }

  runAction($("pa-run-btn"), status, "Assessing pronunciation...", async () => {
    const data = await postAudio("/api/pronunciation", paInput.getBlob(), {
      reference_text: referenceText,
      language: $("pa-language").value,
    });

    // Four score boxes
    const scores = [
      ["Pronunciation", data.pronunciation],
      ["Accuracy", data.accuracy],
      ["Fluency", data.fluency],
      ["Completeness", data.completeness],
    ];
    const scoresBox = $("pa-scores");
    scoresBox.innerHTML = "";
    for (const [name, value] of scores) {
      const box = document.createElement("div");
      box.className = "score";
      box.innerHTML = `<div class="value">${Math.round(value)}</div><div class="name">${name}</div>`;
      scoresBox.append(box);
    }

    // Every word colored by its accuracy
    const wordsBox = $("pa-words");
    wordsBox.innerHTML = "";
    for (const word of data.words) {
      const span = document.createElement("span");
      span.className = `word ${wordClass(word)}`;
      span.textContent = word.word;
      span.title = `Accuracy: ${Math.round(word.accuracy)} | Error: ${word.error}`;
      wordsBox.append(span, " ");
    }

    $("pa-result").classList.remove("hidden");
    showStatus(status, "✓ Pronunciation assessed!", "success");
  });
});

$("pa-clear-btn").addEventListener("click", () => {
  paInput.reset();
  $("pa-result").classList.add("hidden");
});