import { Video } from "lucide-react";

export default function CameraView() {
  const cameraConnected = false;

  return (
    <section>
      {/* HEADER */}
      <div className="flex items-center justify-between mb-3">
        <h2 className="flex items-center gap-[12px] text-[14px] font-bold text-white">
          <Video size={17} className="text-[#148bff]" />
          Main FPV Camera
        </h2>

<div className="flex items-center gap-4">
  <span
    className={`px-[4px] py-[2px] rounded-full border text-[10px] font-extrabold text-white ${
      cameraConnected
        ? "bg-[#1f4d2e] border-[#2f8f5b]"
        : "bg-[#3a2a10] border-[#7a5a20]"
    }`}
  >
    {cameraConnected ? "● LIVE" : "● OFFLINE"}
  </span>

  <span className="text-[11px] pl-[5px] text-[#9b9b9b]">
    {cameraConnected ? "1080p 60fps" : "No signal"}
  </span>
</div>
      </div>

      {/* CAMERA BOX */}
      <div className="h-[370px] rounded-[10px] overflow-hidden border border-[#263146] bg-[#050505] flex items-center justify-center">

        {cameraConnected ? (
          <img
            src=""
            alt="Camera Stream"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className=" flex items-center justify-center">
            
            {/* CONTENU CENTRÉ */}
            <div className="flex flex-col items-center text-center">

              {/* EVA FIX CENTRAGE */}
              <div className="flex items-center justify-center w-[150px] h-[150px] mb-4">
                <div className="translate-x-[8px] scale-[0.9]">
                  <EvaLoader />
                </div>
              </div>

              <h3 className="text-[17px] font-bold text-white">
                Camera stream unavailable
              </h3>

              <p className="text-[12px] text-[#888] mt-2">
                Waiting for ESP32-CAM video feed...
              </p>

            </div>

          </div>
        )}

        {/* Coins caméra */}
      
      </div>
    </section>
  );
}

function Corner({ className }) {
  return (
    <div
      className={`absolute w-[34px] h-[34px] border-[#d7e8ff] opacity-70 ${className}`}
    />
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