import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import logging
from datetime import datetime

class PaymentView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger('invoice_manager')
        self.pack(fill="both", expand=True)
        
        # Store currently selected payment ID
        self.selected_payment_id = None
        
        # Create UI elements
        self._create_widgets()
        
    def _create_widgets(self):
        """Create all UI elements for the payment view"""
        # Title and button frame
        title_frame = ctk.CTkFrame(self)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text="Payment Management", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left", padx=10, pady=10)
        
        add_button = ctk.CTkButton(
            title_frame, 
            text="Record New Payment", 
            command=self._show_add_payment_dialog
        )
        add_button.pack(side="right", padx=10, pady=10)
        
        refresh_button = ctk.CTkButton(
            title_frame, 
            text="Refresh", 
            command=self.controller.load_payments
        )
        refresh_button.pack(side="right", padx=10, pady=10)
        
        # Search frame
        search_frame = ctk.CTkFrame(self)
        search_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        search_label = ctk.CTkLabel(search_frame, text="Search:")
        search_label.pack(side="left", padx=10, pady=10)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self._filter_payments())
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, width=300)
        search_entry.pack(side="left", padx=10, pady=10)
        
        # Payment method filter
        method_label = ctk.CTkLabel(search_frame, text="Payment Method:")
        method_label.pack(side="left", padx=(20, 10), pady=10)
        
        self.method_var = ctk.StringVar(value="All")
        method_options = ["All"] + [method['name'] for method in self.controller.get_payment_methods()]
        method_menu = ctk.CTkOptionMenu(
            search_frame,
            values=method_options,
            variable=self.method_var,
            command=self._filter_payments
        )
        method_menu.pack(side="left", padx=10, pady=10)
        
        # Payment list frame
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Treeview for payments
        # Create a frame for the treeview and scrollbar
        treeview_frame = ctk.CTkFrame(list_frame)
        treeview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Use a regular Treeview (ttk) as CustomTkinter doesn't have a Treeview widget
        self.tree = tk.ttk.Treeview(
            treeview_frame, 
            columns=("ID", "Invoice", "Amount", "Date", "Method", "Reference"),
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
        self.tree.heading("Invoice", text="Invoice #")
        self.tree.heading("Amount", text="Amount")
        self.tree.heading("Date", text="Payment Date")
        self.tree.heading("Method", text="Method")
        self.tree.heading("Reference", text="Reference #")
        
        # Configure column widths and alignment
        self.tree.column("ID", width=50)
        self.tree.column("Invoice", width=150)
        self.tree.column("Amount", width=100, anchor="e")
        self.tree.column("Date", width=120)
        self.tree.column("Method", width=120)
        self.tree.column("Reference", width=150)
        
        # Bind select event
        self.tree.bind("<<TreeviewSelect>>", self._on_payment_select)
        
        # Add scrollbar
        scrollbar = tk.ttk.Scrollbar(treeview_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Action buttons for the selected payment
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        self.view_button = ctk.CTkButton(
            action_frame, 
            text="View Details", 
            state="disabled", 
            command=self._show_view_payment_dialog
        )
        self.view_button.pack(side="left", padx=10, pady=10)
        
        self.edit_button = ctk.CTkButton(
            action_frame, 
            text="Edit Payment", 
            state="disabled", 
            command=self._show_edit_payment_dialog
        )
        self.edit_button.pack(side="left", padx=10, pady=10)
        
        self.delete_button = ctk.CTkButton(
            action_frame, 
            text="Delete Payment", 
            state="disabled",
            fg_color="red",
            hover_color="darkred",
            command=self._confirm_delete_payment
        )
        self.delete_button.pack(side="right", padx=10, pady=10)
        
        # Store payments data
        self.payments_data = []
        
    def display_payments(self, payments_data):
        """Display the list of payments in the treeview"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Store the full data for later use
        self.payments_data = payments_data
        
        # Add payments to the treeview
        for payment in payments_data:
            # Format date
            payment_date = payment['payment_date'].strftime('%Y-%m-%d') if payment['payment_date'] else ""
            
            # Format amount with peso symbol
            amount = f"₱{payment['amount']:.2f}"
            
            # Format payment method
            method = payment['payment_method'].replace('_', ' ').title()
            
            self.tree.insert(
                "", 
                "end", 
                values=(
                    payment['id'],
                    payment['invoice_number'],
                    amount,
                    payment_date,
                    method,
                    payment['reference_number'] or ""
                )
            )
            
        # Reset selection
        self.selected_payment_id = None
        self._update_action_buttons()
        
    def _filter_payments(self, *args):
        """Filter payments based on search text and method"""
        search_text = self.search_var.get().lower()
        method_filter = self.method_var.get()
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add filtered payments to the treeview
        for payment in self.payments_data:
            # Check method filter
            payment_method_name = payment['payment_method'].replace('_', ' ').title()
            if method_filter != "All" and payment_method_name != method_filter:
                continue
                
            # Check search text
            if not (search_text in str(payment['id']).lower() or
                   search_text in payment['invoice_number'].lower() or
                   search_text in str(payment['amount']).lower() or
                   (payment['payment_date'] and search_text in payment['payment_date'].strftime('%Y-%m-%d').lower()) or
                   search_text in payment['payment_method'].lower() or
                   (payment['reference_number'] and search_text in payment['reference_number'].lower())):
                continue
                
            # Format date
            payment_date = payment['payment_date'].strftime('%Y-%m-%d') if payment['payment_date'] else ""
            
            # Format amount with peso symbol
            amount = f"₱{payment['amount']:.2f}"
            
            # Format payment method
            method = payment['payment_method'].replace('_', ' ').title()
            
            self.tree.insert(
                "", 
                "end", 
                values=(
                    payment['id'],
                    payment['invoice_number'],
                    amount,
                    payment_date,
                    method,
                    payment['reference_number'] or ""
                )
            )
                
    def _on_payment_select(self, event):
        """Handle payment selection"""
        selected_items = self.tree.selection()
        if selected_items:
            item = selected_items[0]
            self.selected_payment_id = int(self.tree.item(item, "values")[0])
            self._update_action_buttons()
        else:
            self.selected_payment_id = None
            self._update_action_buttons()
            
    def _update_action_buttons(self):
        """Update the state of action buttons based on payment selection"""
        if self.selected_payment_id:
            self.view_button.configure(state="normal")
            self.edit_button.configure(state="normal")
            self.delete_button.configure(state="normal")
        else:
            self.view_button.configure(state="disabled")
            self.edit_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")
            
    def _show_add_payment_dialog(self, invoice_id=None):
        """Show dialog to add a new payment"""
        # Get unpaid invoices for dropdown
        invoices = self.controller.get_unpaid_invoices()
        if not invoices:
            self.show_error("No unpaid invoices found")
            return
            
        dialog = PaymentDialog(self, "Record New Payment", invoices=invoices, selected_invoice_id=invoice_id)
        dialog.grab_set()  # Make it modal
        self.wait_window(dialog)  # Wait until the dialog is closed
        
        if dialog.result:
            # Process the form data
            success, result = self.controller.add_payment(dialog.result)
            if success:
                self.show_info(f"Payment recorded successfully with ID: {result}")
            else:
                self.show_error(f"Failed to record payment: {result}")
                
    def _show_edit_payment_dialog(self):
        """Show dialog to edit an existing payment"""
        # Get the payment data
        payment_data = self.controller.get_payment(self.selected_payment_id)
        if not payment_data:
            self.show_error("Failed to load payment data")
            return
            
        # Get unpaid invoices for dropdown (for display only in this case)
        invoices = self.controller.get_unpaid_invoices()
            
        dialog = PaymentDialog(self, "Edit Payment", payment_data=payment_data, invoices=invoices)
        dialog.grab_set()  # Make it modal
        self.wait_window(dialog)  # Wait until the dialog is closed
        
        if dialog.result:
            # Process the form data
            success, result = self.controller.update_payment(self.selected_payment_id, dialog.result)
            if success:
                self.show_info(f"Payment updated successfully")
            else:
                self.show_error(f"Failed to update payment: {result}")
                
    def _show_view_payment_dialog(self):
        """Show dialog to view payment details"""
        # Get the payment data
        payment_data = self.controller.get_payment(self.selected_payment_id)
        if not payment_data:
            self.show_error("Failed to load payment data")
            return
            
        # Get unpaid invoices for dropdown (for display only)
        invoices = self.controller.get_unpaid_invoices()
            
        dialog = PaymentDialog(self, "View Payment", payment_data=payment_data, invoices=invoices, readonly=True)
        dialog.grab_set()  # Make it modal
        dialog.wait_window()  # Wait until the dialog is closed
            
    def _confirm_delete_payment(self):
        """Show confirmation dialog before deleting a payment"""
        if not self.selected_payment_id:
            return
            
        # Show confirmation dialog
        if messagebox.askyesno("Confirm Delete", 
                              "Are you sure you want to delete this payment?\nThis action cannot be undone."):
            success, result = self.controller.delete_payment(self.selected_payment_id)
            if success:
                self.show_info("Payment deleted successfully")
            else:
                self.show_error(f"Failed to delete payment: {result}")
    
    def show_error(self, message):
        """Show error message"""
        messagebox.showerror("Error", message)
        
    def show_info(self, message):
        """Show info message"""
        messagebox.showinfo("Information", message)


class PaymentDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, payment_data=None, invoices=None, readonly=False, selected_invoice_id=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("500x550")
        self.resizable(False, False)
        
        # Set up variables
        self.payment_data = payment_data or {}
        self.invoices = invoices or []
        self.readonly = readonly
        self.selected_invoice_id = selected_invoice_id
        self.result = None
        
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
        """Create all UI elements for the payment dialog"""
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
        
        # Form
        form_frame = ctk.CTkFrame(container)
        form_frame.pack(fill="x", padx=10, pady=10)
        
        # Invoice selection
        invoice_frame = ctk.CTkFrame(form_frame)
        invoice_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(invoice_frame, text="Invoice:").pack(anchor="w", padx=10, pady=(10, 0))
        
        # Create invoice dropdown
        invoice_options = []
        for invoice in self.invoices:
            # Format: INV-123456 - Client Name (₱Amount)
            option = f"{invoice['invoice_number']} - {invoice['client_name']} (₱{invoice['remaining_amount']:.2f})"
            invoice_options.append(option)
        
        self.invoice_var = ctk.StringVar()
        self.invoice_dropdown = ctk.CTkComboBox(
            invoice_frame, 
            values=invoice_options,
            variable=self.invoice_var,
            state="readonly" if self.readonly else "normal",
            width=400
        )
        self.invoice_dropdown.pack(fill="x", padx=10, pady=(0, 10))
        
        # Set the selected invoice if editing, viewing or if a specific invoice was selected
        if self.payment_data.get('invoice_id'):
            for i, invoice in enumerate(self.invoices):
                if invoice['id'] == self.payment_data.get('invoice_id'):
                    self.invoice_dropdown.set(invoice_options[i])
                    break
        elif self.selected_invoice_id:
            for i, invoice in enumerate(self.invoices):
                if invoice['id'] == self.selected_invoice_id:
                    self.invoice_dropdown.set(invoice_options[i])
                    break
        elif invoice_options:
            self.invoice_dropdown.set(invoice_options[0])  # Default to first invoice
            
        # Amount
        amount_frame = ctk.CTkFrame(form_frame)
        amount_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(amount_frame, text="Amount:").pack(anchor="w", padx=10, pady=(10, 0))
        
        self.amount_var = ctk.StringVar(value=str(self.payment_data.get('amount', '')))
        self.amount_entry = ctk.CTkEntry(amount_frame, textvariable=self.amount_var)
        self.amount_entry.pack(fill="x", padx=10, pady=(0, 10))
        
        if self.readonly:
            self.amount_entry.configure(state="disabled")
            
        # Payment Date
        date_frame = ctk.CTkFrame(form_frame)
        date_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(date_frame, text="Payment Date:").pack(anchor="w", padx=10, pady=(10, 0))
        
        # Date entry (for simplicity, using separate entry fields for year, month, day)
        date_entry_frame = ctk.CTkFrame(date_frame)
        date_entry_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Year
        self.year_var = ctk.StringVar()
        self.year_entry = ctk.CTkEntry(date_entry_frame, textvariable=self.year_var, width=60)
        self.year_entry.pack(side="left", padx=(0, 5))
        ctk.CTkLabel(date_entry_frame, text="-").pack(side="left", padx=(0, 5))
        
        # Month
        self.month_var = ctk.StringVar()
        self.month_entry = ctk.CTkEntry(date_entry_frame, textvariable=self.month_var, width=40)
        self.month_entry.pack(side="left", padx=(0, 5))
        ctk.CTkLabel(date_entry_frame, text="-").pack(side="left", padx=(0, 5))
        
        # Day
        self.day_var = ctk.StringVar()
        self.day_entry = ctk.CTkEntry(date_entry_frame, textvariable=self.day_var, width=40)
        self.day_entry.pack(side="left")
        
        # Set the payment date if editing an existing payment
        if self.payment_data.get('payment_date'):
            payment_date = self.payment_data.get('payment_date')
            self.year_var.set(str(payment_date.year))
            self.month_var.set(str(payment_date.month).zfill(2))
            self.day_var.set(str(payment_date.day).zfill(2))
        else:
            # Default to today's date for new payments
            today = datetime.now()
            self.year_var.set(str(today.year))
            self.month_var.set(str(today.month).zfill(2))
            self.day_var.set(str(today.day).zfill(2))
            
        if self.readonly:
            self.year_entry.configure(state="disabled")
            self.month_entry.configure(state="disabled")
            self.day_entry.configure(state="disabled")
            
        # Payment Method
        method_frame = ctk.CTkFrame(form_frame)
        method_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(method_frame, text="Payment Method:").pack(anchor="w", padx=10, pady=(10, 0))
        
        # Get payment methods from the controller
        payment_methods = [method['name'] for method in self.parent.controller.get_payment_methods()]
        
        self.method_var = ctk.StringVar()
        self.method_dropdown = ctk.CTkComboBox(
            method_frame, 
            values=payment_methods,
            variable=self.method_var,
            state="readonly" if self.readonly else "normal"
        )
        self.method_dropdown.pack(fill="x", padx=10, pady=(0, 10))
        
        # Set the payment method if editing an existing payment
        if self.payment_data.get('payment_method'):
            method = self.payment_data.get('payment_method').replace('_', ' ').title()
            self.method_dropdown.set(method)
        else:
            self.method_dropdown.set(payment_methods[0] if payment_methods else "Cash")  # Default to first method
            
        # Reference Number
        reference_frame = ctk.CTkFrame(form_frame)
        reference_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(reference_frame, text="Reference Number:").pack(anchor="w", padx=10, pady=(10, 0))
        
        self.reference_var = ctk.StringVar(value=self.payment_data.get('reference_number', ''))
        self.reference_entry = ctk.CTkEntry(reference_frame, textvariable=self.reference_var)
        self.reference_entry.pack(fill="x", padx=10, pady=(0, 10))
        
        if self.readonly:
            self.reference_entry.configure(state="disabled")
            
        # Notes
        notes_frame = ctk.CTkFrame(form_frame)
        notes_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(notes_frame, text="Notes:").pack(anchor="w", padx=10, pady=(10, 0))
        
        self.notes_text = ctk.CTkTextbox(notes_frame, height=100)
        self.notes_text.pack(fill="x", padx=10, pady=(0, 10))
        
        # Set notes if editing an existing payment
        if self.payment_data.get('notes'):
            self.notes_text.insert("1.0", self.payment_data.get('notes'))
            
        if self.readonly:
            self.notes_text.configure(state="disabled")
            
        # Button frame
        button_frame = ctk.CTkFrame(container)
        button_frame.pack(fill="x", pady=10)
        
        if not self.readonly:
            save_button = ctk.CTkButton(
                button_frame, 
                text="Save Payment", 
                command=self._save,
                font=ctk.CTkFont(size=14, weight="bold"),
            )
            save_button.pack(side="left", padx=10, pady=10)
        
        cancel_button = ctk.CTkButton(
            button_frame, 
            text="Close" if self.readonly else "Cancel", 
            command=self.destroy
        )
        cancel_button.pack(side="right", padx=10, pady=10)
        
    def _save(self):
        """Save the payment data"""
        # Validate required fields
        errors = []
        
        # Check for invoice selection
        invoice_id = None
        if self.invoice_dropdown.get():
            try:
                # Find the selected invoice by its display text
                selected_text = self.invoice_dropdown.get()
                for invoice in self.invoices:
                    # Format from dropdown: INV-123456 - Client Name ($Amount)
                    if selected_text.startswith(f"{invoice['invoice_number']} - "):
                        invoice_id = invoice['id']
                        break
                
                if invoice_id is None:
                    errors.append("Invalid invoice selection")
            except (IndexError, ValueError):
                errors.append("Invalid invoice selection")
        else:
            errors.append("Invoice is required")
            
        # Check amount
        try:
            amount = float(self.amount_var.get())
            if amount <= 0:
                errors.append("Amount must be greater than zero")
        except ValueError:
            errors.append("Invalid amount")
            
        # Validate date
        payment_date = None
        try:
            payment_date = datetime(
                int(self.year_var.get()),
                int(self.month_var.get()),
                int(self.day_var.get())
            )
        except (ValueError, TypeError):
            errors.append("Invalid payment date")
            
        # Show errors if any
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return
            
        # Get payment method
        payment_method = self.method_var.get().lower().replace(' ', '_')
        
        # Prepare payment data
        self.result = {
            'invoice_id': invoice_id,
            'amount': amount,
            'payment_date': payment_date,
            'payment_method': payment_method,
            'reference_number': self.reference_var.get().strip(),
            'notes': self.notes_text.get("1.0", "end-1c").strip()
        }
        
        # Close the dialog
        self.destroy()
