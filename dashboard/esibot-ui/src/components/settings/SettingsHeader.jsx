import { Settings } from "lucide-react";

export default function SettingsHeader({ hasChanges, lastSaved }) {
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

      {hasChanges ? (
        <div className="flex items-center gap-[5px] text-[11px] mt-[4px]">
          <span className="w-[7px] h-[7px] rounded-full bg-[#ffa927] shadow-[0_0_8px_rgba(255,169,39,0.9)]" />
          <span className="text-[#ffa927] font-semibold">
            Unsaved changes
          </span>
        </div>
      ) : (
        <div className="flex items-center gap-[5px] text-[11px] text-[#888] mt-[4px]">
          <span className="w-[7px] h-[7px] rounded-full bg-[#50e38b] shadow-[0_0_8px_rgba(80,227,139,0.8)]" />
          <span>Last saved: {lastSaved}</span>
        </div>
      )}
    </header>
  );
}