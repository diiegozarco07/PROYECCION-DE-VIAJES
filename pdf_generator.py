from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import io

def generar_pdf_viaje(viaje, vehiculo=None):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Título
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, f"Reporte de Viaje #{viaje.id_viaje}")

    # Línea separadora
    c.setLineWidth(1)
    c.line(50, height - 60, width - 50, height - 60)

    # Información General
    y = height - 100
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Información General")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Proyecto: {viaje.proyecto}")
    y -= 15
    c.drawString(50, y, f"Destino: {viaje.destino_limpio}")
    y -= 15
    c.drawString(50, y, f"Fechas: {viaje.fecha_inicio} al {viaje.fecha_fin}")
    y -= 15
    c.drawString(50, y, f"Solicitante: {viaje.creador_id} ({viaje.correo_trabajador or 'Sin correo'})")
    
    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Detalles Operativos")
    y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Personal: {viaje.personal_asignado}")
    y -= 15
    # Wrap text for description
    text = c.beginText(50, y)
    text.setFont("Helvetica", 10)
    text.textLines(f"Descripción: {viaje.breve_descripcion}")
    c.drawText(text)
    y -= 40 # Ajustar según largo descripción

    if vehiculo:
        y -= 20
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Vehículo Asignado")
        y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Modelo: {vehiculo.modelo}")
        y -= 15
        c.drawString(50, y, f"Placas: {vehiculo.placas}")
    else:
        y -= 20
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Vehículo: No asignado")

    # Costos (Solo para Admin)
    y -= 40
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Desglose de Costos (Confidencial)")
    y -= 20
    c.setFont("Helvetica", 10)
    
    toka = viaje.costo_toka or 0.0
    casetas = viaje.costo_casetas or 0.0
    hospedaje = viaje.costo_hospedaje or 0.0
    total = toka + casetas + hospedaje

    c.drawString(50, y, f"Toka (Gasolina): ${toka:,.2f}")
    y -= 15
    c.drawString(50, y, f"Casetas: ${casetas:,.2f}")
    y -= 15
    c.drawString(50, y, f"Hospedaje: ${hospedaje:,.2f}")
    y -= 20
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, f"Total Estimado: ${total:,.2f}")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
