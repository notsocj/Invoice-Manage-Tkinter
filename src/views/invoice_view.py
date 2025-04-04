import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import logging
from datetime import datetime, timedelta
import os
import subprocess
import platform

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
            columns=("ID", "Number", "Client", "Issue Date", "Due Date", "Status", "Total"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure the treeview style to match CustomTkinter aesthetics as much as possible
        style = tk.ttk.Style()
        style.configure("Treeview", 
                        background="#2b2b2b", 
                        foreground="white", 
                        rowheight=25, 
                        fieldbackground="#2b2b2b")
        style.map('Treeview', 
                 background=[('selected', '#347ab3')],
                 foreground=[('selected', 'white')])
        
        # Define column headings
        self.tree.heading("ID", text="ID")
        self.tree.heading("Number", text="Number")
        self.tree.heading("Client", text="Client")
        self.tree.heading("Issue Date", text="Issue Date")
        self.tree.heading("Due Date", text="Due Date")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Total", text="Total")
        
        # Configure column widths and alignment
        self.tree.column("ID", width=50)
        self.tree.column("Number", width=150)
        self.tree.column("Client", width=150)
        self.tree.column("Issue Date", width=120)
        self.tree.column("Due Date", width=120)
        self.tree.column("Status", width=100)
        self.tree.column("Total", width=100)
        
        # Bind select event
        self.tree.bind("<<TreeviewSelect>>", self._on_invoice_select)
        
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
                    invoice['client_name'],
                    invoice['issue_date'].strftime("%Y-%m-%d") if invoice['issue_date'] else "",
                    invoice['due_date'].strftime("%Y-%m-%d") if invoice['due_date'] else "",
                    invoice['status'].capitalize(),
                    f"₱{invoice['total_amount']:.2f}"  # Change to peso
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
                search_text in invoice['client_name'].lower() or
                search_text in invoice['status'].lower()):
                
                self.tree.insert(
                    "", 
                    "end", 
                    values=(
                        invoice['id'],
                        invoice['invoice_number'],
                        invoice['client_name'],
                        invoice['issue_date'].strftime("%Y-%m-%d") if invoice['issue_date'] else "",
                        invoice['due_date'].strftime("%Y-%m-%d") if invoice['due_date'] else "",
                        invoice['status'].capitalize(),
                        f"₱{invoice['total_amount']:.2f}"  # Change to peso
                    )
                )
                
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
        dialog = InvoiceDialog(self, "Add New Invoice", self.controller.get_clients())
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
            
        dialog = InvoiceDialog(self, "Edit Invoice", self.controller.get_clients(), invoice_data, items_data)
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
            
        dialog = InvoiceDialog(self, "View Invoice", self.controller.get_clients(), invoice_data, items_data, readonly=True)
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
    def __init__(self, parent, title, clients, invoice_data=None, items_data=None, readonly=False):
        super().__init__(parent)
        self.title(title)
        self.geometry("800x600")
        self.resizable(False, False)
        
        # Set up variables
        self.clients = clients
        self.invoice_data = invoice_data or {}
        self.items_data = items_data or []
        self.readonly = readonly
        self.result = None
        
        # Store line items
        self.line_items = []
        
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
        
        # Create tabs
        self.tabs = ctk.CTkTabview(container)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)
        
        # General tab
        self.general_tab = self.tabs.add("General")
        self._setup_general_tab()
        
        # Line Items tab
        self.items_tab = self.tabs.add("Line Items")
        self._setup_line_items_tab()
        
        # Notes tab
        self.notes_tab = self.tabs.add("Notes")
        self._setup_notes_tab()
        
        # Button frame
        button_frame = ctk.CTkFrame(container)
        button_frame.pack(fill="x", pady=10)
        
        if not self.readonly:
            save_button = ctk.CTkButton(button_frame, text="Save", command=self._save)
            save_button.pack(side="left", padx=10, pady=10)
        
        cancel_button = ctk.CTkButton(
            button_frame, 
            text="Close" if self.readonly else "Cancel", 
            command=self.destroy
        )
        cancel_button.pack(side="right", padx=10, pady=10)
        
    def _setup_general_tab(self):
        """Set up the general tab"""
        # General tab content
        general_frame = ctk.CTkFrame(self.general_tab)
        general_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Invoice number
        invoice_number_label = ctk.CTkLabel(general_frame, text="Invoice Number:")
        invoice_number_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.invoice_number_var = ctk.StringVar(value=self.invoice_data.get('invoice_number', ''))
        invoice_number_entry = ctk.CTkEntry(general_frame, textvariable=self.invoice_number_var, width=200)
        invoice_number_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        if self.readonly:
            invoice_number_entry.configure(state="disabled")
        
        # Client dropdown
        client_label = ctk.CTkLabel(general_frame, text="Client:")
        client_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        client_values = [f"{client['name']} (ID: {client['id']})" for client in self.clients]
        self.client_dropdown = ctk.CTkOptionMenu(general_frame, values=client_values)
        self.client_dropdown.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        
        if self.invoice_data.get('client_id'):
            for client in self.clients:
                if client['id'] == self.invoice_data['client_id']:
                    self.client_dropdown.set(f"{client['name']} (ID: {client['id']})")
                    break
        
        if self.readonly:
            self.client_dropdown.configure(state="disabled")
        
        # Issue date
        issue_date_label = ctk.CTkLabel(general_frame, text="Issue Date:")
        issue_date_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        
        issue_date = self.invoice_data.get('issue_date', datetime.now())
        self.issue_year_var = ctk.StringVar(value=str(issue_date.year))
        self.issue_month_var = ctk.StringVar(value=str(issue_date.month))
        self.issue_day_var = ctk.StringVar(value=str(issue_date.day))
        
        issue_date_frame = ctk.CTkFrame(general_frame)
        issue_date_frame.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        
        issue_year_entry = ctk.CTkEntry(issue_date_frame, textvariable=self.issue_year_var, width=60)
        issue_year_entry.pack(side="left", padx=5)
        
        issue_month_entry = ctk.CTkEntry(issue_date_frame, textvariable=self.issue_month_var, width=40)
        issue_month_entry.pack(side="left", padx=5)
        
        issue_day_entry = ctk.CTkEntry(issue_date_frame, textvariable=self.issue_day_var, width=40)
        issue_day_entry.pack(side="left", padx=5)
        
        if self.readonly:
            issue_year_entry.configure(state="disabled")
            issue_month_entry.configure(state="disabled")
            issue_day_entry.configure(state="disabled")
        
        # Due date
        due_date_label = ctk.CTkLabel(general_frame, text="Due Date:")
        due_date_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        
        due_date = self.invoice_data.get('due_date', datetime.now() + timedelta(days=30))
        self.due_year_var = ctk.StringVar(value=str(due_date.year))
        self.due_month_var = ctk.StringVar(value=str(due_date.month))
        self.due_day_var = ctk.StringVar(value=str(due_date.day))
        
        due_date_frame = ctk.CTkFrame(general_frame)
        due_date_frame.grid(row=3, column=1, padx=10, pady=10, sticky="w")
        
        due_year_entry = ctk.CTkEntry(due_date_frame, textvariable=self.due_year_var, width=60)
        due_year_entry.pack(side="left", padx=5)
        
        due_month_entry = ctk.CTkEntry(due_date_frame, textvariable=self.due_month_var, width=40)
        due_month_entry.pack(side="left", padx=5)
        
        due_day_entry = ctk.CTkEntry(due_date_frame, textvariable=self.due_day_var, width=40)
        due_day_entry.pack(side="left", padx=5)
        
        if self.readonly:
            due_year_entry.configure(state="disabled")
            due_month_entry.configure(state="disabled")
            due_day_entry.configure(state="disabled")
        
        # Status
        status_label = ctk.CTkLabel(general_frame, text="Status:")
        status_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        
        self.status_var = ctk.StringVar(value=self.invoice_data.get('status', 'draft').capitalize())
        status_dropdown = ctk.CTkOptionMenu(
            general_frame, 
            values=["Draft", "Sent", "Paid", "Partial", "Overdue", "Cancelled"],
            variable=self.status_var
        )
        status_dropdown.grid(row=4, column=1, padx=10, pady=10, sticky="w")
        
        if self.readonly:
            status_dropdown.configure(state="disabled")
        
        # Subtotal
        subtotal_label = ctk.CTkLabel(general_frame, text="Subtotal:")
        subtotal_label.grid(row=5, column=0, padx=10, pady=10, sticky="w")
        
        self.subtotal_var = ctk.StringVar(value=f"₱{self.invoice_data.get('subtotal', 0.00):.2f}")
        subtotal_entry = ctk.CTkEntry(general_frame, textvariable=self.subtotal_var, width=100)
        subtotal_entry.grid(row=5, column=1, padx=10, pady=10, sticky="w")
        
        if self.readonly:
            subtotal_entry.configure(state="disabled")
        
        # Tax
        tax_label = ctk.CTkLabel(general_frame, text="Tax:")
        tax_label.grid(row=6, column=0, padx=10, pady=10, sticky="w")
        
        self.tax_var = ctk.StringVar(value=f"{self.invoice_data.get('tax_amount', 0.00):.2f}")
        tax_entry = ctk.CTkEntry(general_frame, textvariable=self.tax_var, width=100)
        tax_entry.grid(row=6, column=1, padx=10, pady=10, sticky="w")
        
        if self.readonly:
            tax_entry.configure(state="disabled")
        
        # Discount
        discount_label = ctk.CTkLabel(general_frame, text="Discount:")
        discount_label.grid(row=7, column=0, padx=10, pady=10, sticky="w")
        
        self.discount_var = ctk.StringVar(value=f"{self.invoice_data.get('discount', 0.00):.2f}")
        discount_entry = ctk.CTkEntry(general_frame, textvariable=self.discount_var, width=100)
        discount_entry.grid(row=7, column=1, padx=10, pady=10, sticky="w")
        
        if self.readonly:
            discount_entry.configure(state="disabled")
        
        # Total
        total_label = ctk.CTkLabel(general_frame, text="Total:")
        total_label.grid(row=8, column=0, padx=10, pady=10, sticky="w")
        
        self.total_var = ctk.StringVar(value=f"₱{self.invoice_data.get('total_amount', 0.00):.2f}")
        total_entry = ctk.CTkEntry(general_frame, textvariable=self.total_var, width=100)
        total_entry.grid(row=8, column=1, padx=10, pady=10, sticky="w")
        
        if self.readonly:
            total_entry.configure(state="disabled")
        
        # Commission Rate
        commission_rate_label = ctk.CTkLabel(general_frame, text="Commission Rate (%):")
        commission_rate_label.grid(row=9, column=0, padx=10, pady=10, sticky="w")
        
        self.commission_rate_var = ctk.StringVar(value=f"{self.invoice_data.get('commission_rate', 0.00) * 100:.2f}")
        commission_rate_entry = ctk.CTkEntry(general_frame, textvariable=self.commission_rate_var, width=100)
        commission_rate_entry.grid(row=9, column=1, padx=10, pady=10, sticky="w")
        
        if self.readonly:
            commission_rate_entry.configure(state="disabled")
        
        # Commission Amount
        commission_amount_label = ctk.CTkLabel(general_frame, text="Commission Amount:")
        commission_amount_label.grid(row=10, column=0, padx=10, pady=10, sticky="w")
        
        self.commission_amount_var = ctk.StringVar(value=f"₱{self.invoice_data.get('commission_amount', 0.00):.2f}")
        commission_amount_entry = ctk.CTkEntry(general_frame, textvariable=self.commission_amount_var, width=100)
        commission_amount_entry.grid(row=10, column=1, padx=10, pady=10, sticky="w")
        
        if self.readonly:
            commission_amount_entry.configure(state="disabled")
        
    def _setup_line_items_tab(self):
        """Set up the line items tab"""
        # Line items tab content
        items_frame = ctk.CTkFrame(self.items_tab)
        items_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add line item button
        if not self.readonly:
            add_item_button = ctk.CTkButton(items_frame, text="Add Line Item", command=self._add_line_item)
            add_item_button.pack(pady=10)
        
        # Line items container
        self.items_container = ctk.CTkFrame(items_frame)
        self.items_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add existing line items
        for item_data in self.items_data:
            self._add_line_item(item_data)
        
        # Totals section
        totals_frame = ctk.CTkFrame(items_frame)
        totals_frame.pack(fill="x", padx=10, pady=10)
        
        # Subtotal
        items_subtotal_label = ctk.CTkLabel(totals_frame, text="Subtotal:")
        items_subtotal_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.items_subtotal_var = ctk.StringVar(value=f"₱{self.invoice_data.get('subtotal', 0.00):.2f}")
        items_subtotal_entry = ctk.CTkEntry(totals_frame, textvariable=self.items_subtotal_var, width=100)
        items_subtotal_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        if self.readonly:
            items_subtotal_entry.configure(state="disabled")
        
        # Tax
        items_tax_label = ctk.CTkLabel(totals_frame, text="Tax:")
        items_tax_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.items_tax_var = ctk.StringVar(value=f"{self.invoice_data.get('tax_amount', 0.00):.2f}")
        items_tax_entry = ctk.CTkEntry(totals_frame, textvariable=self.items_tax_var, width=100)
        items_tax_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        
        if self.readonly:
            items_tax_entry.configure(state="disabled")
        
        # Discount
        items_discount_label = ctk.CTkLabel(totals_frame, text="Discount:")
        items_discount_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        
        self.items_discount_var = ctk.StringVar(value=f"{self.invoice_data.get('discount', 0.00):.2f}")
        items_discount_entry = ctk.CTkEntry(totals_frame, textvariable=self.items_discount_var, width=100)
        items_discount_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        
        if self.readonly:
            items_discount_entry.configure(state="disabled")
        
        # Total
        items_total_label = ctk.CTkLabel(totals_frame, text="Total:")
        items_total_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        
        self.items_total_var = ctk.StringVar(value=f"₱{self.invoice_data.get('total_amount', 0.00):.2f}")
        items_total_entry = ctk.CTkEntry(totals_frame, textvariable=self.items_total_var, width=100)
        items_total_entry.grid(row=3, column=1, padx=10, pady=10, sticky="w")
        
        if self.readonly:
            items_total_entry.configure(state="disabled")
        
    def _setup_notes_tab(self):
        """Set up the notes tab"""
        # Notes tab content
        notes_frame = ctk.CTkFrame(self.notes_tab)
        notes_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Notes field
        notes_label = ctk.CTkLabel(notes_frame, text="Notes:")
        notes_label.pack(anchor="w", padx=10, pady=(10, 0))
        
        self.notes_text = ctk.CTkTextbox(notes_frame, height=200)
        self.notes_text.pack(fill="x", padx=10, pady=(0, 10))
        
        # Insert existing notes if any
        if self.invoice_data.get('notes'):
            self.notes_text.insert("1.0", self.invoice_data.get('notes'))
        
        if self.readonly:
            self.notes_text.configure(state="disabled")
    
    def _add_line_item(self, item_data=None):
        """Add a line item row to the invoice items"""
        # Create a frame for this line item
        item_frame = ctk.CTkFrame(self.items_container)
        item_frame.pack(fill="x", pady=2)
        
        # Description
        description_var = ctk.StringVar(value=item_data.get('description', '') if item_data else '')
        description_entry = ctk.CTkEntry(item_frame, textvariable=description_var, width=300)
        description_entry.pack(side="left", padx=(10, 5))
        
        # Quantity
        quantity_var = ctk.StringVar(value=str(item_data.get('quantity', '1')) if item_data else '1')
        quantity_entry = ctk.CTkEntry(item_frame, textvariable=quantity_var, width=80)
        quantity_entry.pack(side="left", padx=5)
        
        # Unit Price
        unit_price_var = ctk.StringVar(value=str(item_data.get('unit_price', '0.00')) if item_data else '0.00')
        unit_price_entry = ctk.CTkEntry(item_frame, textvariable=unit_price_var, width=100)
        unit_price_entry.pack(side="left", padx=5)
        
        # Total (calculated automatically)
        total_var = ctk.StringVar(value=f"₱{item_data.get('total', 0.00):.2f}" if item_data else "₱0.00")
        total_label = ctk.CTkLabel(item_frame, textvariable=total_var, width=100)
        total_label.pack(side="left", padx=5)
        
        # Delete button if not readonly
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
            
            # Set up event bindings to update calculations
            def update_total(*args):
                try:
                    quantity = float(quantity_var.get()) if quantity_var.get() else 0
                    unit_price = float(unit_price_var.get()) if unit_price_var.get() else 0
                    item_total = quantity * unit_price
                    total_var.set(f"₱{item_total:.2f}")
                    self._update_invoice_totals()
                except ValueError:
                    total_var.set("₱0.00")
            
            quantity_var.trace_add("write", update_total)
            unit_price_var.trace_add("write", update_total)
        
        # If readonly, disable all entry fields
        if self.readonly:
            description_entry.configure(state="disabled")
            quantity_entry.configure(state="disabled")
            unit_price_entry.configure(state="disabled")
        
        # Store the item data for later retrieval
        line_item = {
            'frame': item_frame,
            'description_var': description_var,
            'description_entry': description_entry,
            'quantity_var': quantity_var,
            'quantity_entry': quantity_entry,
            'unit_price_var': unit_price_var,
            'unit_price_entry': unit_price_entry,
            'total_var': total_var,
            'total_label': total_label
        }
        
        self.line_items.append(line_item)
        
        # Calculate initial total
        if not self.readonly:
            update_total()
            
        return line_item
    
    def _delete_line_item(self, item_frame):
        """Delete a line item from the invoice"""
        # Find and remove the line item from our tracking list
        for i, item in enumerate(self.line_items):
            if item['frame'] == item_frame:
                self.line_items.pop(i)
                break
        
        # Remove the widget
        item_frame.destroy()
        
        # Update totals
        self._update_invoice_totals()
    
    def _update_invoice_totals(self):
        """Update all totals based on line items"""
        # Calculate subtotal from line items
        subtotal = 0.0
        for item in self.line_items:
            try:
                # Extract the numeric value from the total string (remove ₱ sign)
                total_text = item['total_var'].get().replace('₱', '')
                total = float(total_text) if total_text else 0
                subtotal += total
            except ValueError:
                pass
        
        # Get tax and discount values
        try:
            tax = float(self.tax_var.get()) if self.tax_var.get() else 0.0
        except ValueError:
            tax = 0.0
            
        try:
            discount = float(self.discount_var.get()) if self.discount_var.get() else 0.0
        except ValueError:
            discount = 0.0
        
        # Calculate total
        total = subtotal + tax - discount
        
        # Update the commission amount based on the rate
        try:
            commission_rate = float(self.commission_rate_var.get()) / 100  # Convert percent to decimal
            commission_amount = total * commission_rate
        except ValueError:
            commission_amount = 0.0
        
        # Update display values
        self.subtotal_var.set(f"₱{subtotal:.2f}")
        self.total_var.set(f"₱{total:.2f}")
        self.commission_amount_var.set(f"₱{commission_amount:.2f}")
        
        # Also update values in the items tab
        self.items_subtotal_var.set(f"₱{subtotal:.2f}")
        self.items_tax_var.set(f"₱{tax:.2f}")
        self.items_discount_var.set(f"₱{discount:.2f}")
        self.items_total_var.set(f"₱{total:.2f}")
    
    def _save(self):
        """Save the invoice data"""
        # Validate required fields
        errors = []
        
        # Check for client selection
        client_id = None
        if self.client_dropdown.get():
            try:
                # Extract client ID from the dropdown text (format: "Client Name (ID: X)")
                client_str = self.client_dropdown.get()
                client_id = int(client_str.split("ID: ")[1].strip(")"))
            except (IndexError, ValueError):
                errors.append("Invalid client selection")
        else:
            errors.append("Client is required")
        
        # Check for line items
        if not self.line_items:
            errors.append("At least one line item is required")
        
        # Validate dates
        issue_date = None
        due_date = None
        
        try:
            issue_date = datetime(
                int(self.issue_year_var.get()),
                int(self.issue_month_var.get()),
                int(self.issue_day_var.get())
            )
        except (ValueError, TypeError):
            errors.append("Invalid issue date")
            
        try:
            due_date = datetime(
                int(self.due_year_var.get()),
                int(self.due_month_var.get()),
                int(self.due_day_var.get())
            )
        except (ValueError, TypeError):
            errors.append("Invalid due date")
        
        # Show errors if any
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return
        
        # Get invoice data
        status_value = self.status_var.get().lower()
        
        try:
            commission_rate = float(self.commission_rate_var.get()) / 100  # Convert percent to decimal
        except ValueError:
            commission_rate = 0
            
        try:
            tax_amount = float(self.tax_var.get())
        except ValueError:
            tax_amount = 0
            
        try:
            discount = float(self.discount_var.get())
        except ValueError:
            discount = 0
        
        # Extract subtotal from displayed value (remove ₱ sign)
        subtotal_text = self.subtotal_var.get().replace('₱', '')
        try:
            subtotal = float(subtotal_text)
        except ValueError:
            subtotal = 0
        
        # Extract total from displayed value (remove ₱ sign)
        total_text = self.total_var.get().replace('₱', '')
        try:
            total_amount = float(total_text)
        except ValueError:
            total_amount = 0
            
        # Extract commission amount from displayed value (remove ₱ sign)
        commission_text = self.commission_amount_var.get().replace('₱', '')
        try:
            commission_amount = float(commission_text)
        except ValueError:
            commission_amount = 0
        
        # Prepare invoice data
        invoice_data = {
            'invoice_number': self.invoice_number_var.get(),
            'client_id': client_id,
            'issue_date': issue_date,
            'due_date': due_date,
            'status': status_value,
            'subtotal': subtotal,
            'tax_amount': tax_amount,
            'discount': discount,
            'total_amount': total_amount,
            'commission_rate': commission_rate,
            'commission_amount': commission_amount,
            'notes': self.notes_text.get("1.0", "end-1c").strip()
        }
        
        # Prepare line items data
        items_data = []
        for item in self.line_items:
            try:
                quantity = float(item['quantity_var'].get()) if item['quantity_var'].get() else 0
                unit_price = float(item['unit_price_var'].get()) if item['unit_price_var'].get() else 0
                total = quantity * unit_price
                
                # Skip empty items
                if not item['description_var'].get().strip():
                    continue
                    
                items_data.append({
                    'description': item['description_var'].get().strip(),
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total': total
                })
            except ValueError:
                pass
        
        # Set the result
        self.result = {
            'invoice': invoice_data,
            'items': items_data
        }
        
        # Close the dialog
        self.destroy()