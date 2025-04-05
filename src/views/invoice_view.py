import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import logging
from datetime import datetime

class InvoiceView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger('invoice_manager')
        self.pack(fill="both", expand=True)
        
        # Store currently selected invoice ID
        self.selected_invoice_id = None
        
        # Create UI elements
        self._create_widgets()
        
    def _create_widgets(self):
        """Create all UI elements for the invoice view"""
        # Title and button frame
        title_frame = ctk.CTkFrame(self)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text="Invoice Management", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left", padx=10, pady=10)
        
        add_button = ctk.CTkButton(
            title_frame, 
            text="Add New Invoice", 
            command=self._show_add_invoice_dialog
        )
        add_button.pack(side="right", padx=10, pady=10)
        
        refresh_button = ctk.CTkButton(
            title_frame, 
            text="Refresh", 
            command=self.controller.load_invoices
        )
        refresh_button.pack(side="right", padx=10, pady=10)
        
        # Search frame
        search_frame = ctk.CTkFrame(self)
        search_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        search_label = ctk.CTkLabel(search_frame, text="Search:")
        search_label.pack(side="left", padx=10, pady=10)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self._filter_invoices())
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, width=300)
        search_entry.pack(side="left", padx=10, pady=10)
        
        # Invoice list frame
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Treeview for invoices
        # Create a frame for the treeview and scrollbar
        treeview_frame = ctk.CTkFrame(list_frame)
        treeview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Use a regular Treeview (ttk) as CustomTkinter doesn't have a Treeview widget
        self.tree = tk.ttk.Treeview(
            treeview_frame, 
            columns=("ID", "Number", "Date", "Customer", "Address", "Total"),
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
        self.tree.heading("ID", text="ID", command=lambda: self._sort_by_column("ID", False))
        self.tree.heading("Number", text="Invoice #", command=lambda: self._sort_by_column("Number", False))
        self.tree.heading("Date", text="Date", command=lambda: self._sort_by_column("Date", False))
        self.tree.heading("Customer", text="Customer", command=lambda: self._sort_by_column("Customer", False))
        self.tree.heading("Address", text="Address", command=lambda: self._sort_by_column("Address", False))
        self.tree.heading("Total", text="Total", command=lambda: self._sort_by_column("Total", False))
        
        # Configure column widths and alignment
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Number", width=100, anchor="center")
        self.tree.column("Date", width=100, anchor="center")
        self.tree.column("Customer", width=200)
        self.tree.column("Address", width=300)
        self.tree.column("Total", width=100, anchor="e")
        
        # Bind select event
        self.tree.bind("<<TreeviewSelect>>", self._on_invoice_select)
        self.tree.bind("<Double-1>", self._on_invoice_double_click)
        
        # Add scrollbar
        scrollbar = tk.ttk.Scrollbar(treeview_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Action buttons for the selected invoice
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        self.view_button = ctk.CTkButton(
            action_frame, 
            text="View Invoice", 
            state="disabled", 
            command=self._show_view_invoice_dialog
        )
        self.view_button.pack(side="left", padx=10, pady=10)
        
        self.edit_button = ctk.CTkButton(
            action_frame, 
            text="Edit Invoice", 
            state="disabled", 
            command=self._show_edit_invoice_dialog
        )
        self.edit_button.pack(side="left", padx=10, pady=10)
        
        self.delete_button = ctk.CTkButton(
            action_frame, 
            text="Delete Invoice", 
            state="disabled",
            fg_color="red",
            hover_color="darkred",
            command=self._confirm_delete_invoice
        )
        self.delete_button.pack(side="right", padx=10, pady=10)
        
        # Store invoices data
        self.invoices_data = []
        self.sorted_column = None
        self.sort_ascending = True
        
    def display_invoices(self, invoices_data):
        """Display the list of invoices in the treeview"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Store the full data for later use
        self.invoices_data = invoices_data
        
        # Add invoices to the treeview
        for invoice in invoices_data:
            self.tree.insert(
                "", 
                "end", 
                values=(
                    invoice['id'],
                    invoice['invoice_number'],
                    invoice['date'],
                    invoice['customer_name'],
                    invoice['customer_address'] or "",
                    f"₱{invoice['total_amount']:.2f}"
                )
            )
            
        # Reset selection
        self.selected_invoice_id = None
        self._update_action_buttons()
        
    def _filter_invoices(self):
        """Filter invoices based on search text"""
        search_text = self.search_var.get().lower()
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add filtered invoices to the treeview
        for invoice in self.invoices_data:
            if (search_text in str(invoice['id']).lower() or
                search_text in invoice['invoice_number'].lower() or
                search_text in invoice['date'].lower() or
                search_text in invoice['customer_name'].lower() or
                (invoice['customer_address'] and search_text in invoice['customer_address'].lower())):
                
                self.tree.insert(
                    "", 
                    "end", 
                    values=(
                        invoice['id'],
                        invoice['invoice_number'],
                        invoice['date'],
                        invoice['customer_name'],
                        invoice['customer_address'] or "",
                        f"₱{invoice['total_amount']:.2f}"
                    )
                )
    
    def _sort_by_column(self, column, reset=True):
        """Sort the tree data by column"""
        if reset or self.sorted_column != column:
            self.sort_ascending = True
            self.sorted_column = column
        else:
            self.sort_ascending = not self.sort_ascending
        
        # Visual indicator of sort direction
        for col in self.tree["columns"]:
            heading_text = col.replace("#", "")
            if col == column:
                if self.sort_ascending:
                    self.tree.heading(col, text=f"{heading_text} ↑")
                else:
                    self.tree.heading(col, text=f"{heading_text} ↓")
            else:
                self.tree.heading(col, text=heading_text)
        
        # Get all items with their values
        items_with_values = [(self.tree.item(item, "values"), item) for item in self.tree.get_children("")]
        
        # Determine column index
        column_indices = {col: idx for idx, col in enumerate(self.tree["columns"])}
        col_idx = column_indices[column]
        
        # Special handling for Total (remove ₱ sign for sorting)
        if column == "Total":
            items_with_values.sort(
                key=lambda x: float(x[0][col_idx].replace('₱', '')) if x[0][col_idx].replace('₱', '') else 0,
                reverse=not self.sort_ascending
            )
        else:
            # Sort items
            items_with_values.sort(
                key=lambda x: (x[0][col_idx] == "", x[0][col_idx]), 
                reverse=not self.sort_ascending
            )
        
        # Rearrange items in the tree
        for idx, (values, item) in enumerate(items_with_values):
            self.tree.move(item, "", idx)
                
    def _on_invoice_select(self, event):
        """Handle invoice selection"""
        selected_items = self.tree.selection()
        if selected_items:
            item = selected_items[0]
            self.selected_invoice_id = int(self.tree.item(item, "values")[0])
            self._update_action_buttons()
        else:
            self.selected_invoice_id = None
            self._update_action_buttons()
    
    def _on_invoice_double_click(self, event):
        """Handle double-click on an invoice"""
        if self.selected_invoice_id:
            self._show_view_invoice_dialog()
            
    def _update_action_buttons(self):
        """Update the state of action buttons based on invoice selection"""
        if self.selected_invoice_id:
            self.view_button.configure(state="normal")
            self.edit_button.configure(state="normal")
            self.delete_button.configure(state="normal")
        else:
            self.view_button.configure(state="disabled")
            self.edit_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")
            
    def _show_add_invoice_dialog(self):
        """Show dialog to add a new invoice"""
        # Generate a new invoice number
        invoice_number = self.controller.generate_invoice_number()
        
        # Get clients for dropdown
        clients = self.controller.get_clients()
        
        dialog = InvoiceDialog(self, "Add New Invoice", invoice_number, clients)
        dialog.grab_set()  # Make it modal
        self.wait_window(dialog)  # Wait until the dialog is closed
        
        if dialog.result:
            # Process the form data
            success, result = self.controller.add_invoice(dialog.result['invoice'], dialog.result['items'])
            if success:
                self.show_info(f"Invoice added successfully with ID: {result}")
            else:
                self.show_error(f"Failed to add invoice: {result}")
                
    def _show_edit_invoice_dialog(self):
        """Show dialog to edit an existing invoice"""
        # Get the invoice data
        invoice_data, items_data = self.controller.get_invoice(self.selected_invoice_id)
        if not invoice_data:
            self.show_error("Failed to load invoice data")
            return
            
        # Get clients for dropdown
        clients = self.controller.get_clients()
            
        dialog = InvoiceDialog(self, "Edit Invoice", invoice_data['invoice_number'], clients, invoice_data, items_data)
        dialog.grab_set()  # Make it modal
        self.wait_window(dialog)  # Wait until the dialog is closed
        
        if dialog.result:
            # Process the form data
            success, result = self.controller.update_invoice(self.selected_invoice_id, dialog.result['invoice'], dialog.result['items'])
            if success:
                self.show_info(f"Invoice updated successfully")
            else:
                self.show_error(f"Failed to update invoice: {result}")
                
    def _show_view_invoice_dialog(self):
        """Show dialog to view invoice details"""
        # Get the invoice data
        invoice_data, items_data = self.controller.get_invoice(self.selected_invoice_id)
        if not invoice_data:
            self.show_error("Failed to load invoice data")
            return
            
        # Get clients for dropdown (for display only)
        clients = self.controller.get_clients()
            
        dialog = InvoiceDialog(self, "View Invoice", invoice_data['invoice_number'], clients, invoice_data, items_data, readonly=True)
        dialog.grab_set()  # Make it modal
        dialog.wait_window()  # Wait until the dialog is closed
            
    def _confirm_delete_invoice(self):
        """Show confirmation dialog before deleting an invoice"""
        if not self.selected_invoice_id:
            return
            
        # Show confirmation dialog
        if messagebox.askyesno("Confirm Delete", 
                              "Are you sure you want to delete this invoice?\nThis action cannot be undone."):
            success, result = self.controller.delete_invoice(self.selected_invoice_id)
            if success:
                self.show_info("Invoice deleted successfully")
            else:
                self.show_error(f"Failed to delete invoice: {result}")
    
    def show_error(self, message):
        """Show error message"""
        messagebox.showerror("Error", message)
        
    def show_info(self, message):
        """Show info message"""
        messagebox.showinfo("Information", message)


class InvoiceDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, invoice_number, clients, invoice_data=None, items_data=None, readonly=False):
        super().__init__(parent)
        self.title(title)
        self.geometry("800x650")  # Increased height to ensure button visibility
        self.resizable(False, False)
        
        # Set up variables
        self.invoice_number = invoice_number
        self.clients = clients
        self.invoice_data = invoice_data or {}
        self.items_data = items_data or []
        self.readonly = readonly
        self.result = None
        
        # Store line items
        self.line_items = []
        
        # Get items for dropdown
        self.items = parent.controller.get_items()
        
        # Create UI
        self._create_widgets()
        
        # Center the dialog
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - self.winfo_width()) // 2
        y = (screen_height - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
    def _create_widgets(self):
        """Create all UI elements for the invoice dialog"""
        # Main container
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Form title
        title_label = ctk.CTkLabel(
            container, 
            text=self.title(), 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Create a scrollable frame to contain all content
        main_content = ctk.CTkScrollableFrame(container)
        main_content.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Invoice header frame
        header_frame = ctk.CTkFrame(main_content)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        # Left side - Invoice number and date
        left_frame = ctk.CTkFrame(header_frame)
        left_frame.pack(side="left", fill="y", expand=True, padx=10)
        
        # Invoice number
        invoice_number_frame = ctk.CTkFrame(left_frame)
        invoice_number_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(invoice_number_frame, text="Invoice #:").pack(side="left", padx=10)
        
        self.invoice_number_var = ctk.StringVar(value=self.invoice_number)
        invoice_number_entry = ctk.CTkEntry(invoice_number_frame, textvariable=self.invoice_number_var, width=150)
        invoice_number_entry.pack(side="left", padx=10)
        
        if self.readonly:
            invoice_number_entry.configure(state="disabled")
        
        # Date
        date_frame = ctk.CTkFrame(left_frame)
        date_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(date_frame, text="Date:").pack(side="left", padx=10)
        
        # Use current date if it's a new invoice, otherwise use stored date
        current_date = datetime.now().strftime("%Y-%m-%d")
        self.date_var = ctk.StringVar(value=self.invoice_data.get('date', current_date))
        date_entry = ctk.CTkEntry(date_frame, textvariable=self.date_var, width=150)
        date_entry.pack(side="left", padx=10)
        
        if self.readonly:
            date_entry.configure(state="disabled")
        
        # Mode of Payment dropdown
        payment_mode_frame = ctk.CTkFrame(left_frame)
        payment_mode_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(payment_mode_frame, text="Payment Mode:").pack(side="left", padx=10)
        
        # Updated payment modes to the specified options
        payment_modes = ["Gcash", "Bank Transfer", "Cash on Delivery"]
        self.payment_mode_var = ctk.StringVar(value=self.invoice_data.get('mode_of_payment', 'Bank Transfer'))
        payment_mode_dropdown = ctk.CTkComboBox(
            payment_mode_frame,
            values=payment_modes,
            variable=self.payment_mode_var,
            width=150
        )
        payment_mode_dropdown.pack(side="left", padx=10)
        
        if self.readonly:
            payment_mode_dropdown.configure(state="disabled")
        
        # Right side - Customer info
        right_frame = ctk.CTkFrame(header_frame)
        right_frame.pack(side="right", fill="y", expand=True, padx=10)
        
        # Customer name (dropdown of clients or direct input)
        customer_name_frame = ctk.CTkFrame(right_frame)
        customer_name_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(customer_name_frame, text="Customer:").pack(side="left", padx=10)
        
        # Customer dropdown with sorted names
        client_names = [""] + sorted([client['name'] for client in self.clients])
        self.customer_var = ctk.StringVar()
        
        # Set the customer name if editing an existing invoice
        if self.invoice_data.get('customer_name'):
            self.customer_var.set(self.invoice_data.get('customer_name'))
        
        self.customer_dropdown = ctk.CTkComboBox(
            customer_name_frame, 
            values=client_names,
            variable=self.customer_var,
            width=250,
            command=self._customer_selected
        )
        self.customer_dropdown.pack(side="left", padx=10)
        
        # Add search as you type functionality
        self.customer_dropdown.bind("<KeyRelease>", self._filter_customer_dropdown)
        
        if self.readonly:
            self.customer_dropdown.configure(state="disabled")
        
        # Customer address
        customer_address_frame = ctk.CTkFrame(right_frame)
        customer_address_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(customer_address_frame, text="Address:").pack(side="left", padx=10)
        
        self.address_text = ctk.CTkTextbox(customer_address_frame, height=60, width=250)
        self.address_text.pack(side="left", padx=10)
        
        # Set the address if editing an existing invoice
        if self.invoice_data.get('customer_address'):
            self.address_text.insert("1.0", self.invoice_data.get('customer_address'))
        
        if self.readonly:
            self.address_text.configure(state="disabled")
        
        # Line items section
        items_frame = ctk.CTkFrame(main_content)
        items_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Items header
        items_header = ctk.CTkFrame(items_frame)
        items_header.pack(fill="x", pady=5)
        
        ctk.CTkLabel(items_header, text="Line Items", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)
        
        if not self.readonly:
            add_item_button = ctk.CTkButton(
                items_header, 
                text="Add Item", 
                command=self._add_line_item,
                width=100
            )
            add_item_button.pack(side="right", padx=10)
        
        # Items list frame
        items_list_frame = ctk.CTkFrame(items_frame)
        items_list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Items header row
        header_row = ctk.CTkFrame(items_list_frame)
        header_row.pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(header_row, text="Item Code", width=80).pack(side="left", padx=(5, 0))
        ctk.CTkLabel(header_row, text="Description", width=200).pack(side="left", padx=5)
        ctk.CTkLabel(header_row, text="Quantity", width=80).pack(side="left", padx=5)
        ctk.CTkLabel(header_row, text="Price", width=80).pack(side="left", padx=5)
        ctk.CTkLabel(header_row, text="Total", width=80).pack(side="left", padx=5)
        
        # Items container (scrollable frame would be better for many items)
        self.items_container = ctk.CTkScrollableFrame(items_list_frame, height=200)
        self.items_container.pack(fill="both", expand=True)
        
        # Add existing line items
        for item_data in self.items_data:
            self._add_line_item(item_data)
        
        # If it's a new invoice with no items, add an empty item row
        if not self.items_data and not self.readonly:
            self._add_line_item()
        
        # Totals section
        totals_frame = ctk.CTkFrame(main_content)
        totals_frame.pack(fill="x", padx=10, pady=10)
        
        # Total amount
        total_frame = ctk.CTkFrame(totals_frame)
        total_frame.pack(side="right", padx=10)
        
        ctk.CTkLabel(total_frame, text="Total Amount:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        
        self.total_var = ctk.StringVar(value=f"₱{self.invoice_data.get('total_amount', 0.0):.2f}")
        total_label = ctk.CTkLabel(total_frame, textvariable=self.total_var, font=ctk.CTkFont(weight="bold"))
        total_label.pack(side="left", padx=10)
        
        # Button frame - moved outside of the scrollable area to always be visible
        button_frame = ctk.CTkFrame(container)
        button_frame.pack(fill="x", pady=10, side="bottom")
        
        if not self.readonly:
            save_button = ctk.CTkButton(
                button_frame, 
                text="Save Invoice", 
                command=self._save,
                font=ctk.CTkFont(size=16, weight="bold"),  # Larger font
                height=40,  # Taller button
                fg_color="#28a745",  # Green color
                hover_color="#218838"  # Darker green on hover
            )
            save_button.pack(side="left", padx=20, pady=15, fill="x", expand=True)
        
        cancel_button = ctk.CTkButton(
            button_frame, 
            text="Close" if self.readonly else "Cancel", 
            command=self.destroy,
            height=40  # Match save button height
        )
        cancel_button.pack(side="right", padx=20, pady=15, fill="x", expand=True)
    
    def _customer_selected(self, customer_name):
        """Auto-populate customer address when a customer is selected"""
        if not customer_name:
            self.address_text.delete("1.0", "end")
            return
        
        # Find customer in clients list
        for client in self.clients:
            if client['name'] == customer_name:
                # Set the address
                self.address_text.delete("1.0", "end")
                if client['address']:
                    self.address_text.insert("1.0", client['address'])
                break
    
    def _filter_customer_dropdown(self, event):
        """Filter customer dropdown options based on typed text"""
        typed_text = self.customer_dropdown.get().lower()
        
        # Don't filter on navigation keys, only on actual text input
        if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Home', 'End', 
                          'BackSpace', 'Delete', 'Escape', 'Tab'):
            return
        
        # Find matching client names
        if typed_text:
            matches = [name for name in sorted([client['name'] for client in self.clients]) 
                      if typed_text in name.lower()]
            
            # If matches found, update dropdown with matching values
            if matches:
                self.customer_dropdown.configure(values=[""] + matches)
                
                # Don't auto-select - just show the matching options
                # Keep the typed text in the entry
                self.customer_dropdown.set(typed_text)
            else:
                # If no matches, keep typed text but show all options
                self.customer_dropdown.configure(values=[""] + sorted([client['name'] for client in self.clients]))
        else:
            # Reset to all options if text field is empty
            self.customer_dropdown.configure(values=[""] + sorted([client['name'] for client in self.clients]))
    
    def _add_line_item(self, item_data=None):
        """Add a line item row to the invoice items"""
        # Create a frame for this line item
        item_frame = ctk.CTkFrame(self.items_container)
        item_frame.pack(fill="x", pady=2)
        
        # Item Code selection (dropdown) - changed from Item ID to Item Code
        # Store item ID internally, but display item code in dropdown
        item_id_var = ctk.StringVar(value=str(item_data.get('item_id', '')) if item_data else '')
        
        # Create the dropdown values for items - using item_code for display
        item_code_to_id = {item['item_code']: str(item['id']) for item in self.items}
        id_to_item_code = {str(item['id']): item['item_code'] for item in self.items}
        
        item_codes = [""] + [item['item_code'] for item in self.items]
        
        # Create the dropdown with item codes instead of IDs
        item_dropdown = ctk.CTkComboBox(
            item_frame, 
            values=item_codes, 
            width=80,
            command=lambda code: self._item_selected(item_code_to_id.get(code, ""), item_frame)
        )
        item_dropdown.pack(side="left", padx=(5, 0))
        
        # If we have item data, set the selected item code
        if item_data and item_data.get('item_id'):
            item_code = id_to_item_code.get(str(item_data.get('item_id')), "")
            if item_code:
                item_dropdown.set(item_code)
        
        # Description
        description_var = ctk.StringVar(value=item_data.get('description', '') if item_data else '')
        description_entry = ctk.CTkEntry(item_frame, textvariable=description_var, width=200)
        description_entry.pack(side="left", padx=5)
        
        # Quantity
        quantity_var = ctk.StringVar(value=str(item_data.get('quantity', 1)) if item_data else '1')
        quantity_entry = ctk.CTkEntry(item_frame, textvariable=quantity_var, width=80)
        quantity_entry.pack(side="left", padx=5)
        
        # Price
        price_var = ctk.StringVar(value=str(item_data.get('price', 0.0)) if item_data else '0.0')
        price_entry = ctk.CTkEntry(item_frame, textvariable=price_var, width=80)
        price_entry.pack(side="left", padx=5)
        
        # Total (calculated field)
        total = float(item_data.get('quantity', 1)) * float(item_data.get('price', 0.0)) if item_data else 0.0
        total_var = ctk.StringVar(value=f"₱{total:.2f}")
        total_label = ctk.CTkLabel(item_frame, textvariable=total_var, width=80)
        total_label.pack(side="left", padx=5)
        
        # Delete button
        if not self.readonly:
            delete_button = ctk.CTkButton(
                item_frame,
                text="X",
                width=30,
                height=24,
                fg_color="red",
                hover_color="darkred",
                command=lambda: self._delete_line_item(item_frame)
            )
            delete_button.pack(side="left", padx=5)
        
        # If readonly, disable all inputs
        if self.readonly:
            item_dropdown.configure(state="disabled")
            description_entry.configure(state="disabled")
            quantity_entry.configure(state="disabled")
            price_entry.configure(state="disabled")
        
        # Add event handlers for updating total
        def update_total(*args):
            try:
                qty = int(quantity_var.get()) if quantity_var.get() else 0
                prc = float(price_var.get()) if price_var.get() else 0.0
                total_var.set(f"₱{qty * prc:.2f}")
                self._calculate_invoice_total()
            except ValueError:
                total_var.set("₱0.00")
        
        quantity_var.trace_add("write", update_total)
        price_var.trace_add("write", update_total)
        
        # Store the line item data
        line_item = {
            'frame': item_frame,
            'item_id_var': item_id_var,  # Store the ID internally
            'item_dropdown': item_dropdown,  # But display the code in the UI
            'description_var': description_var,
            'description_entry': description_entry,
            'quantity_var': quantity_var,
            'quantity_entry': quantity_entry,
            'price_var': price_var,
            'price_entry': price_entry,
            'total_var': total_var
        }
        
        self.line_items.append(line_item)
        return line_item
    
    def _item_selected(self, item_id, item_frame):
        """Handle item selection from dropdown"""
        if not item_id:
            return
            
        # Find the line item that corresponds to this frame
        for line_item in self.line_items:
            if line_item['frame'] == item_frame:
                # Store the selected item_id
                line_item['item_id_var'].set(item_id)
                
                # Find the selected item in the items list
                for item in self.items:
                    if str(item['id']) == item_id:
                        # Set the description and price
                        line_item['description_var'].set(item['name'])
                        line_item['price_var'].set(str(item['price']))
                        
                        # Update the total
                        try:
                            qty = int(line_item['quantity_var'].get()) if line_item['quantity_var'].get() else 0
                            prc = float(line_item['price_var'].get()) if line_item['price_var'].get() else 0.0
                            line_item['total_var'].set(f"₱{qty * prc:.2f}")
                            self._calculate_invoice_total()
                        except ValueError:
                            line_item['total_var'].set("₱0.00")
                        break
                break
    
    def _delete_line_item(self, item_frame):
        """Delete a line item from the invoice"""
        for i, item in enumerate(self.line_items):
            if item['frame'] == item_frame:
                self.line_items.pop(i)
                break
                
        item_frame.destroy()
        self._calculate_invoice_total()
    
    def _calculate_invoice_total(self):
        """Calculate the total amount of the invoice"""
        total = 0.0
        
        for line_item in self.line_items:
            try:
                # Extract the numeric value from the total
                total_text = line_item['total_var'].get().replace('₱', '')
                item_total = float(total_text) if total_text else 0.0
                total += item_total
            except ValueError:
                continue
                
        self.total_var.set(f"₱{total:.2f}")
    
    def _save(self):
        """Save the invoice data"""
        # Validate required fields
        errors = []
        
        if not self.invoice_number_var.get():
            errors.append("Invoice number is required")
            
        if not self.date_var.get():
            errors.append("Date is required")
            
        if not self.customer_var.get():
            errors.append("Customer name is required")
            
        if not self.line_items:
            errors.append("At least one line item is required")
            
        # Check that all line items have item_id, description, quantity, and price
        for i, item in enumerate(self.line_items):
            if not item['item_id_var'].get():
                errors.append(f"Item {i+1}: Item ID is required")
                
            if not item['description_var'].get():
                errors.append(f"Item {i+1}: Description is required")
                
            try:
                qty = int(item['quantity_var'].get())
                if qty <= 0:
                    errors.append(f"Item {i+1}: Quantity must be greater than zero")
            except ValueError:
                errors.append(f"Item {i+1}: Invalid quantity")
                
            try:
                price = float(item['price_var'].get())
                if price < 0:
                    errors.append(f"Item {i+1}: Price cannot be negative")
            except ValueError:
                errors.append(f"Item {i+1}: Invalid price")
        
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return
            
        # Prepare invoice data
        invoice_data = {
            'invoice_number': self.invoice_number_var.get(),
            'date': self.date_var.get(),
            'customer_name': self.customer_var.get(),
            'customer_address': self.address_text.get("1.0", "end-1c").strip(),
            'total_amount': float(self.total_var.get().replace('₱', '')),
            'mode_of_payment': self.payment_mode_var.get(),  # Add mode of payment to the saved data
            'payment_status': 'pending'  # Set default payment status to pending
        }
        
        # Prepare line items data
        items_data = []
        for item in self.line_items:
            try:
                item_id = int(item['item_id_var'].get())
                description = item['description_var'].get()
                quantity = int(item['quantity_var'].get())
                price = float(item['price_var'].get())
                
                items_data.append({
                    'item_id': item_id,
                    'description': description,
                    'quantity': quantity,
                    'price': price
                })
            except ValueError:
                # Skip invalid items (they should've been caught above)
                continue
                
        # Set the result
        self.result = {
            'invoice': invoice_data,
            'items': items_data
        }
        
        # Close the dialog
        self.destroy()