import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from config import REPORT_DIR

def generate_pdf(owner_name, car_model, vehicle_no, model_no, mapped_results, input_path, output_path):
    pdf_path = os.path.join(REPORT_DIR, "damage_report.pdf")

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    y = height - 50

    c.setFont("Helvetica-Bold", 18)
    c.drawString(180, y, "Vehicle Damage Report")

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
    except:
        c.drawString(50, y + 80, "Unable to load uploaded image.")

    try:
        detected_img = ImageReader(output_path)
        c.drawImage(detected_img, 300, y, width=220, height=160, preserveAspectRatio=True, mask='auto')
    except:
        c.drawString(300, y + 80, "Unable to load detected image.")

    c.save()
    return pdf_path