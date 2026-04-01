from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import shutil
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model (pretrained for now)
model = YOLO("yolov8n.pt")   # auto downloads

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    temp_path = f"temp_{file.filename}"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run YOLO inference
    results = model(temp_path)

    damages = []
    confidences = []

    for r in results:
        if r.boxes is not None:
            for box in r.boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                damages.append(model.names[cls_id])
                confidences.append(round(conf, 2))

    os.remove(temp_path)

    if not damages:
        return {
            "damage_detected": False,
            "summary": "No damage detected"
        }

    unique_damages = list(set(damages))
    max_conf = max(confidences)

    # Simple severity logic
    if len(unique_damages) >= 3 or max_conf > 0.85:
        severity = "High"
    elif len(unique_damages) == 2 or max_conf > 0.6:
        severity = "Medium"
    else:
        severity = "Low"

    return {
        "damage_detected": True,
        "damages": unique_damages,
        "confidence": confidences,
        "severity": severity,
        "summary": f"Detected {', '.join(unique_damages)} damage. Severity: {severity}"
    }