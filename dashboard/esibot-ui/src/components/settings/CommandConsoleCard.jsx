import { Terminal, Mic, MicOff, Lightbulb } from "lucide-react";
import { useState, useEffect, useRef } from "react";
import * as ROSLIB from "roslib";
import { ros } from "../../services/ros";
import {
  connectRaspberry,
  sendCommand,
  onMessage,
  offMessage,
} from "../../services/raspberrySocket";

const cmdVel = new ROSLIB.Topic({
  ros,
  name: "/cmd_vel",
  messageType: "geometry_msgs/Twist",
});

const SCRIPT_COMMANDS = {
  slam: "~/start_slam.sh",
  camera: "~/start_camera.sh",
  driver: "~/start_driver.sh",
  tout: "~/start_all.sh",
  all: "~/start_all.sh",
  killall: "~/stop.sh",
};

function publishCmdVel(linearX, angularZ) {
  cmdVel.publish({
    linear: { x: linearX, y: 0.0, z: 0.0 },
    angular: { x: 0.0, y: 0.0, z: angularZ },
  });
}

function executeRobotAction(action) {
  if (action === "forward") {
    publishCmdVel(0.2, 0.0);
  } else if (action === "backward") {
    publishCmdVel(-0.2, 0.0);
  } else if (action === "left") {
    publishCmdVel(0.0, 0.5);

    setTimeout(() => {
      publishCmdVel(0.0, 0.0);
    }, 800);
  } else if (action === "right") {
    publishCmdVel(0.0, -0.5);

    setTimeout(() => {
      publishCmdVel(0.0, 0.0);
    }, 800);
  } else if (action === "stop") {
    publishCmdVel(0.0, 0.0);
  }
}

