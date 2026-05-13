import { Settings } from "lucide-react";

export default function SettingsHeader() {
  return (
    <header className="flex items-start justify-between">
      <div>
        <h2 className="flex items-center gap-[10px] mt-[0px] mb-[4px] text-[28px] font-extrabold text-white">
          <span className="w-[38px] h-[38px] rounded-[12px] bg-[#10243a] text-[#148bff] grid place-items-center justify-center shadow-[0_0_12px_rgba(10,124,255,0.15)]">
            <Settings size={15} />
          </span>
          Settings
        </h2>

        <p className="text-[11px] text-[#555] mt-[10px] ml-[5px]">
          Configure robot system and network
        </p>
      </div>
    </header>
  );
}