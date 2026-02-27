// gui/web/static/js/chat.js
import { dom } from "./dom.js";
import { api } from "./api.js";
import { setBotMode, speak } from "./botui.js";

export function appendMessage(text, who) {
  if (!dom.chatMessages) return;
  const div = document.createElement("div");
  div.className = `bubble ${who}`;
  div.textContent = text;
  dom.chatMessages.appendChild(div);
  dom.chatMessages.scrollTop = dom.chatMessages.scrollHeight;
}

export async function sendChat() {
  const input = dom.chatInput;
  if (!input) return;

  const message = input.value.trim();
  if (!message) return;

  input.value = "";
  appendMessage(message, "user");

  setBotMode(dom.botShellChat, dom.botModeChat, "speaking");
  if (dom.stateChat) dom.stateChat.textContent = "Đang trả lời...";

  try {
    const data = await api.chat(message);
    const answer = data.answer || "...";
    appendMessage(answer, "bot");
    if (dom.stateChat) dom.stateChat.textContent = "Đã trả lời.";
    speak(answer);
  } catch (e) {
    appendMessage("Sunybot hiện không thể trả lời.", "bot");
    if (dom.stateChat) dom.stateChat.textContent = "Lỗi kết nối.";
  } finally {
    setBotMode(dom.botShellChat, dom.botModeChat, "idle");
  }
}

export function quickAsk(text) {
  if (!dom.chatInput) return;
  dom.chatInput.value = text;
  sendChat();
}
