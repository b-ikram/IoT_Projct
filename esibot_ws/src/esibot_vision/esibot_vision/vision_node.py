"""
EsiBot — vision_pipeline.py
────────────────────────────
Nœud ROS2 Python — Vision par ordinateur complète.

Souscrit au topic caméra → détecte → publie les résultats annotés.

Détections :
  1. ArUco markers  (OpenCV ArUco)
  2. Couleurs       (rouge, vert, bleu, jaune — masque HSV)
  3. Lignes au sol  (Canny + HoughLinesP)
  4. Objets/personnes (YOLOv8n)

Topics consommés :
  - /camera_node/image_raw/compressed  (sensor_msgs/CompressedImage)

Topics publiés :
  - /camera/image_annotated   (sensor_msgs/CompressedImage)  → dashboard web
  - /vision/detections        (std_msgs/String, JSON)        → dashboard / autres nœuds

Lancement :
  python3 vision_pipeline.py

Dépendances :
  pip install ultralytics opencv-python
"""

# ══════════════════════════════════════════════
#  ⚙️  CONFIGURATION — MODIFIE ICI
# ══════════════════════════════════════════════

# Topic ROS2 depuis lequel on reçoit les images
# Pour vérifier le nom exact :  ros2 topic list
CAMERA_TOPIC = "/camera_node/image_raw/compressed"          # ← remplace si différent

# Topics de sortie
#OUTPUT_TOPIC_IMAGE      = "/camera/image_annotated"
OUTPUT_TOPIC_IMAGE      = "/camera/image_annotated/compressed"
OUTPUT_TOPIC_DETECTIONS = "/vision/detections"

# Modèle YOLO — se télécharge automatiquement la 1ère fois
YOLO_MODEL_PATH     = "yolov8n.onnx"
YOLO_CONFIDENCE     = 0.5
YOLO_EVERY_N_FRAMES = 3    # YOLO tourne 1 frame sur N → allège le RPi4

# Taille minimale (pixels²) pour valider une détection couleur
MIN_COLOR_AREA = 1500

# ══════════════════════════════════════════════
#  IMPORTS
# ══════════════════════════════════════════════

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String

import cv2
import numpy as np
import json
import time
import onnxruntime as ort

# ══════════════════════════════════════════════
#  COULEURS HSV
# ══════════════════════════════════════════════

COLOR_RANGES = {
    "rouge": [
        (np.array([0,   120, 70]),  np.array([10,  255, 255])),
        (np.array([170, 120, 70]),  np.array([180, 255, 255])),
    ],
    "vert":  [(np.array([36, 100, 100]), np.array([86,  255, 255]))],
    "bleu":  [(np.array([100, 150,  50]), np.array([140, 255, 255]))],
    "jaune": [(np.array([20,  100, 100]), np.array([35,  255, 255]))],
}

COLOR_DRAW = {
    "rouge":  (0,   0,   255),
    "vert":   (0,   255, 0),
    "bleu":   (255, 0,   0),
    "jaune":  (0,   255, 255),
}

# ══════════════════════════════════════════════
#  NŒUD ROS2
# ══════════════════════════════════════════════

