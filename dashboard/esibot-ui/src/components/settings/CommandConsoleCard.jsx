import { Terminal } from "lucide-react";
import { useState } from "react";

export default function CommandConsoleCard() {
  const [input, setInput] = useState("");
  const [logs, setLogs] = useState([
   
  ]);

const handleExecute = () => {
  if (!input.trim()) return;

  if (input === "clear") {
    setLogs([]);
    setInput("");
    return;
  }

  setLogs((prev) => [...prev, `> ${input}`, "Running..."]);
  setInput("");
};

  return (
    <section className="bg-[#2b2b2b] border border-[#3a3a3a] rounded-[16px] p-[20px] text-white shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
      
      {/* HEADER */}
      <div className="flex items-center gap-[16px] mb-4">
        <div className="w-[34px] h-[34px] rounded-[10px] bg-[#10243a] border border-[#0a7cff55] text-[#148bff] grid place-items-center shadow-[0_0_12px_rgba(10,124,255,0.15)]">
          <Terminal size={17} />
        </div>

        <h3 className="text-[14px] font-bold">Command Console</h3>
      </div>

      {/* TERMINAL */}
      <div className="bg-[#121212] border border-[#292929] rounded-[10px] overflow-hidden font-mono text-[12px]">
        
        {/* LOGS */}
        <div className="p-4 px-[5px] min-h-[92px] text-[#a7a7a7] leading-6">
          {logs.map((log, i) => (
            <p key={i} className={log.startsWith(">") ? "text-[#50e38b]" : ""}>
              {log}
            </p>
          ))}
        </div>

        {/* INPUT */}
        <div className="h-[42px] border-t border-[#292929] bg-[#1b1b1b] flex items-center px-[4px]">
          <span className="text-[#50e38b] mr-2">&gt;</span>

          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 bg-transparent outline-none text-[#ccc] placeholder:text-[#555]"
            placeholder="Enter ROS2 command..."
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