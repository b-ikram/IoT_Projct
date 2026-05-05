import { useEffect, useState } from "react";
import SettingsHeader from "../components/settings/SettingsHeader";
import NetworkSettingsCard from "../components/settings/NetworkSettingsCard";
import SystemOperationsCard from "../components/settings/SystemOperationsCard";
import CommandConsoleCard from "../components/settings/CommandConsoleCard";
import SettingsFooter from "../components/settings/SettingsFooter";

export default function Settings() {
  const [hasChanges, setHasChanges] = useState(false);
  const [lastSavedTime, setLastSavedTime] = useState(Date.now() - 2 * 60 * 1000);
  const [lastSavedLabel, setLastSavedLabel] = useState("2 min ago");

  useEffect(() => {
    const updateLabel = () => {
      const diffSeconds = Math.floor((Date.now() - lastSavedTime) / 1000);

      if (diffSeconds < 60) {
        setLastSavedLabel("just now");
      } else if (diffSeconds < 3600) {
        setLastSavedLabel(`${Math.floor(diffSeconds / 60)} min ago`);
      } else {
        setLastSavedLabel(`${Math.floor(diffSeconds / 3600)} h ago`);
      }
    };

    updateLabel();
    const interval = setInterval(updateLabel, 1000);

    return () => clearInterval(interval);
  }, [lastSavedTime]);

  const handleChange = () => {
    setHasChanges(true);
  };

  const handleSave = () => {
    setLastSavedTime(Date.now());
    setHasChanges(false);

    // Plus tard : envoyer les paramètres vers Raspberry / ROS ici
  };

  const handleCancel = () => {
    setHasChanges(false);
  };

  const handleApply = () => {
    console.log("Apply settings");
  };

  return (
    <div className="h-full bg-[#101010] text-white p-[22px] flex flex-col gap-[18px] overflow-auto">
      <SettingsHeader hasChanges={hasChanges} lastSaved={lastSavedLabel} />

      <div className="grid grid-cols-2 gap-[18px]">
        <NetworkSettingsCard onChange={handleChange} />
        <SystemOperationsCard />
      </div>

      <CommandConsoleCard />

      <SettingsFooter
        hasChanges={hasChanges}
        onSave={handleSave}
        onCancel={handleCancel}
        onApply={handleApply}
      />
    </div>
  );
}