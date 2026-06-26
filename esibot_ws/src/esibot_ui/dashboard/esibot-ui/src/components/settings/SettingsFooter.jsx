import { Save, Zap } from "lucide-react";

export default function SettingsFooter({
  hasChanges,
  onSave,
  onCancel,
  onApply,
}) {
  if (!hasChanges) return null;

  return (
    <footer className="mt-auto h-[58px] bg-[#121212] border border-[#2a2a2a] rounded-[14px] py-[10px] px-[12px] flex items-center text-white shadow-[0_10px_25px_rgba(0,0,0,0.35)]">
      <div className="flex items-center gap-[4px] text-[12px] text-[#cfcfcf]">
        <span className="w-[8px] h-[8px] rounded-full bg-[#ffa927] shadow-[0_0_10px_rgba(255,169,39,0.9)]" />
        <span>
          You have <strong className="text-white">unsaved changes</strong> in
          Network settings
        </span>
      </div>

      <div className="ml-auto flex items-center gap-[8px]">
        <button
          onClick={onCancel}
          className="h-9 px-4 rounded-[8px] border border-[#3a3a3a] text-[#aaa] text-[12px]
          hover:bg-[#1d1d1d] hover:text-white
          active:scale-[0.96]
          hover:shadow-[0_0_10px_rgba(255,255,255,0.08)]
          transition-all duration-150"
        >
          Cancel
        </button>

        <button
          onClick={onApply}
          className="h-9 px-4 rounded-[8px] border border-[#0a7cff] bg-[#0a7cff18] text-[#148bff] text-[12px] font-bold flex items-center gap-2
          hover:bg-[#0a7cff28]
          hover:shadow-[0_0_14px_rgba(20,139,255,0.25)]
          active:scale-[0.96]
          transition-all duration-150"
        >
          <Zap size={13} />
          Apply
        </button>

        <button
          onClick={onSave}
          className="h-9 px-5 rounded-[8px] bg-[#148bff] text-white text-[12px] font-bold flex items-center gap-2
          shadow-[0_0_16px_rgba(20,139,255,0.45)]
          hover:bg-[#0f7ee8]
          hover:shadow-[0_0_20px_rgba(20,139,255,0.6)]
          active:scale-[0.96]
          transition-all duration-150"
        >
          <Save size={13} />
          Save Changes
        </button>
      </div>
    </footer>
  );
}