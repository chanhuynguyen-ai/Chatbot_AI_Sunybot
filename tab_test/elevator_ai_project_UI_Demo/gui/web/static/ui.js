function showToast(msg, ms=1600){
  let t = document.getElementById("toast");
  if(!t){
    t = document.createElement("div");
    t.id = "toast";
    t.className = "toast";
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(()=>t.classList.remove("show"), ms);
}

function renderTopbar(){
  const bar = document.createElement("div");
  bar.className = "topbar";
  bar.innerHTML = `
    <div class="topbar-inner">
      <div class="brand">
        <div class="logo"></div>
        <div class="brand-title">Sunybot Elevator</div>
      </div>

      <div class="pills">
        <div class="pill">🕒 <b id="tb_time">--:--</b></div>
        <div class="pill">👥 <b id="tb_people">--</b></div>
        <div class="pill">⛅ <b id="tb_weather">--</b></div>
      </div>
    </div>
  `;
  document.body.prepend(bar);
}

function navGo(href){ window.location.href = href; }

function renderTabbar(activeHref){
  // đúng thứ tự: | SOS | Gọi tầng | Home | Sunybot | Bảo trì |
  const items = [
    { href:"/pages/sos.html",        label:"SOS",     icon:"🆘", cls:"sos" },
    { href:"/pages/call.html",       label:"Gọi tầng",icon:"🔢" },
    { href:"/",                      label:"Home",    icon:"🏠", cls:"home" },
    { href:"/pages/assistant.html",  label:"Sunybot", icon:"🤖" },
    { href:"/pages/maintenance.html",label:"Bảo trì", icon:"🛠" },
  ];

  const bar = document.createElement("div");
  bar.className = "tabbar";
  bar.innerHTML = `
    <div class="tabbar-inner">
      ${items.map(it=>{
        const active = (it.href === activeHref) ? " active" : "";
        const cls = it.cls ? ` ${it.cls}` : "";
        return `
          <button class="tab${cls}${active}" onclick="navGo('${it.href}')">
            <div class="ico">${it.icon}</div>
            <div class="lbl">${it.label}</div>
          </button>
        `;
      }).join("")}
    </div>
  `;
  document.body.appendChild(bar);
}

