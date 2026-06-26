import { Terminal } from "lucide-react";
import { useEffect, useState } from "react";
import * as ROSLIB from "roslib";
import { ros } from "../services/ros";

export default function LogConsole() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    try {
      const topic = new ROSLIB.Topic({
        ros,
        name: "/rosout",
        messageType: "rcl_interfaces/msg/Log",
      });

      topic.subscribe((msg) => {
        setLogs((prev) => [
          ...prev,
          { message: msg.msg, level: getLevel(msg.level) },
        ]);
      });

      return () => topic.unsubscribe();
    } catch (e) {
      console.warn("Rosout topic non disponible", e);
    }
  }, []);

  return (
    <section className="bg-[#151515] border border-[#2f2f2f] rounded-[10px] overflow-hidden flex-1 min-h-[100px]">
      <div className="h-11 flex items-center gap-[8px] px-3.5 border-b border-[#2a2a2a] text-[13px] font-extrabold">
        <Terminal size={18} className="text-[#148bff]" />
        LOG CONSOLE
      </div>

      <div className="h-full p-4 font-mono text-[11px] leading-[1.75] overflow-y-auto">
        {logs.length === 0 ? (
          <div className="h-[60px] flex items-center justify-center text-[#555] text-[12px]">
            No logs received yet
          </div>
        ) : (
          logs.map((log, index) => (
            <p key={index} className={getLogColor(log.level)}>
              {log.message}
            </p>
          ))
        )}
      </div>
    </section>
  );
}

function getLevel(level) {
  if (level === 10) return "debug";
  if (level === 20) return "info";
  if (level === 30) return "warn";
  if (level === 40) return "error";
  return "info";
}

function getLogColor(level) {
  if (level === "error") return "text-[#ff5b5b]";
  if (level === "warn")  return "text-[#ffc247]";
  if (level === "info")  return "text-[#32d884]";
  if (level === "debug") return "text-[#888]";
  return "text-[#cccccc]";
}