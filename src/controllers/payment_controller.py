import logging
import threading
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
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
    
    def load_payments(self):
        """Load all payments from the database"""
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
    
    def get_unpaid_invoices(self):
        """Get all unpaid or partially paid invoices for the dropdown"""
        try:
            session = self.db.get_session()
            invoices = session.query(Invoice).all()
            
            invoices_data = []
            for inv in invoices:
                # Get all payments for this invoice
                payments = session.query(Payment).filter(Payment.invoice_id == inv.id).all()
                total_paid = sum(payment.amount for payment in payments)
                
                # Calculate the remaining amount to be paid
                remaining = inv.total_amount - total_paid
                
                if remaining > 0:
                    invoices_data.append({
                        'id': inv.id,
                        'invoice_number': inv.invoice_number,
                        'customer_name': inv.customer_name,
                        'total_amount': inv.total_amount,
                        'remaining_amount': remaining
                    })
            
            session.close()
            return invoices_data
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching unpaid invoices: {str(e)}")
            return []
    
    def add_payment(self, payment_data):
        """Add a new payment to the database"""
        self.logger.info(f"Adding new payment for invoice: {payment_data['invoice_id']}")
        
        try:
            session = self.db.get_session()
            
            # Get the invoice
            invoice = session.query(Invoice).filter(Invoice.id == payment_data['invoice_id']).first()
            
            if not invoice:
                session.close()
                self.logger.warning(f"Invoice with ID {payment_data['invoice_id']} not found")
                return False, "Invoice not found"
            
            # Create payment
            new_payment = Payment(**payment_data)
            session.add(new_payment)
            
            # Since we don't have a status field in the invoice model anymore,
            # we'll just make sure the total_amount is updated if needed
            session.commit()
            payment_id = new_payment.id
            session.close()
            
            self.logger.info(f"Payment added successfully with ID: {payment_id}")
            self.load_payments()
            return True, payment_id
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error adding payment: {str(e)}")
            return False, str(e)
    
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
            
            # Store the original invoice_id for comparison
            original_invoice_id = payment.invoice_id
            new_invoice_id = payment_data.get('invoice_id', original_invoice_id)
            
            # Update payment attributes
            for key, value in payment_data.items():
                setattr(payment, key, value)
            
            session.commit()
            session.close()
            
            self.logger.info(f"Payment updated successfully: {payment_id}")
            self.load_payments()
            return True, payment_id
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating payment: {str(e)}")
            return False, str(e)
    
    def delete_payment(self, payment_id):
        """Delete a payment from the database"""
        self.logger.info(f"Deleting payment with ID: {payment_id}")
        
        try:
            session = self.db.get_session()
            payment = session.query(Payment).filter(Payment.id == payment_id).first()
            
            if not payment:
                session.close()
                self.logger.warning(f"Payment with ID {payment_id} not found")
                return False, "Payment not found"
            
            # Delete the payment
            session.delete(payment)
            session.commit()
            session.close()
            
            self.logger.info(f"Payment deleted successfully: {payment_id}")
            self.load_payments()
            return True, None
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error deleting payment: {str(e)}")
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
    
    def get_invoice_payment_status(self, invoice_id):
        """Determine the payment status of an invoice based on payments received"""
        try:
            session = self.db.get_session()
            invoice = session.query(Invoice).filter(Invoice.id == invoice_id).first()
            
            if not invoice:
                session.close()
                return "unknown"
                
            payments = session.query(Payment).filter(Payment.invoice_id == invoice_id).all()
            total_paid = sum(payment.amount for payment in payments)
            
            if total_paid >= invoice.total_amount:
                status = "paid"
            elif total_paid > 0:
                status = "partial"
            else:
                status = "unpaid"
                
            session.close()
            return status
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting invoice payment status: {str(e)}")
            return "unknown"
    
    def get_payment_methods(self):
        """Get all available payment methods"""
        return [{'value': method.value, 'name': method.name.replace('_', ' ').title()} 
                for method in PaymentMethod]
