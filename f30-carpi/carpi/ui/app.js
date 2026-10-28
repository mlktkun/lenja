// Oberfläche des Bordcomputers. Bedienung per Touch, iDrive (über den Server)
// oder Tastatur (Entwicklung): ←/→ drehen, Enter drücken, Esc zurück.
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

let socket;
let currentView = "home";
let focusIndex = 0;
let playing = false;
let volume = 50;

// ---------- Verbindung ----------
function connect() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(`${proto}://${location.host}/ws`);
  socket.onopen = () => {
    $("#conn").classList.add("on");
    send({ cmd: "media.state" });
    send({ cmd: "phone.contacts" });
  };
  socket.onclose = () => {
    $("#conn").classList.remove("on");
    setTimeout(connect, 2000);
  };
  socket.onmessage = (msg) => handleEvent(JSON.parse(msg.data));
}

function send(command) {
  if (socket && socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify(command));
}

// ---------- Ereignisse vom Bordcomputer ----------
function handleEvent(ev) {
  switch (ev.type) {
    case "nav": return handleNav(ev);
    case "media.state": return renderMedia(ev);
    case "phone.contacts": return renderContacts(ev.contacts);
    case "phone.call": return renderCall(ev);
    case "agent.question": return addChat("user", ev.text);
    case "agent.reply": return addChat("agent", ev.text);
    case "agent.tool": return addChat("tool", `→ ${ev.name}`);
    case "agent.reset": return addChat("tool", "Neue Unterhaltung");
    case "vehicle.ignition": $("#fact-ignition").textContent = ev.on ? "an" : "aus"; return;
    case "vehicle.power": $("#fact-power").textContent = ev.on ? "an" : "aus (Herunterfahren folgt)"; return;
    case "error": return addChat("tool", `Fehler: ${ev.message}`);
  }
}

function handleNav(ev) {
  $("#fact-nav").textContent = ev.action === "rotate" ? `drehen ${ev.delta}` : ev.button;
  if (ev.action === "rotate") return moveFocus(ev.delta);
  const shortcuts = { media: "media", phone: "phone", voice: "agent", nav: "home", menu: "home" };
  if (ev.button === "enter") return activateFocused();
  if (ev.button === "back") return showView("home");
  if (shortcuts[ev.button]) return showView(shortcuts[ev.button]);
  if (ev.button === "next" || ev.button === "previous") return send({ cmd: "media.control", action: ev.button });
  if (ev.button === "vol_up") return changeVolume(10);
  if (ev.button === "vol_down") return changeVolume(-10);
  if (ev.button === "left" || ev.button === "up") return moveFocus(-1);
  if (ev.button === "right" || ev.button === "down") return moveFocus(1);
}

// ---------- Ansichten und Fokus (Dreh-Drück-Steller) ----------
function showView(name) {
  currentView = name;
  $$(".view").forEach((v) => v.classList.toggle("active", v.id === `view-${name}`));
  focusIndex = 0;
  updateFocus();
  if (name === "agent") $("#ask-input").focus();
}

function focusables() {
  return $$(`#view-${currentView} .focusable`);
}

function moveFocus(delta) {
  const items = focusables();
  if (!items.length) return;
  focusIndex = (focusIndex + delta + items.length) % items.length;
  updateFocus();
}

function updateFocus() {
  $$(".focused").forEach((el) => el.classList.remove("focused"));
  const el = focusables()[focusIndex];
  if (el) {
    el.classList.add("focused");
    el.scrollIntoView({ block: "nearest" });
  }
}

function activateFocused() {
  const el = focusables()[focusIndex];
  if (!el) return;
  if (el.tagName === "INPUT") el.focus();
  else el.click();
}

document.addEventListener("keydown", (e) => {
  const typing = document.activeElement && document.activeElement.tagName === "INPUT";
  if (e.key === "Escape") return showView("home");
  if (typing) return;
  if (e.key === "ArrowRight" || e.key === "ArrowDown") moveFocus(1);
  else if (e.key === "ArrowLeft" || e.key === "ArrowUp") moveFocus(-1);
  else if (e.key === "Enter") activateFocused();
  else return;
  e.preventDefault();
});

// ---------- Musik ----------
function renderMedia(state) {
  playing = state.playing;
  volume = state.volume ?? volume;
  $("#track-title").textContent = state.title || "–";
  $("#track-artist").textContent = state.artist || "–";
  $("#volume").textContent = `${volume} %`;
  const toggle = $("#play-toggle");
  toggle.textContent = playing ? "⏸" : "▶";
  toggle.dataset.media = playing ? "pause" : "play";
}

function changeVolume(step) {
  send({ cmd: "media.volume", percent: Math.max(0, Math.min(100, volume + step)) });
}

// ---------- Telefon ----------
function renderContacts(contacts) {
  const list = $("#contacts");
  list.replaceChildren(
    ...contacts.map((c) => {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.className = "focusable";
      btn.dataset.dial = c.number;
      const name = document.createElement("span");
      name.textContent = c.name;
      const number = document.createElement("span");
      number.className = "muted";
      number.textContent = c.number;
      btn.append(name, number);
      li.append(btn);
      return li;
    })
  );
}

function renderCall(ev) {
  const labels = { dialing: "Wählt", active: "Gespräch", incoming: "Eingehend", ended: "Beendet" };
  const label = labels[ev.state] || ev.state;
  $("#call-number").textContent = ev.number ? `${label}: ${ev.number}` : label;
  $("#call-status").textContent = ev.state === "ended" ? "" : `☎ ${label}`;
  if (ev.state === "incoming") showView("phone");
}

// ---------- Assistent ----------
function addChat(kind, text) {
  const div = document.createElement("div");
  div.className = `msg ${kind}`;
  div.textContent = text;
  $("#chat").append(div);
  div.scrollIntoView({ block: "end" });
}

$("#ask-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const input = $("#ask-input");
  const text = input.value.trim();
  if (!text) return;
  send({ cmd: "agent.ask", text });
  input.value = "";
});

$("#agent-reset").addEventListener("click", () => send({ cmd: "agent.reset" }));

// ---------- Klicks (Touch und iDrive-Drücken) ----------
document.addEventListener("click", (e) => {
  const el = e.target.closest("button");
  if (!el) return;
  if (el.dataset.open) showView(el.dataset.open);
  else if (el.dataset.media) send({ cmd: "media.control", action: el.dataset.media });
  else if (el.dataset.volume) changeVolume(Number(el.dataset.volume));
  else if (el.dataset.phone) send({ cmd: `phone.${el.dataset.phone}` });
  else if (el.dataset.dial) send({ cmd: "phone.dial", number: el.dataset.dial });
});

// ---------- Start ----------
function tick() {
  $("#clock").textContent = new Date().toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" });
}

async function loadStatus() {
  try {
    const status = await (await fetch("/api/status")).json();
    $("#fact-mode").textContent = status.mode === "car" ? "Auto" : "Simulation";
    $("#fact-agent").textContent = status.agent ? "bereit" : "nicht eingerichtet";
  } catch {
    /* Server noch nicht bereit */
  }
}

tick();
setInterval(tick, 10_000);
loadStatus();
connect();
updateFocus();
