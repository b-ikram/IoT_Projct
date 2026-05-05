import { useState } from "react";
import Sidebar from "../components/Sidebar";
import Dashboard from "../pages/Dashboard";
import Settings from "../pages/Settings";
import MapPanel from "../components/MapPanel";
import LidarGauge from "../components/LidarGauge";
import Controls from "../components/Controls";

export default function MainLayout() {
  const [page, setPage] = useState("dashboard");

  return (
    <div className="h-screen w-screen bg-[#101010] text-white overflow-hidden">
      <div
        className={
          page === "dashboard"
            ? "grid h-full w-full grid-cols-[clamp(260px,17vw,300px)_minmax(0,1fr)_clamp(330px,24vw,420px)]"
            : "grid h-full w-full grid-cols-[clamp(260px,17vw,300px)_minmax(0,1fr)]"
        }
      >
        <Sidebar page={page} setPage={setPage} />

        <main className="min-w-0 h-full overflow-hidden">
          {page === "dashboard" ? <Dashboard /> : <Settings />}
        </main>

        {page === "dashboard" && (
          <aside className="min-w-0 h-full bg-[#202020] border-l border-[#303030] p-[14px] flex flex-col gap-4 overflow-y-auto overflow-x-hidden">
  <MapPanel />
  <LidarGauge />
  <Controls />
</aside>
        )}
      </div>
    </div>
  );
}


