import CameraView from "../components/CameraView";
import LogConsole from "../components/LogConsole";
import StatusBar from "../components/StatusBar";

export default function Dashboard() {
  return (
    <div className="h-full flex flex-col bg-[#101010]">

      {/* CONTENU SCROLLABLE */}
      <div className="flex-1 overflow-y-auto p-[18px] flex flex-col gap-[16px]">
        <CameraView />
        <LogConsole />
      </div>

      {/* BAR FIX EN BAS */}
      <div className="p-[18px] pt-0">
        <StatusBar />
      </div>

    </div>
  );
}