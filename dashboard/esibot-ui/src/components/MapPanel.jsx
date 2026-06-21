import { useEffect, useRef, useState } from "react";
import * as ROSLIB from "roslib";
import { ros } from "../services/ros";
import { Crosshair, Maximize2, Navigation, X } from "lucide-react";

const goalTopic = new ROSLIB.Topic({
  ros,
  name: "/goal_pose",
  messageType: "geometry_msgs/PoseStamped",
});

export default function MapPanel({ isAdmin }) {
  const canvasRef = useRef(null);
  const mapInfoRef = useRef(null);
  const mapDataRef = useRef(null);
  const robotPosRef = useRef({ x: 0, y: 0, yaw: 0 });
  const targetRef = useRef(null);
  const drawMapRef = useRef(null);

  const [robotPos, setRobotPos] = useState({ x: 0, y: 0, yaw: 0 });
  const [target, setTarget] = useState(null);
  const [mapSize, setMapSize] = useState("--");
  const [mapReceived, setMapReceived] = useState(false);

  useEffect(() => {
    const drawMap = () => {
      const canvas = canvasRef.current;
      const mapData = mapDataRef.current;
      const info = mapInfoRef.current;

      if (!canvas || !mapData || !info) return;

      canvas.width = mapData.width;
      canvas.height = info.height;

      const ctx = canvas.getContext("2d");
      ctx.imageSmoothingEnabled = false;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      for (let i = 0; i < mapData.data.length; i++) {
        const val = mapData.data[i];
        const x = i % mapData.width;
        const y = Math.floor(i / mapData.width);

        if (val === -1) ctx.fillStyle = "#0f172a";
        else if (val === 0) ctx.fillStyle = "#f8fafc";
        else ctx.fillStyle = "#148bff";

        ctx.fillRect(x, info.height - y - 1, 1, 1);
      }

      const rx =
        (robotPosRef.current.x - info.origin.position.x) / info.resolution;
      const ry =
        info.height -
        (robotPosRef.current.y - info.origin.position.y) / info.resolution;

      ctx.beginPath();
      ctx.arc(rx, ry, 4, 0, 2 * Math.PI);
      ctx.fillStyle = "#ff3b30";
      ctx.fill();

      ctx.beginPath();
      ctx.moveTo(rx, ry);
      ctx.lineTo(
        rx + Math.cos((robotPosRef.current.yaw * Math.PI) / 180) * 12,
        ry - Math.sin((robotPosRef.current.yaw * Math.PI) / 180) * 12
      );
      ctx.strokeStyle = "#ff3b30";
      ctx.lineWidth = 1;
      ctx.stroke();

      if (isAdmin && targetRef.current) {
        const tx =
          (targetRef.current.x - info.origin.position.x) / info.resolution;
        const ty =
          info.height -
          (targetRef.current.y - info.origin.position.y) / info.resolution;

        ctx.beginPath();
        ctx.arc(tx, ty, 5, 0, 2 * Math.PI);
        ctx.fillStyle = "#50e38b";
        ctx.fill();

        ctx.beginPath();
        ctx.moveTo(tx - 8, ty);
        ctx.lineTo(tx + 8, ty);
        ctx.moveTo(tx, ty - 8);
        ctx.lineTo(tx, ty + 8);
        ctx.strokeStyle = "#50e38b";
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    };

    drawMapRef.current = drawMap;

    const mapTopic = new ROSLIB.Topic({
      ros,
      name: "/map_web",
      messageType: "nav_msgs/OccupancyGrid",
      throttle_rate: 500,
      queue_length: 1,
    });

    mapTopic.subscribe((msg) => {
      const { width, height, resolution, origin } = msg.info;

      mapInfoRef.current = { width, height, resolution, origin };
      mapDataRef.current = { data: msg.data, width, height };

      setMapSize(`${width}x${height}`);
      setMapReceived(true);

      requestAnimationFrame(drawMap);
    });

    const odomTopic = new ROSLIB.Topic({
      ros,
      name: "/odometry/filtered",
      messageType: "nav_msgs/Odometry",
      throttle_rate: 200,
      queue_length: 1,
    });

    odomTopic.subscribe((msg) => {
      const qz = msg.pose.pose.orientation.z;
      const qw = msg.pose.pose.orientation.w;

      const yaw = ((2 * Math.atan2(qz, qw) * 180) / Math.PI + 360) % 360;

      const pos = {
        x: msg.pose.pose.position.x,
        y: msg.pose.pose.position.y,
        yaw,
      };

      robotPosRef.current = pos;
      setRobotPos(pos);

      requestAnimationFrame(drawMap);
    });

    return () => {
      mapTopic.unsubscribe();
      odomTopic.unsubscribe();
    };
  }, [isAdmin]);

  const getWorldPointFromCanvasClick = (event, canvas, info) => {
    const rect = canvas.getBoundingClientRect();

    const canvasRatio = canvas.width / canvas.height;
    const rectRatio = rect.width / rect.height;

    let displayedWidth = rect.width;
    let displayedHeight = rect.height;
    let offsetX = 0;
    let offsetY = 0;

    if (rectRatio > canvasRatio) {
      displayedHeight = rect.height;
      displayedWidth = displayedHeight * canvasRatio;
      offsetX = (rect.width - displayedWidth) / 2;
    } else {
      displayedWidth = rect.width;
      displayedHeight = displayedWidth / canvasRatio;
      offsetY = (rect.height - displayedHeight) / 2;
    }

    const clickX = event.clientX - rect.left - offsetX;
    const clickY = event.clientY - rect.top - offsetY;

    if (
      clickX < 0 ||
      clickY < 0 ||
      clickX > displayedWidth ||
      clickY > displayedHeight
    ) {
      return null;
    }

    const pixelX = (clickX / displayedWidth) * canvas.width;
    const pixelY = (clickY / displayedHeight) * canvas.height;

    return {
      x: pixelX * info.resolution + info.origin.position.x,
      y: (info.height - pixelY) * info.resolution + info.origin.position.y,
    };
  };

  const handleCanvasClick = (event) => {
    if (!isAdmin) return;

    const canvas = canvasRef.current;
    const info = mapInfoRef.current;
    const mapData = mapDataRef.current;

    if (!canvas || !info || !mapData) return;

    const newTarget = getWorldPointFromCanvasClick(event, canvas, info);

    if (!newTarget) return;

    targetRef.current = newTarget;
    setTarget(newTarget);

    requestAnimationFrame(drawMapRef.current);
  };

  const publishGoal = (goal) => {
    if (!goal || !isAdmin) return;

    goalTopic.publish({
      header: {
        frame_id: "map",
      },
      pose: {
        position: {
          x: goal.x,
          y: goal.y,
          z: 0.0,
        },
        orientation: {
          x: 0.0,
          y: 0.0,
          z: 0.0,
          w: 1.0,
        },
      },
    });
  };

  const handleSendGoal = () => {
    publishGoal(target);
  };

  const handleClearTarget = () => {
    targetRef.current = null;
    setTarget(null);
    requestAnimationFrame(drawMapRef.current);
  };

  const handleExpand = () => {
    const win = window.open("", "_blank", "width=1200,height=800");

    const adminPanelHtml = isAdmin
      ? `
    <div>
      <div class="panel-title">Navigation Target</div>
      <div class="panel-sub">Click on the SLAM map to select a goal, then send it to ROS2 navigation.</div>
    </div>

    <div class="pos-row">
      <div class="pos-box"><span class="pos-label">TARGET X</span><strong id="target-x" class="pos-value">--</strong></div>
      <div class="pos-box"><span class="pos-label">TARGET Y</span><strong id="target-y" class="pos-value">--</strong></div>
    </div>

    <div class="btn-row">
      <button id="send" disabled>SEND GOAL</button>
      <button id="clear">CLEAR</button>
    </div>
    `
      : "";

    const adminScript = isAdmin
      ? `
canvas.addEventListener('click', function(event){
  var point = getWorldPoint(event);
  if (!point) return;

  target = point;

  document.getElementById('target-x').textContent = target.x.toFixed(2) + 'm';
  document.getElementById('target-y').textContent = target.y.toFixed(2) + 'm';
  document.getElementById('send').disabled = false;

  requestAnimationFrame(drawMap);
});

document.getElementById('clear').addEventListener('click', function(){
  target = null;
  document.getElementById('target-x').textContent = '--';
  document.getElementById('target-y').textContent = '--';
  document.getElementById('send').disabled = true;
  requestAnimationFrame(drawMap);
});

document.getElementById('send').addEventListener('click', function(){
  if (!target) return;

  goalTopic.publish({
    header: { frame_id: 'map' },
    pose: {
      position: { x: target.x, y: target.y, z: 0.0 },
      orientation: { x: 0.0, y: 0.0, z: 0.0, w: 1.0 }
    }
  });
});
`
      : "";

    win.document.write(`<!DOCTYPE html>
<html>
<head>
<title>SLAM Map</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{background:#101010;color:white;font-family:sans-serif;overflow:hidden;}
#header{height:76px;background:#171717;display:flex;align-items:center;padding:0 28px;border-bottom:1px solid #333;justify-content:space-between;}
#header h1{font-size:26px;font-weight:900;}
#layout{width:100vw;height:calc(100vh - 76px);display:grid;grid-template-columns:1fr 300px;gap:16px;padding:18px;background:#101010;}
#map-wrapper{width:100%;height:100%;display:flex;align-items:center;justify-content:center;background:#0b0b0b;border:1px solid #222;border-radius:18px;overflow:hidden;}
#map-canvas{image-rendering:pixelated;width:100%;height:100%;object-fit:contain;cursor:${isAdmin ? "crosshair" : "default"};}
#side{background:#171717;border:1px solid #2a2a2a;border-radius:16px;padding:16px;display:flex;flex-direction:column;gap:14px;}
.pos-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
.pos-box{background:#111;border:1px solid #252525;padding:10px 12px;border-radius:10px;}
.pos-label{font-size:9px;color:#888;display:block;margin-bottom:6px;}
.pos-value{color:#148bff;font-size:14px;font-weight:800;}
.panel-title{font-size:13px;font-weight:900;margin-bottom:4px;}
.panel-sub{font-size:10px;color:#777;line-height:14px;}
.btn-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
button{height:36px;border-radius:9px;border:none;font-size:11px;font-weight:900;cursor:pointer;}
#send{background:#148bff;color:white;}
#send:disabled{background:#222;color:#555;cursor:not-allowed;}
#clear{background:#222;color:#aaa;}
#status{font-size:13px;color:#888;}
@media(max-width:800px){
  #layout{grid-template-columns:1fr;grid-template-rows:1fr auto;}
  #side{max-height:260px;}
}
</style>
</head>
<body>
<div id="header">
  <h1>SLAM Map</h1>
  <div style="display:flex;gap:12px;align-items:center;">
    <span id="status">Connecting...</span>
  </div>
</div>

<div id="layout">
  <div id="map-wrapper">
    <canvas id="map-canvas"></canvas>
  </div>

  <div id="side">
    <div>
      <div class="panel-title">Robot Pose</div>
      <div class="pos-row">
        <div class="pos-box"><span class="pos-label">X</span><strong id="pos-x" class="pos-value">0.000m</strong></div>
        <div class="pos-box"><span class="pos-label">Y</span><strong id="pos-y" class="pos-value">0.000m</strong></div>
        <div class="pos-box"><span class="pos-label">YAW</span><strong id="pos-yaw" class="pos-value">0.0°</strong></div>
        <div class="pos-box"><span class="pos-label">MAP</span><strong id="map-size" class="pos-value">--</strong></div>
      </div>
    </div>

    ${adminPanelHtml}
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/roslib@1.4.1/build/roslib.min.js"></script>
<script>
var ros = new ROSLIB.Ros({ url: 'ws://iot-project:9090' });

var mapInfo = null;
var mapData = null;
var robotX = 0;
var robotY = 0;
var robotYaw = 0;
var target = null;

var canvas = document.getElementById('map-canvas');

var goalTopic = new ROSLIB.Topic({
  ros: ros,
  name: '/goal_pose',
  messageType: 'geometry_msgs/PoseStamped'
});

ros.on('connection', function(){
  document.getElementById('status').textContent = 'Connected';
  document.getElementById('status').style.color = '#50e38b';
});

ros.on('error', function(){
  document.getElementById('status').textContent = 'Disconnected';
  document.getElementById('status').style.color = '#ff5050';
});

function drawMap(){
  if (!mapData || !mapInfo) return;

  var w = mapInfo.width;
  var h = mapInfo.height;

  canvas.width = w;
  canvas.height = h;

  var ctx = canvas.getContext('2d');
  ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, w, h);

  for (var i = 0; i < mapData.length; i++) {
    var val = mapData[i];
    var x = i % w;
    var y = Math.floor(i / w);

    if (val === -1) ctx.fillStyle = '#0f172a';
    else if (val === 0) ctx.fillStyle = '#f8fafc';
    else ctx.fillStyle = '#148bff';

    ctx.fillRect(x, h - y - 1, 1, 1);
  }

  var rx = (robotX - mapInfo.origin.position.x) / mapInfo.resolution;
  var ry = h - (robotY - mapInfo.origin.position.y) / mapInfo.resolution;

  ctx.beginPath();
  ctx.arc(rx, ry, 4, 0, 2 * Math.PI);
  ctx.fillStyle = '#ff3b30';
  ctx.fill();

  ctx.beginPath();
  ctx.moveTo(rx, ry);
  ctx.lineTo(
    rx + Math.cos(robotYaw * Math.PI / 180) * 12,
    ry - Math.sin(robotYaw * Math.PI / 180) * 12
  );
  ctx.strokeStyle = '#ff3b30';
  ctx.lineWidth = 1;
  ctx.stroke();

  if (target) {
    var tx = (target.x - mapInfo.origin.position.x) / mapInfo.resolution;
    var ty = h - (target.y - mapInfo.origin.position.y) / mapInfo.resolution;

    ctx.beginPath();
    ctx.arc(tx, ty, 5, 0, 2 * Math.PI);
    ctx.fillStyle = '#50e38b';
    ctx.fill();

    ctx.beginPath();
    ctx.moveTo(tx - 8, ty);
    ctx.lineTo(tx + 8, ty);
    ctx.moveTo(tx, ty - 8);
    ctx.lineTo(tx, ty + 8);
    ctx.strokeStyle = '#50e38b';
    ctx.lineWidth = 1;
    ctx.stroke();
  }
}

function getWorldPoint(event) {
  if (!mapInfo || !mapData) return null;

  var rect = canvas.getBoundingClientRect();
  var canvasRatio = canvas.width / canvas.height;
  var rectRatio = rect.width / rect.height;

  var displayedWidth = rect.width;
  var displayedHeight = rect.height;
  var offsetX = 0;
  var offsetY = 0;

  if (rectRatio > canvasRatio) {
    displayedHeight = rect.height;
    displayedWidth = displayedHeight * canvasRatio;
    offsetX = (rect.width - displayedWidth) / 2;
  } else {
    displayedWidth = rect.width;
    displayedHeight = displayedWidth / canvasRatio;
    offsetY = (rect.height - displayedHeight) / 2;
  }

  var clickX = event.clientX - rect.left - offsetX;
  var clickY = event.clientY - rect.top - offsetY;

  if (clickX < 0 || clickY < 0 || clickX > displayedWidth || clickY > displayedHeight) {
    return null;
  }

  var pixelX = (clickX / displayedWidth) * canvas.width;
  var pixelY = (clickY / displayedHeight) * canvas.height;

  return {
    x: pixelX * mapInfo.resolution + mapInfo.origin.position.x,
    y: (mapInfo.height - pixelY) * mapInfo.resolution + mapInfo.origin.position.y
  };
}

${adminScript}

new ROSLIB.Topic({
  ros: ros,
  name: '/map_web',
  messageType: 'nav_msgs/OccupancyGrid',
  throttle_rate: 500,
  queue_length: 1
}).subscribe(function(msg){
  mapInfo = msg.info;
  mapData = msg.data;
  document.getElementById('map-size').textContent = msg.info.width + 'x' + msg.info.height;
  requestAnimationFrame(drawMap);
});

new ROSLIB.Topic({
  ros: ros,
  name: "/odometry/filtered",
  messageType: 'nav_msgs/Odometry',
  throttle_rate: 200,
  queue_length: 1
}).subscribe(function(msg){
  robotX = msg.pose.pose.position.x;
  robotY = msg.pose.pose.position.y;

  var q = msg.pose.pose.orientation;
  var yaw = Math.atan2(
    2 * (q.w * q.z + q.x * q.y),
    1 - 2 * (q.y * q.y + q.z * q.z)
  );

  robotYaw = ((yaw * 180 / Math.PI) % 360 + 360) % 360;

  document.getElementById('pos-x').textContent = robotX.toFixed(3) + 'm';
  document.getElementById('pos-y').textContent = robotY.toFixed(3) + 'm';
  document.getElementById('pos-yaw').textContent = robotYaw.toFixed(1) + '°';

  requestAnimationFrame(drawMap);
});
</script>
</body>
</html>`);

    win.document.close();
  };

  return (
    <section className="bg-[#2b2b2b] border border-[#3a3a3a] rounded-[16px] p-[18px] text-white shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
      <div className="flex items-center justify-between mb-[18px]">
        <h3 className="flex items-center gap-[10px] text-[15px] font-extrabold">
          <Crosshair size={18} className="text-white" />
          Real-time SLAM Map
        </h3>

        <button
          onClick={handleExpand}
          className="h-[38px] px-[14px] rounded-[10px] bg-[#1a1a1a] border border-[#3a3a3a] text-[#aaa] text-[12px] flex items-center gap-2 hover:text-white hover:border-[#555] transition-all"
        >
          <Maximize2 size={14} />
          Expand
        </button>
      </div>

      <div className="h-[230px] bg-[#101010] rounded-[14px] overflow-hidden relative flex items-center justify-center">
        {!mapReceived && (
          <span className="text-[#555] text-[12px]">
            En attente de la carte SLAM...
          </span>
        )}

        <canvas
          ref={canvasRef}
          onClick={handleCanvasClick}
          style={{
            imageRendering: "pixelated",
            width: "100%",
            height: "100%",
            objectFit: "contain",
            display: mapReceived ? "block" : "none",
            cursor: isAdmin ? "crosshair" : "default",
          }}
        />
      </div>

      <div className="grid grid-cols-2 gap-[8px] mt-[12px]">
        <InfoBox label="X" value={`${robotPos.x.toFixed(3)}m`} />
        <InfoBox label="Y" value={`${robotPos.y.toFixed(3)}m`} />
        <InfoBox label="YAW" value={`${robotPos.yaw.toFixed(1)}°`} />
        <InfoBox label="MAP" value={mapSize} muted />
      </div>

      {isAdmin && (
        <div className="mt-[14px] bg-[#111] border border-[#2a2a2a] rounded-[12px] p-[12px]">
          <div className="flex items-start gap-[8px] mb-[12px]">
            <Navigation size={15} className="text-[#148bff] mt-[2px] shrink-0" />

            <div>
              <p className="text-[12px] font-extrabold text-white leading-none">
                Navigation Target
              </p>
              <p className="text-[10px] text-[#777] mt-[6px] leading-[14px]">
                Click on the SLAM map to select a goal.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-[8px] mb-[12px]">
            <InfoBox
              label="TARGET X"
              value={target ? `${target.x.toFixed(2)}m` : "--"}
            />
            <InfoBox
              label="TARGET Y"
              value={target ? `${target.y.toFixed(2)}m` : "--"}
            />
          </div>

          <div className="grid grid-cols-2 gap-[8px]">
            <button
              onClick={handleSendGoal}
              disabled={!target}
              className={`h-[36px] rounded-[8px] text-[11px] font-bold transition ${
                target
                  ? "bg-[#148bff] text-white hover:bg-[#0f7ee8]"
                  : "bg-[#1f1f1f] text-[#555] cursor-not-allowed"
              }`}
            >
              SEND GOAL
            </button>

            <button
              onClick={handleClearTarget}
              className="h-[36px] rounded-[8px] bg-[#222] text-[#aaa] text-[11px] font-bold hover:text-white transition flex items-center justify-center gap-1"
            >
              <X size={13} />
              CLEAR
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

function InfoBox({ label, value, muted }) {
  return (
    <div className="bg-[#111] border border-[#1f1f1f] px-[12px] py-[9px] rounded-[9px] min-w-0">
      <span className="block text-[9px] text-[#888] leading-none mb-[6px]">
        {label}
      </span>

      <strong
        className={
          muted
            ? "block text-[11px] text-[#888] leading-none truncate"
            : "block text-[13px] text-[#148bff] leading-none truncate"
        }
      >
        {value}
      </strong>
    </div>
  );
}