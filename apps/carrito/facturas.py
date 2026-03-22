from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from django.conf import settings
import os
from datetime import datetime

def generar_factura_pdf(pedido, output_path=None):
    """
    Genera una factura PDF para un pedido
    """
    
    if not output_path:
        output_path = os.path.join(settings.MEDIA_ROOT, f'facturas/factura_{pedido.id}.pdf')
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Crear el documento PDF
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    normal_style = styles['Normal']
    
    # Encabezado
    title = Paragraph("FACTURA", title_style)
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Información de la empresa
    empresa_data = [
        ["Perfumería RD", ""],
        ["RNC: 123456789", ""],
        ["Dirección: Calle Principal #123, Santo Domingo", ""],
        ["Teléfono: +1 (809) 123-4567", ""],
        ["Email: info@perfumeria.com", ""],
    ]
    
    empresa_table = Table(empresa_data, colWidths=[4*inch, 2*inch])
    empresa_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    
    story.append(empresa_table)
    story.append(Spacer(1, 20))
    
    # Información del cliente y pedido
    cliente_data = [
        ["FACTURA A:", f"{pedido.nombre_completo or pedido.usuario.username}"],
        ["Email:", pedido.usuario.email],
        ["Teléfono:", pedido.telefono or "N/A"],
        ["Dirección:", f"{pedido.direccion}, {pedido.ciudad}, {pedido.provincia}"],
        ["Código Postal:", pedido.codigo_postal],
        ["", ""],
        ["No. Factura:", f"F{pedido.id:06d}"],
        ["Fecha:", datetime.now().strftime("%d/%m/%Y")],
        ["No. Pedido:", f"P{pedido.id:06d}"],
        ["Estado:", pedido.get_estado_display()],
    ]
    
    cliente_table = Table(cliente_data, colWidths=[2*inch, 4*inch])
    cliente_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (6, 0), (6, -1), colors.blue),
        ('FONTNAME', (6, 0), (6, -1), 'Helvetica-Bold'),
    ]))
    
    story.append(cliente_table)
    story.append(Spacer(1, 20))
    
    # Productos
    headers = ["Producto", "Cantidad", "Precio Unit.", "Subtotal"]
    data = [headers]
    
    for item in pedido.items.select_related('producto').all():
        data.append([
            f"{item.producto.nombre}\n{item.producto.marca} - {item.producto.tamano_ml}ml",
            str(item.cantidad),
            f"${item.precio:.2f}",
            f"${item.subtotal():.2f}"
        ])
    
    # Totales
    data.append(["", "", "Subtotal:", f"${pedido.subtotal:.2f}"])
    data.append(["", "", "Envío:", f"${pedido.costo_envio:.2f}"])
    data.append(["", "", "ITBIS (18%):", f"${pedido.subtotal * 0.18:.2f}"])
    data.append(["", "", "TOTAL:", f"${pedido.total:.2f}"])
    
    # Tabla de productos
    products_table = Table(data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
    products_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TEXTCOLOR', (-2, -4), (-1, -1), colors.blue),
        ('FONTNAME', (-2, -4), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (-2, -4), (-1, -1), 12),
    ]))
    
    story.append(products_table)
    story.append(Spacer(1, 30))
    
    # Términos y condiciones
    terminos = """
    <b>Términos y Condiciones:</b><br/>
    • Los precios están en dólares estadounidenses<br/>
    • El ITBIS (18%) está incluido en el total<br/>
    • Los productos tienen 30 días de garantía<br/>
    • Las devoluciones deben estar en su estado original<br/>
    • Los costos de envío no son reembolsables<br/><br/>
    <b>Métodos de Pago:</b><br/>
    • Aceptamos PayPal, tarjetas de crédito/débito y transferencias<br/>
    • Los pagos son procesados de forma segura<br/>
    """
    
    terminos_para = Paragraph(terminos, normal_style)
    story.append(terminos_para)
    story.append(Spacer(1, 20))
    
    # Firma
    firma_data = [
        ["", "Firma Autorizada"],
        ["", ""],
        ["", ""],
        ["", "_________________________"],
        ["", "Perfumería RD"],
    ]
    
    firma_table = Table(firma_data, colWidths=[4*inch, 2*inch])
    firma_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    
    story.append(firma_table)
    
    # Generar el PDF
    doc.build(story)
    
    return output_path

def generar_factura_para_pedido(pedido):
    """
    Función simple para generar factura y retornar la ruta
    """
    try:
        ruta = generar_factura_pdf(pedido)
        print(f"✅ Factura generada: {ruta}")
        return ruta
    except Exception as e:
        print(f"❌ Error generando factura: {e}")
        return None
