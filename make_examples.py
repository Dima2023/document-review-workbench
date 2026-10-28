"""Generate two synthetic digital PDF fixtures. Requires reportlab."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
root=Path(__file__).parent/'examples'
root.mkdir(exist_ok=True)
layouts=[['Invoice: DEMO-001','Date: 2026-10-01','Subtotal: 100.00','Tax: 20.00','Total: 120.00','Currency: USD'],['Invoice number | DEMO-002','Issue date | 2026-10-02','Net amount | 50.00','Tax amount | 0.00','Amount due | 50.00','Currency | EUR']]
for index,lines in enumerate(layouts,1):
 c=canvas.Canvas(str(root/f'invoice-{index}.pdf'),pagesize=(612,792),invariant=1)
 c.setFillColor(HexColor('#12253b')); c.rect(0,640,612,152,fill=1,stroke=0)
 c.setFillColor(HexColor('#64e5ba')); c.setFont('Helvetica-Bold',12); c.drawString(48,742,'SYNTHETIC DOCUMENT / LEARNING DEMO')
 c.setFillColor(HexColor('#ffffff')); c.setFont('Helvetica-Bold',28); c.drawString(48,688,'Example invoice')
 c.setFillColor(HexColor('#12253b')); c.setFont('Helvetica',17)
 for i,line in enumerate(lines):c.drawString(48,580-i*52,line)
 c.setFont('Helvetica',10); c.drawString(48,120,'No real customer, seller, account or payment information.')
 c.drawString(48,100,'Generated for testing document extraction and human review only.')
 c.save()
