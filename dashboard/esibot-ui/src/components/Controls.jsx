import { useState } from "react";
import {
  Gamepad2,
  ChevronUp,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Circle,
  AlertTriangle,
} from "lucide-react";

export default function Controls() {
  const [manual, setManual] = useState(false);

  return (
    <section className="bg-[#2b2b2b] border border-[#3a3a3a] rounded-[16px] p-[20px] flex-1 flex flex-col min-h-[390px] text-white shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
      {/* HEADER */}
      <div className="flex justify-between items-center">
        <h3 className="flex items-center gap-[10px] text-[15px] font-extrabold">
          <Gamepad2 size={18} className="text-[#148bff]" />
          Manual Override
        </h3>

        <button
          type="button"
          onClick={() => setManual(!manual)}
          className={`w-[44px] h-[24px] rounded-full relative transition-all duration-200 ${
            manual ? "bg-[#148bff]" : "bg-[#111]"
          }`}
        >
          <span
            className={`absolute top-[3px] w-[18px] h-[18px] rounded-full bg-[#bdbdbd] transition-all duration-200 ${
              manual ? "left-[23px] bg-white" : "left-[3px]"
            }`}
          />
        </button>
      </div>

      {/* CONTROLS */}
      <div className="flex-1 flex items-center justify-center">
        <div className="grid grid-cols-3 grid-rows-3 gap-[12px]">
          <ControlButton disabled={!manual} className="col-start-2 row-start-1">
            <ChevronUp size={30} />
          </ControlButton>

          <ControlButton disabled={!manual} className="col-start-1 row-start-2">
            <ChevronLeft size={30} />
          </ControlButton>

          <ControlButton
            disabled={!manual}
            active
            className="col-start-2 row-start-2"
          >
            <Circle size={20} />
          </ControlButton>

          <ControlButton disabled={!manual} className="col-start-3 row-start-2">
            <ChevronRight size={30} />
          </ControlButton>

          <ControlButton disabled={!manual} className="col-start-2 row-start-3">
            <ChevronDown size={30} />
          </ControlButton>
        </div>
      </div>

      {/* STOP */}
      <button
        type="button"
        className="h-[45px] mt-[20px] rounded-[14px] border border-[#ff50506b] bg-[#ff505021] text-[#ff5050] text-[20px] font-black tracking-[5px] flex items-center justify-center gap-[10px] hover:bg-[#ff505030] active:scale-[0.97] transition-all duration-150"
      >
        <AlertTriangle size={23} />
        STOP
      </button>
    </section>
  );
}

function ControlButton({ children, active, disabled, className = "" }) {
  return (
    <button
      type="button"
      disabled={disabled}
      className={`w-[68px] h-[68px] rounded-[14px] border border-[#252525] grid place-items-center transition-all duration-150
        ${
          active
            ? "bg-[#101010] text-[#148bff]"
            : "bg-[#171717] text-[#bdbdbd]"
        }
        ${
          disabled
            ? "opacity-45 cursor-not-allowed"
            : "hover:bg-[#202020] hover:text-white active:scale-[0.94]"
        }
        ${className}`}
    >
      {children}
    </button>
  );
}