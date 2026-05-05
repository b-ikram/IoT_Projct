import { Terminal } from "lucide-react";

export default function LogConsole({ logs = [] }) {
  return (
    <section className="bg-[#151515] border border-[#2f2f2f] rounded-[10px] overflow-hidden flex-1 min-h-[230px]">
      <div className="h-11 flex items-center gap-[8px] px-3.5 border-b border-[#2a2a2a] text-[13px] font-extrabold">
        <Terminal size={18} className="text-[#148bff]" />
        LOG CONSOLE
      </div>

      <div className="h-full p-4 font-mono text-[11px] leading-[1.75] overflow-y-auto">
        {logs.length === 0 ? (
          <div className="h-[160px] flex items-center justify-center text-[#555] text-[12px]">
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

function getLogColor(level) {
  if (level === "error") return "text-[#ff5b5b]";
  if (level === "warn") return "text-[#ffc247]";
  if (level === "info") return "text-[#32d884]";
  if (level === "debug") return "text-[#888]";
  return "text-[#cccccc]";
}