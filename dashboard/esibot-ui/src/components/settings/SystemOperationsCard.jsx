import { AlertTriangle, Power, RotateCcw } from "lucide-react";

export default function SystemOperationsCard() {
  return (
    <section className="bg-[#2b2b2b] border border-[#3a3a3a] rounded-[16px] p-[20px] text-white shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
      {/* HEADER */}
      <div className="flex items-center gap-[16px] mb-[6px]">
        <div className="w-[38px] h-[38px] rounded-[10px] bg-[#10243a] border border-[#0a7cff55] text-[#148bff] grid place-items-center shadow-[0_0_14px_rgba(20,140,255,0.15)]">
          <AlertTriangle size={17} />
        </div>

        <h3 className="text-[15px] font-extrabold text-white">
          System Operations
        </h3>
      </div>

      {/* BUTTONS */}
      <div className="flex flex-col gap-[26px]">
        <Operation
          color="green"
          icon={<RotateCcw size={22} />}
          label="POWER ON"
        />

        <Operation
          color="yellow"
          icon={<RotateCcw size={22} />}
          label="REBOOT"
        />

        <Operation
          color="red"
          icon={<Power size={22} />}
          label="SHUTDOWN"
        />
      </div>

      {/* METRICS */}
      <div className="grid grid-cols-2 gap-3 mt-[26px]">
        <Metric label="CPU LOAD / TEMP" value="42% / 54°C" />
        <Metric label="STORAGE FREE" value="24.5 GB / 64 GB" />
      </div>
    </section>
  );
}
function Operation({ color, icon, label, onClick }) {
  const styles = {
    green: {
      box: `
        bg-[#244632] border-[#2e8f50] text-[#50e38b]
        hover:bg-[#2b573d]
        hover:shadow-[0_0_20px_rgba(80,227,139,0.3)]
      `,
    },
    yellow: {
      box: `
        bg-[#44351f] border-[#94651a] text-[#ffa927]
        hover:bg-[#503e23]
        hover:shadow-[0_0_20px_rgba(255,169,39,0.3)]
      `,
    },
    red: {
      box: `
        bg-[#442727] border-[#8f3737] text-[#ff5050]
        hover:bg-[#512d2d]
        hover:shadow-[0_0_20px_rgba(255,80,80,0.3)]
      `,
    },
  };

  return (
    <button
      type="button"
      onClick={onClick}
      className={`
        group
        h-[64px] w-full rounded-[10px] border
        flex flex-col items-center justify-center gap-[6px]

        transition-all duration-200 ease-out

        hover:scale-[1.02]
        active:scale-[0.96]

        ${styles[color].box}
      `}
    >
      {/* ICON avec animation */}
      <span className="transition-transform duration-200 group-hover:-translate-y-[2px]">
        {icon}
      </span>

      {/* TEXTE */}
      <span className="text-[10px] font-extrabold tracking-[0.5px]">
        {label}
      </span>

      {/* SHINE */}
      <span className="absolute inset-0 rounded-[10px] opacity-0 group-hover:opacity-100 transition duration-300 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.08),transparent_70%)] pointer-events-none" />
    </button>
  );
}

function Metric({ label, value }) {
  return (
    <div className="relative h-[64px] rounded-[10px] bg-[#141414] border border-[#252525] px-[12px] py-3 flex flex-col justify-center transition-all duration-200 hover:border-[#3a3a3a] hover:bg-[#181818]">

      {/* glow subtil */}
      <span className="absolute inset-0 rounded-[10px] bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.04),transparent_70%)] pointer-events-none" />

      {/* LABEL */}
      <span className="text-[9px] text-[#7a7a7a] font-bold tracking-[0.6px]">
        {label}
      </span>

      {/* VALUE */}
      <strong className="text-[14px] text-white mt-[6px] font-extrabold tracking-[0.3px]">
        {value}
      </strong>
    </div>
  );
}