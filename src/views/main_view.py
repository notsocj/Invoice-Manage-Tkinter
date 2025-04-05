import customtkinter as ctk
import tkinter as tk
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
        self.sidebar.grid_rowconfigure(8, weight=1)  # Increased row number to accommodate new button
        
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
        
        self.items_button = ctk.CTkButton(self.sidebar, text="Items", command=self.show_items)
        self.items_button.grid(row=5, column=0, padx=20, pady=10)
        
        # Add new Print Invoices button
        self.print_invoices_button = ctk.CTkButton(self.sidebar, text="Print Invoices", command=self.show_print_invoices)
        self.print_invoices_button.grid(row=6, column=0, padx=20, pady=10)
        
        self.reports_button = ctk.CTkButton(self.sidebar, text="Reports", command=self.show_reports)
        self.reports_button.grid(row=7, column=0, padx=20, pady=10)
        
        # Appearance mode selector at the bottom
        self.appearance_label = ctk.CTkLabel(self.sidebar, text="Appearance Mode:")
        self.appearance_label.grid(row=9, column=0, padx=20, pady=(10, 0))
        
        self.appearance_menu = ctk.CTkOptionMenu(
            self.sidebar, 
            values=["System", "Light", "Dark"],
            command=self.change_appearance_mode
        )
        self.appearance_menu.grid(row=10, column=0, padx=20, pady=(5, 20))
        
    def create_main_content_area(self):
        """Create the main content area"""
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Default view - Dashboard
        self.show_dashboard()
    
    def show_dashboard(self):
        self.clear_main_frame()
        self.logger.info("Showing dashboard")
        
        # Create dashboard title
        title_label = ctk.CTkLabel(self.main_frame, text="Dashboard", font=ctk.CTkFont(size=24, weight="bold"))
        title_label.pack(pady=(20, 10))
        
        # Create refresh button
        refresh_frame = ctk.CTkFrame(self.main_frame)
        refresh_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        refresh_button = ctk.CTkButton(
            refresh_frame, 
            text="Refresh", 
            command=self.controller.dashboard_controller.refresh_dashboard,
            width=100
        )
        refresh_button.pack(side="right", padx=10, pady=5)
        
        # Create summary cards
        summary_frame = ctk.CTkFrame(self.main_frame)
        summary_frame.pack(fill="x", padx=20, pady=10)
        
        # Configure grid columns to be equal width
        summary_frame.columnconfigure((0, 1, 2), weight=1)
        
        # Total invoices card
        self.invoice_card = self._create_dashboard_card(
            summary_frame, 
            "Total Invoices", 
            "0",
            0, 0  # Grid position
        )
        
        # Pending payments card
        self.pending_card = self._create_dashboard_card(
            summary_frame, 
            "Pending Payments", 
            "0",
            0, 1  # Grid position
        )
        
        # Total revenue card
        self.revenue_card = self._create_dashboard_card(
            summary_frame, 
            "Total Revenue", 
            "₱0.00",
            0, 2  # Grid position
        )
        
        # Recent invoices section
        recent_frame = ctk.CTkFrame(self.main_frame)
        recent_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        recent_title = ctk.CTkLabel(
            recent_frame, 
            text="Recent Invoices", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        recent_title.pack(anchor="w", padx=10, pady=10)
        
        # Treeview for recent invoices
        treeview_frame = ctk.CTkFrame(recent_frame)
        treeview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Use a regular Treeview (ttk) as CustomTkinter doesn't have a Treeview widget
        self.recent_invoices_tree = tk.ttk.Treeview(
            treeview_frame, 
            columns=("Invoice #", "Date", "Customer", "Total", "Status"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure the treeview style to match CustomTkinter aesthetics
        style = tk.ttk.Style()
        
        if ctk.get_appearance_mode() == "Dark":
            style.configure("Treeview", 
                            background="#2b2b2b", 
                            foreground="white", 
                            rowheight=25, 
                            fieldbackground="#2b2b2b")
            style.map('Treeview', 
                     background=[('selected', '#347ab3')],
                     foreground=[('selected', 'white')])
        else:
            style.configure("Treeview", 
                            background="#f0f0f0", 
                            foreground="black", 
                            rowheight=25, 
                            fieldbackground="#f0f0f0")
            style.map('Treeview', 
                     background=[('selected', '#2874A6')],
                     foreground=[('selected', 'white')])
        
        # Define column headings
        self.recent_invoices_tree.heading("Invoice #", text="Invoice #")
        self.recent_invoices_tree.heading("Date", text="Date")
        self.recent_invoices_tree.heading("Customer", text="Customer")
        self.recent_invoices_tree.heading("Total", text="Total")
        self.recent_invoices_tree.heading("Status", text="Status")
        
        # Configure column widths and alignment
        self.recent_invoices_tree.column("Invoice #", width=100, anchor="center")
        self.recent_invoices_tree.column("Date", width=100, anchor="center")
        self.recent_invoices_tree.column("Customer", width=200)
        self.recent_invoices_tree.column("Total", width=100, anchor="e")
        self.recent_invoices_tree.column("Status", width=100, anchor="center")
        
        # Add scrollbar
        scrollbar = tk.ttk.Scrollbar(treeview_frame, orient="vertical", command=self.recent_invoices_tree.yview)
        self.recent_invoices_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.recent_invoices_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Load initial dashboard data
        self.controller.dashboard_controller.refresh_dashboard()
    
    def _create_dashboard_card(self, parent, title, value, row, column):
        """Create a dashboard card with title and value"""
        card = ctk.CTkFrame(parent)
        card.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")
        
        title_label = ctk.CTkLabel(
            card, 
            text=title, 
            font=ctk.CTkFont(size=14)
        )
        title_label.pack(anchor="w", padx=15, pady=(15, 5))
        
        value_label = ctk.CTkLabel(
            card, 
            text=value, 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        value_label.pack(anchor="w", padx=15, pady=(5, 15))
        
        return value_label  # Return the value label for later updates
    
    def update_dashboard(self, dashboard_data):
        """Update the dashboard with the provided data"""
        # Update the summary cards
        self.invoice_card.configure(text=str(dashboard_data['total_invoices']))
        self.pending_card.configure(text=str(dashboard_data['pending_payments']))
        
        # Format the total revenue with PHP currency symbol and comma separators
        self.revenue_card.configure(text=f"₱{dashboard_data['total_revenue']:,.2f}")
        
        # Clear the recent invoices tree
        for item in self.recent_invoices_tree.get_children():
            self.recent_invoices_tree.delete(item)
        
        # Add recent invoices to the tree
        for invoice in dashboard_data['recent_invoices']:
            status_text = invoice['payment_status'].capitalize()
            
            # Format tags for color coding
            tags = (invoice['payment_status'],)
            
            self.recent_invoices_tree.insert(
                "", 
                "end", 
                values=(
                    invoice['invoice_number'],
                    invoice['date'],
                    invoice['customer_name'],
                    f"₱{invoice['total_amount']:,.2f}",
                    status_text
                ),
                tags=tags
            )
        
        # Configure tags for color coding
        self.recent_invoices_tree.tag_configure('pending', background='#d4ca00')
        self.recent_invoices_tree.tag_configure('completed', background='#029e02')
        self.recent_invoices_tree.tag_configure('cancelled', background='#b30000')
        self.recent_invoices_tree.tag_configure('partial', background='#0095de')
    
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
    
    def show_print_invoices(self):
        """Show the print invoices view"""
        self.clear_main_frame()
        self.logger.info("Showing print invoices view")
        self.controller.print_controller.load_view(self.main_frame)
    
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
