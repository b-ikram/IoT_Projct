import { Video } from "lucide-react";
import { useState, useEffect } from "react";
import * as ROSLIB from "roslib";
import { ros } from "../services/ros";

const RAW_TOPIC = "/camera_node/image_raw/compressed";
const CV_TOPIC = "/camera/image_annotated";

export default function CameraView() {
  const [mode, setMode] = useState("raw");
  const [imageSrc, setImageSrc] = useState(null);

  const topicName = mode === "cv" ? CV_TOPIC : RAW_TOPIC;
  const cameraConnected = imageSrc !== null;

useEffect(() => {
  setImageSrc(null);

  const topic = new ROSLIB.Topic({
    ros,
    name: topicName,
    messageType: "sensor_msgs/CompressedImage",
    queue_length: 1,
    throttle_rate: 150,
    compression: "none",
  });

  let lastUpdate = 0;
  let latestImage = null;
  let rafId = null;

  const renderLatest = () => {
    if (latestImage) {
      setImageSrc(latestImage);
      latestImage = null;
    }
    rafId = null;
  };

  topic.subscribe((msg) => {
    const now = Date.now();

    if (now - lastUpdate < 150) return;
    lastUpdate = now;

    latestImage = `data:image/jpeg;base64,${msg.data}`;

    if (!rafId) {
      rafId = requestAnimationFrame(renderLatest);
    }
  });

  return () => {
    topic.unsubscribe();

    if (rafId) {
      cancelAnimationFrame(rafId);
    }
  };
}, [topicName]);
  return (
    <section>
      {/* HEADER */}
      <div className="flex items-center justify-between mb-4 gap-3">
        <h2 className="flex items-center gap-3 text-[15px] font-bold text-white">
          <Video size={18} className="text-[#148bff]" />
          {mode === "cv" ? "Computer Vision Camera" : "Raw Camera Stream"}
        </h2>

        <div className="flex items-center gap-3">
          <div className="flex items-center bg-[#0f172a] border border-[#263146] rounded-[12px] p-1">
            <button
              onClick={() => setMode("raw")}
              className={`px-4 py-2 rounded-[10px] text-[12px] font-semibold transition-all duration-200 ${
                mode === "raw"
                  ? "bg-[#148bff] text-white shadow-md"
                  : "text-[#cbd5e1] hover:text-white"
              }`}
            >
              Stream
            </button>

            <button
              onClick={() => setMode("cv")}
              className={`px-4 py-2 rounded-[10px] text-[12px] font-semibold transition-all duration-200 ${
                mode === "cv"
                  ? "bg-[#148bff] text-white shadow-md"
                  : "text-[#cbd5e1] hover:text-white"
              }`}
            >
              Vision
            </button>
          </div>

          <div
            className={`px-4 py-2 rounded-[12px] border text-[11px] font-bold ${
              cameraConnected
                ? "bg-[#052e16] border-[#22c55e] text-[#86efac]"
                : "bg-[#2a1405] border-[#f97316] text-[#fdba74]"
            }`}
          >
            {cameraConnected ? "● LIVE" : "● OFFLINE"}
          </div>
        </div>
      </div>

      {/* VIDEO */}
      <div className="h-[500px] rounded-[14px] overflow-hidden border border-[#263146] bg-[#050505] flex items-center justify-center shadow-lg">
        {cameraConnected ? (
          <img
            src={imageSrc}
            alt="Camera Stream"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="flex flex-col items-center text-center">
            <div className="mb-4">
              <EvaLoader />
            </div>

            <h3 className="text-[17px] font-bold text-white">
              Camera stream unavailable
            </h3>

            <p className="text-[12px] text-[#888] mt-2">
              Waiting for{" "}
              {mode === "cv" ? "computer vision feed" : "raw camera feed"}...
            </p>
          </div>
        )}
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