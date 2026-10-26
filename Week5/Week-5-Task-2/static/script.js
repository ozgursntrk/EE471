// ================= Elements =================
const display = document.getElementById("display");
const micBtn = document.getElementById("mic-btn");
const statusText = document.getElementById("status");

// What each key says (from the command table)
const KEY_WORDS = {
  "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
  "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine",
  ".": "point", "/": "over", "*": "times", "+": "plus", "-": "minus", "=": "is",
};
const OPERATIONS = { "+": "add", "-": "subtract", "*": "multiply", "/": "divide" };
const SYMBOLS = { "+": "+", "-": "−", "*": "×", "/": "÷" };

// ================= Calculator state (same idea as Week 4) =================
let firstNumber = null;  // e.g. "8"
let operator = null;     // e.g. "/"
let current = "0";       // the number being typed
let startNew = true;     // does the next digit start a new number?

function render() {
  if (operator === null) {
    display.textContent = current;
  } else {
    display.textContent = `${firstNumber} ${SYMBOLS[operator]} ${startNew ? "" : current}`;
  }
}

function reset() {
  firstNumber = null;
  operator = null;
  current = "0";
  startNew = true;
  render();
}

// ================= Speaking (Azure text-to-speech) =================
const audioCache = new Map();     // text -> Promise of an audio URL
let speechQueue = Promise.resolve();

function getSpeechUrl(text) {
  if (!audioCache.has(text)) {
    const promise = fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text }),
    })
      .then((response) => {
        if (!response.ok) throw new Error("Speech failed");
        return response.blob();
      })
      .then((blob) => URL.createObjectURL(blob));
    promise.catch(() => audioCache.delete(text));  // try again next time
    audioCache.set(text, promise);
  }
  return audioCache.get(text);
}

function playUrl(url) {
  return new Promise((resolve) => {
    const audio = new Audio(url);
    audio.onended = resolve;
    audio.onerror = resolve;
    audio.play().catch(resolve);
  });
}

// Words are spoken one after another, in the order the keys were pressed
function speak(text) {
  const urlPromise = getSpeechUrl(text);  // start downloading immediately
  speechQueue = speechQueue.then(() => urlPromise).then(playUrl).catch(() => {});
}

// Download the 16 key words once when the page opens, so the buttons speak instantly
Object.values(KEY_WORDS).forEach(getSpeechUrl);

// ================= Pressing a key =================
async function pressKey(key, { speakKey }) {
  if (speakKey && key !== "=") speak(KEY_WORDS[key]);

  if (/^[0-9.]$/.test(key)) {
    if (startNew) {
      current = key === "." ? "0." : key;
      startNew = false;
    } else {
      if (key === "." && current.includes(".")) return;
      current += key;
    }
    render();
  } else if (key in OPERATIONS) {
    if (operator === null || !startNew) firstNumber = current;
    operator = key;
    startNew = true;
    render();
  } else if (key === "=") {
    await equals();
  }
}

// "=" sends the calculation to Flask (no math in JavaScript) and speaks "is <result>"
async function equals() {
  if (operator === null || startNew) {
    speak("is " + current);
    return;
  }

  const response = await fetch("/api/calculate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      a: Number(firstNumber),
      b: Number(current),
      operation: OPERATIONS[operator],
    }),
  });
  const data = await response.json();

  operator = null;
  startNew = true;
  if (response.ok) {
    current = String(data.result);
    render();
    speak("is " + data.result);
  } else {
    current = "0";
    display.textContent = data.error;
    speak("Error. " + data.error);
  }
}

// Button -> voice: every button press is also spoken
document.querySelectorAll(".buttons button").forEach((button) => {
  button.addEventListener("click", () => pressKey(button.dataset.key, { speakKey: true }));
});

display.addEventListener("click", reset);  // click the display to clear

// ================= Microphone: voice -> button =================
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
    mediaRecorder.onstop = () => {
      stream.getTracks().forEach((track) => track.stop());  // turn the microphone off
      handleVoiceCommand(new Blob(chunks, { type: mediaRecorder.mimeType }));
    };
    mediaRecorder.start();
    micBtn.classList.add("listening");
    statusText.textContent = "Listening... say e.g. \"five plus two is\", then click the mic again.";
  } catch (err) {
    statusText.textContent = "Microphone access was denied.";
  }
});

async function handleVoiceCommand(blob) {
  micBtn.classList.remove("listening");
  micBtn.classList.add("busy");
  statusText.textContent = "Recognizing...";

  try {
    const form = new FormData();
    form.append("audio", await toWav16k(blob), "command.wav");
    const response = await fetch("/api/voice-command", { method: "POST", body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);

    statusText.textContent = `Heard: "${data.heard}"`;
    for (const key of data.keys) {
      flashButton(key);
      await pressKey(key, { speakKey: false });
      await sleep(250);  // small pause so you can see each key being pressed
    }
  } catch (err) {
    statusText.textContent = err.message;
  } finally {
    micBtn.classList.remove("busy");
  }
}

function flashButton(key) {
  const button = document.querySelector(`.buttons button[data-key="${key}"]`);
  button.classList.add("pressed");
  setTimeout(() => button.classList.remove("pressed"), 200);
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// ================= Convert any audio to 16 kHz mono WAV (the format Azure expects) =================
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