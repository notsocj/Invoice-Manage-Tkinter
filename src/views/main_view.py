import customtkinter as ctk
from PIL import Image
import os
import logging

class MainView:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.logger = logging.getLogger('invoice_manager')
        
        # Set row and column weights to enable proper resizing
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Current active frame
        self.current_frame = None
        
    def setup(self):
        """Set up the main UI components"""
        self.create_sidebar()
        self.create_main_content_area()
        
    def create_sidebar(self):
        """Create sidebar with navigation buttons"""
        # Create sidebar frame
        self.sidebar = ctk.CTkFrame(self.root, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(7, weight=1)  # Push everything up
        
        # App logo/title
        self.logo_label = ctk.CTkLabel(self.sidebar, text="Invoice Manager", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 20))
        
        # Navigation buttons
        self.dashboard_button = ctk.CTkButton(self.sidebar, text="Dashboard", command=self.show_dashboard)
        self.dashboard_button.grid(row=1, column=0, padx=20, pady=10)
        
        self.clients_button = ctk.CTkButton(self.sidebar, text="Clients", command=self.show_clients)
        self.clients_button.grid(row=2, column=0, padx=20, pady=10)
        
        self.invoices_button = ctk.CTkButton(self.sidebar, text="Invoices", command=self.show_invoices)
        self.invoices_button.grid(row=3, column=0, padx=20, pady=10)
        
        self.payments_button = ctk.CTkButton(self.sidebar, text="Payments", command=self.show_payments)
        self.payments_button.grid(row=4, column=0, padx=20, pady=10)
        
        # Add the new Items button
        self.items_button = ctk.CTkButton(self.sidebar, text="Items", command=self.show_items)
        self.items_button.grid(row=5, column=0, padx=20, pady=10)
        
        self.reports_button = ctk.CTkButton(self.sidebar, text="Reports", command=self.show_reports)
        self.reports_button.grid(row=6, column=0, padx=20, pady=10)
        
        # Appearance mode selector at the bottom
        self.appearance_label = ctk.CTkLabel(self.sidebar, text="Appearance Mode:")
        self.appearance_label.grid(row=8, column=0, padx=20, pady=(10, 0))
        
        self.appearance_menu = ctk.CTkOptionMenu(
            self.sidebar, 
            values=["System", "Light", "Dark"],
            command=self.change_appearance_mode
        )
        self.appearance_menu.grid(row=9, column=0, padx=20, pady=(5, 20))
        
    def create_main_content_area(self):
        """Create the main content area"""
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Default view - Dashboard
        self.show_dashboard()
    
    def show_dashboard(self):
        self.clear_main_frame()
        self.logger.info("Showing dashboard")
        
        # Dashboard content will go here - for now just a placeholder
        label = ctk.CTkLabel(self.main_frame, text="Dashboard", font=ctk.CTkFont(size=24, weight="bold"))
        label.pack(pady=20)
        
        # Example dashboard widgets
        summary_frame = ctk.CTkFrame(self.main_frame)
        summary_frame.pack(fill="x", padx=20, pady=10)
        
        # Some basic metrics
        ctk.CTkLabel(summary_frame, text="Total Invoices: 0").pack(side="left", padx=20, pady=10)
        ctk.CTkLabel(summary_frame, text="Pending Payments: 0").pack(side="left", padx=20, pady=10)
        ctk.CTkLabel(summary_frame, text="Total Revenue: $0.00").pack(side="left", padx=20, pady=10)
    
    def show_clients(self):
        self.clear_main_frame()
        self.logger.info("Showing clients view")
        self.controller.client_controller.load_view(self.main_frame)
    
    def show_invoices(self):
        self.clear_main_frame()
        self.logger.info("Showing invoices view")
        self.controller.invoice_controller.load_view(self.main_frame)
    
    def show_payments(self):
        self.clear_main_frame()
        self.logger.info("Showing payments view")
        self.controller.payment_controller.load_view(self.main_frame)
    
    def show_items(self):
        """Show the items view"""
        self.clear_main_frame()
        self.logger.info("Showing items view")
        self.controller.item_controller.load_view(self.main_frame)
    
    def show_reports(self):
        self.clear_main_frame()
        self.logger.info("Showing reports view")
        
        label = ctk.CTkLabel(self.main_frame, text="Reports", font=ctk.CTkFont(size=24, weight="bold"))
        label.pack(pady=20)
        
        # Report generation options
        options_frame = ctk.CTkFrame(self.main_frame)
        options_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(options_frame, text="Report Type:").grid(row=0, column=0, padx=10, pady=10)
        report_type = ctk.CTkComboBox(options_frame, values=["Invoice Summary", "Payment History", "Client List", "Commission Report"])
        report_type.grid(row=0, column=1, padx=10, pady=10)
        
        ctk.CTkLabel(options_frame, text="Format:").grid(row=1, column=0, padx=10, pady=10)
        report_format = ctk.CTkComboBox(options_frame, values=["PDF", "Excel", "CSV"])
        report_format.grid(row=1, column=1, padx=10, pady=10)
        
        ctk.CTkLabel(options_frame, text="Date Range:").grid(row=2, column=0, padx=10, pady=10)
        date_range = ctk.CTkComboBox(options_frame, values=["This Month", "Last Month", "This Quarter", "Last Quarter", "This Year", "Custom"])
        date_range.grid(row=2, column=1, padx=10, pady=10)
        
        generate_button = ctk.CTkButton(options_frame, text="Generate Report")
        generate_button.grid(row=3, column=0, columnspan=2, padx=10, pady=20)
    
    def clear_main_frame(self):
        """Clear all widgets from the main frame"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    def change_appearance_mode(self, new_appearance_mode):
        """Change the app's appearance mode (light/dark)"""
        ctk.set_appearance_mode(new_appearance_mode)
        self.logger.info(f"Changed appearance mode to {new_appearance_mode}")