export default function CommandConsoleCard() {
  const [input, setInput] = useState("");
  const [logs, setLogs] = useState([]);
  const [connected, setConnected] = useState(false);
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);

  useEffect(() => {
    connectRaspberry({
      onOpen: () => setConnected(true),
      onClose: () => setConnected(false),
      onError: () => setConnected(false),
    });

    const handler = (data) => {
      setLogs((prev) => [...prev, ...data.lines]);
    };

    onMessage("console", handler);

    return () => offMessage("console", handler);
  }, []);

  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setLogs((prev) => [
        ...prev,
        "Speech recognition not supported in this browser",
      ]);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "fr-FR";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      setListening(true);
      setLogs((prev) => [...prev, "Listening..."]);
    };

    recognition.onend = () => {
      setListening(false);
    };

    recognition.onerror = (event) => {
      setListening(false);
      setLogs((prev) => [...prev, `Voice error: ${event.error}`]);
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript.toLowerCase().trim();

      setLogs((prev) => [...prev, `Heard: ${transcript}`]);

      const action = detectVoiceCommand(transcript);

      if (!action) {
        setLogs((prev) => [...prev, "⚠️ Command not recognized"]);
        return;
      }

      setLogs((prev) => [...prev, `Detected command: ${action}`]);
      executeRobotAction(action);
    };

    recognitionRef.current = recognition;
  }, []);

  const detectVoiceCommand = (text) => {
    if (
      text.includes("avance") ||
      text.includes("avancer") ||
      text.includes("avant") ||
      text.includes("forward")
    ) {
      return "forward";
    }

    if (
      text.includes("recule") ||
      text.includes("reculer") ||
      text.includes("arrière") ||
      text.includes("backward")
    ) {
      return "backward";
    }

    if (text.includes("gauche") || text.includes("left")) return "left";
    if (text.includes("droite") || text.includes("right")) return "right";

    if (
      text.includes("stop") ||
      text.includes("arrêt") ||
      text.includes("arrete") ||
      text.includes("arrête")
    ) {
      return "stop";
    }

    return null;
  };

  const startVoiceRecognition = () => {
    if (!recognitionRef.current) {
      setLogs((prev) => [...prev, "Voice recognition unavailable"]);
      return;
    }

    recognitionRef.current.start();
  };

  const showHelp = () => {
    setLogs((prev) => [
      ...prev,
      "═══════════════════════════════",
      "Available commands:",
      "═══════════════════════════════",
      "Voice/manual → avance, avancer, avant, forward, recule, reculer, arrière, backward, gauche, left, droite, right, arrêt, stop",
      "Scripts → slam, camera, driver, tout, all, killall",
      "Utility → clear",
      "═══════════════════════════════",
    ]);
  };

  const handleExecute = () => {
    const cleanInput = input.trim().toLowerCase();

    if (!cleanInput) return;

    if (cleanInput === "clear") {
      setLogs([]);
      setInput("");
      return;
    }

    const detected = detectVoiceCommand(cleanInput);

    if (detected) {
      setLogs((prev) => [
        ...prev,
        `> ${input}`,
        `Detected text command: ${detected}`,
      ]);

      executeRobotAction(detected);
      setInput("");
      return;
    }

    if (SCRIPT_COMMANDS[cleanInput]) {
      if (!connected) {
        setLogs((prev) => [...prev, "Raspberry not connected"]);
        setInput("");
        return;
      }

      setLogs((prev) => [
        ...prev,
        `> ${input}`,
        `Executing script: ${SCRIPT_COMMANDS[cleanInput]}`,
      ]);

      sendCommand(SCRIPT_COMMANDS[cleanInput]);
      setInput("");
      return;
    }

    if (!connected) {
      setLogs((prev) => [...prev, "Raspberry not connected"]);
      setInput("");
      return;
    }

    setLogs((prev) => [...prev, `> ${input}`]);
    sendCommand(input);
    setInput("");
  };

  return (
    <section className="bg-[#2b2b2b] border border-[#3a3a3a] rounded-[16px] p-[20px] text-white shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
      <div className="flex items-center gap-[16px] mb-4">
        <div className="w-[34px] h-[34px] rounded-[10px] bg-[#10243a] border border-[#0a7cff55] text-[#148bff] grid place-items-center shadow-[0_0_12px_rgba(10,124,255,0.15)]">
          <Terminal size={17} />
        </div>

        <h3 className="text-[14px] font-bold">Command Console</h3>

        <button
          onClick={showHelp}
          className="ml-auto h-[32px] px-3 rounded-[9px] border text-[11px] font-bold flex items-center gap-2 transition bg-[#2a2410] border-[#facc1555] text-[#facc15] hover:border-[#facc15]"
        >
          <Lightbulb size={14} />
          Help
        </button>

        <button
          onClick={startVoiceRecognition}
          className={`h-[32px] px-3 rounded-[9px] border text-[11px] font-bold flex items-center gap-2 transition ${
            listening
              ? "bg-[#3a1111] border-[#ff5050] text-[#ff8080]"
              : "bg-[#10243a] border-[#148bff55] text-[#148bff] hover:border-[#148bff]"
          }`}
        >
          {listening ? <MicOff size={14} /> : <Mic size={14} />}
          {listening ? "Listening" : "Voice"}
        </button>

        <span
          className={`text-[10px] font-bold flex items-center gap-[5px] ${
            connected ? "text-[#50e38b]" : "text-[#ff5050]"
          }`}
        >
          <span
            className={`w-[6px] h-[6px] rounded-full ${
              connected ? "bg-[#50e38b]" : "bg-[#ff5050]"
            }`}
          />
          {connected ? "Connected" : "Disconnected"}
        </span>
      </div>

      <div className="bg-[#121212] border border-[#292929] rounded-[10px] overflow-hidden font-mono text-[12px]">
        <div className="p-4 px-[5px] min-h-[92px] text-[#a7a7a7] leading-6 max-h-[180px] overflow-y-auto">
          {logs.length === 0 ? (
            <p className="text-[#555]">
              {connected
                ? "Try: slam, camera, driver, tout, killall, avance, stop..."
                : "Waiting for Raspberry..."}
            </p>
          ) : (
            logs.map((log, i) => (
              <p
                key={i}
                className={
                  log.startsWith(">")
                    ? "text-[#50e38b]"
                    : log.startsWith("⚠️")
                    ? "text-[#ffa927]"
                    : log.toLowerCase().includes("error") ||
                      log.toLowerCase().includes("not connected") ||
                      log.toLowerCase().includes("unavailable")
                    ? "text-[#ff5050]"
                    : log.toLowerCase().includes("detected") ||
                      log.toLowerCase().includes("executing")
                    ? "text-[#50e38b]"
                    : log.toLowerCase().includes("heard") ||
                      log.toLowerCase().includes("listening")
                    ? "text-[#148bff]"
                    : log.toLowerCase().includes("available") ||
                      log.toLowerCase().includes("voice/manual") ||
                      log.toLowerCase().includes("scripts") ||
                      log.toLowerCase().includes("utility")
                    ? "text-[#facc15]"
                    : ""
                }
              >
                {log}
              </p>
            ))
          )}
        </div>

        <div className="h-[42px] border-t border-[#292929] bg-[#1b1b1b] flex items-center px-[4px]">
          <span className="text-[#50e38b] mr-2">&gt;</span>

          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 bg-transparent outline-none text-[#ccc] placeholder:text-[#555]"
            placeholder={
              connected
                ? "Try: slam, camera, driver, tout, killall, avance, stop..."
                : "Raspberry not connected..."
            }
            onKeyDown={(e) => e.key === "Enter" && handleExecute()}
          />

          <button
            onClick={handleExecute}
            className="px-4 py-2 rounded-[7px] bg-[#148bff] text-[#ffffff] text-[11px] font-bold hover:bg-[#0f7ee8] active:scale-[0.96] transition"
          >
            Execute
          </button>
        </div>
      </div>
    </section>
  );
}