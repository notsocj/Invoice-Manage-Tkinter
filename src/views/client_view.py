import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import logging

class ClientView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger('invoice_manager')
        self.pack(fill="both", expand=True)
        
        # Store currently selected client ID
        self.selected_client_id = None
        
        # Pagination settings
        self.current_page = 1
        self.per_page = 20
        self.total_pages = 1
        self.total_count = 0
        
        # Create UI elements
        self._create_widgets()
        
    def _create_widgets(self):
        """Create all UI elements for the client view"""
        # Title and button frame
        title_frame = ctk.CTkFrame(self)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text="Customer Management", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left", padx=10, pady=10)
        
        add_button = ctk.CTkButton(
            title_frame, 
            text="Add New Customer", 
            command=self._show_add_client_dialog,
            hover_color=("gray70", "gray30")
        )
        add_button.pack(side="right", padx=10, pady=10)
        
        refresh_button = ctk.CTkButton(
            title_frame, 
            text="Refresh", 
            command=self._refresh_clients,
            hover_color=("gray70", "gray30")
        )
        refresh_button.pack(side="right", padx=10, pady=10)
        
        # Search and filter frame
        search_frame = ctk.CTkFrame(self)
        search_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        search_label = ctk.CTkLabel(search_frame, text="Search:")
        search_label.pack(side="left", padx=10, pady=10)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self._filter_clients())
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, width=300)
        search_entry.pack(side="left", padx=10, pady=10)
        
        # Page size selector
        page_size_label = ctk.CTkLabel(search_frame, text="Records per page:")
        page_size_label.pack(side="right", padx=10, pady=10)
        
        self.page_size_var = ctk.StringVar(value=str(self.per_page))
        page_size_options = ["10", "20", "50", "100"]
        page_size_menu = ctk.CTkOptionMenu(
            search_frame,
            values=page_size_options,
            variable=self.page_size_var,
            command=self._change_page_size
        )
        page_size_menu.pack(side="right", padx=5, pady=10)
        
        # Client list frame
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Treeview for clients
        # Create a frame for the treeview and scrollbar
        treeview_frame = ctk.CTkFrame(list_frame)
        treeview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Modified Treeview for clients - simplified columns
        self.tree = tk.ttk.Treeview(
            treeview_frame, 
            columns=("ID", "Name", "Mobile", "Address", "Status"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure the treeview style to match CustomTkinter aesthetics as much as possible
        style = tk.ttk.Style()
        
        # Adjust style based on appearance mode
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
        self.tree.heading("Name", text="Name", command=lambda: self._sort_by_column("Name", False))
        self.tree.heading("Mobile", text="Mobile", command=lambda: self._sort_by_column("Mobile", False))
        self.tree.heading("Address", text="Address", command=lambda: self._sort_by_column("Address", False))
        self.tree.heading("Status", text="Status", command=lambda: self._sort_by_column("Status", False))
        
        # Configure column widths and alignment
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Name", width=200)
        self.tree.column("Mobile", width=150)
        self.tree.column("Address", width=300)
        self.tree.column("Status", width=80, anchor="center")
        
        # Bind select event
        self.tree.bind("<<TreeviewSelect>>", self._on_client_select)
        self.tree.bind("<Double-1>", self._on_client_double_click)
        
        # Add scrollbar
        scrollbar = tk.ttk.Scrollbar(treeview_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Pagination controls
        pagination_frame = ctk.CTkFrame(self)
        pagination_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.prev_page_button = ctk.CTkButton(
            pagination_frame,
            text="< Previous",
            width=100,
            command=self._previous_page,
            state="disabled"
        )
        self.prev_page_button.pack(side="left", padx=10, pady=10)
        
        self.pagination_label = ctk.CTkLabel(
            pagination_frame,
            text="Page 1 of 1 (0 records)"
        )
        self.pagination_label.pack(side="left", padx=10, pady=10)
        
        self.next_page_button = ctk.CTkButton(
            pagination_frame,
            text="Next >",
            width=100,
            command=self._next_page,
            state="disabled"
        )
        self.next_page_button.pack(side="left", padx=10, pady=10)
        
        # Jump to page
        self.jump_to_page_var = ctk.StringVar(value="1")
        jump_to_page_entry = ctk.CTkEntry(
            pagination_frame,
            textvariable=self.jump_to_page_var,
            width=50,
            justify="center"
        )
        jump_to_page_entry.pack(side="right", padx=5, pady=10)
        
        goto_label = ctk.CTkLabel(pagination_frame, text="Go to page:")
        goto_label.pack(side="right", padx=5, pady=10)
        
        goto_button = ctk.CTkButton(
            pagination_frame,
            text="Go",
            width=50,
            command=self._goto_page
        )
        goto_button.pack(side="right", padx=5, pady=10)
        
        # Action buttons for the selected client
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        self.view_button = ctk.CTkButton(
            action_frame, 
            text="View Customer", 
            state="disabled", 
            command=self._show_view_client_dialog,
            hover_color=("gray70", "gray30")
        )
        self.view_button.pack(side="left", padx=10, pady=10)
        
        self.edit_button = ctk.CTkButton(
            action_frame, 
            text="Edit Customer", 
            state="disabled", 
            command=self._show_edit_client_dialog,
            hover_color=("gray70", "gray30")
        )
        self.edit_button.pack(side="left", padx=10, pady=10)
        
        self.delete_button = ctk.CTkButton(
            action_frame, 
            text="Delete Customer", 
            state="disabled",
            fg_color="red",
            hover_color="darkred",
            command=self._confirm_delete_client
        )
        self.delete_button.pack(side="right", padx=10, pady=10)
        
        # Store clients data
        self.clients_data = []
        self.sorted_column = None
        self.sort_ascending = True
        
    def display_clients(self, clients_data, pagination_info=None):
        """Display the list of clients in the treeview"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Store the full data for later use
        self.clients_data = clients_data
        
        # Update pagination information
        if pagination_info:
            self.current_page = pagination_info['current_page']
            self.per_page = pagination_info['per_page']
            self.total_count = pagination_info['total_count']
            self.total_pages = pagination_info['total_pages']
            self._update_pagination_controls()
        
        # Add clients to the treeview
        for client in clients_data:
            status = "Active" if client['is_active'] else "Inactive"
            
            self.tree.insert(
                "", 
                "end", 
                values=(
                    client['id'],
                    client['name'],
                    client['mobile'] or "",
                    client['address'] or "",
                    status
                )
            )
            
        # Reset selection
        self.selected_client_id = None
        self._update_action_buttons()
        
        # Update status message
        start_record = (self.current_page - 1) * self.per_page + 1 if self.clients_data else 0
        end_record = start_record + len(self.clients_data) - 1 if self.clients_data else 0
        
        message = f"Showing {start_record} to {end_record} of {self.total_count} customers"
        if self.search_var.get():
            message += f" (filtered by '{self.search_var.get()}')"
        
        self.logger.info(message)
        
    def _filter_clients(self):
        """Filter clients based on search text"""
        search_text = self.search_var.get().lower()
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add filtered clients to the treeview
        for client in self.clients_data:
            if (search_text in str(client['id']).lower() or
                search_text in client['name'].lower() or
                search_text in (client['mobile'] or "").lower() or
                search_text in (client['address'] or "").lower()):
                
                status = "Active" if client['is_active'] else "Inactive"
                self.tree.insert(
                    "", 
                    "end", 
                    values=(
                        client['id'],
                        client['name'],
                        client['mobile'] or "",
                        client['address'] or "",
                        status
                    )
                )
        
    def _update_pagination_controls(self):
        """Update pagination controls based on current state"""
        # Update pagination label
        self.pagination_label.configure(
            text=f"Page {self.current_page} of {self.total_pages} ({self.total_count} records)"
        )
        
        # Update jump to page default value
        self.jump_to_page_var.set(str(self.current_page))
        
        # Enable/disable previous/next buttons
        if self.current_page <= 1:
            self.prev_page_button.configure(state="disabled")
        else:
            self.prev_page_button.configure(state="normal")
            
        if self.current_page >= self.total_pages:
            self.next_page_button.configure(state="disabled")
        else:
            self.next_page_button.configure(state="normal")
    
    def _previous_page(self):
        """Go to the previous page"""
        if self.current_page > 1:
            self.current_page -= 1
            self.controller.load_clients(
                page=self.current_page, 
                per_page=self.per_page,
                search_text=self.search_var.get()
            )
    
    def _next_page(self):
        """Go to the next page"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.controller.load_clients(
                page=self.current_page, 
                per_page=self.per_page,
                search_text=self.search_var.get()
            )
    
    def _goto_page(self):
        """Go to a specific page"""
        try:
            page = int(self.jump_to_page_var.get())
            if 1 <= page <= self.total_pages:
                self.current_page = page
                self.controller.load_clients(
                    page=self.current_page, 
                    per_page=self.per_page,
                    search_text=self.search_var.get()
                )
            else:
                self.jump_to_page_var.set(str(self.current_page))
                self.show_error(f"Page number must be between 1 and {self.total_pages}")
        except ValueError:
            self.jump_to_page_var.set(str(self.current_page))
            self.show_error("Please enter a valid page number")
    
    def _change_page_size(self, size):
        """Change the number of records per page"""
        try:
            self.per_page = int(size)
            self.current_page = 1  # Reset to first page
            self.controller.load_clients(
                page=self.current_page, 
                per_page=self.per_page,
                search_text=self.search_var.get()
            )
        except ValueError:
            self.show_error("Invalid page size")
    
    def _refresh_clients(self):
        """Refresh the client list"""
        self.controller.load_clients(
            page=self.current_page, 
            per_page=self.per_page,
            search_text=self.search_var.get()
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
        
        # Sort items
        items_with_values.sort(key=lambda x: (x[0][col_idx] == "", x[0][col_idx]), reverse=not self.sort_ascending)
        
        # Rearrange items in the tree
        for idx, (values, item) in enumerate(items_with_values):
            self.tree.move(item, "", idx)
        
    def _on_client_select(self, event):
        """Handle client selection"""
        selected_items = self.tree.selection()
        if selected_items:
            item = selected_items[0]
            self.selected_client_id = int(self.tree.item(item, "values")[0])
            self._update_action_buttons()
        else:
            self.selected_client_id = None
            self._update_action_buttons()
    
    def _on_client_double_click(self, event):
        """Handle double-click on a client (view details)"""
        if self.selected_client_id:
            self._show_view_client_dialog()
            
    def _update_action_buttons(self):
        """Update the state of action buttons based on client selection"""
        if self.selected_client_id:
            self.view_button.configure(state="normal")
            self.edit_button.configure(state="normal")
            self.delete_button.configure(state="normal")
        else:
            self.view_button.configure(state="disabled")
            self.edit_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")
            
    def _show_add_client_dialog(self):
        """Show dialog to add a new client"""
        dialog = ClientDialog(self, "Add New Customer")
        dialog.grab_set()  # Make it modal
        self.wait_window(dialog)  # Wait until the dialog is closed
        
        if dialog.result:
            # Process the form data
            success, result = self.controller.add_client(dialog.result)
            if success:
                self.show_info(f"Customer added successfully with ID: {result}")
            else:
                self.show_error(f"Failed to add customer: {result}")
                
    def _show_edit_client_dialog(self):
        """Show dialog to edit an existing client"""
        # Get the client data
        client_data = self.controller.get_client(self.selected_client_id)
        if not client_data:
            self.show_error("Failed to load customer data")
            return
            
        dialog = ClientDialog(self, "Edit Customer", client_data)
        dialog.grab_set()  # Make it modal
        self.wait_window(dialog)  # Wait until the dialog is closed
        
        if dialog.result:
            # Process the form data
            success, result = self.controller.update_client(self.selected_client_id, dialog.result)
            if success:
                self.show_info(f"Customer updated successfully")
            else:
                self.show_error(f"Failed to update customer: {result}")
                
    def _show_view_client_dialog(self):
        """Show dialog to view client details"""
        # Get the client data
        client_data = self.controller.get_client(self.selected_client_id)
        if not client_data:
            self.show_error("Failed to load customer data")
            return
            
        dialog = ClientDialog(self, "View Customer", client_data, readonly=True)
        dialog.grab_set()  # Make it modal
        dialog.wait_window()  # Wait until the dialog is closed
            
    def _confirm_delete_client(self):
        """Show confirmation dialog before deleting a client"""
        if not self.selected_client_id:
            return
            
        # Show confirmation dialog
        if messagebox.askyesno("Confirm Delete", 
                              "Are you sure you want to delete this customer?\nThis action cannot be undone."):
            success, result = self.controller.delete_client(self.selected_client_id)
            if success:
                self.show_info("Customer deleted successfully")
            else:
                self.show_error(f"Failed to delete customer: {result}")
    
    def show_error(self, message):
        """Show error message"""
        messagebox.showerror("Error", message)
        
    def show_info(self, message):
        """Show info message"""
        messagebox.showinfo("Information", message)


class ClientDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, client_data=None, readonly=False):
        super().__init__(parent)
        self.title(title)
        self.geometry("600x400")
        self.resizable(False, False)
        
        # Set up variables
        self.client_data = client_data or {}
        self.readonly = readonly
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
        """Create all UI elements for the client dialog"""
        # Main container
        container_frame = ctk.CTkFrame(self)
        container_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Form title
        title_label = ctk.CTkLabel(
            container_frame, 
            text=self.title(), 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Create simple form - no tabs needed for simplified fields
        form = ctk.CTkFrame(container_frame)
        form.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Name (required)
        name_label = ctk.CTkLabel(form, text="Name:*")
        name_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        self.name_var = ctk.StringVar(value=self.client_data.get('name', ''))
        name_entry = ctk.CTkEntry(form, textvariable=self.name_var, width=400)
        name_entry.grid(row=0, column=1, padx=10, pady=(10, 5), sticky="w")
        
        if self.readonly:
            name_entry.configure(state="disabled")
        
        # Mobile phone
        mobile_label = ctk.CTkLabel(form, text="Mobile:")
        mobile_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.mobile_var = ctk.StringVar(value=self.client_data.get('mobile', ''))
        mobile_entry = ctk.CTkEntry(form, textvariable=self.mobile_var, width=200)
        mobile_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        if self.readonly:
            mobile_entry.configure(state="disabled")
        
        # Address - using a text box for multiline address
        address_label = ctk.CTkLabel(form, text="Address:")
        address_label.grid(row=2, column=0, padx=10, pady=5, sticky="nw")
        
        self.address_text = ctk.CTkTextbox(form, height=80, width=400)
        self.address_text.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        # Insert existing address if any
        if self.client_data.get('address'):
            self.address_text.insert("1.0", self.client_data.get('address'))
            
        if self.readonly:
            self.address_text.configure(state="disabled")
        
        # Status (Active/Inactive) - uses a checkbox
        status_label = ctk.CTkLabel(form, text="Status:")
        status_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        
        self.is_active_var = ctk.BooleanVar(value=self.client_data.get('is_active', True))
        status_checkbox = ctk.CTkCheckBox(
            form, 
            text="Active", 
            variable=self.is_active_var,
            state="disabled" if self.readonly else "normal"
        )
        status_checkbox.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        
        # Button frame
        button_frame = ctk.CTkFrame(container_frame)
        button_frame.pack(fill="x", pady=10)
        
        if not self.readonly:
            save_button = ctk.CTkButton(
                button_frame, 
                text="Save", 
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
        """Save the form data"""
        # Validate form data
        errors = self._validate_form()
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return
        
        # Collect data from form fields
        self.result = {
            'name': self.name_var.get().strip(),
            'mobile': self.mobile_var.get().strip(),
            'address': self.address_text.get("1.0", "end-1c").strip(),
            'is_active': self.is_active_var.get(),
            # Preserve other fields if they exist in the original data
            'company': self.client_data.get('company', ''),
            'email': self.client_data.get('email', ''),
            'city': self.client_data.get('city', ''),
            'state': self.client_data.get('state', ''),
            'postal_code': self.client_data.get('postal_code', ''),
            'country': self.client_data.get('country', ''),
            'payment_terms': self.client_data.get('payment_terms', 30),
            'credit_limit': self.client_data.get('credit_limit', 0.0),
            'notes': self.client_data.get('notes', '')
        }
        
        # Close the dialog
        self.destroy()
    
    def _validate_form(self):
        """Validate form data"""
        errors = []
        
        # Validate required fields
        if not self.name_var.get().strip():
            errors.append("Name is required")
        
        # Validate mobile number if provided
        mobile = self.mobile_var.get().strip()
        if mobile and not self._is_valid_phone(mobile):
            errors.append("Invalid mobile number format")
        
        return errors
    
    def _is_valid_phone(self, phone):
        """Validate phone number format (basic validation)"""
        import re
        # Allow digits, spaces, dashes, plus, and parentheses
        pattern = r'^[0-9\s\(\)\-\+]{7,20}$'
        return re.match(pattern, phone) is not None
