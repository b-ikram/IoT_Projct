import { useEffect, useRef, useState } from "react";
import * as ROSLIB from "roslib";
import { ros } from "../services/ros";
import { Crosshair, Maximize2 } from "lucide-react";

export default function MapPanel() {
  const canvasRef = useRef(null);
  const mapInfoRef = useRef(null);
  const mapDataRef = useRef(null);
  const robotPosRef = useRef({ x: 0, y: 0, yaw: 0 });

  const [robotPos, setRobotPos] = useState({ x: 0, y: 0, yaw: 0 });
  const [mapSize, setMapSize] = useState("--");
  const [mapReceived, setMapReceived] = useState(false);

  useEffect(() => {
    const drawMap = () => {
      const canvas = canvasRef.current;
      const mapData = mapDataRef.current;
      const info = mapInfoRef.current;

      if (!canvas || !mapData || !info) return;

      canvas.width = mapData.width;
      canvas.height = mapData.height;

      const ctx = canvas.getContext("2d");

      ctx.imageSmoothingEnabled = true;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      for (let i = 0; i < mapData.data.length; i++) {
        const val = mapData.data[i];
        const x = i % mapData.width;
        const y = Math.floor(i / mapData.width);

        if (val === -1) ctx.fillStyle = "#0f172a";
        else if (val === 0) ctx.fillStyle = "#f8fafc";
        else ctx.fillStyle = "#148bff";

        ctx.fillRect(x, mapData.height - y - 1, 1, 1);
      }

      const rx =
        (robotPosRef.current.x - info.origin.position.x) / info.resolution;
      const ry =
        mapData.height -
        (robotPosRef.current.y - info.origin.position.y) / info.resolution;

      ctx.beginPath();
      ctx.arc(rx, ry, 2.5, 0, 2 * Math.PI);
      ctx.fillStyle = "#ff3b30";
      ctx.fill();

      ctx.beginPath();
      ctx.moveTo(rx, ry);
      ctx.lineTo(
        rx + Math.cos((robotPosRef.current.yaw * Math.PI) / 180) * 7,
        ry - Math.sin((robotPosRef.current.yaw * Math.PI) / 180) * 7
      );
      ctx.strokeStyle = "#ff3b30";
      ctx.lineWidth = 1;
      ctx.stroke();
    };

    const mapTopic = new ROSLIB.Topic({
      ros,
      name: "/map",
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
      name: "/odom",
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
  }, []);

  const handleExpand = () => {
    const win = window.open("", "_blank", "width=1200,height=800");

    win.document.write(`<!DOCTYPE html>
<html>
<head>
<title>SLAM Map</title>
<style>
*{
  margin:0;
  padding:0;
  box-sizing:border-box;
}

body{
  background:#101010;
  color:white;
  font-family:sans-serif;
}

#header{
  height:70px;
  background:#171717;
  display:flex;
  align-items:center;
  padding:0 28px;
  border-bottom:1px solid #333;
  justify-content:space-between;
}

#header h1{
  font-size:26px;
  font-weight:900;
}

#map-container{
  width:100vw;
  height:calc(100vh - 70px);
  background:#101010;
  display:flex;
  align-items:center;
  justify-content:center;
  overflow:hidden;
}

#map-wrapper{
  width:92%;
  height:92%;
  display:flex;
  align-items:center;
  justify-content:center;
  background:#0b0b0b;
  border:1px solid #222;
  border-radius:18px;
  overflow:hidden;
}

#map-canvas{
  image-rendering:pixelated;
  width:70%;
  height:70%;
  object-fit:contain;
}

.pos-box{
  background:#111;
  padding:7px 14px;
  border-radius:10px;
}

.pos-label{
  font-size:9px;
  color:#888;
  display:block;
}

.pos-value{
  color:#148bff;
  font-size:14px;
  font-weight:800;
}

#status{
  font-size:13px;
  color:#888;
}
</style>
</head>

<body>
<div id="header">
  <h1>🗺️ SLAM Map</h1>

  <div style="display:flex;gap:12px;align-items:center;">
    <div class="pos-box">
      <span class="pos-label">X</span>
      <strong id="pos-x" class="pos-value">0.000m</strong>
    </div>

    <div class="pos-box">
      <span class="pos-label">Y</span>
      <strong id="pos-y" class="pos-value">0.000m</strong>
    </div>

    <div class="pos-box">
      <span class="pos-label">YAW</span>
      <strong id="pos-yaw" class="pos-value">0.0°</strong>
    </div>

    <span id="status">Connecting...</span>
  </div>
</div>

<div id="map-container">
  <div id="map-wrapper">
    <canvas id="map-canvas"></canvas>
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
var canvas = document.getElementById('map-canvas');

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
  ctx.imageSmoothingEnabled = true;
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
  ctx.arc(rx, ry, 2.5, 0, 2 * Math.PI);
  ctx.fillStyle = '#ff3b30';
  ctx.fill();

  ctx.beginPath();
  ctx.moveTo(rx, ry);
  ctx.lineTo(
    rx + Math.cos(robotYaw * Math.PI / 180) * 7,
    ry - Math.sin(robotYaw * Math.PI / 180) * 7
  );
  ctx.strokeStyle = '#ff3b30';
  ctx.lineWidth = 1;
  ctx.stroke();
}

new ROSLIB.Topic({
  ros: ros,
  name: '/map',
  messageType: 'nav_msgs/OccupancyGrid',
  throttle_rate: 500,
  queue_length: 1
}).subscribe(function(msg){
  mapInfo = msg.info;
  mapData = msg.data;
  requestAnimationFrame(drawMap);
});

new ROSLIB.Topic({
  ros: ros,
  name: '/odom',
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
          style={{
  imageRendering: "pixelated",
  width: "85%",
  height: "85%",
  objectFit: "contain",
  display: mapReceived ? "block" : "none",
}}
        />
      </div>

      <div className="flex items-center gap-[8px] mt-4">
        <InfoBox label="X" value={`${robotPos.x.toFixed(3)}m`} />
        <InfoBox label="Y" value={`${robotPos.y.toFixed(3)}m`} />
        <InfoBox label="YAW" value={`${robotPos.yaw.toFixed(1)}°`} />
        <InfoBox label="MAP" value={mapSize} muted />
      </div>
    </section>
  );
}

function InfoBox({ label, value, muted }) {
  return (
    <div className="flex-1 bg-[#111] px-[10px] py-[6px] rounded-[8px]">
      <span className="block text-[9px] text-[#888]">{label}</span>
      <strong className={muted ? "text-[11px] text-[#888]" : "text-[13px] text-[#148bff]"}>
        {value}
      </strong>
    </div>
  );
}