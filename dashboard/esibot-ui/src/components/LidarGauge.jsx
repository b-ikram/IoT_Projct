import { Radio } from "lucide-react";

export default function LidarGauge() {
  const angle = 90; // change cette valeur plus tard avec ROS

  return (
    <section className="bg-[#2b2b2b] mt-[20px]  mb-[20px] border border-[#3a3a3a] rounded-[16px] p-[18px] text-white shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
      <div className="flex items-center justify-between mb-[8px]">
        <h3 className="flex items-center gap-[10px] text-[15px] font-extrabold">
          <Radio size={17} className="text-[#148bff]" />
          LIDAR Sweep
        </h3>

        <span className="text-[13px] text-[#aaa]">15 Hz</span>
      </div>

      <div className="relative h-[190px]">
        <svg viewBox="0 0 280 165" className="w-full h-full">
          {/* BACKGROUND ARC */}
          <path
            d="M 35 125 A 105 105 0 0 1 245 125"
            fill="none"
            stroke="#0b0b0b"
            strokeWidth="18"
            strokeLinecap="butt"
          />

          {/* PROGRESS ARC */}
          <path
            d="M 35 125 A 105 105 0 0 1 245 125"
            fill="none"
            stroke="#148bff"
            strokeWidth="18"
            strokeLinecap="butt"
            pathLength="100"
            strokeDasharray={`${(angle / 180) * 100} 100`}
          />

         

          <text x="32" y="140" fill="#ffffff" fontSize="11" textAnchor="middle">
            0
          </text>

        

          <text x="245" y="140" fill="#cccccc" fontSize="11" textAnchor="middle">
            180
          </text>
        </svg>

        <div className="absolute left-1/2 top-[58%] -translate-x-1/2 -translate-y-1/2 text-center">
          <p className="text-[11px] text-[#999]">Angle (°)</p>
          <strong className="block text-[30px] leading-none mt-1">
            {angle}
          </strong>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-[6px]">
        <div className="h-[38px] bg-[#111] rounded-[7px] px-[8px] flex items-center justify-between">
          <span className="text-[12px] text-[#8a8a8a]">MIN</span>
          <strong className="text-[13px]">0.4m</strong>
        </div>

        <div className="h-[38px] bg-[#111] rounded-[7px] px-[8px] flex items-center justify-between">
          <span className="text-[12px] text-[#8a8a8a]">MAX</span>
          <strong className="text-[13px]">12.0m</strong>
        </div>
      </div>
    </section>
  );
}