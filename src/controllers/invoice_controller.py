import logging
import threading
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from src.models.invoice_model import Invoice, InvoiceItem, InvoiceStatus
from src.models.client_model import Client
from src.views.invoice_view import InvoiceView
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import os

class InvoiceController:
    def __init__(self, db, main_view):
        self.db = db
        self.main_view = main_view
        self.view = None
        self.logger = logging.getLogger('invoice_manager')
    
    def load_view(self, parent_frame):
        """Load the invoice view into the parent frame"""
        self.view = InvoiceView(parent_frame, self)
        self.load_invoices()
    
    def load_invoices(self):
        """Load all invoices from the database"""
        self.logger.info("Loading invoices")
        
        # Use a separate thread for database operations
        def fetch_invoices():
            try:
                session = self.db.get_session()
                invoices = session.query(Invoice).order_by(Invoice.created_at.desc()).all()
                invoices_data = [invoice.to_dict() for invoice in invoices]
                session.close()
                
                # Update UI in the main thread
                self.view.after(0, lambda: self.view.display_invoices(invoices_data))
                
            except SQLAlchemyError as e:
                self.logger.error(f"Error fetching invoices: {str(e)}")
                self.view.after(0, lambda: self.view.show_error("Failed to load invoices"))
        
        thread = threading.Thread(target=fetch_invoices)
        thread.daemon = True
        thread.start()
    
    def get_clients(self):
        """Get all clients for the dropdown"""
        try:
            session = self.db.get_session()
            clients = session.query(Client).order_by(Client.name).all()
            clients_data = [{'id': client.id, 'name': client.name} for client in clients]
            session.close()
            return clients_data
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching clients: {str(e)}")
            return []
    
    def generate_invoice_number(self):
        """Generate a unique invoice number"""
        try:
            session = self.db.get_session()
            # Get the highest invoice number
            last_invoice = session.query(Invoice).order_by(Invoice.id.desc()).first()
            session.close()
            
            # Generate new invoice number
            today = datetime.now()
            year_month = today.strftime("%Y%m")
            
            if last_invoice:
                last_num = 0
                # Try to parse the last invoice number
                try:
                    last_id_str = last_invoice.invoice_number.split('-')[-1]
                    last_num = int(last_id_str)
                except (ValueError, IndexError):
                    pass
                
                new_num = last_num + 1
            else:
                new_num = 1
                
            # Format: INV-YYYYMM-XXXX (e.g., INV-202305-0001)
            invoice_number = f"INV-{year_month}-{new_num:04d}"
            
            return invoice_number
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error generating invoice number: {str(e)}")
            # Fallback invoice number
            return f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def add_invoice(self, invoice_data, items_data):
        """Add a new invoice to the database"""
        self.logger.info(f"Adding new invoice for client: {invoice_data['client_id']}")
        
        try:
            session = self.db.get_session()
            
            # Create invoice
            new_invoice = Invoice(**invoice_data)
            session.add(new_invoice)
            session.flush()  # This gives us the invoice ID without committing
            
            # Add invoice items
            for item_data in items_data:
                item_data['invoice_id'] = new_invoice.id
                item = InvoiceItem(**item_data)
                item.calculate_total()
                session.add(item)
            
            # Calculate invoice totals
            new_invoice.calculate_totals()
            
            session.commit()
            invoice_id = new_invoice.id
            session.close()
            
            self.logger.info(f"Invoice added successfully with ID: {invoice_id}")
            self.load_invoices()
            return True, invoice_id
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error adding invoice: {str(e)}")
            return False, str(e)
    
    def update_invoice(self, invoice_id, invoice_data, items_data):
        """Update an existing invoice"""
        self.logger.info(f"Updating invoice with ID: {invoice_id}")
        
        try:
            session = self.db.get_session()
            invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()
            
            if not invoice:
                session.close()
                self.logger.warning(f"Invoice with ID {invoice_id} not found")
                return False, "Invoice not found"
            
            # Update invoice attributes
            for key, value in invoice_data.items():
                setattr(invoice, key, value)
            
            # Delete existing items
            session.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice_id).delete()
            
            # Add updated items
            for item_data in items_data:
                item_data['invoice_id'] = invoice_id
                item = InvoiceItem(**item_data)
                item.calculate_total()
                session.add(item)
            
            # Recalculate invoice totals
            invoice.calculate_totals()
            
            session.commit()
            session.close()
            
            self.logger.info(f"Invoice updated successfully: {invoice_id}")
            self.load_invoices()
            return True, invoice_id
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating invoice: {str(e)}")
            return False, str(e)
    
    def delete_invoice(self, invoice_id):
        """Delete an invoice from the database"""
        self.logger.info(f"Deleting invoice with ID: {invoice_id}")
        
        try:
            session = self.db.get_session()
            invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()
            
            if not invoice:
                session.close()
                self.logger.warning(f"Invoice with ID {invoice_id} not found")
                return False, "Invoice not found"
            
            session.delete(invoice)  # This will cascade delete invoice items
            session.commit()
            session.close()
            
            self.logger.info(f"Invoice deleted successfully: {invoice_id}")
            self.load_invoices()
            return True, None
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error deleting invoice: {str(e)}")
            return False, str(e)
    
    def get_invoice(self, invoice_id):
        """Get a specific invoice by ID"""
        try:
            session = self.db.get_session()
            invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()
            
            if not invoice:
                session.close()
                return None, None
            
            invoice_data = invoice.to_dict()
            items_data = [item.to_dict() for item in invoice.items]
            
            session.close()
            return invoice_data, items_data
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching invoice: {str(e)}")
            return None, None
    
    def generate_pdf(self, invoice_id, output_path=None):
        """Generate a PDF for the invoice"""
        self.logger.info(f"Generating PDF for invoice: {invoice_id}")
        
        try:
            session = self.db.get_session()
            invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()
            
            if not invoice:
                session.close()
                self.logger.warning(f"Invoice with ID {invoice_id} not found")
                return False, "Invoice not found"
            
            if not output_path:
                # Create a directory for invoices if it doesn't exist
                invoice_dir = os.path.join(os.getcwd(), 'invoices')
                os.makedirs(invoice_dir, exist_ok=True)
                output_path = os.path.join(invoice_dir, f"invoice_{invoice.invoice_number}.pdf")
            
            # Create PDF
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            
            # Add title
            elements.append(Paragraph(f"INVOICE #{invoice.invoice_number}", styles['Title']))
            elements.append(Spacer(1, 20))
            
            # Add invoice information
            elements.append(Paragraph(f"Date: {invoice.issue_date.strftime('%B %d, %Y')}", styles['Normal']))
            elements.append(Paragraph(f"Due Date: {invoice.due_date.strftime('%B %d, %Y') if invoice.due_date else 'N/A'}", styles['Normal']))
            elements.append(Paragraph(f"Status: {invoice.status.value.upper()}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Add client information
            elements.append(Paragraph("Bill To:", styles['Heading2']))
            client = invoice.client
            elements.append(Paragraph(f"{client.name}", styles['Normal']))
            if client.company:
                elements.append(Paragraph(f"{client.company}", styles['Normal']))
            if client.address:
                elements.append(Paragraph(f"{client.address}", styles['Normal']))
            elements.append(Paragraph(f"{client.city}, {client.state} {client.postal_code}", styles['Normal']))
            elements.append(Paragraph(f"{client.country}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Add invoice items
            data = [["Description", "Quantity", "Unit Price", "Total"]]
            for item in invoice.items:
                data.append([
                    item.description,
                    str(item.quantity),
                    f"${item.unit_price:.2f}",
                    f"${item.total:.2f}"
                ])
            
            # Add totals
            data.append(["", "", "Subtotal:", f"${invoice.subtotal:.2f}"])
            if invoice.tax_amount > 0:
                data.append(["", "", "Tax:", f"${invoice.tax_amount:.2f}"])
            if invoice.discount > 0:
                data.append(["", "", "Discount:", f"${invoice.discount:.2f}"])
            data.append(["", "", "TOTAL:", f"${invoice.total_amount:.2f}"])
            
            table = Table(data, colWidths=[300, 70, 70, 70])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -5), 1, colors.black),
                ('LINEBELOW', (2, -4), (-1, -1), 1, colors.black),
                ('FONTNAME', (2, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 30))
            
            # Add notes
            if invoice.notes:
                elements.append(Paragraph("Notes:", styles['Heading3']))
                elements.append(Paragraph(invoice.notes, styles['Normal']))
            
            # Build PDF
            doc.build(elements)
            session.close()
            
            self.logger.info(f"Invoice PDF generated successfully: {output_path}")
            return True, output_path
        
        except Exception as e:
            self.logger.error(f"Error generating invoice PDF: {str(e)}")
            return False, str(e)
