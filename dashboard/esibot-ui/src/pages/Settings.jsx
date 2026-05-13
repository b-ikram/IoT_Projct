import SettingsHeader from "../components/settings/SettingsHeader";
import NetworkSettingsCard from "../components/settings/NetworkSettingsCard";
import SystemOperationsCard from "../components/settings/SystemOperationsCard";
import CommandConsoleCard from "../components/settings/CommandConsoleCard";

export default function Settings() {
  return (
    <div className="h-full bg-[#101010] text-white p-[22px] flex flex-col gap-[18px] overflow-auto">
      <SettingsHeader />

      <div className="grid grid-cols-2 gap-[18px]">
        <NetworkSettingsCard />
        <SystemOperationsCard />
      </div>

      <CommandConsoleCard />
    </div>
  );
}