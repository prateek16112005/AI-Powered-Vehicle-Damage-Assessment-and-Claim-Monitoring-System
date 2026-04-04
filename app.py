from flask import Flask, render_template, request, send_file
from ultralytics import YOLO
from werkzeug.utils import secure_filename
import os
import cv2
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

app = Flask(__name__)

# -----------------------------
# Paths
# -----------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")
RESULT_DIR = os.path.join(STATIC_DIR, "results")
REPORT_DIR = os.path.join(BASE_DIR, "reports")
MODEL_DIR = os.path.join(BASE_DIR, "models")

PART_MODEL_PATH = os.path.join(MODEL_DIR, "part_model.pt")
DAMAGE_MODEL_PATH = os.path.join(MODEL_DIR, "damage_model.pt")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

# -----------------------------
# Load models once
# -----------------------------
part_model = YOLO(PART_MODEL_PATH)
damage_model = YOLO(DAMAGE_MODEL_PATH)

# -----------------------------
# Helper functions
# -----------------------------
def calculate_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_w = max(0, x2 - x1)
    inter_h = max(0, y2 - y1)
    inter_area = inter_w * inter_h

    box1_area = max(0, box1[2] - box1[0]) * max(0, box1[3] - box1[1])
    box2_area = max(0, box2[2] - box2[0]) * max(0, box2[3] - box2[1])

    union_area = box1_area + box2_area - inter_area
    if union_area == 0:
        return 0

    return inter_area / union_area


def map_damage_to_parts(parts, damages):
    mapped_results = []

    for damage in damages:
        best_part = None
        best_iou = 0

        for part in parts:
            iou = calculate_iou(damage["box"], part["box"])
            if iou > best_iou:
                best_iou = iou
                best_part = part["label"]

        if best_part:
            mapped_results.append(f'{damage["label"]} on {best_part}')
        else:
            mapped_results.append(f'{damage["label"]} detected')

    return mapped_results


def generate_pdf(owner_name, car_model, vehicle_no, model_no, mapped_results, input_path, output_path):
    pdf_path = os.path.join(REPORT_DIR, "damage_report.pdf")

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 18)
    c.drawString(170, y, "Vehicle Damage Report")

    y -= 40
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Owner Name: {owner_name}")
    y -= 20
    c.drawString(50, y, f"Car Model: {car_model}")
    y -= 20
    c.drawString(50, y, f"Vehicle Number: {vehicle_no}")
    y -= 20
    c.drawString(50, y, f"Model Number: {model_no}")

    y -= 30
    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, y, "Detected Damage Summary:")
    y -= 20

    c.setFont("Helvetica", 12)
    if mapped_results:
        for item in mapped_results:
            c.drawString(70, y, f"- {item}")
            y -= 18
            if y < 120:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 12)
    else:
        c.drawString(70, y, "No damage detected.")
        y -= 20

    y -= 20
    if y < 250:
        c.showPage()
        y = height - 50

    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, y, "Uploaded Image")
    c.drawString(300, y, "Detection Result")
    y -= 190

    try:
        uploaded_img = ImageReader(input_path)
        c.drawImage(uploaded_img, 50, y, width=220, height=160, preserveAspectRatio=True, mask='auto')
    except Exception:
        c.drawString(50, y + 80, "Unable to load uploaded image.")

    try:
        detected_img = ImageReader(output_path)
        c.drawImage(detected_img, 300, y, width=220, height=160, preserveAspectRatio=True, mask='auto')
    except Exception:
        c.drawString(300, y + 80, "Unable to load detected image.")

    c.save()
    return pdf_path


def run_detection(input_path):
    parts = []
    damages = []

    # Part detection
    part_results = part_model.predict(source=input_path, conf=0.25)
    part_boxes = part_results[0].boxes

    if part_boxes is not None and len(part_boxes) > 0:
        for box in part_boxes:
            cls_id = int(box.cls.item())
            conf = float(box.conf.item())
            coords = box.xyxy[0].tolist()
            parts.append({
                "label": part_results[0].names[cls_id],
                "confidence": conf,
                "box": coords
            })

    # Damage detection
    damage_results = damage_model.predict(source=input_path, conf=0.25)
    damage_boxes = damage_results[0].boxes

    if damage_boxes is not None and len(damage_boxes) > 0:
        for box in damage_boxes:
            cls_id = int(box.cls.item())
            conf = float(box.conf.item())
            coords = box.xyxy[0].tolist()
            damages.append({
                "label": damage_results[0].names[cls_id],
                "confidence": conf,
                "box": coords
            })

    # Save plotted damage image
    output_path = os.path.join(RESULT_DIR, "output.jpg")
    plotted = damage_results[0].plot()
    cv2.imwrite(output_path, plotted)

    return parts, damages, output_path


# -----------------------------
# Routes
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        owner_name = request.form.get("owner_name", "").strip()
        car_model = request.form.get("car_model", "").strip()
        vehicle_no = request.form.get("vehicle_no", "").strip()
        model_no = request.form.get("model_no", "").strip()
        file = request.files.get("image")

        if not owner_name or not car_model or not vehicle_no or not model_no:
            return render_template("index.html", error="Please fill all details.")

        if not file or file.filename == "":
            return render_template("index.html", error="Please upload an image.")

        filename = secure_filename(file.filename)
        if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
            return render_template("index.html", error="Please upload PNG, JPG, or JPEG only.")

        input_path = os.path.join(UPLOAD_DIR, "input.jpg")
        file.save(input_path)

        parts, damages, output_path = run_detection(input_path)
        mapped_results = map_damage_to_parts(parts, damages)

        generate_pdf(
            owner_name,
            car_model,
            vehicle_no,
            model_no,
            mapped_results,
            input_path,
            output_path
        )

        return render_template(
            "index.html",
            success="Detection completed successfully.",
            owner_name=owner_name,
            car_model=car_model,
            vehicle_no=vehicle_no,
            model_no=model_no,
            input_image="uploads/input.jpg",
            output_image="results/output.jpg",
            detected_parts=[p["label"] for p in parts],
            detected_damages=[d["label"] for d in damages],
            mapped_results=mapped_results,
            pdf_ready=True
        )

    return render_template("index.html")


@app.route("/download-pdf")
def download_pdf():
    pdf_path = os.path.join(REPORT_DIR, "damage_report.pdf")
    return send_file(pdf_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)