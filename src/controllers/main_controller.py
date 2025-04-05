import logging
import customtkinter as ctk
from src.views.main_view import MainView
from src.controllers.client_controller import ClientController
from src.controllers.invoice_controller import InvoiceController
from src.controllers.payment_controller import PaymentController
from src.controllers.item_controller import ItemController
from src.controllers.print_controller import PrintController
from src.controllers.dashboard_controller import DashboardController

class MainController:
    def __init__(self, db):
        self.logger = logging.getLogger('invoice_manager')
        self.db = db
        
        # Set default appearance mode and theme
        ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"
        
        # Initialize the main window
        self.root = ctk.CTk()
        self.root.title("Invoice Manager")
        self.root.geometry("1200x700")
        
        # Initialize main view
        self.view = MainView(self.root, self)
        
        # Initialize sub-controllers
        self.dashboard_controller = DashboardController(self.db, self.view)
        self.client_controller = ClientController(self.db, self.view)
        self.invoice_controller = InvoiceController(self.db, self.view)
        self.payment_controller = PaymentController(self.db, self.view)
        self.item_controller = ItemController(self.db, self.view)
        self.print_controller = PrintController(self.db, self.view)
        
    def run(self):
        """Start the main application loop"""
        self.logger.info("Starting main application loop")
        self.view.setup()
        self.root.mainloop()
    
    def exit_application(self):
        """Safely exit the application"""
        self.logger.info("Exiting application")
        self.db.close()
        self.root.quit()
