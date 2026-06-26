import { Wifi } from "lucide-react";
import { useState, useEffect } from "react";
import {
  connectRaspberry,
  sendCommand,
  onMessage,
  offMessage,
} from "../../services/raspberrySocket";

export default function NetworkSettingsCard() {
  const [ip, setIp] = useState("--");
  const [rosbridgePort, setRosbridgePort] = useState("9090");
  const [websocketPort, setWebsocketPort] = useState("9091");
  const [testStatus, setTestStatus] = useState(null);

  useEffect(() => {
    connectRaspberry();

    const handler = (data) => {
      setIp(data.ip || "--");
      setRosbridgePort(data.rosbridge_port || "9090");
      setWebsocketPort(data.websocket_port || "9091");
    };

    onMessage("networkinfo", handler);
    sendCommand("networkinfo");

    return () => offMessage("networkinfo", handler);
  }, []);

  const handleTest = () => {
    setTestStatus("testing");
    sendCommand("status");

    setTimeout(() => {
      setTestStatus("ok");
    }, 1000);
  };

  const isOnline = ip !== "--";

  return (
    <section className="bg-[#2b2b2b] border border-[#3a3a3a] rounded-[16px] p-[20px] text-white shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
      <div className="flex items-center gap-[16px] mb-[18px]">
        <div className="w-[40px] h-[40px] rounded-[12px] bg-[#10243a] text-[#148bff] grid place-items-center shadow-[0_0_12px_rgba(10,124,255,0.15)]">
          <Wifi size={18} />
        </div>

        <div>
          <h3 className="text-[17px] font-bold text-white leading-tight">
            Network Settings
          </h3>

          <p className="text-[12px] text-[#7a7a7a] mt-[2px]">
            ROS2 & Network Configuration
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-5">
        <ReadField label="Raspberry IP" value={ip} />
        <ReadField label="ROS2 Rosbridge Port" value={rosbridgePort} />

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_140px] gap-4 items-end">
          <ReadField
            label="WebSocket Port"
            value={websocketPort}
            noMargin
          />

          <div className="w-full">
            <label className="label text-center lg:text-left block">
              Test Connection
            </label>

            <div className="w-full flex justify-center">
              <button
                type="button"
                onClick={handleTest}
                className={`
                  btn-test
                  w-[220px]
                  max-w-full
                  text-[11px]
                  transition-all duration-150
                  active:scale-[0.95]
                  active:translate-y-[1px]
                  ${
                    testStatus === "ok"
                      ? "border-[#50e38b] text-[#50e38b]"
                      : ""
                  }
                  ${testStatus === "testing" ? "opacity-60" : ""}
                `}
              >
                {testStatus === "testing"
                  ? "TESTING..."
                  : testStatus === "ok"
                  ? "✓ OK"
                  : "RUN TEST"}
              </button>
            </div>
          </div>
        </div>

        <div className="mt-5 border-t border-[#2a2a2a] pt-4"></div>

       <div className="flex flex-col items-center text-center gap-3 bg-[#141414] border border-[#2a2a2a] rounded-[10px] px-[12px] py-[18px]">
  <div className="flex flex-col items-center gap-[6px]">
    <p className="text-[12px] font-semibold">
      Connection Status
    </p>

    <p className="text-[10px] text-[#6e6e6e] max-w-[260px]">
      {isOnline
        ? `Connected to ${ip}`
        : "Waiting for Raspberry Pi connection..."}
    </p>
  </div>

  <span
    className={`w-fit text-[10px] font-bold px-[8px] py-[4px] rounded-full ${
      isOnline
        ? "bg-[#1f4d2e] text-[#50e38b] border border-[#2f8f5b]"
        : "bg-[#3a2a10] text-[#ffa927] border border-[#7a5a20]"
    }`}
  >
    {isOnline ? "● ONLINE" : "● WAITING"}
  </span>
</div>
      </div>
    </section>
  );
}

function ReadField({ label, value, noMargin }) {
  return (
    <div className={noMargin ? "" : "mb-[2px]"}>
      <label className="label">{label}</label>

      <div
        className="
          w-full
          bg-[#141414]
          text-[#e4e4e4]
          px-[14px]
          py-[10px]
          rounded-[10px]
          border
          border-[#2a2a2a]
          text-[13px]
        "
      >
        {value}
      </div>
    </div>
  );
}