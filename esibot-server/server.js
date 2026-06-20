const WebSocket = require("ws");
const { exec, execSync } = require("child_process");
const os = require("os");

const wss = new WebSocket.Server({ host: "0.0.0.0", port: 9091 });
console.log("EsiBot WebSocket server running on port 9091");

wss.on("connection", (ws) => {
  console.log("Frontend connected");

  ws.on("message", (message) => {
    const command = message.toString();
    console.log("Received:", command);

    if (command === "status") {
      ws.send(JSON.stringify({
        type: "console",
        lines: ["Robot: ONLINE", "Connection: Raspberry OK"]
      }));
      return;
    }

    if (command === "sysinfo") {
      const cpu = (os.loadavg()[0] * 25).toFixed(0);
      const totalMem = os.totalmem() / 1e9;
      const freeMem = os.freemem() / 1e9;
      let temp = "N/A";
      try {
        temp = execSync("vcgencmd measure_temp").toString().replace("temp=", "").trim();
      } catch {}
      ws.send(JSON.stringify({
        type: "sysinfo",
        cpu: cpu,
        temp: temp,
        memory: (totalMem - freeMem).toFixed(1) + " / " + totalMem.toFixed(0) + " GB"
      }));
      return;
    }

    if (command === "storageinfo") {
      try {
        const result = execSync("df -h / | tail -1").toString().split(/\s+/);
        ws.send(JSON.stringify({
          type: "storageinfo",
          storage: result[3] + " / " + result[1]
        }));
      } catch (e) {
        ws.send(JSON.stringify({
          type: "storageinfo",
          storage: "N/A"
        }));
      }
      return;
    }

    if (command === "networkinfo") {
      try {
        const ip = execSync("hostname -I").toString().trim().split(" ")[0];
        const ssid = execSync("iwgetid -r 2>/dev/null || echo 'Unknown'").toString().trim();
        ws.send(JSON.stringify({
          type: "networkinfo",
          ip: ip,
          ssid: ssid,
          rosbridge_port: "9090",
          websocket_port: "9091"
        }));
      } catch (e) {
        ws.send(JSON.stringify({
          type: "networkinfo",
          ip: "unavailable",
          ssid: "unavailable",
          rosbridge_port: "9090",
          websocket_port: "9091"
        }));
      }
      return;
    }

    exec(command, { timeout: 5000 }, (error, stdout, stderr) => {
      if (error) {
        ws.send(JSON.stringify({
          type: "console",
          lines: ["Error: " + (stderr || error.message)]
        }));
        return;
      }

      const lines = stdout
        .split("\n")
        .filter((line) => line.trim() !== "");

      ws.send(JSON.stringify({
        type: "console",
        lines: lines.length > 0 ? lines : ["Done (no output)"]
      }));
    });
  });
});
