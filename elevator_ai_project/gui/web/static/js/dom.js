// gui/web/static/js/dom.js
export const $ = (id) => document.getElementById(id);

export const dom = {
  // topbar (renderTopbar tạo ra)
  tb_time: $("tb_time"),
  tb_people: $("tb_people"),
  tb_weather: $("tb_weather"),

  // home status
  floor: $("floor"),
  overload: $("overload"),
  direction: $("direction"),
  door: $("door"),
  people: $("people"),
  clock: $("clock"),
  weather: $("weather"),

  // home bot
  botShell: $("botShell"),
  botMode: $("botMode"),
  state: $("state"),

  // chat screen
  chatMessages: $("chatMessages"),
  chatInput: $("chatInput"),
  botShellChat: $("botShellChat"),
  botModeChat: $("botModeChat"),
  stateChat: $("stateChat"),

  // sos
  sosTime: $("sosTime"),
  sosStatus: $("sosStatus"),
  sosLocation: $("sosLocation"),

  // maint
  maintLogin: $("maint-login"),
  maintDash: $("maint-dashboard"),
  maintUser: $("maintUser"),
  maintPass: $("maintPass"),
  maintLan: $("maintLan"),
  maintFloor: $("maintFloor"),
  maintDirection: $("maintDirection"),
  maintDoor: $("maintDoor"),
  maintPeople: $("maintPeople"),
  maintTime: $("maintTime"),
  llmInput: $("llmInput"),
  llmOutput: $("llmOutput"),
};
