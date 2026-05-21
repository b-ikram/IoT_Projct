import { Radio } from "lucide-react";
import { useState, useEffect } from "react";
import * as ROSLIB from "roslib";
import { ros } from "../services/ros";

export default function LidarGauge() {
  const [angle, setAngle] = useState(0);

  useEffect(() => {
    try {
      const topic = new ROSLIB.Topic({
        ros,
        name: "/odom",
        messageType: "nav_msgs/Odometry",
      });

      topic.subscribe((msg) => {
        const qz = msg.pose.pose.orientation.z;
        const qw = msg.pose.pose.orientation.w;

        const yaw = 2 * Math.atan2(qz, qw);
        const degrees = ((yaw * 180 / Math.PI) % 360 + 360) % 360;
        setAngle(Math.round(degrees));
      });

      return () => topic.unsubscribe();
    } catch (e) {
      console.warn("IMU topic non disponible", e);
    }
  }, []);

  const cx = 140;
  const cy = 140;
  const r = 100;

  const toRad = (deg) => (deg * Math.PI) / 180;
  const startAngle = -90;
  const endAngle = startAngle + angle;

  const x1 = cx + r * Math.cos(toRad(startAngle));
  const y1 = cy + r * Math.sin(toRad(startAngle));
  const x2 = cx + r * Math.cos(toRad(endAngle));
  const y2 = cy + r * Math.sin(toRad(endAngle));

  const largeArc = angle > 180 ? 1 : 0;

  return (
    <section className="bg-[#2b2b2b] mt-[20px] mb-[20px] border border-[#3a3a3a] rounded-[16px] p-[18px] text-white shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
      <div className="flex items-center justify-between mb-[8px]">
        <h3 className="flex items-center gap-[10px] text-[15px] font-extrabold">
          <Radio size={17} className="text-[#148bff]" />
          IMU Heading
        </h3>
        <span className="text-[13px] text-[#aaa]">20 Hz</span>
      </div>

      <div className="relative h-[200px]">
        <svg viewBox="0 0 280 280" className="w-full h-full">

          <circle
            cx={cx}
            cy={cy}
            r={r}
            fill="none"
            stroke="#0b0b0b"
            strokeWidth="18"
          />

          {angle > 0 && angle < 360 && (
            <path
              d={`M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`}
              fill="none"
              stroke="#148bff"
              strokeWidth="18"
              strokeLinecap="butt"
            />
          )}

          {angle >= 360 && (
            <circle
              cx={cx}
              cy={cy}
              r={r}
              fill="none"
              stroke="#148bff"
              strokeWidth="18"
            />
          )}

          <text x={cx} y={cy - r - 12} fill="#ffffff" fontSize="11" textAnchor="middle">0°</text>
          <text x={cx + r + 12} y={cy + 4} fill="#cccccc" fontSize="11" textAnchor="start">90°</text>
          <text x={cx} y={cy + r + 18} fill="#cccccc" fontSize="11" textAnchor="middle">180°</text>
          <text x={cx - r - 12} y={cy + 4} fill="#cccccc" fontSize="11" textAnchor="end">270°</text>

          <text x={cx} y={cy - 8} fill="#999" fontSize="11" textAnchor="middle">Yaw (°)</text>
          <text x={cx} y={cy + 20} fill="#ffffff" fontSize="28" fontWeight="bold" textAnchor="middle">{angle}</text>

        </svg>
      </div>
    </section>
  );
}