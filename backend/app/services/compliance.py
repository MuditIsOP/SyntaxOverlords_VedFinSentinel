from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io
from datetime import datetime
from typing import List

def generate_compliance_report(logs: List[dict]) -> io.BytesIO:
    """
    Generates an enterprise-grade compliance PDF report for fraud audits.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Header
    elements.append(Paragraph("VedFin Sentinel — Compliance Audit Report", title_style))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    elements.append(Spacer(1, 20))
    
    # Summary Section
    elements.append(Paragraph("Audit Summary", subtitle_style))
    total_logs = len(logs)
    fraud_count = len([l for l in logs if l.get('risk_band') == 'FRAUD'])
    elements.append(Paragraph(f"Total Transactions Reviewed: {total_logs}", normal_style))
    elements.append(Paragraph(f"High-Risk Flags (FRAUD): {fraud_count}", normal_style))
    elements.append(Spacer(1, 20))
    
    # Table Data
    data = [["TXN ID", "Risk Band", "Score", "Action", "Timestamp"]]
    for log in logs:
        # Truncate TXN ID for display
        txn_id = str(log.get('txn_id', ''))[:8] + "..."
        data.append([
            txn_id,
            log.get('risk_band', 'N/A'),
            f"{log.get('fraud_score', 0):.3f}",
            log.get('action_taken', 'N/A'),
            log.get('created_at', '')[:19] # Truncate isoformat
        ])
    
    # Table Styling
    table = Table(data, colWidths=[100, 80, 60, 100, 150])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    table.setStyle(style)
    elements.append(table)
    
    # Build
    doc.build(elements)
    buffer.seek(0)
    return buffer
