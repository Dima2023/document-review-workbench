"""Generate synthetic digital PDF fixtures (skips files that already exist). Requires reportlab."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

root = Path(__file__).parent / 'examples'
root.mkdir(exist_ok=True)
layouts = [
    ['Invoice: DEMO-001', 'Date: 2026-10-01', 'Subtotal: 100.00', 'Tax: 20.00', 'Total: 120.00', 'Currency: USD'],
    ['Invoice number | DEMO-002', 'Issue date | 2026-10-02', 'Net amount | 50.00', 'Tax amount | 0.00', 'Amount due | 50.00', 'Currency | EUR'],
]


def simple_invoice(path, lines):
    c = canvas.Canvas(str(path), pagesize=(612, 792), invariant=1)
    c.setFillColor(HexColor('#12253b')); c.rect(0, 640, 612, 152, fill=1, stroke=0)
    c.setFillColor(HexColor('#64e5ba')); c.setFont('Helvetica-Bold', 12); c.drawString(48, 742, 'SYNTHETIC DOCUMENT / LEARNING DEMO')
    c.setFillColor(HexColor('#ffffff')); c.setFont('Helvetica-Bold', 28); c.drawString(48, 688, 'Example invoice')
    c.setFillColor(HexColor('#12253b')); c.setFont('Helvetica', 17)
    for i, line in enumerate(lines):
        c.drawString(48, 580 - i * 52, line)
    c.setFont('Helvetica', 10); c.drawString(48, 120, 'No real customer, seller, account or payment information.')
    c.drawString(48, 100, 'Generated for testing document extraction and human review only.')
    c.save()


def realistic_invoice(path):
    """A layout the offline rules do not know: free-form labels, £ symbols, thousands separators, line items."""
    c = canvas.Canvas(str(path), pagesize=(595, 842), invariant=1)
    ink, accent = HexColor('#1d2733'), HexColor('#2f6fd6')
    c.setFillColor(accent); c.setFont('Helvetica-Bold', 26); c.drawString(50, 780, 'INVOICE')
    c.setFillColor(ink); c.setFont('Helvetica-Bold', 11); c.drawString(50, 750, 'Northwind Analytics Ltd (synthetic)')
    c.setFont('Helvetica', 10)
    for i, line in enumerate(['12 Example Street', 'London EC1A 1AA', 'VAT reg. GB000000000']):
        c.drawString(50, 735 - i * 14, line)
    c.setFont('Helvetica', 10)
    meta = [('Invoice No.', 'INV-2026-0147'), ('Invoice date', '14 October 2026'), ('Payment terms', '30 days')]
    for i, (label, value) in enumerate(meta):
        c.drawString(360, 750 - i * 16, label); c.drawRightString(545, 750 - i * 16, value)
    c.setFont('Helvetica-Bold', 10); c.drawString(50, 660, 'Bill to'); c.setFont('Helvetica', 10)
    c.drawString(50, 645, 'Example Retail GmbH (synthetic), Berlin')
    c.setFillColor(HexColor('#eef3fb')); c.rect(50, 590, 495, 22, fill=1, stroke=0); c.setFillColor(ink)
    c.setFont('Helvetica-Bold', 10)
    for x, title in [(58, 'Description'), (330, 'Qty'), (400, 'Unit price'), (545, 'Amount')]:
        (c.drawRightString if title == 'Amount' else c.drawString)(x, 597, title)
    c.setFont('Helvetica', 10)
    items = [('Weekly sales dashboard setup', '1', '£800.00', '£800.00'),
             ('CSV data cleaning (per file)', '4', '£85.00', '£340.00'),
             ('Support hours', '2', '£50.00', '£100.00')]
    for i, (desc, qty, unit, amount) in enumerate(items):
        y = 570 - i * 20
        c.drawString(58, y, desc); c.drawString(330, y, qty); c.drawString(400, y, unit); c.drawRightString(545, y, amount)
    totals = [('Net total', '£1,240.00'), ('VAT (20%)', '£248.00')]
    for i, (label, value) in enumerate(totals):
        c.drawString(360, 480 - i * 18, label); c.drawRightString(545, 480 - i * 18, value)
    c.setFont('Helvetica-Bold', 12); c.drawString(360, 438, 'Total due'); c.drawRightString(545, 438, '£1,488.00')
    c.setFont('Helvetica', 8); c.drawString(50, 60, 'Synthetic document generated for a portfolio demo. No real company, customer or payment data.')
    c.save()


for index, lines in enumerate(layouts, 1):
    target = root / f'invoice-{index}.pdf'
    if not target.exists():
        simple_invoice(target, lines)
target = root / 'invoice-3.pdf'
if not target.exists():
    realistic_invoice(target)
