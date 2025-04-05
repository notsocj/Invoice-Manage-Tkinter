import os
import tempfile
import logging
import subprocess
import platform
import time
from datetime import datetime
from reportlab.lib.pagesizes import A6
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, Flowable, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfMerger  # Add this import for merging PDFs

# Register a font that properly supports the peso sign
try:
    # Try to register DejaVuSans as it supports currency symbols
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))
except:
    # Font files might not be available, will handle this case in generate_invoice_pdf
    pass

class MCLine(Flowable):
    """Custom Flowable for drawing a line with custom style"""
    def __init__(self, width, height=0, color=colors.black, dash=None):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.color = color
        self.dash = dash

    def draw(self):
        self.canv.saveState()
        self.canv.setLineWidth(self.height)
        self.canv.setStrokeColor(self.color)
        if self.dash:
            self.canv.setDash(self.dash, 0)
        self.canv.line(0, 0, self.width, 0)
        self.canv.restoreState()

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
                rightMargin=2*mm,  # Reduced margins for smaller paper
                leftMargin=2*mm,
                topMargin=2*mm,
                bottomMargin=2*mm
            )
            
            # Check if DejaVuSans was registered, use regular fonts otherwise
            use_default_fonts = True
            try:
                pdfmetrics.getFont('DejaVuSans')
                use_default_fonts = False
            except:
                pass
            
            # Prepare styles
            
            styles = getSampleStyleSheet()
            
            # Determine if we need to adjust for multiple items
            has_multiple_items = len(items_data) > 1
            # Calculate how much to reduce sizes (more items = smaller size)
            scaling_factor = max(0.85, min(1.0, 1.1 - 0.05 * len(items_data)))
            
            # Add custom styles with smaller font sizes for smaller paper
            if not use_default_fonts:
                base_font = 'DejaVuSans'
                bold_font = 'DejaVuSans-Bold'
            else:
                base_font = 'Helvetica'
                bold_font = 'Helvetica-Bold'
            
            # Define styles - we'll use smaller fonts when there are multiple items
            base_size = 12 if not has_multiple_items else 11
            styles.add(
                ParagraphStyle(
                    name='CompanyName',
                    parent=styles['Heading1'],
                    fontName=bold_font,
                    fontSize=base_size,  # Adjust base size
                    alignment=1,  # Center
                    spaceAfter=1*mm  # Reduced spacing after company name
                )
            )
            
            # Location style - smaller for multiple items
            location_size = 8 if not has_multiple_items else 7
            styles.add(
                ParagraphStyle(
                    name='Location',
                    parent=styles['Normal'],
                    fontName=base_font,
                    fontSize=location_size,
                    alignment=1,  # Center
                    spaceAfter=2*mm * scaling_factor  # Reduce spacing with scaling factor
                )
            )
            
            # Invoice title - smaller for multiple items
            title_size = 10 if not has_multiple_items else 9
            styles.add(
                ParagraphStyle(
                    name='InvoiceTitle',
                    parent=styles['Heading1'],
                    fontName=bold_font,
                    fontSize=title_size,
                    alignment=1,  # Center
                    spaceAfter=2*mm * scaling_factor  # Reduced spacing
                )
            )
            
            # Section title - smaller for multiple items
            section_size = 8 if not has_multiple_items else 7
            styles.add(
                ParagraphStyle(
                    name='SectionTitle',
                    parent=styles['Heading2'],
                    fontName=bold_font,
                    fontSize=section_size,
                    alignment=0,  # Left
                    spaceAfter=1*mm * scaling_factor  # Tighter spacing
                )
            )
            
            # Add other styles with similar scaling logic
            styles.add(
                ParagraphStyle(
                    name='Normal_Center',
                    parent=styles['Normal'],
                    fontName=base_font,
                    fontSize=8 * scaling_factor,
                    alignment=1  # Center
                )
            )
            
            normal_small_size = 7 if not has_multiple_items else 6
            styles.add(
                ParagraphStyle(
                    name='Normal_Small',
                    parent=styles['Normal'],
                    fontName=base_font,
                    fontSize=normal_small_size  # Even smaller font for details
                )
            )
            
            bold_small_size = 7 if not has_multiple_items else 6
            styles.add(
                ParagraphStyle(
                    name='Bold_Small',
                    parent=styles['Normal'],
                    fontName=bold_font,
                    fontSize=bold_small_size  # Small bold text
                )
            )
            
            # Very small font for footer
            styles.add(
                ParagraphStyle(
                    name='Small',
                    parent=styles['Normal'],
                    fontName=base_font,
                    fontSize=6  # Very small font for footer info
                )
            )
            
            # Footer stays smallest regardless of item count
            styles.add(
                ParagraphStyle(
                    name='Footer',
                    parent=styles['Normal'],
                    fontName=base_font,
                    fontSize=6,  # Very small font for footer
                    alignment=1,  # Center
                    spaceAfter=0,  # No spacing after paragraphs in footer
                    leading=6  # Even tighter line spacing when multiple items
                )
            )
            
            # Address style - scale down for multiple items
            address_size = 7 if not has_multiple_items else 6
            address_leading = 8 if not has_multiple_items else 7
            styles.add(
                ParagraphStyle(
                    name='CustomerAddress',
                    parent=styles['Normal'],
                    fontName=base_font,
                    fontSize=address_size,
                    leading=address_leading,  # Tighter line spacing for address
                    spaceAfter=1*mm * scaling_factor  # Minimal spacing after address
                )
            )
            
            # Define peso symbol with fallbacks if font doesn't support it
            if use_default_fonts:
                peso_symbol = "PHP "  # Use PHP text as fallback
            else:
                peso_symbol = "₱"  # Use proper peso sign
            
            # Build content for PDF
            elements = []
            
            # Create a light gray color for backgrounds
            light_gray = colors.Color(0.9, 0.9, 0.9)  # Use explicit RGB values instead of .lighter() method
            lighter_gray = colors.Color(0.95, 0.95, 0.95)  # Very light gray for subtle backgrounds
            
            # Header with light gray background - make it more compact if multiple items
            header_height = 20*mm if not has_multiple_items else 18*mm
            header_background = Table(
                [[""]],
                colWidths=[96*mm],
                rowHeights=[header_height]
            )
            header_background.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), light_gray),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
            ]))
            
            # Header - Company Name and Logo
            header_data = []
            
            # Logo size adjusted for multiple items
            logo_size = 15*mm if not has_multiple_items else 12*mm
            
            if logo_path and os.path.exists(logo_path):
                # Add logo with adjusted size
                try:
                    img = Image(logo_path, width=logo_size, height=logo_size)
                    header_data.append(img)
                except Exception as e:
                    # If logo loading fails, log error but continue without logo
                    self.logger.error(f"Failed to load logo: {str(e)}")
                    header_data.append("")
            
            # Company name and location with enhanced styling
            company_info = [
                Paragraph("Thirdy Kitchenwares", styles['CompanyName']),
                Paragraph("Mexico, Pampanga", styles['Location'])
            ]
            header_data.append(company_info)
            
            # Create a table for the header to position logo and company name side by side
            if len(header_data) > 1:  # If we have a logo
                header_table = Table([header_data], colWidths=[logo_size, 96*mm-logo_size])
                header_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                    ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ]))
                
                # Wrap header in a container table with background
                header_container = Table(
                    [[header_table]],
                    colWidths=[96*mm],
                    style=[
                        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 3 if has_multiple_items else 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 3 if has_multiple_items else 6),
                    ]
                )
                elements.append(header_container)
            else:
                # Just add the company info
                company_container = Table(
                    [[company_info[0]], [company_info[1]]],
                    colWidths=[96*mm],
                    style=[
                        ('BACKGROUND', (0, 0), (-1, -1), light_gray),
                        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 2 if has_multiple_items else 3),
                        ('TOPPADDING', (0, 0), (-1, -1), 2 if has_multiple_items else 3),
                    ]
                )
                elements.append(company_container)
            
            # Space after header reduced for multiple items
            elements.append(Spacer(1, 1*mm if has_multiple_items else 2*mm))
            
            # Invoice Title with decorative lines
            thin_line = 0.3 if has_multiple_items else 0.5
            elements.append(HRFlowable(width="100%", thickness=thin_line, color=colors.grey, spaceAfter=0.5*mm))
            elements.append(Paragraph("SALES INVOICE", styles['InvoiceTitle']))
            elements.append(HRFlowable(width="100%", thickness=thin_line, color=colors.grey, spaceBefore=0.5*mm, spaceAfter=1*mm))
            
            # Invoice info table with better styling - more compact for multiple items
            invoice_info_data = [
                ["Invoice Number:", invoice_data.get('invoice_number', 'N/A')],
                ["Date:", invoice_data.get('date', 'N/A')]
            ]
            
            # Adjust cell padding based on item count
            cell_padding = 1 if has_multiple_items else 2
            
            invoice_info_table = Table(
                invoice_info_data,
                colWidths=[30*mm, 64*mm],
                style=[
                    ('FONT', (0, 0), (0, -1), bold_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 7 * scaling_factor),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), cell_padding),
                    ('TOPPADDING', (0, 0), (-1, -1), cell_padding),
                    ('BACKGROUND', (0, 0), (0, -1), light_gray),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
            elements.append(invoice_info_table)
            elements.append(Spacer(1, 1*mm if has_multiple_items else 3*mm))
            
            # Customer section with decorative box
            customer_title = Table(
                [["TO:"]],
                colWidths=[96*mm],
                style=[
                    ('FONT', (0, 0), (-1, -1), bold_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 8 * scaling_factor),
                    ('BACKGROUND', (0, 0), (-1, -1), light_gray),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), cell_padding),
                    ('TOPPADDING', (0, 0), (-1, -1), cell_padding),
                    ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
                ]
            )
            elements.append(customer_title)
            
            # Format customer name and address properly in a styled box
            customer_data = []
            customer_name = invoice_data.get('customer_name', 'N/A')
            customer_data.append([Paragraph(f"<b>{customer_name}</b>", styles['Normal_Small'])])
            
            # Format address with line breaks if provided (with error handling)
            customer_address = invoice_data.get('customer_address', '')
            if customer_address:
                try:
                    # Replace any newlines with <br/> for proper paragraph formatting
                    formatted_address = customer_address.replace('\n', '<br/>')
                    # Truncate address if it's too long and we have multiple items
                    if has_multiple_items and len(formatted_address) > 100:
                        formatted_address = formatted_address[:97] + "..."
                    customer_data.append([Paragraph(formatted_address, styles['CustomerAddress'])])
                except Exception as e:
                    # If address formatting fails, use plain text
                    self.logger.error(f"Failed to format address: {str(e)}")
                    customer_data.append([Paragraph(customer_address, styles['CustomerAddress'])])
            
            customer_box = Table(
                customer_data,
                colWidths=[96*mm],
                style=[
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 2*mm),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), cell_padding),
                    ('TOPPADDING', (0, 0), (-1, -1), cell_padding),
                ]
            )
            elements.append(customer_box)
            elements.append(Spacer(1, 1*mm if has_multiple_items else 3*mm))
            
            # Items section title with background
            items_title = Table(
                [["ITEMS"]],
                colWidths=[96*mm],
                style=[
                    ('FONT', (0, 0), (-1, -1), bold_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 8 * scaling_factor),
                    ('BACKGROUND', (0, 0), (-1, -1), light_gray),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5 if has_multiple_items else 1),
                    ('TOPPADDING', (0, 0), (-1, -1), 0.5 if has_multiple_items else 1),
                    ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ]
            )
            elements.append(items_title)
            
            # Items table with more professional design
            items_table_data = [['Item Code', 'Description', 'Qty', 'Price', 'Total']]
            
            # Add items with error handling
            for item in items_data:
                try:
                    # Prioritize getting the actual item_code instead of item_id
                    # Look for item_code directly or as a property in an Item object
                    if 'item_code' in item:
                        item_code = item['item_code']
                    # If there's an item object reference with an item_code attribute
                    elif 'item' in item and hasattr(item['item'], 'item_code'):
                        item_code = item['item'].item_code
                    # Last resort: use item_id and format it like a code
                    else:
                        item_id = item.get('item_id', 'N/A')
                        # Try to format it like TKW-xxx if numeric
                        try:
                            if isinstance(item_id, int) or (isinstance(item_id, str) and item_id.isdigit()):
                                item_code = f"TKW-{int(item_id):03d}"
                            else:
                                item_code = str(item_id)
                        except Exception:
                            item_code = str(item_id)
                    
                    description = item.get('description', 'N/A')
                    
                    # Truncate description if too long and we have multiple items
                    if has_multiple_items and len(description) > 15:
                        description = description[:12] + "..."
                    
                    quantity = item.get('quantity', 0)
                    price = item.get('price', 0.0)
                    item_total = quantity * price
                    
                    # Format price and total with more compact representation
                    price_display = f"{peso_symbol}{price:.2f}"
                    total_display = f"{peso_symbol}{item_total:.2f}"
                    
                    items_table_data.append([
                        item_code,
                        description,
                        str(quantity),
                        price_display,
                        total_display
                    ])
                except Exception as e:
                    # If item processing fails, log error and add a placeholder row
                    self.logger.error(f"Error processing item: {str(e)}")
                    items_table_data.append([
                        "Error",
                        "Error processing item",
                        "0",
                        f"{peso_symbol}0.00",
                        f"{peso_symbol}0.00"
                    ])
            
            # Add total as the last row (with error handling)
            try:
                total_amount = invoice_data.get('total_amount', 0.0)
                total_display = f"{peso_symbol}{total_amount:.2f}"
                items_table_data.append(['', '', '', 'Total:', total_display])
            except Exception as e:
                self.logger.error(f"Error formatting total: {str(e)}")
                items_table_data.append(['', '', '', 'Total:', f"{peso_symbol}0.00"])
            
            # Create items table with enhanced styling - smaller row heights for multiple items
            row_padding = 0.5 if has_multiple_items else 1
            
            # Adjust column widths to better fit currency values
            item_code_width = 13*mm if has_multiple_items else 15*mm
            desc_width = 35*mm if has_multiple_items else 33*mm  # Slightly reduced to give more space to price/total
            qty_width = 8*mm if has_multiple_items else 10*mm
            price_width = 16*mm if has_multiple_items else 18*mm  # Increased width for price
            total_width = 18*mm if has_multiple_items else 20*mm  # Increased width for total
            
            items_table = Table(
                items_table_data,
                colWidths=[item_code_width, desc_width, qty_width, price_width, total_width],
                style=[
                    # Header styling
                    ('BACKGROUND', (0, 0), (-1, 0), light_gray),
                    ('FONT', (0, 0), (-1, 0), bold_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 7 * scaling_factor),
                    
                    # Grid styling
                    ('GRID', (0, 0), (-1, -2), 0.3 if has_multiple_items else 0.5, colors.grey),
                    
                    # Alignment
                    ('ALIGN', (0, 0), (0, -2), 'CENTER'),  # Center item codes
                    ('ALIGN', (2, 0), (2, -2), 'CENTER'),  # Center quantities
                    ('ALIGN', (3, 0), (4, -1), 'RIGHT'),   # Right align prices and totals
                    ('RIGHTPADDING', (3, 0), (4, -1), 4),  # Extra right padding for price/total columns
                    
                    # Total row styling
                    ('FONTNAME', (3, -1), (-1, -1), bold_font),
                    ('LINEABOVE', (3, -1), (-1, -1), 1, colors.black),
                    ('SPAN', (0, -1), (2, -1)),            # Span the empty cells in total row
                    
                    # Make rows more compact for many items
                    ('BOTTOMPADDING', (0, 0), (-1, -1), row_padding),
                    ('TOPPADDING', (0, 0), (-1, -1), row_padding),
                ]
            )
            elements.append(items_table)
            elements.append(Spacer(1, 1*mm if has_multiple_items else 3*mm))
            
            # Payment information in a styled box - more compact for multiple items
            payment_mode = invoice_data.get('mode_of_payment', 'N/A')
            payment_info = Table(
                [[Paragraph(f"<b>Mode of Payment:</b> {payment_mode}", styles['Normal_Small'])]],
                colWidths=[96*mm],
                style=[
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (-1, -1), lighter_gray),
                    ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 2*mm),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 1 if has_multiple_items else 2),
                    ('TOPPADDING', (0, 0), (-1, -1), 1 if has_multiple_items else 2),
                ]
            )
            elements.append(payment_info)
            
            # Note about shipping in italics with visual emphasis
            shipping_note = Table(
                [[Paragraph("<i>Note: Shipping fee is upon delivery!</i>", styles['Normal_Small'])]],
                colWidths=[96*mm],
                style=[
                    ('LEFTPADDING', (0, 0), (-1, -1), 2*mm),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 2*mm),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 1 if has_multiple_items else 2),
                    ('TOPPADDING', (0, 0), (-1, -1), 1 if has_multiple_items else 2),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ]
            )
            elements.append(shipping_note)
            
            # Calculate remaining space for footer positioning
            # Estimate used space so far
            remaining_space = page_height - 120*mm - (len(items_data) * 5*mm)
            
            # Add a spacer to push the footer to the bottom, but adjust for item count
            # The more items, the less space we add
            spacer_height = max(2*mm, min(10*mm, remaining_space))
            elements.append(Spacer(1, spacer_height))
            
            # Add a line before footer
            elements.append(HRFlowable(width="100%", thickness=0.3, color=colors.grey, spaceBefore=0.5*mm, spaceAfter=0.5*mm))
            
            # Payment Details as footer - use KeepTogether to ensure footer stays together
            # For multiple items, make footer even more compact
            footer_elements = []
            if has_multiple_items:
                # Ultra compact footer for multiple items
                footer_elements = [
                    Paragraph("Payment: Gcash 0954-437-0316/0317 Desiree Salazar | 0906-295-9278 Robert Salazar", styles['Footer']),
                    Paragraph("BDO: 001330781323 Desiree S Salazar | FB: Thirdy Kitchenwares", styles['Footer'])
                ]
            else:
                # Standard footer
                footer_elements = [
                    Paragraph("Payment Details:", styles['Footer']),
                    Paragraph(f"Gcash: 09544370316 / 09544370317 - Desiree Salazar", styles['Footer']),
                    Paragraph(f"Gcash: 09062959278 - Robert Salazar", styles['Footer']),
                    Paragraph(f"BDO: 001330781323 - Desiree S Salazar", styles['Footer']),
                    Paragraph(f"Facebook: Thirdy Kitchenwares", styles['Footer'])
                ]
            
            # Create footer with background for visual separation
            footer_table = Table(
                [[element] for element in footer_elements],
                colWidths=[96*mm],
                style=[
                    ('BACKGROUND', (0, 0), (-1, 0), lighter_gray),  # Light background for footer title
                    ('FONTNAME', (0, 0), (0, 0), bold_font),  # Bold the title
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5 if has_multiple_items else 1),
                    ('TOPPADDING', (0, 0), (-1, -1), 0.5 if has_multiple_items else 1),
                ]
            )
            
            # Use KeepTogether to ensure footer stays as one block
            elements.append(KeepTogether(footer_table))
            
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
    
    def print_pdf(self, pdf_path):
        """Print the PDF directly to the default printer (without previewing)"""
        if not os.path.exists(pdf_path):
            self.logger.error(f"PDF file not found: {pdf_path}")
            return False
            
        try:
            if platform.system() == 'Windows':
                # First try: Use SumatraPDF if available (best for thermal printing with custom paper size)
                sumatra_paths = [
                    r"C:\Program Files\SumatraPDF\SumatraPDF.exe",
                    r"C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe"
                ]
                
                for sumatra_path in sumatra_paths:
                    if os.path.exists(sumatra_path):
                        try:
                            # Use shell=True to avoid permission issues
                            subprocess.run([
                                sumatra_path, 
                                "-print-to-default", 
                                "-print-settings", "paper=Custom.100x150mm",
                                pdf_path
                            ], check=True, shell=True)
                            self.logger.info(f"Printed PDF using SumatraPDF: {pdf_path}")
                            return True
                        except subprocess.SubprocessError as e:
                            self.logger.warning(f"SumatraPDF printing failed: {str(e)}")
                            # Continue to next fallback option
                
                # Second try: Use the default Windows print command
                try:
                    # Try to import win32 modules
                    try:
                        import win32api
                        import win32print
                        
                        win32api.ShellExecute(0, "print", pdf_path, None, ".", 0)
                        self.logger.info(f"Printed PDF using win32api: {pdf_path}")
                        return True
                    except ImportError:
                        self.logger.warning("win32api module not available")
                    
                    # Third try: Use os.startfile with "print" verb
                    try:
                        os.startfile(pdf_path, "print")
                        self.logger.info(f"Printed PDF using os.startfile: {pdf_path}")
                        return True
                    except Exception as e:
                        self.logger.warning(f"os.startfile printing failed: {str(e)}")
                    
                    # Last resort: Just open the PDF - fallback to showing print dialog
                    self.logger.warning("Direct printing failed, opening PDF for manual printing")
                    os.startfile(pdf_path)
                    self.logger.info(f"Opened PDF for manual printing: {pdf_path}")
                    return True
                    
                except Exception as e:
                    self.logger.error(f"All Windows printing methods failed: {str(e)}")
                    return False
                
            elif platform.system() == 'Darwin':  # macOS
                try:
                    # Try with paper size option first
                    subprocess.run([
                        'lpr', 
                        '-o', 'media=Custom.100x150mm',  # Set paper size
                        pdf_path
                    ], check=True)
                    self.logger.info(f"Printed PDF using lpr with custom size: {pdf_path}")
                    return True
                except subprocess.SubprocessError:
                    # Fallback to standard lpr command without paper size
                    try:
                        subprocess.run(['lpr', pdf_path], check=True)
                        self.logger.info(f"Printed PDF using standard lpr: {pdf_path}")
                        return True
                    except subprocess.SubprocessError as e:
                        self.logger.error(f"macOS printing failed: {str(e)}")
                        # Open PDF as last resort
                        subprocess.run(['open', pdf_path], check=True)
                        return False
                
            else:  # Linux
                try:
                    # Try with paper size option first
                    subprocess.run([
                        'lp', 
                        '-o', 'media=Custom.100x150mm',  
                        pdf_path
                    ], check=True)
                    self.logger.info(f"Printed PDF using lp with custom size: {pdf_path}")
                    return True
                except subprocess.SubprocessError:
                    # Fallback to standard lp command
                    try:
                        subprocess.run(['lp', pdf_path], check=True)
                        self.logger.info(f"Printed PDF using standard lp: {pdf_path}")
                        return True
                    except subprocess.SubprocessError as e:
                        self.logger.error(f"Linux printing failed: {str(e)}")
                        # Open PDF as last resort
                        subprocess.run(['xdg-open', pdf_path], check=True)
                        return False
                
        except Exception as e:
            self.logger.error(f"Error printing PDF: {str(e)}")
            # As a fallback, just try to open the PDF
            try:
                self.open_pdf(pdf_path)
                self.logger.info(f"Opened PDF after print error: {pdf_path}")
                return False  # Still return False as direct printing failed
            except:
                pass
            return False
    
    def print_direct(self, invoice_data=None, items_data=None, logo_path=None, pdf_path=None):
        """Print invoice directly using a simple and reliable approach
        
        Args:
            invoice_data: Invoice data dict (can be None if pdf_path provided)
            items_data: Items data dict (can be None if pdf_path provided)
            logo_path: Optional path to logo image
            pdf_path: Optional direct path to PDF (skips PDF generation if provided)
            
        Returns:
            Boolean indicating success/failure
        """
        try:
            # If pdf_path is not provided, generate it
            if not pdf_path:
                pdf_path = self.generate_invoice_pdf(invoice_data, items_data, logo_path)
                
            if not pdf_path:
                self.logger.error("Failed to obtain PDF for printing")
                return False
            
            # Use the most reliable method to print on the current OS
            if platform.system() == 'Windows':
                # On Windows, use os.startfile with 'print' verb
                self.logger.info(f"Printing PDF using os.startfile: {pdf_path}")
                os.startfile(pdf_path, 'print')
                return True
                
            elif platform.system() == 'Darwin':  # macOS
                # For macOS, use lpr command for direct printing
                self.logger.info(f"Printing PDF using lpr: {pdf_path}")
                os.system(f"lpr '{pdf_path}'")
                return True
                
            else:  # Linux
                # For Linux, use lp command
                self.logger.info(f"Printing PDF using lp: {pdf_path}")
                os.system(f"lp '{pdf_path}'")
                return True
                
        except Exception as e:
            self.logger.error(f"Error in direct printing: {str(e)}")
            # As a fallback, try to open the PDF regularly
            try:
                self.open_pdf(pdf_path)
                self.logger.info(f"Opened PDF after print error: {pdf_path}")
                return True  # Consider this a success since at least the user can see the document
            except Exception as open_error:
                self.logger.error(f"Error opening PDF: {str(open_error)}")
                return False
    
    def print_multiple_invoices_as_one(self, invoice_data_list, logo_path=None):
        """Generate a single PDF with multiple invoices and print it
        
        Args:
            invoice_data_list: List of (invoice_data, items_data) tuples
            logo_path: Optional path to logo image
            
        Returns:
            Boolean indicating success/failure
        """
        try:
            # Generate individual invoice PDFs first
            pdf_paths = []
            for invoice_data, items_data in invoice_data_list:
                pdf_path = self.generate_invoice_pdf(invoice_data, items_data, logo_path)
                if pdf_path:
                    pdf_paths.append(pdf_path)
            
            if not pdf_paths:
                self.logger.error("Failed to generate any invoice PDFs for batch printing")
                return False
                
            # If there's only one PDF, print it directly
            if len(pdf_paths) == 1:
                return self.print_direct(None, None, pdf_path=pdf_paths[0])
                
            # Merge all PDFs into one file
            merged_pdf_path = self._merge_pdfs(pdf_paths)
            if not merged_pdf_path:
                self.logger.error("Failed to merge invoice PDFs")
                return False
                
            # Print the merged PDF
            return self.print_direct(None, None, pdf_path=merged_pdf_path)
            
        except Exception as e:
            self.logger.error(f"Error in batch printing: {str(e)}")
            return False
    
    def _merge_pdfs(self, pdf_paths):
        """Merge multiple PDFs into a single file
        
        Args:
            pdf_paths: List of PDF file paths to merge
            
        Returns:
            Path to merged PDF file or None if failed
        """
        try:
            # Create output file path
            output_path = os.path.join(
                self.temp_dir, 
                f"batch_invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
            # Use PdfMerger to combine PDFs
            merger = PdfMerger()
            
            for pdf_path in pdf_paths:
                if os.path.exists(pdf_path):
                    merger.append(pdf_path)
                
            # Write to output file
            merger.write(output_path)
            merger.close()
            
            self.logger.info(f"Successfully merged {len(pdf_paths)} PDFs into: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error merging PDFs: {str(e)}")
            return None
    
    def batch_print_invoices(self, pdf_paths):
        """Print multiple PDFs in sequence"""
        success_count = 0
        fail_count = 0
        
        for pdf_path in pdf_paths:
            # Add a small delay between print jobs to avoid printer queue issues
            if success_count > 0:
                time.sleep(1)  # 1-second delay between prints
                
            result = self.print_pdf(pdf_path)
            if result:
                success_count += 1
            else:
                fail_count += 1
        
        self.logger.info(f"Batch printing completed: {success_count} succeeded, {fail_count} failed")
        return success_count, fail_count
