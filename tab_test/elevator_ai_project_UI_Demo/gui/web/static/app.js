function nowHHMM() {
  const d = new Date();
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${hh}:${mm}`;
}

function addMsg(msgsEl, role, text, meta = "", timeText = null) {
  const wrap = document.createElement("div");
  wrap.className = "msgwrap";

  const t = document.createElement("div");
  t.className = "time";
  t.textContent = timeText || nowHHMM();
  wrap.appendChild(t);

  const row = document.createElement("div");
  row.className = "row " + (role === "me" ? "me" : "bot");

  const b = document.createElement("div");
  b.className = "bubble";
  b.textContent = text;

  row.appendChild(b);
  wrap.appendChild(row);

  if (meta) {
    const m = document.createElement("div");
    m.className = "meta";
    m.textContent = meta;
    wrap.appendChild(m);
  }

  msgsEl.appendChild(wrap);
  msgsEl.scrollTop = msgsEl.scrollHeight;
  return wrap;
}

function addTyping(msgsEl, role = "bot") {
  const wrap = document.createElement("div");
  wrap.className = "msgwrap";

  const t = document.createElement("div");
  t.className = "time";
  t.textContent = nowHHMM();
  wrap.appendChild(t);

  const row = document.createElement("div");
  row.className = "row " + (role === "me" ? "me" : "bot");

  const b = document.createElement("div");
  b.className = "bubble";

  const typing = document.createElement("div");
  typing.className = "typing";

  const dots = document.createElement("div");
  dots.className = "dots";
  dots.innerHTML = `<span class="dot"></span><span class="dot"></span><span class="dot"></span>`;

  typing.appendChild(dots);
  b.appendChild(typing);

  const thinking = document.createElement("div");
  thinking.className = "thinking";
  thinking.textContent = "đang suy nghĩ";
  b.appendChild(thinking);

  row.appendChild(b);
  wrap.appendChild(row);

  msgsEl.appendChild(wrap);
  msgsEl.scrollTop = msgsEl.scrollHeight;
  return wrap;
}

async function bindChatUI({ msgsId="msgs", inputId="text", buttonId="send", welcomeText=null }) {
  const msgs = document.getElementById(msgsId);
  const input = document.getElementById(inputId);
  const btn = document.getElementById(buttonId);

  async function send() {
    const text = input.value.trim();
    if (!text) return;

    addMsg(msgs, "me", text);
    input.value = "";
    btn.disabled = true;

    const typingNode = addTyping(msgs, "bot");

    try {
      const r = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
      });

      const data = await r.json();
      typingNode.remove();

      const meta =
        `source=${data.source}` +
        (data.intent ? ` • intent=${data.intent}` : "") +
        (data.confidence != null ? ` • conf=${Number(data.confidence).toFixed(3)}` : "");

      addMsg(msgs, "bot", data.answer, meta);

    } catch (e) {
      typingNode.remove();
      addMsg(msgs, "bot",
        "Sunybot hiện không thể trả lời câu hỏi này, vui lòng nhập câu hỏi khác",
        "source=FALLBACK"
      );
    } finally {
      btn.disabled = false;
      input.focus();
    }
  }

  btn.addEventListener("click", send);
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") send(); });

  if (welcomeText) {
    addMsg(msgs, "bot", welcomeText, "source=DB_PROMPT");
  }
}