class VisionPipeline(Node):

    def __init__(self):
        super().__init__("vision_pipeline")
        self.get_logger().info("Initialisation du pipeline de vision...")

        # ── Modèle YOLO ONNX ──
        self.get_logger().info("Chargement YOLOv8n ONNX...")
        self.yolo_session = ort.InferenceSession(YOLO_MODEL_PATH, providers=["CPUExecutionProvider"])
        self.yolo_input_name = self.yolo_session.get_inputs()[0].name
        self.get_logger().info("YOLOv8n ONNX prêt.")

        # ── Détecteur ArUco ──
        aruco_dict   = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        aruco_params = cv2.aruco.DetectorParameters()
        self.aruco_detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)

        # ── Subscriber ──
        self.sub = self.create_subscription(
            CompressedImage,
            CAMERA_TOPIC,
            self.callback,
            10
        )

        # ── Publishers ──
        self.pub_image = self.create_publisher(
            CompressedImage,
            OUTPUT_TOPIC_IMAGE,
            10
        )
        self.pub_detections = self.create_publisher(
            String,
            OUTPUT_TOPIC_DETECTIONS,
            10
        )

        self.frame_count = 0
        self.yolo_cache  = []
        self.get_logger().info(f"En écoute sur : {CAMERA_TOPIC}")
        self.get_logger().info("Pipeline prêt.\n")

    # ──────────────────────────────────────────
    #  CALLBACK — appelé à chaque frame reçue
    # ──────────────────────────────────────────

    def callback(self, msg: CompressedImage):
        t_start = time.time()

        # Décoder la frame compressée → image OpenCV
        np_arr = np.frombuffer(msg.data, np.uint8)
        frame  = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            self.get_logger().warn("Frame vide reçue, ignorée.")
            return

        # ── Détections ──
        aruco_results = self._detect_aruco(frame)
        color_results = self._detect_colors(frame)
        line_results  = self._detect_lines(frame)

        if self.frame_count % YOLO_EVERY_N_FRAMES == 0:
            self.yolo_cache = self._detect_yolo(frame)
        yolo_results = self.yolo_cache

        fps = round(1 / (time.time() - t_start + 1e-9), 1)

        # ── Résumé terminal ──
        self.get_logger().info(
            f"[Frame {self.frame_count}] FPS={fps} | "
            f"ArUco={[r['id'] for r in aruco_results]} | "
            f"Couleurs={[r['color'] for r in color_results]} | "
            f"Lignes={len(line_results)} | "
            f"YOLO={[(r['label'], r['conf']) for r in yolo_results]}"
        )

        # ── Annoter la frame ──
        annotated = self._annotate(frame, aruco_results, color_results,
                                   line_results, yolo_results, fps)

        # ── Publier image annotée → dashboard ──
        _, encoded  = cv2.imencode(".jpg", annotated)
        out_img         = CompressedImage()
        out_img.header  = msg.header
        out_img.format  = "jpeg"
        out_img.data    = encoded.tobytes()
        self.pub_image.publish(out_img)

        # ── Publier détections JSON → dashboard / autres nœuds ──
        detections = {
            "frame":   self.frame_count,
            "fps":     fps,
            "aruco":   [{"id": r["id"], "center": r["center"].tolist()} for r in aruco_results],
            "colors":  [{"color": r["color"], "area": r["area"]}        for r in color_results],
            "lines":   len(line_results),
            "objects": [{"label": r["label"], "conf": r["conf"]}        for r in yolo_results],
        }
        msg_det      = String()
        msg_det.data = json.dumps(detections)
        self.pub_detections.publish(msg_det)

        self.frame_count += 1

    # ──────────────────────────────────────────
    #  DÉTECTIONS
    # ──────────────────────────────────────────

    def _detect_aruco(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = self.aruco_detector.detectMarkers(gray)
        results = []
        if ids is not None:
            for i, corner in enumerate(corners):
                results.append({
                    "id":      int(ids[i][0]),
                    "center":  corner[0].mean(axis=0).astype(int),
                    "corners": corner,
                })
        return results

    def _detect_colors(self, frame):
        hsv     = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        results = []
        kernel  = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        for name, ranges in COLOR_RANGES.items():
            mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            for (lo, hi) in ranges:
                mask |= cv2.inRange(hsv, lo, hi)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > MIN_COLOR_AREA:
                    x, y, w, h = cv2.boundingRect(cnt)
                    results.append({"color": name, "bbox": (x, y, w, h),
                                    "area": int(area)})
        return results

    def _detect_lines(self, frame):
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur  = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)
        h, w  = edges.shape
        roi   = edges[h // 2:]
        lines = cv2.HoughLinesP(roi, 1, np.pi / 180,
                                threshold=80, minLineLength=60, maxLineGap=20)
        results = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                results.append({"line": (x1, y1 + h // 2, x2, y2 + h // 2)})
        return results

    COCO = ["person","bicycle","car","motorcycle","airplane","bus","train","truck","boat",
        "traffic light","fire hydrant","stop sign","parking meter","bench","bird","cat",
        "dog","horse","sheep","cow","elephant","bear","zebra","giraffe","backpack",
        "umbrella","handbag","tie","suitcase","frisbee","skis","snowboard","sports ball",
        "kite","baseball bat","baseball glove","skateboard","surfboard","tennis racket",
        "bottle","wine glass","cup","fork","knife","spoon","bowl","banana","apple",
        "sandwich","orange","broccoli","carrot","hot dog","pizza","donut","cake","chair",
        "couch","potted plant","bed","dining table","toilet","tv","laptop","mouse",
        "remote","keyboard","cell phone","microwave","oven","toaster","sink","refrigerator",
        "book","clock","vase","scissors","teddy bear","hair drier","toothbrush"]

    def _detect_yolo(self, frame):
        h0, w0 = frame.shape[:2]
        img = cv2.resize(frame, (640, 640))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        img = np.transpose(img, (2,0,1))[None]
        preds = self.yolo_session.run(None, {self.yolo_input_name: img})[0][0].T
        results = []
        for p in preds:
            scores = p[4:]
            cls_id = int(np.argmax(scores))
            conf   = float(scores[cls_id])
            if conf < YOLO_CONFIDENCE:
                continue
            cx,cy,w,h = p[:4]
            x1 = int((cx-w/2)/640*w0); y1 = int((cy-h/2)/640*h0)
            x2 = int((cx+w/2)/640*w0); y2 = int((cy+h/2)/640*h0)
            results.append({"label": self.COCO[cls_id] if cls_id < len(self.COCO) else str(cls_id),
                             "conf": round(conf,2), "bbox": (x1,y1,x2,y2)})
        return results

    # ──────────────────────────────────────────
    #  ANNOTATION
    # ──────────────────────────────────────────

    def _annotate(self, frame, aruco, colors, lines, yolo, fps):
        out = frame.copy()

        for r in aruco:
            cv2.aruco.drawDetectedMarkers(out, [r["corners"]])
            cx, cy = r["center"]
            cv2.putText(out, f"ArUco ID={r['id']}", (cx - 30, cy - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 200), 2)

        for r in colors:
            x, y, w, h = r["bbox"]
            col = COLOR_DRAW[r["color"]]
            cv2.rectangle(out, (x, y), (x + w, y + h), col, 2)
            cv2.putText(out, r["color"], (x, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, col, 2)

        for r in lines:
            x1, y1, x2, y2 = r["line"]
            cv2.line(out, (x1, y1), (x2, y2), (255, 200, 0), 2)

        for r in yolo:
            x1, y1, x2, y2 = r["bbox"]
            col = (0, 100, 255) if r["label"] == "person" else (200, 200, 200)
            cv2.rectangle(out, (x1, y1), (x2, y2), col, 2)
            cv2.putText(out, f"{r['label']} {r['conf']}", (x1, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, col, 2)

        cv2.putText(out, f"FPS: {fps}", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return out


# ══════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════

def main():
    rclpy.init()
    node = VisionPipeline()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Arrêt du pipeline.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
