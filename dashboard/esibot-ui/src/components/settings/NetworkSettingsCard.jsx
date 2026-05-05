import { Wifi, Eye } from "lucide-react";
import { useState } from "react";

export default function NetworkSettingsCard({ onChange }) {
  const [show, setShow] = useState(false);
  const [staticIP, setStaticIP] = useState(true);

  const [ssid, setSsid] = useState("EsiBot_Network_5G");
  const [password, setPassword] = useState("password123");
  const [rosUri, setRosUri] = useState("http://192.168.1.100:11311");
  const [websocketPort, setWebsocketPort] = useState("9090");

  const markChanged = () => {
    onChange?.();
  };

  const handleStaticIP = () => {
    setStaticIP((prev) => !prev);
    markChanged();
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
        <Field
          label="WIFI SSID"
          value={ssid}
          onChange={(value) => {
            setSsid(value);
            markChanged();
          }}
        />
{/* PASSWORD */}
<div>
  <label className="label">Password</label>

  <div className="relative">
    <input
      type={show ? "text" : "password"}
      value={password}
      onChange={(e) => {
        setPassword(e.target.value);
        markChanged();
      }}
      className="
        w-full
        bg-[#141414]
        text-[#e4e4e4]
        px-[14px] py-[10px]
        pr-[52px]
        rounded-[10px]
        border border-[#2a2a2a]
        focus:outline-none
        focus:border-[#0a7cff]
        hover:border-[#3a3a3a]
        transition
      "
    />

    <button
      type="button"
      onClick={() => setShow(!show)}
      className="
        absolute right-[8px] top-1/2 -translate-y-1/2
        h-[28px] w-[28px]
        flex items-center justify-center
        rounded-[8px]
        text-[#8a8a8a]
        bg-[#1a1a1a]
        border border-[#2a2a2a]
        hover:bg-[#222]
        hover:text-white
        active:scale-[0.92]
        transition-all duration-150
      "
    >
      <Eye size={14} />
    </button>
  </div>
</div>

        <Field
          label="ROS2 Master URI"
          value={rosUri}
          onChange={(value) => {
            setRosUri(value);
            markChanged();
          }}
        />

        {/* PORT + TEST */}
        <div className="grid grid-cols-[1fr_140px] gap-4 items-end">
          <Field
            label="WebSocket Port"
            value={websocketPort}
            noMargin
            onChange={(value) => {
              setWebsocketPort(value);
              markChanged();
            }}
          />

          <div>
            <label className="label">Test Connection</label>

           <button
  type="button"
  className="
    
    text-[11px]

    btn-test

    transition-all duration-150
    active:scale-[0.95]
    active:translate-y-[1px]
  "
>
  RUN TEST
</button>
          </div>
        </div>

        <div className="mt-5 border-t border-[#2a2a2a] pt-4"></div>

        {/* STATIC IP */}
        <div className="flex items-center justify-between bg-[#141414] border border-[#2a2a2a] rounded-[10px] px-[12px] ">
  
           <div className="flex flex-col gap-[2px]">
            <p className="text-[12px] font-semibold">Static IP</p>
            <p className="text-[10px] text-[#6e6e6e]">
              Use manual address configuration
            </p>
          </div>

          <button
            type="button"
            onClick={handleStaticIP}
            className={`switch ${staticIP ? "active" : ""}`}
          />
        </div>
      </div>
    </section>
  );
}
function Field({ label, value, onChange, noMargin }) {
  return (
    <div className={noMargin ? "" : "mb-[2px]"}>
      <label className="label">{label}</label>

      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="
          w-full
          bg-[#141414]
          text-[#e4e4e4]

          px-[14px] py-[10px]
          rounded-[10px]

          border border-[#2a2a2a]

          focus:outline-none
          focus:border-[#0a7cff]

          transition
        "
      />
    </div>
  );
}