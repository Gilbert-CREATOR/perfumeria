from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from django.conf import settings
from django.utils import timezone
from apps.core.models import ConfiguracionSitio
import os
import logging
from decimal import Decimal


logger = logging.getLogger(__name__)

def generar_factura_pdf(pedido, output_path=None):
    """
    Genera una factura PDF para un pedido
    """
    
    if not output_path:
        output_path = os.path.join(settings.MEDIA_ROOT, f'facturas/factura_{pedido.id}.pdf')
    
    # Crear directorio únicamente cuando se genera en disco. También admite BytesIO.
    if isinstance(output_path, (str, bytes, os.PathLike)):
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
    configuracion = ConfiguracionSitio.cargar()
    empresa_data = [
        [configuracion.marca, ""],
        [f"Dirección: {configuracion.direccion_linea_1} {configuracion.direccion_linea_2}".strip(), ""],
        [f"Teléfono: {configuracion.telefono_contacto}", ""],
        [f"Email: {configuracion.email_contacto}", ""],
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
    usuario = pedido.usuario
    cliente_data = [
        ["FACTURA A:", f"{pedido.nombre_completo or (usuario.username if usuario else 'Cliente')}"],
        ["Email:", usuario.email if usuario else "Cuenta eliminada"],
        ["Teléfono:", pedido.telefono or "N/A"],
        ["Dirección:", f"{pedido.direccion}, {pedido.ciudad}, {pedido.provincia}"],
        ["Código Postal:", pedido.codigo_postal],
        ["", ""],
        ["No. Factura:", f"F{pedido.id:06d}"],
        ["Fecha:", timezone.localtime().strftime("%d/%m/%Y")],
        ["No. Pedido:", f"P{pedido.id:06d}"],
        ["Estado:", pedido.get_estado_display()],
    ]
    
    cliente_table = Table(cliente_data, colWidths=[2*inch, 4*inch])
    cliente_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 6), (0, -1), colors.blue),
        ('FONTNAME', (0, 6), (0, -1), 'Helvetica-Bold'),
    ]))
    
    story.append(cliente_table)
    story.append(Spacer(1, 20))
    
    # Productos
    headers = ["Producto", "Cantidad", "Precio Unit.", "Subtotal"]
    data = [headers]
    
    for item in pedido.items.select_related('producto').all():
        marca = item.marca_producto or (item.producto.marca if item.producto else '')
        tamano = item.producto.tamano_ml if item.producto else None
        descripcion = f"{item.nombre_visible}\n{marca}"
        if tamano:
            descripcion += f" - {tamano}ml"
        data.append([
            descripcion,
            str(item.cantidad),
            f"${item.precio:,.1f}",
            f"${item.subtotal():,.1f}"
        ])
    
    # Totales
    data.append(["", "", "Subtotal:", f"${pedido.subtotal:,.1f}"])
    data.append(["", "", "Envío:", f"${pedido.costo_envio:,.1f}"])
    itbis_incluido = pedido.subtotal - (pedido.subtotal / Decimal('1.18'))
    data.append(["", "", "ITBIS incluido:", f"${itbis_incluido:,.1f}"])
    data.append(["", "", "TOTAL:", f"${pedido.total:,.1f}"])
    
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
    • Los precios están expresados en la moneda indicada en el pedido<br/>
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
        ["", configuracion.marca],
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
        logger.info('Factura generada para el pedido %s', pedido.pk)
        return ruta
    except Exception:
        logger.exception('Error generando factura para el pedido %s', pedido.pk)
        return None
