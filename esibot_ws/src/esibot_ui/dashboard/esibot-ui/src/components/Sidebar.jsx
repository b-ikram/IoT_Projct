import { Bot, Home, Settings, Battery } from "lucide-react";
import { useEffect, useState } from "react";
import * as ROSLIB from "roslib";
import { ros } from "../services/ros";
import { supabase } from "../services/supabaseClient";

const IGNORED_NODES = [
  "rosapi",
  "rosbridge",
  "rosout",
  "transform_listener",
  "lifecycle_manager",
];
export default function Sidebar({ page, setPage, isAdmin }) {

  const [level, setLevel] = useState(70);
  const [voltage, setVoltage] = useState(11.1);
  const [nodes, setNodes] = useState([]);

  useEffect(() => {
    const batteryTopic = new ROSLIB.Topic({
      ros,
      name: "/battery_state",
      messageType: "sensor_msgs/BatteryState",
    });

    batteryTopic.subscribe((msg) => {
      setLevel(Math.round((msg.percentage || 0) * 100));
      setVoltage(Number(msg.voltage || 0).toFixed(1));
    });

    return () => batteryTopic.unsubscribe();
  }, []);

  useEffect(() => {
    const nodesService = new ROSLIB.Service({
      ros,
      name: "/rosapi/nodes",
      serviceType: "rosapi_msgs/srv/Nodes",
    });

    const checkNodes = () => {
      nodesService.callService(
        {},
        (result) => {
          const activeNodes = result.nodes || [];

          const cleanNodes = activeNodes
            .map((nodeName) => nodeName.replace("/", ""))
            .filter(
              (nodeName) =>
                nodeName &&
                !IGNORED_NODES.some((ignored) =>
                  nodeName.toLowerCase().includes(ignored)
                )
            )
            .sort();

          setNodes(
            cleanNodes.map((name) => ({
              name,
              online: true,
              status: "ACTIVE",
            }))
          );
        },
        () => {
          setNodes([]);
        }
      );
    };

    checkNodes();
    const interval = setInterval(checkNodes, 2000);

    return () => clearInterval(interval);
  }, []);

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

  const batteryHealth = level > 70 ? "OK" : level > 30 ? "Low" : "Critical";

  return (
    <aside className="h-full w-full bg-[#1E1E1E] border-r border-[#303030] px-[14px] py-[14px] flex flex-col text-white overflow-y-auto overflow-x-hidden overflow-x-hidden ">
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

      <nav className="mt-[20px] flex flex-col gap-[8px]">
        <NavButton
          active={page === "dashboard"}
          onClick={() => setPage("dashboard")}
          icon={<Home size={16} />}
        >
          Dashboard
        </NavButton>

       {isAdmin && (
  <NavButton
    active={page === "settings"}
    onClick={() => setPage("settings")}
    icon={<Settings size={16} />}
  >
    Settings
  </NavButton>
)}
      </nav>

      <div className="mt-[20px] rounded-[10px] bg-[#2c2c2c] border border-[#383838] px-[12px] py-[12px]">
        <div className="flex items-center justify-between">
          <h3 className="text-[10px] text-[#a7a7a7] tracking-[1.2px] font-extrabold">
            POWER
          </h3>
          <Battery size={15} className={batteryColor} />
        </div>

        <div className="flex items-end gap-[8px] mt-[8px]">
          <span className="text-[24px] font-extrabold">{level}%</span>
          <span className="text-[9px] text-[#969696] mb-[2px]">~25 min</span>
        </div>

        <div className="h-[5px] bg-[#111] rounded-full overflow-hidden mt-[8px] mb-[8px]">
          <div
            className={`h-full rounded-full transition-all duration-300 ${batteryBg}`}
            style={{ width: `${level}%` }}
          />
        </div>

        <div className="grid grid-cols-2 gap-[6px]">
          <SmallBox label="Volt" value={`${voltage}V`} />
          <SmallBox
            label="Health"
            value={batteryHealth}
            green={level > 70}
            warning={level <= 70 && level > 30}
            error={level <= 30}
          />
        </div>
      </div>

   {isAdmin && (
  <div className="mt-[14px] rounded-[12px] bg-[#2c2c2c] border border-[#383838] px-[14px] py-[14px]">
    <div className="flex items-center justify-between mb-[10px]">
      <h3 className="text-[11px] text-[#a7a7a7] tracking-[1.3px] font-extrabold">
        NODE HEALTH
      </h3>

      <span className="text-[10px] text-[#50e38b] font-bold">
        {nodes.length} ACTIVE
      </span>
    </div>

    <div className="flex flex-col gap-[8px]">
      {nodes.length === 0 ? (
        <p className="text-[10px] text-[#777]">
          No active nodes detected
        </p>
      ) : (
        nodes.map((node) => (
          <Node
            key={node.name}
            name={node.name}
            status={node.status}
            error={!node.online}
          />
        ))
      )}
    </div>
  </div>
)}




<div className="mt-auto pt-4">
  <button
    onClick={() => supabase.auth.signOut()}
    className="
      w-full
      h-[46px]
      flex items-center justify-center gap-3
      rounded-[14px]
      border border-[#4a1d1d]
      bg-gradient-to-r from-[#2b1313] to-[#1d1010]
      text-[#ff6b6b]
      font-bold text-[13px]
      shadow-[0_0_15px_rgba(255,80,80,0.12)]
      hover:border-[#ff5050]
      hover:bg-[#351515]
      hover:shadow-[0_0_20px_rgba(255,80,80,0.25)]
      transition-all duration-300
      active:scale-[0.97]
    "
  >
    <svg
      className="w-[17px] h-[17px]"
      viewBox="0 0 512 512"
      fill="currentColor"
    >
      <path d="M377.9 105.9L500.7 228.7c7.2 7.2 11.3 17.1 11.3 27.3s-4.1 20.1-11.3 27.3L377.9 406.1c-6.4 6.4-15 9.9-24 9.9c-18.7 0-33.9-15.2-33.9-33.9l0-62.1-128 0c-17.7 0-32-14.3-32-32l0-64c0-17.7 14.3-32 32-32l128 0 0-62.1c0-18.7 15.2-33.9 33.9-33.9c9 0 17.6 3.6 24 9.9zM160 96L96 96c-17.7 0-32 14.3-32 32l0 256c0 17.7 14.3 32 32 32l64 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l-64 0c-53 0-96-43-96-96L0 128C0 75 43 32 96 32l64 0c17.7 0 32 14.3 32 32s-14.3 32-32 32z" />
    </svg>

    <span className="w-2 h-2 rounded-full bg-[#ff5050] animate-pulse" />
<span>Logout</span>
  </button>
</div>
    </aside>
  );
}

function NavButton({ active, icon, children, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`nav-btn ${active ? "nav-btn-active" : ""}`}
    >
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

function Node({ name, status, error }) {
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
            error
              ? "bg-[#ff5050] text-[#ff5050]"
              : "bg-[#50e38b] text-[#50e38b]"
          }`}
        />
      </span>

      <span className="text-[11px] leading-none text-[#d7d7d7] truncate">
        {name}
      </span>

      <span
        className={`text-[10px] leading-none font-bold ${
          error ? "text-[#ff5050]" : "text-[#50e38b]"
        }`}
      >
        {status}
      </span>
    </div>
  );
}