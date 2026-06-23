import { useEffect, useRef, useState } from "react";
import * as ROSLIB from "roslib";
import { ros } from "../services/ros";
import { AlertTriangle, X, Volume2 } from "lucide-react";

const CMD_THRESHOLD = 0.05;
const SPEED_DROP_WINDOW_MS = 1500;
const ACK_SILENCE_MS = 5000;
const STARTUP_GRACE_MS = 3000;

export default function EncoderFaultAlarm() {
  const [alarm, setAlarm] = useState(false);
  const [message, setMessage] = useState("");

  const lastMovingTimeRef = useRef(0);
  const lastSpeedRef = useRef(0);
  const startupTimeRef = useRef(Date.now());
  const acknowledgeUntilRef = useRef(0);
  const alarmAudioRef = useRef(null);
  const alarmActiveRef = useRef(false);

  const startAlarmSound = () => {
    if (!alarmAudioRef.current) return;
    alarmAudioRef.current.currentTime = 0;
    alarmAudioRef.current.loop = true;
    alarmAudioRef.current.volume = 0.8;
    alarmAudioRef.current.play().catch(() => {});
  };

  const stopAlarmSound = () => {
    if (!alarmAudioRef.current) return;
    alarmAudioRef.current.pause();
    alarmAudioRef.current.currentTime = 0;
  };

  const triggerAlarm = () => {
    if (alarmActiveRef.current) return;

    alarmActiveRef.current = true;
    setMessage(
      "The robot velocity suddenly dropped to zero. Possible emergency stop, motor interruption, command loss, or safety stop."
    );
    setAlarm(true);
    startAlarmSound();
  };

  useEffect(() => {
    alarmAudioRef.current = new Audio("/alarm.mp3");

    return () => {
      stopAlarmSound();
    };
  }, []);

  useEffect(() => {
    const cmdTopic = new ROSLIB.Topic({
      ros,
      name: "/cmd_vel",
      messageType: "geometry_msgs/Twist",
    });

    cmdTopic.subscribe((msg) => {
      const linear = Math.abs(msg.linear?.x || 0);
      const angular = Math.abs(msg.angular?.z || 0);
      const speed = linear + angular;
      const now = Date.now();

      const startupGrace = now - startupTimeRef.current < STARTUP_GRACE_MS;
      const acknowledged = now < acknowledgeUntilRef.current;

      const wasMoving = lastSpeedRef.current > CMD_THRESHOLD;
      const nowStopped = speed <= CMD_THRESHOLD;
      const stoppedSuddenly =
        wasMoving &&
        nowStopped &&
        now - lastMovingTimeRef.current < SPEED_DROP_WINDOW_MS;

      if (!startupGrace && !acknowledged && stoppedSuddenly) {
        triggerAlarm();
      }

      if (speed > CMD_THRESHOLD) {
        lastMovingTimeRef.current = now;
      }

      lastSpeedRef.current = speed;
    });

    return () => {
      cmdTopic.unsubscribe();
      stopAlarmSound();
    };
  }, []);

  const closeAlarm = () => {
    acknowledgeUntilRef.current = Date.now() + ACK_SILENCE_MS;
    alarmActiveRef.current = false;
    setAlarm(false);
    stopAlarmSound();
  };

  const testAlarm = () => {
    triggerAlarm();
  };

  return (
    <>
      <button
        onClick={testAlarm}
        className="
          fixed bottom-4 right-4 z-[9998]
          h-[40px] px-4 rounded-[14px]
          bg-gradient-to-r from-[#351515] to-[#1d0d0d]
          border border-[#ff505055]
          text-[#ff7070] text-[11px] font-extrabold
          shadow-[0_0_18px_rgba(255,80,80,0.18)]
          hover:border-[#ff5050]
          hover:shadow-[0_0_24px_rgba(255,80,80,0.32)]
          transition active:scale-[0.97]
          flex items-center gap-2
        "
      >
        <AlertTriangle size={15} className="text-[#ffcc00]" />
        Test Alarm
      </button>

      {!alarm ? null : (
        <div className="fixed inset-0 z-[99999] bg-black/80 backdrop-blur-[4px] flex items-center justify-center px-4">
          <div className="relative w-full max-w-[520px] bg-[#241010] border border-[#ff5050] rounded-[26px] p-[30px] text-white shadow-[0_0_70px_rgba(255,80,80,0.42)] overflow-hidden">
            <div className="absolute -top-16 -right-16 w-[180px] h-[180px] rounded-full bg-[#ff5050]/10 blur-[8px]" />
            <div className="absolute -bottom-20 -left-20 w-[190px] h-[190px] rounded-full bg-[#ff5050]/10 blur-[10px]" />

            <div className="relative flex items-start gap-5">
              <div className="relative w-[72px] h-[72px] rounded-[22px] bg-[#ffcc00]/20 grid place-items-center shadow-[0_0_30px_rgba(255,204,0,0.35)] shrink-0">
                <span className="absolute inset-0 rounded-[22px] bg-[#ffcc00]/20 animate-ping z-0" />
                <AlertTriangle
                  size={44}
                  strokeWidth={2.8}
                  className="relative z-20 text-[#ffcc00] animate-pulse"
                />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <Volume2 size={18} className="text-[#ff7b7b]" />
                  <span className="text-[10px] text-[#ff9b9b] font-extrabold tracking-[1.6px]">
                    SAFETY ALERT
                  </span>
                </div>

                <h2 className="text-[24px] font-extrabold text-[#ff6b6b] mt-2">
                  Sudden Stop Detected
                </h2>

                <p className="text-[13px] text-[#f5b5b5] mt-3 leading-6">
                  {message}
                </p>

                <div className="mt-4 rounded-[14px] bg-[#120808] border border-[#ff505033] px-4 py-3">
                  <p className="text-[11px] text-[#ffb3b3] leading-5">
                    Recommended action: check motor driver, command source,
                    emergency stop condition, and robot power supply.
                  </p>
                </div>
              </div>

              <button
                onClick={closeAlarm}
                className="relative z-10 w-[34px] h-[34px] rounded-[10px] bg-[#1b0b0b] border border-[#ff505033] text-[#ffb3b3] hover:text-white hover:border-[#ff5050] transition grid place-items-center"
              >
                <X size={20} />
              </button>
            </div>

            <button
              onClick={closeAlarm}
              className="relative z-10 mt-7 w-full h-[46px] rounded-[15px] bg-[#ff5050] text-black font-extrabold hover:bg-[#ff7070] active:scale-[0.97] transition"
            >
              ACKNOWLEDGE
            </button>
          </div>
        </div>
      )}
    </>
  );
}