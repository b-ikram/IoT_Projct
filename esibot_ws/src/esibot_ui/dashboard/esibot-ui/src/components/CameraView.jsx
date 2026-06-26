import { Video } from "lucide-react";
import { useMemo, useState } from "react";

const RPI_IP = "172.20.10.8";
const IDRIS_LAPTOP_IP = "172.20.10.8";

const RAW_STREAM_URL = `http://${RPI_IP}:8080/stream?topic=/camera_node/image_raw&type=ros_compressed`;
const CV_STREAM_URL = `http://${IDRIS_LAPTOP_IP}:8080/stream?topic=/camera_node/image_annotated&type=ros_compressed`;

export default function CameraView() {
  const [mode, setMode] = useState("raw");
  const [isLoaded, setIsLoaded] = useState(false);

  const imageSrc = useMemo(() => {
    return mode === "cv" ? CV_STREAM_URL : RAW_STREAM_URL;
  }, [mode]);

  const title = mode === "cv" ? "Computer Vision Camera" : "Raw Camera Stream";

  const handleModeChange = (newMode) => {
    setIsLoaded(false);
    setMode(newMode);
  };

  return (
    <section>
      <div className="flex items-center justify-between gap-8 mb-6">
        <h2 className="flex items-center text-[15px] font-bold">
          <span className="inline-flex w-[34px] min-w-[34px] justify-center">
            <Video size={20} strokeWidth={2.5} className="text-[#148bff]" />
          </span>

          <span className="pl-[8px]">{title}</span>
        </h2>

        <div className="flex items-center gap-[22px]">
          <div className="flex items-center gap-2 rounded-[16px] bg-[#111] border border-[#2a2a2a] p-[4px]">
            <button
              onClick={() => handleModeChange("raw")}
              className={`px-4 py-[5px] rounded-[12px] text-[12px] font-semibold transition-all duration-200 ${
                mode === "raw"
                  ? "bg-[#148bff] text-black shadow-md"
                  : "bg-white text-black hover:bg-[#e8e8e8]"
              }`}
            >
              Stream
            </button>

            <button
              onClick={() => handleModeChange("cv")}
              className={`px-4 py-[5px] rounded-[12px] text-[12px] font-semibold transition-all duration-200 ${
                mode === "cv"
                  ? "bg-[#148bff] text-black shadow-md"
                  : "bg-white text-black hover:bg-[#e8e8e8]"
              }`}
            >
              Vision
            </button>
          </div>

          <div
            className={`px-4 py-[5px] rounded-[14px] border text-[11px] font-bold whitespace-nowrap ${
              isLoaded
                ? "bg-[#052e16] border-[#22c55e] text-[#86efac]"
                : "bg-[#2a1405] border-[#f97316] text-[#fdba74]"
            }`}
          >
            {isLoaded ? "● LIVE" : "● LOADING"}
          </div>
        </div>
      </div>

      <div className="h-[500px] rounded-[14px] overflow-hidden border border-[#263146] bg-[#050505] flex items-center justify-center shadow-lg relative">
        {!isLoaded && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center bg-[#050505] z-10">
            <div className="mb-4">
              <EvaLoader />
            </div>

            <h3 className="text-[17px] font-bold text-white">
              Camera stream loading
            </h3>

            <p className="text-[12px] text-[#888] mt-2">
              Waiting for {mode === "cv" ? "computer vision feed" : "raw camera feed"}...
            </p>
          </div>
        )}

        <img
          key={imageSrc}
          src={imageSrc}
          alt="Camera Stream"
          onLoad={() => setIsLoaded(true)}
          onError={() => setIsLoaded(false)}
          className="w-full h-full object-cover"
        />
      </div>
    </section>
  );
}

function EvaLoader() {
  return (
    <div className="eva-modelViewPort">
      <div className="eva-model">
        <div className="eva-head">
          <div className="eva-eyeChamber">
            <div className="eva-eye"></div>
            <div className="eva-eye"></div>
          </div>
        </div>

        <div className="eva-body">
          <div className="eva-hand"></div>
          <div className="eva-hand"></div>
          <div className="eva-scannerThing"></div>
          <div className="eva-scannerOrigin"></div>
        </div>
      </div>
    </div>
  );
}