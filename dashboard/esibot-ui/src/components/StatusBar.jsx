import { useState } from "react";

export default function StatusBar() {
  const [mode, setMode] = useState("Mapping");

  return (
    <div className="h-[54px] bg-[#171717] border border-[#262626] rounded-[13px] px-[10px] flex items-center text-white">

      {/* LEFT - STATS */}
      <div className="flex items-center gap-[20px] flex-1">

        <Stat label="SCAN RATE" value="15.4 Hz" />

        <Divider />

        <Stat label="CPU LOAD" value="42%" />

        <Divider />

        <Stat label="MEMORY" value="1.4 / 4 GB" />

      </div>

      {/* RIGHT - MODE */}
      <div className="flex items-center">

  <span className="text-[10px] font-extrabold text-[#888] tracking-[0.5px] mr-[8px] ">
    CURRENT MODE
  </span>

  <div className="flex bg-[#333333] border border-[#333333] p-[2px] rounded-[10px]">

    {["Mapping", "Navigation", "Idle"].map((item) => (
      <button
        key={item}
        onClick={() => setMode(item)}
        className={`h-[30px] px-[14px]  text-[12px] font-semibold transition-all duration-150 ${
          mode === item
            ? "bg-[#1E1E1E] border-transparent  text-[#ffffff] rounded-[10px] "
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