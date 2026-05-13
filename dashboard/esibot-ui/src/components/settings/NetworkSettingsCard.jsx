import { Wifi } from "lucide-react";
import { useState, useEffect } from "react";
import { connectRaspberry, sendCommand, onMessage, offMessage } from "../../services/raspberrySocket";

export default function NetworkSettingsCard() {
  const [ssid, setSsid] = useState("--");
  const [ip, setIp] = useState("--");
  const [rosbridgePort, setRosbridgePort] = useState("9090");
  const [websocketPort, setWebsocketPort] = useState("9091");
  const [testStatus, setTestStatus] = useState(null);

  useEffect(() => {
    connectRaspberry();

    const handler = (data) => {
      setSsid(data.ssid);
      setIp(data.ip);
      setRosbridgePort(data.rosbridge_port);
      setWebsocketPort(data.websocket_port);
    };

    onMessage("networkinfo", handler);

    sendCommand("networkinfo");

    return () => offMessage("networkinfo", handler);
  }, []);

  const handleTest = () => {
    setTestStatus("testing");
    sendCommand("status");
    setTimeout(() => setTestStatus("ok"), 1000);
  };

  return (
    <section className="bg-[#2b2b2b] border border-[#3a3a3a] rounded-[16px] p-[20px] text-white shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
      {/* HEADER */}
      <div className="flex items-center gap-[16px] mt-[0px] mb-[4px]">
        <div className="w-[40px] h-[40px] rounded-[12px] bg-[#10243a] text-[#148bff] grid place-items-center justify-center shadow-[0_0_12px_rgba(10,124,255,0.15)]">
          <Wifi size={18} />
        </div>

        <div>
          <h3 className="text-[17px] font-bold text-white mb-[0px] leading-tight">
            Network Settings
          </h3>
          <p className="text-[12px] text-[#7a7a7a] mt-[0px]">
            WiFi & Connectivity
          </p>
        </div>
      </div>

      {/* FIELDS */}
      <div className="flex flex-col gap-5">
        <ReadField label="WIFI SSID" value={ssid} />
        <ReadField label="Raspberry IP" value={ip} />
        <ReadField label="ROS2 Rosbridge Port" value={rosbridgePort} />

        {/* PORT + TEST */}
        <div className="grid grid-cols-[1fr_140px] gap-4 items-end">
          <ReadField label="WebSocket Port" value={websocketPort} noMargin />

          <div>
            <label className="label">Test Connection</label>
            <button
              type="button"
              onClick={handleTest}
              className={`
                btn-test text-[11px]
                transition-all duration-150
                active:scale-[0.95]
                active:translate-y-[1px]
                ${testStatus === "ok" ? "border-[#50e38b] text-[#50e38b]" : ""}
                ${testStatus === "testing" ? "opacity-60" : ""}
              `}
            >
              {testStatus === "testing" ? "TESTING..." : testStatus === "ok" ? "✓ OK" : "RUN TEST"}
            </button>
          </div>
        </div>

        <div className="mt-5 border-t border-[#2a2a2a] pt-4"></div>

        {/* STATIC IP */}
        <div className="flex items-center justify-between bg-[#141414] border border-[#2a2a2a] rounded-[10px] px-[12px] py-[10px]">
          <div className="flex flex-col gap-[2px]">
            <p className="text-[12px] font-semibold">Raspberry IP</p>
            <p className="text-[10px] text-[#6e6e6e]">
              {ip !== "--" ? ip : "Fetching..."}
            </p>
          </div>
          <span className={`text-[10px] font-bold px-[8px] py-[4px] rounded-full ${
            ip !== "--"
              ? "bg-[#1f4d2e] text-[#50e38b] border border-[#2f8f5b]"
              : "bg-[#3a2a10] text-[#ffa927] border border-[#7a5a20]"
          }`}>
            {ip !== "--" ? "● ONLINE" : "● WAITING"}
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
      <div className="
        w-full
        bg-[#141414]
        text-[#e4e4e4]
        px-[14px] py-[10px]
        rounded-[10px]
        border border-[#2a2a2a]
        text-[13px]
      ">
        {value}
      </div>
    </div>
  );
}