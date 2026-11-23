// ---------- page elements ----------
const imageBox = {
    placeholder: document.getElementById("placeholder"),
    image: document.getElementById("outputImage"),
    loading: document.getElementById("imageLoading"),
};
const paintButton = document.getElementById("paintButton");
const promptInput = document.getElementById("promptInput");
const chatHistory = document.getElementById("chatHistory");
const micButton = document.getElementById("micButton");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const statusText = document.getElementById("status");

const messages = [];          // the whole conversation: {role: "user" | "assistant", content}

function setStatus(text) {
    statusText.textContent = text;
}

// POST a JSON body (or FormData) to the Flask API and return the JSON answer
async function postApi(url, body) {
    const options = body instanceof FormData
        ? { method: "POST", body }
        : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    return data;
}


// ========== 1) Image generation ==========
async function generateImage() {
    const prompt = promptInput.value.trim();
    if (!prompt) {
        setStatus("Write a prompt first.");
        promptInput.focus();
        return;
    }
    paintButton.disabled = true;
    imageBox.loading.hidden = false;
    setStatus("Painting your image…");
    try {
        const data = await postApi("/api/generate-image", { prompt });
        imageBox.image.src = data.image;
        imageBox.image.hidden = false;
        imageBox.placeholder.hidden = true;
        setStatus(`Image ready in ${data.seconds} s`);
    } catch (error) {
        setStatus(`Image error: ${error.message}`);
    } finally {
        paintButton.disabled = false;
        imageBox.loading.hidden = true;
    }
}

paintButton.addEventListener("click", generateImage);
promptInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && event.ctrlKey) generateImage();     // Ctrl+Enter = paint
});


// ========== 2) Chat ==========
function addBubble(role, text, withPromptButton = true) {
    const bubble = document.createElement("div");
    bubble.className = `bubble ${role === "user" ? "user" : "bot"}`;
    bubble.textContent = text;
    if (role === "assistant" && withPromptButton) {
        // small helper: put the bot's suggestion into the prompt box
        const quoted = text.match(/"([^"]{10,})"/);
        const usePrompt = document.createElement("button");
        usePrompt.className = "use-prompt";
        usePrompt.textContent = "🎨 Use as prompt";
        usePrompt.addEventListener("click", () => {
            promptInput.value = quoted ? quoted[1] : text;
            promptInput.focus();
        });
        bubble.appendChild(usePrompt);
    }
    chatHistory.appendChild(bubble);
    chatHistory.scrollTop = chatHistory.scrollHeight;       // always show the newest message
    return bubble;
}

async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;
    messageInput.value = "";
    messages.push({ role: "user", content: text });
    addBubble("user", text);

    const typing = addBubble("user", "");
    typing.className = "bubble bot typing";
    typing.textContent = "DreamCanvas is typing…";
    sendButton.disabled = true;
    try {
        const data = await postApi("/api/chat", { messages });
        messages.push({ role: "assistant", content: data.reply });
        typing.remove();
        addBubble("assistant", data.reply);
        setStatus("");
    } catch (error) {
        typing.remove();
        setStatus(`Chat error: ${error.message}`);
    } finally {
        sendButton.disabled = false;
        messageInput.focus();
    }
}

sendButton.addEventListener("click", sendMessage);
messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") sendMessage();
});


// ========== 3) Microphone -> WAV -> Whisper ==========
// The browser records raw samples; we pack them into a 16 kHz WAV file ourselves,
// so the server does not need ffmpeg to decode the audio.
let recorder = null;

async function startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const context = new AudioContext();
    const source = context.createMediaStreamSource(stream);
    const processor = context.createScriptProcessor(4096, 1, 1);
    const chunks = [];
    processor.onaudioprocess = (event) => chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));
    source.connect(processor);
    processor.connect(context.destination);
    recorder = { stream, context, processor, chunks };
    micButton.classList.add("recording");
    setStatus("Listening… press the mic again to stop.");
}

async function stopRecording() {
    const { stream, context, processor, chunks } = recorder;
    recorder = null;
    processor.disconnect();
    stream.getTracks().forEach((track) => track.stop());
    await context.close();
    micButton.classList.remove("recording");

    const wav = encodeWav(mergeChunks(chunks), context.sampleRate, 16000);
    const form = new FormData();
    form.append("audio", wav, "speech.wav");
    micButton.disabled = true;
    setStatus("Converting speech to text…");
    try {
        const data = await postApi("/api/transcribe", form);
        messageInput.value = data.text;            // the text appears in the message box
        messageInput.focus();
        setStatus(data.text ? "Press send (or Enter) to send the message." : "I didn't hear anything, try again.");
    } catch (error) {
        setStatus(`Speech error: ${error.message}`);
    } finally {
        micButton.disabled = false;
    }
}

micButton.addEventListener("click", async () => {
    try {
        if (recorder) await stopRecording();
        else await startRecording();
    } catch (error) {
        setStatus(`Microphone error: ${error.message}`);
        micButton.classList.remove("recording");
        recorder = null;
    }
});

function mergeChunks(chunks) {
    const result = new Float32Array(chunks.reduce((sum, c) => sum + c.length, 0));
    let offset = 0;
    for (const chunk of chunks) {
        result.set(chunk, offset);
        offset += chunk.length;
    }
    return result;
}

// Float samples -> 16-bit mono WAV file at targetRate
function encodeWav(samples, sourceRate, targetRate) {
    const ratio = sourceRate / targetRate;
    const length = Math.floor(samples.length / ratio);
    const buffer = new ArrayBuffer(44 + length * 2);
    const view = new DataView(buffer);
    const writeText = (offset, text) => [...text].forEach((ch, i) => view.setUint8(offset + i, ch.charCodeAt(0)));

    writeText(0, "RIFF");
    view.setUint32(4, 36 + length * 2, true);
    writeText(8, "WAVE");
    writeText(12, "fmt ");
    view.setUint32(16, 16, true);              // size of the format block
    view.setUint16(20, 1, true);               // PCM
    view.setUint16(22, 1, true);               // mono
    view.setUint32(24, targetRate, true);
    view.setUint32(28, targetRate * 2, true);  // bytes per second
    view.setUint16(32, 2, true);               // bytes per sample
    view.setUint16(34, 16, true);              // bits per sample
    writeText(36, "data");
    view.setUint32(40, length * 2, true);

    for (let i = 0; i < length; i++) {
        const s = Math.max(-1, Math.min(1, samples[Math.floor(i * ratio)]));
        view.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
    return new Blob([view], { type: "audio/wav" });
}


// ---------- first message ----------
addBubble("assistant", "Hi! I am DreamCanvas. Ask me for an image idea, for example: write a prompt for a beautiful landscape.", false);
