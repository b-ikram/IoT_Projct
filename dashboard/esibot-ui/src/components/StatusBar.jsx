import { useState, useEffect } from "react";
import { connectRaspberry, sendCommand, onMessage, offMessage } from "../services/raspberrySocket";

export default function StatusBar() {
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