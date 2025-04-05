import logging
import threading
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from src.models.payment_model import Payment, PaymentMethod
from src.models.invoice_model import Invoice
from src.views.payment_view import PaymentView

class PaymentController:
    def __init__(self, db, main_view):
        self.db = db
        self.main_view = main_view
        self.view = None
        self.logger = logging.getLogger('invoice_manager')
    
    def load_view(self, parent_frame):
        """Load the payment view into the parent frame"""
        self.view = PaymentView(parent_frame, self)
        self.load_payments()
        self.load_invoices()
    
    def load_payments(self):
        """Load payments from the database"""
        self.logger.info("Loading payments")
        
        # Use a separate thread for database operations
        def fetch_payments():
            try:
                session = self.db.get_session()
                payments = session.query(Payment).order_by(Payment.payment_date.desc()).all()
                payments_data = [payment.to_dict() for payment in payments]
                session.close()
                
                # Update UI in the main thread
                self.view.after(0, lambda: self.view.display_payments(payments_data))
                
            except SQLAlchemyError as e:
                self.logger.error(f"Error fetching payments: {str(e)}")
                self.view.after(0, lambda: self.view.show_error("Failed to load payments"))
        
        thread = threading.Thread(target=fetch_payments)
        thread.daemon = True
        thread.start()
    
    def load_invoices(self, status_filter=None):
        """Load invoices from the database with optional status filter"""
        self.logger.info(f"Loading invoices with status filter: {status_filter}")
        
        # Use a separate thread for database operations
        def fetch_invoices():
            try:
                session = self.db.get_session()
                
                # Base query
                query = session.query(Invoice)
                
                # Apply status filter if provided
                if status_filter and status_filter != "All":
                    query = query.filter(Invoice.payment_status == status_filter.lower())
                
                # Order by date descending
                invoices = query.order_by(Invoice.date.desc()).all()
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
    
    def update_payment_status(self, invoice_id, new_status):
        """Update the payment status of an invoice"""
        self.logger.info(f"Updating payment status for invoice {invoice_id} to {new_status}")
        
        try:
            session = self.db.get_session()
            invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()
            
            if not invoice:
                session.close()
                self.logger.warning(f"Invoice with ID {invoice_id} not found")
                return False, "Invoice not found"
            
            # Update the status
            invoice.payment_status = new_status.lower()
            session.commit()
            session.close()
            
            self.logger.info(f"Payment status updated for invoice {invoice_id}")
            
            # Reload invoices to reflect the changes
            self.load_invoices(self.view.status_filter_var.get() if hasattr(self.view, 'status_filter_var') else None)
            
            return True, None
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating payment status: {str(e)}")
            return False, str(e)
    
    def get_payment_methods(self):
        """Get available payment methods"""
        try:
            session = self.db.get_session()
            # First try to get methods from database
            methods = session.query(PaymentMethod).filter(PaymentMethod.is_active == 1).all()
            session.close()
            
            if methods:
                return [method.to_dict() for method in methods]
            else:
                # If no methods in database, return default methods
                return [
                    {'id': 'cash', 'name': 'Cash'},
                    {'id': 'bank_transfer', 'name': 'Bank Transfer'},
                    {'id': 'gcash', 'name': 'GCash'},
                    {'id': 'credit_card', 'name': 'Credit Card'},
                    {'id': 'check', 'name': 'Check'}
                ]
                
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching payment methods: {str(e)}")
            # Return default methods on error
            return [
                {'id': 'cash', 'name': 'Cash'},
                {'id': 'bank_transfer', 'name': 'Bank Transfer'},
                {'id': 'gcash', 'name': 'GCash'},
                {'id': 'credit_card', 'name': 'Credit Card'},
                {'id': 'check', 'name': 'Check'}
            ]
    
    def get_payment_statuses(self):
        """Get available payment statuses"""
        return ["All", "Pending", "Completed", "Cancelled"]
    
    def get_unpaid_invoices(self):
        """Get invoices that are not fully paid yet"""
        try:
            session = self.db.get_session()
            
            # Get invoices with pending or partial payment status
            invoices = session.query(Invoice).filter(
                Invoice.payment_status.in_(['pending', 'partial'])
            ).order_by(Invoice.date.desc()).all()
            
            result = []
            for invoice in invoices:
                # Calculate remaining amount to be paid
                total_payments = sum(payment.amount for payment in invoice.payments)
                remaining_amount = invoice.total_amount - total_payments
                
                if remaining_amount > 0:
                    result.append({
                        'id': invoice.id,
                        'invoice_number': invoice.invoice_number,
                        'client_name': invoice.customer_name,
                        'total_amount': invoice.total_amount,
                        'paid_amount': total_payments,
                        'remaining_amount': remaining_amount
                    })
            
            session.close()
            return result
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching unpaid invoices: {str(e)}")
            return []
    
    def add_payment(self, payment_data):
        """Add a new payment"""
        self.logger.info("Adding new payment")
        
        try:
            session = self.db.get_session()
            
            # Create new payment object
            new_payment = Payment(
                invoice_id=payment_data.get('invoice_id'),
                amount=payment_data.get('amount'),
                payment_date=payment_data.get('payment_date'),
                payment_method=payment_data.get('payment_method'),
                reference_number=payment_data.get('reference_number'),
                notes=payment_data.get('notes')
            )
            
            session.add(new_payment)
            
            # Update invoice payment status
            invoice = session.query(Invoice).filter(Invoice.id == payment_data.get('invoice_id')).first()
            if invoice:
                # Calculate total payments for this invoice
                existing_payments = sum(payment.amount for payment in invoice.payments)
                new_total_payments = existing_payments + payment_data.get('amount')
                
                # Update status based on payment amount
                if new_total_payments >= invoice.total_amount:
                    invoice.payment_status = 'completed'
                else:
                    invoice.payment_status = 'partial'
            
            session.commit()
            session.refresh(new_payment)
            payment_id = new_payment.id
            session.close()
            
            # Reload data
            self.load_payments()
            self.load_invoices(self.view.status_filter_var.get() if hasattr(self.view, 'status_filter_var') else None)
            
            return True, payment_id
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error adding payment: {str(e)}")
            return False, str(e)
    
    def get_payment(self, payment_id):
        """Get a specific payment by ID"""
        try:
            session = self.db.get_session()
            payment = session.query(Payment).filter(Payment.id == payment_id).first()
            
            if not payment:
                session.close()
                return None
            
            payment_data = payment.to_dict()
            session.close()
            return payment_data
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching payment: {str(e)}")
            return None
    
    def update_payment(self, payment_id, payment_data):
        """Update an existing payment"""
        self.logger.info(f"Updating payment with ID: {payment_id}")
        
        try:
            session = self.db.get_session()
            payment = session.query(Payment).filter(Payment.id == payment_id).first()
            
            if not payment:
                session.close()
                self.logger.warning(f"Payment with ID {payment_id} not found")
                return False, "Payment not found"
            
            # Store old amount and invoice_id for recalculating status
            old_amount = payment.amount
            old_invoice_id = payment.invoice_id
            
            # Update payment attributes
            payment.invoice_id = payment_data.get('invoice_id')
            payment.amount = payment_data.get('amount')
            payment.payment_date = payment_data.get('payment_date')
            payment.payment_method = payment_data.get('payment_method')
            payment.reference_number = payment_data.get('reference_number')
            payment.notes = payment_data.get('notes')
            
            # Update payment status for old invoice if needed
            if old_invoice_id:
                old_invoice = session.query(Invoice).filter(Invoice.id == old_invoice_id).first()
                if old_invoice:
                    # Recalculate total payments without the old amount
                    total_payments = sum(p.amount for p in old_invoice.payments if p.id != payment_id)
                    
                    # Update status based on payment amount
                    if total_payments >= old_invoice.total_amount:
                        old_invoice.payment_status = 'completed'
                    elif total_payments > 0:
                        old_invoice.payment_status = 'partial'
                    else:
                        old_invoice.payment_status = 'pending'
            
            # Update payment status for new invoice
            if payment.invoice_id:
                invoice = session.query(Invoice).filter(Invoice.id == payment.invoice_id).first()
                if invoice:
                    # Recalculate total payments including the new amount
                    total_payments = sum(p.amount for p in invoice.payments if p.id != payment_id) + payment.amount
                    
                    # Update status based on payment amount
                    if total_payments >= invoice.total_amount:
                        invoice.payment_status = 'completed'
                    elif total_payments > 0:
                        invoice.payment_status = 'partial'
                    else:
                        invoice.payment_status = 'pending'
            
            session.commit()
            session.close()
            
            # Reload data
            self.load_payments()
            self.load_invoices(self.view.status_filter_var.get() if hasattr(self.view, 'status_filter_var') else None)
            
            return True, payment_id
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating payment: {str(e)}")
            return False, str(e)
    
    def delete_payment(self, payment_id):
        """Delete a payment"""
        self.logger.info(f"Deleting payment with ID: {payment_id}")
        
        try:
            session = self.db.get_session()
            payment = session.query(Payment).filter(Payment.id == payment_id).first()
            
            if not payment:
                session.close()
                self.logger.warning(f"Payment with ID {payment_id} not found")
                return False, "Payment not found"
            
            # Store invoice_id for updating status after deletion
            invoice_id = payment.invoice_id
            
            # Delete the payment
            session.delete(payment)
            session.commit()
            
            # Update invoice payment status
            if invoice_id:
                invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()
                if invoice:
                    # Recalculate total payments
                    total_payments = sum(payment.amount for payment in invoice.payments)
                    
                    # Update status based on payment amount
                    if total_payments >= invoice.total_amount:
                        invoice.payment_status = 'completed'
                    elif total_payments > 0:
                        invoice.payment_status = 'partial'
                    else:
                        invoice.payment_status = 'pending'
                    
                    session.commit()
            
            session.close()
            
            # Reload data
            self.load_payments()
            self.load_invoices(self.view.status_filter_var.get() if hasattr(self.view, 'status_filter_var') else None)
            
            return True, None
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error deleting payment: {str(e)}")
            return False, str(e)
