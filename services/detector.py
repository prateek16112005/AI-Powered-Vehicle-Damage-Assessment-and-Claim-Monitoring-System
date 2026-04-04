from ultralytics import YOLO
import cv2
import os
from config import PART_MODEL_PATH, DAMAGE_MODEL_PATH, RESULT_DIR

part_model = YOLO(PART_MODEL_PATH)
damage_model = YOLO(DAMAGE_MODEL_PATH)

def detect_parts_and_damage(image_path):
    part_results = part_model(image_path)
    damage_results = damage_model(image_path)

    parts = []
    damages = []

    part_boxes = part_results[0].boxes
    damage_boxes = damage_results[0].boxes

    if part_boxes is not None and len(part_boxes) > 0:
        for box in part_boxes:
            cls_id = int(box.cls.item())
            coords = box.xyxy[0].tolist()
            conf = float(box.conf.item())
            parts.append({
                "label": part_results[0].names[cls_id],
                "box": coords,
                "confidence": conf
            })

    if damage_boxes is not None and len(damage_boxes) > 0:
        for box in damage_boxes:
            cls_id = int(box.cls.item())
            coords = box.xyxy[0].tolist()
            conf = float(box.conf.item())
            damages.append({
                "label": damage_results[0].names[cls_id],
                "box": coords,
                "confidence": conf
            })

    plotted = damage_results[0].plot()
    output_path = os.path.join(RESULT_DIR, "output.jpg")
    cv2.imwrite(output_path, plotted)

    return parts, damages, output_path