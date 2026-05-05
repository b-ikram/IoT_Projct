import { Crosshair, MapPin } from "lucide-react";
import { useState } from "react";

export default function MapPanel() {
  const [selectingGoal, setSelectingGoal] = useState(false);
  const [goal, setGoal] = useState(null);
const [robot, setRobot] = useState({ x: 12, y: 150 });
  const handleMapClick = (e) => {
    if (!selectingGoal) return;

    const rect = e.currentTarget.getBoundingClientRect();

    const x = ((e.clientX - rect.left) / rect.width) * 360;
    const y = ((e.clientY - rect.top) / rect.height) * 230;

    setGoal({ x, y });
    setSelectingGoal(false);
  };

  return (
    <section className="bg-[#2b2b2b] border border-[#3a3a3a] rounded-[16px] p-[18px] text-white shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
      <div className="flex items-center justify-between mb-[18px]">
        <h3 className="flex items-center gap-[10px] text-[15px] font-extrabold">
          <Crosshair size={18} className="text-white" />
          Real-time SLAM Map
        </h3>

        <button
          onClick={() => setSelectingGoal(true)}
          className={`h-[42px] px-[18px] rounded-[10px] text-[#ffffff] text-[14px] font-bold border-transparent active:scale-[0.96] transition-all ${
            selectingGoal
              ? "bg-[#ffa927] shadow-[0_0_14px_rgba(255,169,39,0.35)]"
              : "bg-[#148bff] shadow-[0_0_14px_rgba(20,139,255,0.35)] hover:bg-[#0f7ee8]"
          }`}
        >
          {selectingGoal ? "Click Map" : "Set Goal"}
        </button>
      </div>

      <div
        onClick={handleMapClick}
        className={`h-[230px] bg-[#101010] rounded-[14px] overflow-hidden relative ${
          selectingGoal ? "cursor-crosshair ring-1 ring-[#ffa927]" : ""
        }`}
      >
        <svg viewBox="0 0 360 230" className="w-full h-full">
          <path
            d="M55 88 C92 34 145 55 177 112 S245 203 290 151 S312 58 323 25"
            fill="none"
            stroke="#148bff"
            strokeWidth="3"
            strokeDasharray="7 9"
            opacity="0.75"
          />

          <rect x="225" y="92" width="70" height="84" fill="#1d1d1d" opacity="0.95" />

          <ellipse
            cx="192"
            cy="110"
            rx="15"
            ry="8"
            fill="#343434"
            opacity="0.9"
            transform="rotate(-20 192 110)"
          />

          <circle cx={robot.x} cy={robot.y}  r="17" fill="#06264a" stroke="#148bff" strokeWidth="2" />
          <circle cx={robot.x} cy={robot.y}  r="9" fill="none" stroke="#148bff" strokeWidth="2" />
          <circle cx={robot.x} cy={robot.y}  fill="#148bff" />

          <path
  d={`M ${robot.x} ${robot.y - 7} L ${robot.x + 6} ${robot.y} L ${robot.x} ${robot.y + 7}`}
  fill="none"
  stroke="#148bff"
  strokeWidth="2"
  strokeLinecap="round"
  strokeLinejoin="round"
/>

          {goal && (
            <g>
              <circle
                cx={goal.x}
                cy={goal.y}
                r="12"
                fill="rgba(255,169,39,0.18)"
                stroke="#ffa927"
                strokeWidth="2"
              />
              <circle cx={goal.x} cy={goal.y} r="4" fill="#ffa927" />
              <path
                d={`M ${goal.x} ${goal.y - 18} L ${goal.x} ${goal.y + 18} M ${goal.x - 18} ${goal.y} L ${goal.x + 18} ${goal.y}`}
                stroke="#ffa927"
                strokeWidth="2"
                opacity="0.8"
              />
            </g>
          )}
        </svg>

        {selectingGoal && (
          <div className="absolute left-3 top-3 px-3 py-1.5 rounded-full bg-[#ffa92722] border border-[#ffa92755] text-[#ffa927] text-[11px] font-bold">
            Select destination
          </div>
        )}
      </div>

      <div className="flex items-center justify-between mt-[14px] text-[12px] text-[#9a9a9a]">
        <span>Odometry Drift: 0.02m</span>

        <em className={selectingGoal ? "text-[#ffa927]" : ""}>
          {goal
            ? `Goal set: x=${goal.x.toFixed(0)}, y=${goal.y.toFixed(0)}`
            : "Click on map to set navigation goal"}
        </em>
      </div>
    </section>
  );
}