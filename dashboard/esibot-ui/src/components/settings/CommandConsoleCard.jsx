import { Terminal } from "lucide-react";
import { useState, useEffect } from "react";
import { connectRaspberry, sendCommand, onMessage, offMessage } from "../../services/raspberrySocket";

export default function CommandConsoleCard() {
  const [input, setInput] = useState("");
  const [logs, setLogs] = useState([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    connectRaspberry({
      onOpen:  () => setConnected(true),
      onClose: () => setConnected(false),
      onError: () => setConnected(false),
    });

    const handler = (data) => {
      setLogs((prev) => [...prev, ...data.lines]);
    };

    onMessage("console", handler);

    return () => offMessage("console", handler);
  }, []);

  const handleExecute = () => {
    if (!input.trim()) return;
    if (input === "clear") { setLogs([]); setInput(""); return; }

    if (!connected) {
      setLogs((prev) => [...prev, "❌ Raspberry not connected"]);
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

        <span className={`ml-auto text-[10px] font-bold flex items-center gap-[5px] ${connected ? "text-[#50e38b]" : "text-[#ff5050]"}`}>
          <span className={`w-[6px] h-[6px] rounded-full ${connected ? "bg-[#50e38b]" : "bg-[#ff5050]"}`} />
          {connected ? "Connected" : "Disconnected"}
        </span>
      </div>

      <div className="bg-[#121212] border border-[#292929] rounded-[10px] overflow-hidden font-mono text-[12px]">
        <div className="p-4 px-[5px] min-h-[92px] text-[#a7a7a7] leading-6">
          {logs.length === 0 ? (
            <p className="text-[#555]">
              {connected ? "Ready — enter a command" : "⚠️ Waiting for Raspberry..."}
            </p>
          ) : (
            logs.map((log, i) => (
              <p key={i} className={
                log.startsWith(">") ? "text-[#50e38b]" :
                log.startsWith("❌") ? "text-[#ff5050]" : ""
              }>
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
            placeholder={connected ? "Enter ROS2 command..." : "Raspberry not connected..."}
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