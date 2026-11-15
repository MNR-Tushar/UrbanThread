from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def invoice_pdf(order):
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()
    address = order.shipping_address or {}
    elements = [Paragraph('UrbanThread - Order invoice', styles['Title']),
                Paragraph(f'Order {order.order_number} - {order.created_at:%d %b %Y}', styles['Normal']), Spacer(1, 16),
                Paragraph(f"Ship to: {escape(str(address.get('full_name', '')))} - {escape(str(address.get('phone', '')))}<br/>{escape(str(address.get('address', '')))}, {escape(str(address.get('city', '')))}, {escape(str(address.get('state', '')))} {escape(str(address.get('pincode', '')))}", styles['Normal']), Spacer(1, 16)]
    rows = [['Product', 'Variant', 'Qty', 'Unit price', 'Subtotal']]
    for item in order.items.select_related('product', 'color', 'size').all():
        rows.append([item.product.product_name, f'{item.color.color} / {item.size.size_type}', str(item.quantity), f'BDT {item.price}', f'BDT {item.price * item.quantity}'])
    rows.extend([['', '', '', 'Shipping', f'BDT {order.shipping_fee}'], ['', '', '', 'Total', f'BDT {order.total_amount}']])
    table = Table(rows, colWidths=[170, 105, 35, 85, 95], repeatRows=1)
    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#536b4d')), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('GRID', (0, 0), (-1, -1), .4, colors.lightgrey), ('PADDING', (0, 0), (-1, -1), 7), ('ALIGN', (2, 1), (-1, -1), 'RIGHT')]))
    elements.extend([table, Spacer(1, 14), Paragraph(f'Payment: {order.payment_status} - Order status: {order.order_status}', styles['Normal'])])
    doc.build(elements)
    return output.getvalue()
