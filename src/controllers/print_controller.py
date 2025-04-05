import logging
import threading
import os
import tempfile
import time  # Add the missing time import
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_
from src.models.invoice_model import Invoice, InvoiceItem
from src.views.print_view import PrintView
from src.utils.print_manager import PrintManager

class PrintController:
    def __init__(self, db, main_view):
        self.db = db
        self.main_view = main_view
        self.view = None
        self.logger = logging.getLogger('invoice_manager')
        self.print_manager = PrintManager()
    
    def load_view(self, parent_frame):
        """Load the print invoices view into the parent frame"""
        self.view = PrintView(parent_frame, self)
        self.load_invoices()
    
    def load_invoices(self, date_filter=None):
        """Load invoices from the database based on date filter"""
        self.logger.info(f"Loading invoices for printing with filter: {date_filter}")
        
        # Use a separate thread for database operations
        def fetch_invoices():
            try:
                session = self.db.get_session()
                
                # Base query
                query = session.query(Invoice)
                
                # Apply date filter if provided
                if date_filter:
                    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    
                    if date_filter == "today":
                        # Invoices from today
                        query = query.filter(Invoice.date == today.strftime('%Y-%m-%d'))
                    elif date_filter == "past_7_days":
                        # Invoices from the past 7 days
                        seven_days_ago = today - timedelta(days=7)
                        query = query.filter(Invoice.date >= seven_days_ago.strftime('%Y-%m-%d'))
                    elif date_filter == "past_30_days":
                        # Invoices from the past 30 days
                        thirty_days_ago = today - timedelta(days=30)
                        query = query.filter(Invoice.date >= thirty_days_ago.strftime('%Y-%m-%d'))
                    # Custom date filtering can be added here if needed
                
                # Order by most recent first
                query = query.order_by(Invoice.date.desc())
                
                # Execute query
                invoices = query.all()
                invoices_data = [invoice.to_dict() for invoice in invoices]
                
                session.close()
                
                # Update UI in the main thread
                self.view.after(0, lambda: self.view.display_invoices(invoices_data))
                
            except SQLAlchemyError as e:
                self.logger.error(f"Error fetching invoices for printing: {str(e)}")
                self.view.after(0, lambda: self.view.show_error("Failed to load invoices"))
        
        thread = threading.Thread(target=fetch_invoices)
        thread.daemon = True
        thread.start()
    
    def get_invoice_details(self, invoice_id):
        """Get detailed invoice information including items"""
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
            self.logger.error(f"Error fetching invoice details for printing: {str(e)}")
            return None, None
    
    def print_invoice(self, invoice_id, silent=False, direct_print=True):
        """Print the selected invoice
        
        Args:
            invoice_id: The ID of the invoice to print
            silent: If True, suppresses success/error messages
            direct_print: If True, sends directly to printer instead of preview
        
        Returns:
            Tuple containing (success status, PDF path)
        """
        self.logger.info(f"Printing invoice with ID: {invoice_id}")
        
        # Get invoice details
        invoice_data, items_data = self.get_invoice_details(invoice_id)
        
        if not invoice_data:
            if not silent:
                self.view.show_error("Failed to load invoice data for printing")
            return False, None
        
        try:
            # Check if there's a logo file in the app directory
            logo_path = os.path.join(os.getcwd(), "logo.jpg")
            if not os.path.exists(logo_path):
                logo_path = None
            
            if direct_print:
                # Use direct printing method that shows system print dialog
                success = self.print_manager.print_direct(invoice_data, items_data, logo_path)
                
                if success:
                    if not silent:
                        self.view.show_info(f"Invoice {invoice_data['invoice_number']} sent to printer")
                    return True, None
                else:
                    if not silent:
                        self.view.show_error("Failed to send invoice to printer")
                    return False, None
            else:
                # Generate PDF for preview
                pdf_path = self.print_manager.generate_invoice_pdf(
                    invoice_data, 
                    items_data, 
                    logo_path=logo_path
                )
                
                if not pdf_path:
                    if not silent:
                        self.view.show_error("Failed to generate invoice PDF")
                    return False, None
                
                # Open the PDF for viewing
                self.print_manager.open_pdf(pdf_path)
                if not silent:
                    self.view.show_info(f"Invoice {invoice_data['invoice_number']} ready for printing")
                return True, pdf_path
                
        except Exception as e:
            self.logger.error(f"Error printing invoice: {str(e)}")
            if not silent:
                self.view.show_error(f"Error printing invoice: {str(e)}")
            return False, None
    
    def print_multiple_invoices(self, invoice_ids):
        """Print multiple invoices in batch by combining them into a single PDF
        
        Args:
            invoice_ids: List of invoice IDs to print
            
        Returns:
            Tuple containing (success count, fail count)
        """
        if not invoice_ids:
            self.view.show_error("No invoices selected for printing")
            return 0, 0
            
        self.logger.info(f"Batch printing {len(invoice_ids)} invoices as one document")
        
        # Show processing indicator in the UI
        self.view.show_processing_indicator(True, f"Preparing {len(invoice_ids)} invoices for printing...")
        
        # Use a worker thread for batch processing
        def process_batch():
            # Collect all invoice data
            invoice_data_list = []
            failed_ids = []
            
            # Get data for all selected invoices
            for invoice_id in invoice_ids:
                invoice_data, items_data = self.get_invoice_details(invoice_id)
                if invoice_data and items_data:
                    invoice_data_list.append((invoice_data, items_data))
                else:
                    failed_ids.append(invoice_id)
            
            # Check if there's a logo file in the app directory
            logo_path = os.path.join(os.getcwd(), "logo.jpg")
            if not os.path.exists(logo_path):
                logo_path = None
            
            # Process the batch if we have any valid invoices
            if invoice_data_list:
                success = self.print_manager.print_multiple_invoices_as_one(invoice_data_list, logo_path)
                if success:
                    success_count = len(invoice_data_list)
                    fail_count = len(failed_ids)
                else:
                    success_count = 0
                    fail_count = len(invoice_ids)
            else:
                success_count = 0
                fail_count = len(invoice_ids)
            
            # Update UI when complete
            self.view.after(0, lambda: self.view.show_processing_indicator(False))
            if fail_count == 0:
                self.view.after(0, lambda: self.view.show_info(f"Successfully sent {success_count} invoice(s) to printer"))
            else:
                self.view.after(0, lambda: self.view.show_info(
                    f"Sent {success_count} invoice(s) to printer. Failed to print {fail_count} invoice(s)."
                ))
        
        # Run the batch processing in a thread
        thread = threading.Thread(target=process_batch)
        thread.daemon = True
        thread.start()
        
        return len(invoice_ids), 0  # Return expected processing count
    
    def preview_invoice(self, invoice_id):
        """Generate and display a preview of the invoice"""
        return self.print_invoice(invoice_id, direct_print=False)[0]
