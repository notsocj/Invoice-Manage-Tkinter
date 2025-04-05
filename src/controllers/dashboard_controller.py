import logging
import threading
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, and_, or_
from src.models.invoice_model import Invoice
from src.models.payment_model import Payment

class DashboardController:
    def __init__(self, db, main_view):
        self.db = db
        self.main_view = main_view
        self.logger = logging.getLogger('invoice_manager')
    
    def get_dashboard_data(self):
        """Fetch data for dashboard widgets"""
        self.logger.info("Fetching dashboard data")
        
        try:
            session = self.db.get_session()
            
            # Get total number of invoices
            total_invoices = session.query(func.count(Invoice.id)).scalar() or 0
            
            # Get number of pending payments
            pending_payments = session.query(func.count(Invoice.id)).filter(
                Invoice.payment_status.in_(['pending', 'partial'])
            ).scalar() or 0
            
            # Get total revenue (from completed payments)
            total_revenue = session.query(func.sum(Invoice.total_amount)).filter(
                Invoice.payment_status == 'completed'
            ).scalar() or 0.0
            
            # Get recent invoices (last 5)
            recent_invoices = session.query(Invoice).order_by(
                Invoice.date.desc()
            ).limit(5).all()
            recent_invoices_data = [invoice.to_dict() for invoice in recent_invoices]
            
            session.close()
            
            return {
                'total_invoices': total_invoices,
                'pending_payments': pending_payments,
                'total_revenue': total_revenue,
                'recent_invoices': recent_invoices_data
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching dashboard data: {str(e)}")
            return {
                'total_invoices': 0,
                'pending_payments': 0,
                'total_revenue': 0.0,
                'recent_invoices': []
            }
    
    def refresh_dashboard(self):
        """Refresh the dashboard data and update the UI"""
        self.logger.info("Refreshing dashboard data")
        
        # Use a separate thread for database operations
        def fetch_data():
            dashboard_data = self.get_dashboard_data()
            
            # Update UI in the main thread
            self.main_view.root.after(0, lambda: self.main_view.update_dashboard(dashboard_data))
        
        thread = threading.Thread(target=fetch_data)
        thread.daemon = True
        thread.start()
