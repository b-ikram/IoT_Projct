import * as ROSLIB from "roslib";

export const ros = new ROSLIB.Ros({});

ros.connect("ws://10.82.115.2:9090");

ros.on("connection", () => console.log(" ROS2 connecté"));
ros.on("error",      (e) => console.warn(" ROS2 offline", e));
ros.on("close",      () => console.log("ROS2 déconnecté"));