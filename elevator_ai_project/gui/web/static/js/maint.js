import { dom } from "./dom.js";

export function initMaint(){
  if(localStorage.getItem("maint_authed")==="1"){
    showDash(true);
  }
}
function showDash(on){
  if(dom.maintLogin) dom.maintLogin.style.display = on ? "none":"block";
  if(dom.maintDash) dom.maintDash.style.display = on ? "block":"none";
}

export function maintenanceLogin(){
  const u = dom.maintUser?.value.trim();
  const p = dom.maintPass?.value.trim();
  if(!u || !p){ showToast?.("Vui lòng nhập tài khoản và mật khẩu"); return; }
  localStorage.setItem("maint_authed","1");
  showDash(true);
}

export function maintenanceLogout(){
  localStorage.removeItem("maint_authed");
  showDash(false);
}

export function fillDemo(){
  if(dom.maintUser) dom.maintUser.value="engineer";
  if(dom.maintPass) dom.maintPass.value="123456";
  if(dom.maintLan) dom.maintLan.value="192.168.1.10";
}

export function runLLMQuery(){
  const q = dom.llmInput?.value.trim();
  if(!q){ if(dom.llmOutput) dom.llmOutput.textContent="Nhập câu hỏi để truy vấn."; return; }
  if(dom.llmOutput) dom.llmOutput.textContent="Đang truy vấn...";
  setTimeout(()=>{
    if(dom.llmOutput) dom.llmOutput.textContent="Kết quả mẫu: Lỗi cửa kẹt xuất hiện nhiều nhất lúc 08:00-09:00.";
  }, 700);
}
