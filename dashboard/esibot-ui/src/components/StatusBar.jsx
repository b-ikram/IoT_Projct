import { useState, useEffect } from "react";
import { connectRaspberry, sendCommand, onMessage, offMessage } from "../services/raspberrySocket";

export default function StatusBar() {
  const [mode, setMode] = useState("Mapping");
  const [cpu, setCpu] = useState("--");
  const [memory, setMemory] = useState("-- / -- GB");

  useEffect(() => {
    connectRaspberry();

    const handler = (data) => {
      setCpu(`${data.cpu}%`);
      setMemory(data.memory);
    };

    onMessage("sysinfo", handler);

    const interval = setInterval(() => {
      sendCommand("sysinfo");
    }, 3000);

    return () => {
      offMessage("sysinfo", handler);
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="h-[54px] bg-[#171717] border border-[#262626] rounded-[13px] px-[10px] flex items-center text-white">

      <div className="flex items-center gap-[20px] flex-1">
        <Stat label="CPU LOAD" value={cpu} />
        <Divider />
        <Stat label="MEMORY" value={memory} />
      </div>

      <div className="flex items-center">
        <span className="text-[10px] font-extrabold text-[#888] tracking-[0.5px] mr-[8px]">
          CURRENT MODE
        </span>

        <div className="flex bg-[#333333] border border-[#333333] p-[2px] rounded-[10px]">
          {["Mapping", "Navigation", "Idle"].map((item) => (
            <button
              key={item}
              onClick={() => setMode(item)}
              className={`h-[30px] px-[14px] text-[12px] font-semibold transition-all duration-150 ${
                mode === item
                  ? "bg-[#1E1E1E] border-transparent text-[#ffffff] rounded-[10px]"
                  : "bg-transparent border-transparent text-[#A0A0A0] hover:text-white"
              }`}
            >
              {item}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="flex flex-col justify-center">
      <span className="text-[10px] text-[#8a8a8a] font-extrabold tracking-[0.5px]">
        {label}
      </span>
      <strong className="text-[12px] text-white mt-[2px]">
        {value}
      </strong>
    </div>
  );
}

function Divider() {
  return (
    <div className="h-[28px] w-px bg-[#2a2a2a]" />
  );
}