
let socket = null;
const listeners = {};
const statusCallbacks = [];

export function connectRaspberry(callbacks = {}) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    callbacks.onOpen?.();
    return;
  }

  socket = new WebSocket("ws://iot-project:9091");

  socket.onopen = () => {
    console.log(" Raspberry connected");
    callbacks.onOpen?.();
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (listeners[data.type]) {
        listeners[data.type].forEach((cb) => cb(data));
      }
    } catch {
      console.warn(" invalide Message", event.data);
    }
  };

  socket.onerror = () => {
    console.warn(" Raspberry disconnected");
    callbacks.onError?.();
  };

  socket.onclose = () => {
    console.log("Raspberry disconnected");
    callbacks.onClose?.();
    socket = null;
  };
}

export function sendCommand(command) {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    console.warn("Raspberry disconnected, cannot send command");
    return;
  }
  socket.send(command);
}

export function onMessage(type, callback) {
  if (!listeners[type]) listeners[type] = [];
  listeners[type].push(callback);
}

export function offMessage(type, callback) {
  if (!listeners[type]) return;
  listeners[type] = listeners[type].filter((cb) => cb !== callback);
}