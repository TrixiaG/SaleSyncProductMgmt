import sys
import os

# Add the root directory of the project to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from .models import ProdInventory, db  # Use the absolute import here

        
# Inventory Report setup
testid = datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p")
documentTitle = 'The Crazy Fish'
subTitle = f"Report Generated at {testid}"
basename = str("InventoryReport")
fileName = "_".join([basename, testid])

pdf = canvas.Canvas(fileName, pagesize=letter)

# Fetch data from database
inventory_data = ProdInventory.query.all()


pdf.setTitle(documentTitle)


pdf.setFont('Helvetica-Bold', 12)
pdf.drawCentredString(300, 750, "THE CRAZY FISH MAN")
pdf.drawCentredString(300, 735, "Inventory Report")

pdf.setFont('Helvetica', 10)
pdf.drawCentredString(300, 700, subTitle)

# Table data and formatting
data = [['Product Type', 'Product Code', 'Product Name', 'Stock', 'Price']]

for item in inventory_data:
    data.append([
        item.ptype,
        item.pcode,
        item.pname,
        str(item.pstock),
        str(item.pprice)
    ])

table_style = TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.orange),  # Header color
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.gray),     # Header text color
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
])

# Create Table object
table = Table(data)
table.setStyle(table_style)

# Draw table on PDF
table.wrapOn(pdf, 400, 600)
table.drawOn(pdf, 72, 600)  

# Save PDF buffer
pdf.save()


print(f"PDF generated successfully: {fileName}")

