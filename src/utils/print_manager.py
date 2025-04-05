import os
import tempfile
import logging
import subprocess
import platform
from datetime import datetime
from reportlab.lib.pagesizes import A6
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class PrintManager:
    def __init__(self):
        self.logger = logging.getLogger('invoice_manager')
        # Create a temp directory for generated PDFs if it doesn't exist
        self.temp_dir = os.path.join(tempfile.gettempdir(), 'invoice_manager')
        os.makedirs(self.temp_dir, exist_ok=True)
        
    def generate_invoice_pdf(self, invoice_data, items_data, logo_path=None):
        """Generate PDF invoice for 100x150mm paper size"""
        try:
            # Set up file path
            pdf_path = os.path.join(
                self.temp_dir, 
                f"invoice_{invoice_data['invoice_number'].replace('-', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
            # Create custom page size (100x150mm)
            page_width = 100 * mm
            page_height = 150 * mm
            
            # Create PDF document with exact 100x150mm size
            doc = SimpleDocTemplate(
                pdf_path, 
                pagesize=(page_width, page_height),
                rightMargin=3*mm,  # Reduced margins for smaller paper
                leftMargin=3*mm,
                topMargin=3*mm,
                bottomMargin=3*mm
            )
            
            # Prepare styles
            styles = getSampleStyleSheet()
            
            # Add custom styles with smaller font sizes for smaller paper
            styles.add(
                ParagraphStyle(
                    name='CompanyName',
                    parent=styles['Heading1'],
                    fontSize=12,  # Smaller font size
                    alignment=1,  # Center
                    spaceAfter=1*mm  # Reduced spacing after company name
                )
            )
            
            styles.add(
                ParagraphStyle(
                    name='Location',
                    parent=styles['Normal'],
                    fontSize=8,  # Smaller font size for location
                    alignment=1,  # Center
                    spaceAfter=4*mm  # Add margin between location and title
                )
            )
            
            styles.add(
                ParagraphStyle(
                    name='InvoiceTitle',
                    parent=styles['Heading1'],
                    fontSize=10,  # Smaller font size
                    alignment=1,  # Center
                    spaceAfter=2*mm  # Reduced spacing
                )
            )
            
            styles.add(
                ParagraphStyle(
                    name='SectionTitle',
                    parent=styles['Heading2'],
                    fontSize=8,  # Smaller font size
                    alignment=0  # Left
                )
            )
            
            styles.add(
                ParagraphStyle(
                    name='Normal_Center',
                    parent=styles['Normal'],
                    fontSize=8,  # Smaller font size
                    alignment=1  # Center
                )
            )
            
            styles.add(
                ParagraphStyle(
                    name='Normal_Small',
                    parent=styles['Normal'],
                    fontSize=7  # Even smaller font for details
                )
            )
            
            styles.add(
                ParagraphStyle(
                    name='Small',
                    parent=styles['Normal'],
                    fontSize=6  # Very small font for footer info
                )
            )
            
            styles.add(
                ParagraphStyle(
                    name='Footer',
                    parent=styles['Normal'],
                    fontSize=6,  # Very small font for footer
                    alignment=1,  # Center
                    spaceAfter=0,  # No spacing after paragraphs in footer
                    leading=7  # Tighter line spacing
                )
            )
            
            # Build content for PDF
            elements = []
            
            # Header - Company Name and Logo
            header_data = []
            
            if logo_path and os.path.exists(logo_path):
                # Add logo with smaller size
                img = Image(logo_path, width=15*mm, height=15*mm)
                header_data.append(img)
            
            # Company name and location - Updated company name to "Thirdy Kitchenwares"
            company_info = [
                Paragraph("Thirdy Kitchenwares", styles['CompanyName']),
                Paragraph("Mexico, Pampanga", styles['Location'])
            ]
            header_data.append(company_info)
            
            # Create a table for the header to position logo and company name side by side
            if len(header_data) > 1:  # If we have a logo
                header_table = Table([header_data], colWidths=[15*mm, 79*mm])
                header_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                    ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ]))
                elements.append(header_table)
            else:
                # Just add the company info
                elements.extend(company_info)
            
            # Invoice Title
            elements.append(Paragraph("SALES INVOICE", styles['InvoiceTitle']))
            
            # Invoice Number
            elements.append(Paragraph(f"INVOICE NUMBER: {invoice_data['invoice_number']}", styles['SectionTitle']))
            elements.append(Spacer(1, 1*mm))
            
            # Date
            elements.append(Paragraph(f"Date: {invoice_data['date']}", styles['Normal_Small']))
            elements.append(Spacer(1, 1*mm))
            
            # Customer Details
            elements.append(Paragraph(f"Customer: {invoice_data['customer_name']}", styles['Normal_Small']))
            elements.append(Spacer(1, 1*mm))
            
            # Items table - more compact for smaller paper
            items_table_data = [['Code', 'Item', 'Price']]  # Shorter column headers
            for item in items_data:
                # Add peso sign to price
                items_table_data.append([
                    item['item_id'],
                    item['description'],
                    f"₱{item['price']:.2f}"
                ])
            
            # Add total as the last row with peso sign
            items_table_data.append(['', 'Total:', f"₱{invoice_data['total_amount']:.2f}"])
            
            # Create items table - optimize column widths for the small paper
            items_table = Table(
                items_table_data,
                colWidths=[15*mm, 59*mm, 20*mm],  # Adjusted widths
                style=[
                    ('GRID', (0, 0), (-1, -2), 0.25, colors.grey),  # Lighter grid lines
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 7),  # Smaller font for table
                ]
            )
            elements.append(items_table)
            elements.append(Spacer(1, 2*mm))
            
            # Note about shipping
            elements.append(Paragraph("Note: Shipping fee is upon delivery!", styles['Normal_Small']))
            
            # Add a spacer to push the footer to the bottom
            elements.append(Spacer(1, 15*mm))
            
            # Payment Details as footer - use KeepTogether to ensure footer stays together
            footer_elements = [
                Paragraph(f"Mode of Payment: {invoice_data['mode_of_payment']}", styles['Footer']),
                Paragraph("Gcash: 09544370316 / 09544370317 - Desiree Salazar", styles['Footer']),
                Paragraph("Gcash: 09062959278 - Robert Salazar", styles['Footer']),
                Paragraph("BDO: 001330781323 - Desiree S Salazar", styles['Footer']),
                Paragraph("Facebook: Thirdy Kitchenwares", styles['Footer'])
            ]
            
            # Use KeepTogether to ensure footer stays as one block
            elements.append(KeepTogether(footer_elements))
            
            # Build the PDF
            doc.build(elements)
            
            self.logger.info(f"Generated invoice PDF: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            self.logger.error(f"Error generating PDF: {str(e)}")
            return None
    
    def open_pdf(self, pdf_path):
        """Open the PDF with the default system PDF viewer"""
        if not os.path.exists(pdf_path):
            self.logger.error(f"PDF file not found: {pdf_path}")
            return False
            
        try:
            if platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', pdf_path], check=True)
            elif platform.system() == 'Windows':  # Windows
                os.startfile(pdf_path)
            else:  # Linux or other
                subprocess.run(['xdg-open', pdf_path], check=True)
                
            self.logger.info(f"Opened PDF: {pdf_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error opening PDF: {str(e)}")
            return False
