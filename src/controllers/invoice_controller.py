import logging
import threading
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from src.models.invoice_model import Invoice, InvoiceItem
from src.models.client_model import Client
from src.views.invoice_view import InvoiceView
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
                invoices = session.query(Invoice).order_by(Invoice.id.desc()).all()
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
            clients_data = [{'id': client.id, 'name': client.name, 'address': client.address} for client in clients]
            session.close()
            return clients_data
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching clients: {str(e)}")
            return []
    
    def generate_invoice_number(self):
        """Generate a sequential invoice number in the format INV-001"""
        try:
            session = self.db.get_session()
            
            # Get the highest invoice number
            last_invoice = session.query(Invoice).order_by(Invoice.id.desc()).first()
            session.close()
            
            if last_invoice and last_invoice.invoice_number:
                try:
                    # Try to parse the last invoice number format (INV-XXX)
                    last_num = int(last_invoice.invoice_number.split('-')[1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    # If parsing fails, start from 1
                    new_num = 1
            else:
                # No invoices yet, start from 1
                new_num = 1
                
            # Format: INV-XXX (e.g., INV-001)
            invoice_number = f"INV-{new_num:03d}"
            
            return invoice_number
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error generating invoice number: {str(e)}")
            # Fallback invoice number
            return f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def add_invoice(self, invoice_data, items_data):
        """Add a new invoice to the database"""
        self.logger.info(f"Adding new invoice for customer: {invoice_data['customer_name']}")
        
        # Ensure payment_status is set to pending if not provided
        if 'payment_status' not in invoice_data:
            invoice_data['payment_status'] = 'pending'
        
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
                session.add(item)
            
            # Calculate invoice total
            new_invoice.calculate_total()
            
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
                session.add(item)
            
            # Recalculate invoice total
            invoice.calculate_total()
            
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
    
    def get_items(self):
        """Get all items for the dropdown"""
        try:
            session = self.db.get_session()
            
            # This assumes you have an 'items' table - replace with your actual item query
            from src.models.item_model import Item
            items = session.query(Item).all()
            items_data = [item.to_dict() for item in items]
            
            session.close()
            return items_data
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching items: {str(e)}")
            return []
