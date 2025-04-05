import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import logging
from datetime import datetime

class PrintView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger('invoice_manager')
        self.pack(fill="both", expand=True)
        
        # Store currently selected invoice ID and selected invoices for batch printing
        self.selected_invoice_id = None
        self.selected_invoices = set()  # Store IDs of selected invoices
        
        # Create UI elements
        self._create_widgets()
        
    def _create_widgets(self):
        """Create all UI elements for the print invoices view"""
        # Title and filter frame
        title_frame = ctk.CTkFrame(self)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text="Print Invoices", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left", padx=10, pady=10)
        
        # Date filter dropdown
        filter_label = ctk.CTkLabel(title_frame, text="Date Filter:")
        filter_label.pack(side="right", padx=(10, 0), pady=10)
        
        self.date_filter_var = ctk.StringVar(value="All Invoices")
        date_filter_options = [
            "All Invoices", 
            "Today", 
            "Past 7 Days", 
            "Past 30 Days"
        ]
        
        date_filter_menu = ctk.CTkOptionMenu(
            title_frame,
            values=date_filter_options,
            variable=self.date_filter_var,
            command=self._apply_date_filter
        )
        date_filter_menu.pack(side="right", padx=10, pady=10)
        
        # Search frame
        search_frame = ctk.CTkFrame(self)
        search_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        search_label = ctk.CTkLabel(search_frame, text="Search:")
        search_label.pack(side="left", padx=10, pady=10)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self._filter_invoices())
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, width=300)
        search_entry.pack(side="left", padx=10, pady=10)
        
        # Add checkbox for multiple selection mode
        self.multi_select_var = ctk.BooleanVar(value=False)
        multi_select_checkbox = ctk.CTkCheckBox(
            search_frame, 
            text="Enable Multiple Selection",
            variable=self.multi_select_var,
            command=self._toggle_multi_selection
        )
        multi_select_checkbox.pack(side="right", padx=10, pady=10)
        
        # Invoice list frame
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Treeview for invoices
        treeview_frame = ctk.CTkFrame(list_frame)
        treeview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Use a regular Treeview (ttk)
        self.tree = tk.ttk.Treeview(
            treeview_frame, 
            columns=("Select", "ID", "Number", "Date", "Customer", "Total"),
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
        self.tree.heading("Select", text="Select")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Number", text="Invoice #")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Customer", text="Customer")
        self.tree.heading("Total", text="Total")
        
        # Configure column widths and alignment
        self.tree.column("Select", width=50, anchor="center")
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Number", width=120, anchor="center")
        self.tree.column("Date", width=120, anchor="center")
        self.tree.column("Customer", width=250)
        self.tree.column("Total", width=100, anchor="e")
        
        # Bind select event and click event for checkbox column
        self.tree.bind("<<TreeviewSelect>>", self._on_invoice_select)
        self.tree.bind("<Double-1>", self._on_invoice_double_click)
        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)
        
        # Add scrollbar
        scrollbar = tk.ttk.Scrollbar(treeview_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Action buttons for the selected invoice
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        self.preview_button = ctk.CTkButton(
            action_frame, 
            text="Preview Invoice", 
            state="disabled",
            command=self._preview_invoice
        )
        self.preview_button.pack(side="left", padx=10, pady=10)
        
        self.print_button = ctk.CTkButton(
            action_frame, 
            text="Print Invoice", 
            state="disabled", 
            command=self._print_invoice,
            fg_color="#28a745",  # Green color for print button
            hover_color="#218838"  # Darker green on hover
        )
        self.print_button.pack(side="left", padx=10, pady=10)
        
        # Add print selected button (initially hidden)
        self.print_selected_button = ctk.CTkButton(
            action_frame, 
            text="Print Selected Invoices", 
            state="disabled", 
            command=self._print_selected_invoices,
            fg_color="#007bff",  # Blue color for multiple selection
            hover_color="#0056b3"  # Darker blue on hover
        )
        self.print_selected_button.pack(side="right", padx=10, pady=10)
        self.print_selected_button.pack_forget()  # Hide initially
        
        # Store invoices data
        self.invoices_data = []
        
    def display_invoices(self, invoices_data):
        """Display the list of invoices in the treeview"""
        # Clear existing items and selection
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.selected_invoices.clear()
        
        # Store the full data for later use
        self.invoices_data = invoices_data
        
        # Add invoices to the treeview
        for invoice in invoices_data:
            self.tree.insert(
                "", 
                "end", 
                values=(
                    "□",  # Empty checkbox
                    invoice['id'],
                    invoice['invoice_number'],
                    invoice['date'],
                    invoice['customer_name'],
                    f"₱{invoice['total_amount']:.2f}"
                )
            )
            
        # Reset selection
        self.selected_invoice_id = None
        self._update_action_buttons()
        
        # Update status message
        self.logger.info(f"Displaying {len(invoices_data)} invoices for printing")
        
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
                search_text in invoice['customer_name'].lower()):
                
                checkbox = "☑" if invoice['id'] in self.selected_invoices else "□"
                
                self.tree.insert(
                    "", 
                    "end", 
                    values=(
                        checkbox,
                        invoice['id'],
                        invoice['invoice_number'],
                        invoice['date'],
                        invoice['customer_name'],
                        f"₱{invoice['total_amount']:.2f}"
                    )
                )
    
    def _apply_date_filter(self, filter_option):
        """Apply date filter to load invoices"""
        if filter_option == "All Invoices":
            filter_param = None
        elif filter_option == "Today":
            filter_param = "today"
        elif filter_option == "Past 7 Days":
            filter_param = "past_7_days"
        elif filter_option == "Past 30 Days":
            filter_param = "past_30_days"
        else:
            filter_param = None
            
        # Load invoices with the selected filter
        self.controller.load_invoices(filter_param)
    
    def _toggle_multi_selection(self):
        """Toggle between single and multiple selection modes"""
        is_multi_select = self.multi_select_var.get()
        
        if is_multi_select:
            # Show print selected button
            self.print_selected_button.pack(side="right", padx=10, pady=10)
            # Clear current selection
            self.selected_invoice_id = None
            self._update_print_selected_button()
        else:
            # Hide print selected button
            self.print_selected_button.pack_forget()
            # Clear selections
            self.selected_invoices.clear()
            self._refresh_checkboxes()
        
        self._update_action_buttons()
    
    def _on_tree_click(self, event):
        """Handle click on tree item (especially for checkbox column)"""
        if not self.multi_select_var.get():
            return
            
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
            
        column = self.tree.identify_column(event.x)
        if column != "#1":  # Checkbox column
            return
            
        # Get the item that was clicked
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
            
        # Get invoice ID from the row
        values = self.tree.item(item_id, "values")
        if not values or len(values) < 2:
            return
            
        invoice_id = int(values[1])
        
        # Toggle selection
        if invoice_id in self.selected_invoices:
            self.selected_invoices.remove(invoice_id)
            new_checkbox = "□"  # Unchecked
        else:
            self.selected_invoices.add(invoice_id)
            new_checkbox = "☑"  # Checked
            
        # Update the checkbox in the tree
        self.tree.item(item_id, values=(new_checkbox,) + values[1:])
        
        # Update button state
        self._update_print_selected_button()
    
    def _refresh_checkboxes(self):
        """Refresh all checkboxes based on selected_invoices set"""
        for item_id in self.tree.get_children():
            values = self.tree.item(item_id, "values")
            if not values or len(values) < 2:
                continue
                
            invoice_id = int(values[1])
            checkbox = "☑" if invoice_id in self.selected_invoices else "□"
            
            self.tree.item(item_id, values=(checkbox,) + values[1:])
    
    def _on_invoice_select(self, event):
        """Handle invoice selection"""
        if self.multi_select_var.get():
            # In multi-select mode, ignore tree selection
            return
            
        selected_items = self.tree.selection()
        if selected_items:
            item = selected_items[0]
            self.selected_invoice_id = int(self.tree.item(item, "values")[1])  # ID is now at index 1
            self._update_action_buttons()
        else:
            self.selected_invoice_id = None
            self._update_action_buttons()
    
    def _on_invoice_double_click(self, event):
        """Handle double-click on an invoice (preview)"""
        if self.multi_select_var.get():
            return  # Disable double-click in multi-select mode
            
        if self.selected_invoice_id:
            self._preview_invoice()
            
    def _update_action_buttons(self):
        """Update the state of action buttons based on invoice selection"""
        if self.multi_select_var.get():
            # In multi-select mode
            self.preview_button.configure(state="disabled")
            self.print_button.configure(state="disabled")
        elif self.selected_invoice_id:
            # Single item selected in single-select mode
            self.preview_button.configure(state="normal")
            self.print_button.configure(state="normal")
        else:
            # Nothing selected
            self.preview_button.configure(state="disabled")
            self.print_button.configure(state="disabled")
    
    def _update_print_selected_button(self):
        """Update state of print selected button based on number of selections"""
        if len(self.selected_invoices) > 0:
            self.print_selected_button.configure(
                state="normal",
                text=f"Print Selected ({len(self.selected_invoices)})"
            )
        else:
            self.print_selected_button.configure(
                state="disabled",
                text="Print Selected Invoices"
            )
    
    def _preview_invoice(self):
        """Preview the selected invoice"""
        if self.selected_invoice_id:
            self.controller.preview_invoice(self.selected_invoice_id)
    
    def _print_invoice(self):
        """Print the selected invoice"""
        if self.selected_invoice_id:
            self.controller.print_invoice(self.selected_invoice_id)
    
    def _print_selected_invoices(self):
        """Print all selected invoices"""
        if not self.selected_invoices:
            return
            
        success_count = 0
        fail_count = 0
        
        for invoice_id in self.selected_invoices:
            success = self.controller.print_invoice(invoice_id, silent=True)
            if success:
                success_count += 1
            else:
                fail_count += 1
        
        # Show summary message
        if fail_count == 0:
            self.show_info(f"Successfully printed {success_count} invoice(s)")
        else:
            self.show_info(f"Printed {success_count} invoice(s). Failed to print {fail_count} invoice(s).")
    
    def show_error(self, message):
        """Show error message"""
        messagebox.showerror("Error", message)
        
    def show_info(self, message):
        """Show info message"""
        messagebox.showinfo("Information", message)
