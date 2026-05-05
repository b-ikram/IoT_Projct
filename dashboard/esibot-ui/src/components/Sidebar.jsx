import {
  Bot,
  Home,
  Settings,
  Battery,
} from "lucide-react";

const level = 70;

const batteryColor =
  level > 70
    ? "text-[#50e38b]"
    : level > 30
    ? "text-[#ffa927]"
    : "text-[#ff5050]";

const batteryBg =
  level > 70
    ? "bg-[#50e38b]"
    : level > 30
    ? "bg-[#ffa927]"
    : "bg-[#ff5050]";

const batteryHealth =
  level > 70 ? "OK" : level > 30 ? "Low" : "Critical";

export default function Sidebar({ page, setPage }) {
  return (
    <aside className="h-full w-full bg-[#1E1E1E] border-r border-[#303030] px-[14px] py-[14px] flex flex-col text-white overflow-y-auto overflow-x-hidden">
      {/* HEADER */}
      <div className="flex items-center gap-[12px] px-[6px]">
        <div className="w-[38px] h-[38px] rounded-[10px] bg-gradient-to-br from-[#0b74ff] to-[#159bff] grid place-items-center shadow-[0_8px_20px_rgba(20,139,255,.35)]">
          <Bot size={22} strokeWidth={2.5} />
        </div>

        <div>
          <h1 className="text-[22px] mb-[0px] font-extrabold leading-[17px] tracking-[-0.4px]">
            EsiBot
          </h1>
          <p className="text-[10px] text-[#a8a8a8] font-bold tracking-[1.5px] mt-[3px]">
            COMMAND CENTER
          </p>
        </div>
      </div>

      {/* NAV */}
      <nav className="mt-[20px] flex flex-col gap-[8px]">
        <NavButton
          active={page === "dashboard"}
          onClick={() => setPage("dashboard")}
          icon={<Home size={16} />}
        >
          Dashboard
        </NavButton>

        <NavButton
          active={page === "settings"}
          onClick={() => setPage("settings")}
          icon={<Settings size={16} />}
        >
          Settings
        </NavButton>
      </nav>

      {/* POWER */}
      <div className="mt-[20px] rounded-[10px] bg-[#2c2c2c] border border-[#383838] px-[12px] py-[12px]">
        <div className="flex items-center justify-between">
          <h3 className="text-[10px] text-[#a7a7a7] tracking-[1.2px] font-extrabold">
            POWER
          </h3>

          <Battery size={15} className={batteryColor} />
        </div>

        <div className="flex items-end gap-[8px] mt-[8px]">
          <span className="text-[24px] font-extrabold">{level}%</span>
          <span className="text-[9px] text-[#969696] mb-[2px]">
            ~25 min
          </span>
        </div>

        <div className="h-[5px] bg-[#111] rounded-full overflow-hidden mt-[8px] mb-[8px]">
          <div
            className={`h-full rounded-full transition-all duration-300 ${batteryBg}`}
            style={{ width: `${level}%` }}
          />
        </div>

        <div className="grid grid-cols-2 gap-[6px]">
          <SmallBox label="Volt" value="11.1V" />
          <SmallBox label="Health" value={batteryHealth} green={level > 70} warning={level <= 70 && level > 30} error={level <= 30} />
        </div>
      </div>

      {/* NODE HEALTH */}
      <div className="mt-[14px] rounded-[12px] bg-[#2c2c2c] border border-[#383838] px-[14px] py-[14px]">
        <h3 className="text-[11px] text-[#a7a7a7] tracking-[1.3px] font-extrabold mb-[10px]">
          NODE HEALTH
        </h3>

        <div className="flex flex-col gap-[8px]">
          <Node name="esibot_driver" time="2ms" />
          <Node name="lidar_node" time="14ms" />
          <Node name="slam_toolbox" time="45ms" />
          <Node name="nav2" time="32ms" />
          <Node name="camera_node" time="TIMEOUT" error />
        </div>
      </div>
    </aside>
  );
}

function NavButton({ active, icon, children, onClick }) {
  return (
    <button onClick={onClick} className={`nav-btn ${active ? "nav-btn-active" : ""}`}>
      <span className="nav-icon">{icon}</span>
      <span>{children}</span>
    </button>
  );
}

function SmallBox({ label, value, green, warning, error }) {
  const color = green
    ? "text-[#54e88a]"
    : warning
    ? "text-[#ffa927]"
    : error
    ? "text-[#ff5050]"
    : "text-white";

  return (
    <div className="h-[42px] rounded-[7px] bg-[#111] px-[8px] py-[6px]">
      <span className="block text-[9px] text-[#7e7e7e]">{label}</span>
      <strong className={color}>{value}</strong>
    </div>
  );
}

function Node({ name, time, error }) {
  return (
    <div className="grid grid-cols-[16px_1fr_auto] items-center gap-[10px]">
      <span className="relative flex h-[16px] w-[16px] items-center justify-center">
        <span
          className={`absolute h-[14px] w-[14px] rounded-full blur-[5px] opacity-40 ${
            error ? "bg-[#ff5050]" : "bg-[#50e38b]"
          }`}
        />
        <span
          className={`relative h-[7px] w-[7px] rounded-full shadow-[0_0_8px_currentColor] ${
            error ? "bg-[#ff5050] text-[#ff5050]" : "bg-[#50e38b] text-[#50e38b]"
          }`}
        />
      </span>

      <span className="text-[11px] leading-none text-[#d7d7d7]">{name}</span>

      <span className={`text-[10px] leading-none ${error ? "text-[#ff5050]" : "text-[#9b9b9b]"}`}>
        {time}
      </span>
    </div>
  );
}