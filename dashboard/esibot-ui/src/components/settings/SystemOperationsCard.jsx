import { AlertTriangle, Power, RotateCcw, Play } from "lucide-react";
import { useState, useEffect } from "react";
import {
  connectRaspberry,
  sendCommand,
  onMessage,
  offMessage,
} from "../../services/raspberrySocket";

export default function SystemOperationsCard() {
  const [cpu, setCpu] = useState("--");
  const [uptime, setUptime] = useState("--");

  useEffect(() => {
    connectRaspberry();

    const sysHandler = (data) => {
      setCpu(`${data.cpu}% / ${data.temp || "N/A"}`);
    };

    const uptimeHandler = (data) => {
      setUptime(data.uptime || "--");
    };

    onMessage("sysinfo", sysHandler);
    onMessage("uptimeinfo", uptimeHandler);

    sendCommand("uptimeinfo");

    return () => {
      offMessage("sysinfo", sysHandler);
      offMessage("uptimeinfo", uptimeHandler);
    };
  }, []);

  const handleStartServices = () => {
    if (window.confirm("Start ROS services ?")) {
      sendCommand(
        "bash -c 'source /opt/ros/humble/setup.bash && source ~/esibot_ws/install/setup.bash && ros2 launch rosbridge_server rosbridge_websocket_launch.xml & sleep 2 && ros2 launch esibot_bringup esibot_driver.launch.py &'"
      );
    }
  };

  const handleReboot = () => {
    if (window.confirm("Reboot Raspberry Pi ?")) {
      sendCommand("sudo reboot");
    }
  };

  const handleShutdown = () => {
    if (window.confirm("Shutdown Raspberry Pi ?")) {
      sendCommand("sudo poweroff");
    }
  };

  return (
    <section className="bg-[#2b2b2b] border border-[#3a3a3a] rounded-[16px] p-[20px] text-white shadow-[0_10px_30px_rgba(0,0,0,0.35)] h-full">
      <div className="flex items-center gap-[16px] mb-[38px]">
        <div className="w-[40px] h-[40px] rounded-[12px] bg-[#10243a] border border-[#0a7cff55] text-[#148bff] grid place-items-center shadow-[0_0_14px_rgba(20,140,255,0.15)]">
          <AlertTriangle size={18} />
        </div>

        <div>
          <h3 className="text-[17px] font-bold text-white leading-tight">
            System Operations
          </h3>

          <p className="text-[12px] text-[#7a7a7a] mt-[2px]">
            ROS2 services & power control
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-[26px]">
        <Operation
          color="green"
          icon={<Play size={22} />}
          label="START SERVICES"
          onClick={handleStartServices}
        />

        <Operation
          color="yellow"
          icon={<RotateCcw size={22} />}
          label="REBOOT"
          onClick={handleReboot}
        />

        <Operation
          color="red"
          icon={<Power size={22} />}
          label="SHUTDOWN"
          onClick={handleShutdown}
        />
      </div>

      <div className="grid grid-cols-2 gap-3 mt-[34px]">
        <Metric label="CPU LOAD / TEMP" value={cpu} />
        <Metric label="SYSTEM UPTIME" value={uptime} />
      </div>
    </section>
  );
}

function Operation({ color, icon, label, onClick }) {
  const styles = {
    green: {
      box: `bg-[#244632] border-[#2e8f50] text-[#50e38b] hover:bg-[#2b573d] hover:shadow-[0_0_20px_rgba(80,227,139,0.3)]`,
    },
    yellow: {
      box: `bg-[#44351f] border-[#94651a] text-[#ffa927] hover:bg-[#503e23] hover:shadow-[0_0_20px_rgba(255,169,39,0.3)]`,
    },
    red: {
      box: `bg-[#442727] border-[#8f3737] text-[#ff5050] hover:bg-[#512d2d] hover:shadow-[0_0_20px_rgba(255,80,80,0.3)]`,
    },
  };

  return (
    <button
      type="button"
      onClick={onClick}
      className={`
        group relative h-[64px] w-full rounded-[10px] border
        flex flex-col items-center justify-center gap-[6px]
        transition-all duration-200 ease-out
        hover:scale-[1.02] active:scale-[0.96]
        ${styles[color].box}
      `}
    >
      <span className="transition-transform duration-200 group-hover:-translate-y-[2px]">
        {icon}
      </span>

      <span className="text-[10px] font-extrabold tracking-[0.5px]">
        {label}
      </span>

      <span className="absolute inset-0 rounded-[10px] opacity-0 group-hover:opacity-100 transition duration-300 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.08),transparent_70%)] pointer-events-none" />
    </button>
  );
}

function Metric({ label, value }) {
  return (
    <div className="relative h-[64px] rounded-[10px] bg-[#141414] border border-[#252525] px-[12px] py-3 flex flex-col justify-center transition-all duration-200 hover:border-[#3a3a3a] hover:bg-[#181818]">
      <span className="absolute inset-0 rounded-[10px] bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.04),transparent_70%)] pointer-events-none" />

      <span className="text-[9px] text-[#7a7a7a] font-bold tracking-[0.6px]">
        {label}
      </span>

      <strong className="text-[14px] text-white mt-[6px] font-extrabold tracking-[0.3px]">
        {value}
      </strong>
    </div>
  );
}