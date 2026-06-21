import { useEffect, useRef, useState } from "react";
import * as ROSLIB from "roslib";
import { ros } from "../services/ros";
import { TriangleAlert, X } from "lucide-react";

const LEFT_ENCODER_TOPIC = "/esibot/encoders/left";
const RIGHT_ENCODER_TOPIC = "/esibot/encoders/right";

export default function EncoderFaultAlarm() {
  const [alarm, setAlarm] = useState(false);
  const [message, setMessage] = useState("");

  const movingRef = useRef(false);
  const lastCmdTimeRef = useRef(0);

  const leftRef = useRef(null);
  const rightRef = useRef(null);
  const lastEncoderChangeRef = useRef(Date.now());

  const alarmAudioRef = useRef(null);

  useEffect(() => {
    alarmAudioRef.current = new Audio("/alarm.mp3");
    alarmAudioRef.current.loop = true;
    alarmAudioRef.current.volume = 0.7;
  }, []);

  useEffect(() => {
    const cmdTopic = new ROSLIB.Topic({
      ros,
      name: "/cmd_vel",
      messageType: "geometry_msgs/Twist",
    });

    const leftEncoderTopic = new ROSLIB.Topic({
      ros,
      name: LEFT_ENCODER_TOPIC,
      messageType: "std_msgs/Int32",
    });

    const rightEncoderTopic = new ROSLIB.Topic({
      ros,
      name: RIGHT_ENCODER_TOPIC,
      messageType: "std_msgs/Int32",
    });

    cmdTopic.subscribe((msg) => {
      const linear = Math.abs(msg.linear?.x || 0);
      const angular = Math.abs(msg.angular?.z || 0);

      movingRef.current = linear > 0.05 || angular > 0.05;

      if (movingRef.current) {
        lastCmdTimeRef.current = Date.now();
      } else {
        setAlarm(false);
        alarmAudioRef.current?.pause();
      }
    });

    leftEncoderTopic.subscribe((msg) => {
      const value = msg.data;

      if (leftRef.current !== null && value !== leftRef.current) {
        lastEncoderChangeRef.current = Date.now();
      }

      leftRef.current = value;
    });

    rightEncoderTopic.subscribe((msg) => {
      const value = msg.data;

      if (rightRef.current !== null && value !== rightRef.current) {
        lastEncoderChangeRef.current = Date.now();
      }

      rightRef.current = value;
    });

    const checker = setInterval(() => {
      const now = Date.now();

      const robotWasCommandedRecently = now - lastCmdTimeRef.current < 4000;
      const encodersFrozen = now - lastEncoderChangeRef.current > 2500;

      if (movingRef.current && robotWasCommandedRecently && encodersFrozen) {
        setMessage(
          "A movement command was sent, but wheel encoder feedback did not change. Possible motor stall, disconnected encoder, or mechanical blockage."
        );
        setAlarm(true);
        alarmAudioRef.current?.play().catch(() => {});
      }
    }, 500);

    return () => {
      cmdTopic.unsubscribe();
      leftEncoderTopic.unsubscribe();
      rightEncoderTopic.unsubscribe();
      clearInterval(checker);
      alarmAudioRef.current?.pause();
    };
  }, []);

  const closeAlarm = () => {
    setAlarm(false);
    alarmAudioRef.current?.pause();
  };

  if (!alarm) return null;

  return (
    <div className="fixed inset-0 z-[99999] bg-black/70 flex items-center justify-center px-4">
      <div className="w-full max-w-[460px] bg-[#2b1414] border border-[#ff5050] rounded-[22px] p-[26px] text-white shadow-[0_0_50px_rgba(255,80,80,0.35)]">
        <div className="flex items-start gap-4">
          <div className="w-[58px] h-[58px] rounded-[18px] bg-[#ff5050]/20 text-[#ff5050] grid place-items-center">
            <TriangleAlert size={34} />
          </div>

          <div className="flex-1">
            <h2 className="text-[22px] font-extrabold text-[#ff6b6b]">
              Encoder Motion Failure
            </h2>

            <p className="text-[13px] text-[#f5b5b5] mt-3 leading-6">
              {message}
            </p>
          </div>

          <button
            onClick={closeAlarm}
            className="text-[#ffb3b3] hover:text-white transition"
          >
            <X size={22} />
          </button>
        </div>

        <button
          onClick={closeAlarm}
          className="mt-6 w-full h-[42px] rounded-[12px] bg-[#ff5050] text-black font-extrabold hover:bg-[#ff7070] active:scale-[0.97] transition"
        >
          ACKNOWLEDGE
        </button>
      </div>
    </div>
  );
}