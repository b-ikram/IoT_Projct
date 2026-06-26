import { useEffect, useState } from "react";
import Sidebar from "../components/Sidebar";
import Dashboard from "../pages/Dashboard";
import Settings from "../pages/Settings";
import MapPanel from "../components/MapPanel";
import LidarGauge from "../components/LidarGauge";
import Controls from "../components/Controls";
import EncoderFaultAlarm from "../components/EncoderFaultAlarm";

export default function MainLayout({ isAdmin }) {
  const [page, setPage] = useState("dashboard");
  const [showSidebar, setShowSidebar] = useState(false);
  const [showAside, setShowAside] = useState(false);

  useEffect(() => {
    if (!isAdmin && page === "settings") {
      setPage("dashboard");
    }
  }, [isAdmin, page]);

  return (
    <div className="h-screen w-screen bg-[#101010] text-white overflow-hidden">
      <div className="[@media(min-width:900px)]:hidden h-[48px] bg-[#1E1E1E] border-b border-[#303030] flex items-center justify-between px-4">
        <button
          onClick={() => setShowSidebar(!showSidebar)}
          className="text-white text-[20px]"
        >
          ☰
        </button>

        <span className="font-extrabold text-[14px]">EsiBot</span>

        {page === "dashboard" && (
          <button
            onClick={() => setShowAside(!showAside)}
            className="text-[#148bff] text-[12px] font-bold"
          >
            Controls
          </button>
        )}
      </div>

      {showSidebar && (
        <div className="[@media(min-width:900px)]:hidden fixed inset-0 z-50 flex">
          <div className="w-[280px] h-full overflow-y-auto">
            <Sidebar
  page={page}
  setPage={(p) => {
    setPage(p);
    setShowSidebar(false);
  }}
  isAdmin={isAdmin}
/>
          </div>
          <div
            className="flex-1 bg-black/50"
            onClick={() => setShowSidebar(false)}
          />
        </div>
      )}

      <div
        className={
          page === "dashboard"
            ? "[@media(min-width:900px)]:grid hidden h-full w-full grid-cols-[clamp(260px,17vw,300px)_minmax(0,1fr)_clamp(330px,24vw,420px)]"
            : "[@media(min-width:900px)]:grid hidden h-full w-full grid-cols-[clamp(260px,17vw,300px)_minmax(0,1fr)]"
        }
      >
        <Sidebar page={page} setPage={setPage} isAdmin={isAdmin} />

        <main className="min-w-0 h-full overflow-hidden">
          {page === "dashboard" ? <Dashboard /> : isAdmin ? <Settings /> : <Dashboard />}
        </main>

        {page === "dashboard" && (
          <aside className="min-w-0 h-full bg-[#202020] border-l border-[#303030] p-[14px] flex flex-col gap-4 overflow-y-auto overflow-x-hidden">
            <MapPanel isAdmin={isAdmin} />
            <LidarGauge />
            <Controls />
          </aside>
        )}
      </div>

      <div className="[@media(min-width:900px)]:hidden h-[calc(100vh-48px)] overflow-y-auto">
        {showAside && page === "dashboard" ? (
          <div className="p-4 flex flex-col gap-4">
            <MapPanel isAdmin={isAdmin} />
            <LidarGauge />
            <Controls />
          </div>
        ) : (
          <div className="h-full overflow-hidden">
            {page === "dashboard" ? <Dashboard /> : isAdmin ? <Settings /> : <Dashboard />}
          </div>
        )}
      </div>
         <EncoderFaultAlarm />
    </div>
  );
}