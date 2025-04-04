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
        
        # Create UI elements
        self._create_widgets()
        
    def _create_widgets(self):
        """Create all UI elements for the client view"""
        # Title and button frame
        title_frame = ctk.CTkFrame(self)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text="Client Management", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left", padx=10, pady=10)
        
        add_button = ctk.CTkButton(
            title_frame, 
            text="Add New Client", 
            command=self._show_add_client_dialog
        )
        add_button.pack(side="right", padx=10, pady=10)
        
        refresh_button = ctk.CTkButton(
            title_frame, 
            text="Refresh", 
            command=self.controller.load_clients
        )
        refresh_button.pack(side="right", padx=10, pady=10)
        
        # Search frame
        search_frame = ctk.CTkFrame(self)
        search_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        search_label = ctk.CTkLabel(search_frame, text="Search:")
        search_label.pack(side="left", padx=10, pady=10)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self._filter_clients())
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, width=300)
        search_entry.pack(side="left", padx=10, pady=10)
        
        # Client list frame
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Treeview for clients
        # Create a frame for the treeview and scrollbar
        treeview_frame = ctk.CTkFrame(list_frame)
        treeview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Use a regular Treeview (ttk) as CustomTkinter doesn't have a Treeview widget
        self.tree = tk.ttk.Treeview(
            treeview_frame, 
            columns=("ID", "Name", "Company", "Email", "Phone", "City", "Status"),
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
        self.tree.heading("Name", text="Name")
        self.tree.heading("Company", text="Company")
        self.tree.heading("Email", text="Email")
        self.tree.heading("Phone", text="Phone")
        self.tree.heading("City", text="City")
        self.tree.heading("Status", text="Status")
        
        # Configure column widths and alignment
        self.tree.column("ID", width=50)
        self.tree.column("Name", width=150)
        self.tree.column("Company", width=150)
        self.tree.column("Email", width=200)
        self.tree.column("Phone", width=120)
        self.tree.column("City", width=120)
        self.tree.column("Status", width=80)
        
        # Bind select event
        self.tree.bind("<<TreeviewSelect>>", self._on_client_select)
        
        # Add scrollbar
        scrollbar = tk.ttk.Scrollbar(treeview_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Action buttons for the selected client
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        self.view_button = ctk.CTkButton(
            action_frame, 
            text="View Client", 
            state="disabled", 
            command=self._show_view_client_dialog
        )
        self.view_button.pack(side="left", padx=10, pady=10)
        
        self.edit_button = ctk.CTkButton(
            action_frame, 
            text="Edit Client", 
            state="disabled", 
            command=self._show_edit_client_dialog
        )
        self.edit_button.pack(side="left", padx=10, pady=10)
        
        self.delete_button = ctk.CTkButton(
            action_frame, 
            text="Delete Client", 
            state="disabled",
            fg_color="red",
            hover_color="darkred",
            command=self._confirm_delete_client
        )
        self.delete_button.pack(side="right", padx=10, pady=10)
        
        # Store clients data
        self.clients_data = []
        
    def display_clients(self, clients_data):
        """Display the list of clients in the treeview"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Store the full data for later use
        self.clients_data = clients_data
        
        # Add clients to the treeview
        for client in clients_data:
            status = "Active" if client['is_active'] else "Inactive"
            self.tree.insert(
                "", 
                "end", 
                values=(
                    client['id'],
                    client['name'],
                    client['company'] or "",
                    client['email'] or "",
                    client['phone'] or "",
                    client['city'] or "",
                    status
                )
            )
            
        # Reset selection
        self.selected_client_id = None
        self._update_action_buttons()
        
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
                search_text in (client['company'] or "").lower() or
                search_text in (client['email'] or "").lower() or
                search_text in (client['phone'] or "").lower() or
                search_text in (client['city'] or "").lower()):
                
                status = "Active" if client['is_active'] else "Inactive"
                self.tree.insert(
                    "", 
                    "end", 
                    values=(
                        client['id'],
                        client['name'],
                        client['company'] or "",
                        client['email'] or "",
                        client['phone'] or "",
                        client['city'] or "",
                        status
                    )
                )
                
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
        dialog = ClientDialog(self, "Add New Client")
        dialog.grab_set()  # Make it modal
        self.wait_window(dialog)  # Wait until the dialog is closed
        
        if dialog.result:
            # Process the form data
            success, result = self.controller.add_client(dialog.result)
            if success:
                self.show_info(f"Client added successfully with ID: {result}")
            else:
                self.show_error(f"Failed to add client: {result}")
                
    def _show_edit_client_dialog(self):
        """Show dialog to edit an existing client"""
        # Get the client data
        client_data = self.controller.get_client(self.selected_client_id)
        if not client_data:
            self.show_error("Failed to load client data")
            return
            
        dialog = ClientDialog(self, "Edit Client", client_data)
        dialog.grab_set()  # Make it modal
        self.wait_window(dialog)  # Wait until the dialog is closed
        
        if dialog.result:
            # Process the form data
            success, result = self.controller.update_client(self.selected_client_id, dialog.result)
            if success:
                self.show_info(f"Client updated successfully")
            else:
                self.show_error(f"Failed to update client: {result}")
                
    def _show_view_client_dialog(self):
        """Show dialog to view client details"""
        # Get the client data
        client_data = self.controller.get_client(self.selected_client_id)
        if not client_data:
            self.show_error("Failed to load client data")
            return
            
        dialog = ClientDialog(self, "View Client", client_data, readonly=True)
        dialog.grab_set()  # Make it modal
        dialog.wait_window()  # Wait until the dialog is closed
            
    def _confirm_delete_client(self):
        """Show confirmation dialog before deleting a client"""
        if not self.selected_client_id:
            return
            
        # Show confirmation dialog
        if messagebox.askyesno("Confirm Delete", 
                              "Are you sure you want to delete this client?\nThis action cannot be undone."):
            success, result = self.controller.delete_client(self.selected_client_id)
            if success:
                self.show_info("Client deleted successfully")
            else:
                self.show_error(f"Failed to delete client: {result}")
    
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
        self.geometry("600x550")
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
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Form title
        title_label = ctk.CTkLabel(
            container, 
            text=self.title(), 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Create form fields
        form = ctk.CTkFrame(container)
        form.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Two column layout for the form
        left_column = ctk.CTkFrame(form)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        right_column = ctk.CTkFrame(form)
        right_column.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Left column fields
        self._add_field(left_column, "Name", "name", 0, required=True)
        self._add_field(left_column, "Company", "company", 1)
        self._add_field(left_column, "Email", "email", 2)
        self._add_field(left_column, "Phone", "phone", 3)
        self._add_field(left_column, "Address", "address", 4, is_text=True)
        
        # Right column fields
        self._add_field(right_column, "City", "city", 0)
        self._add_field(right_column, "State/Province", "state", 1)
        self._add_field(right_column, "Postal Code", "postal_code", 2)
        self._add_field(right_column, "Country", "country", 3)
        
        # Status (Active/Inactive) - uses a checkbox
        status_frame = ctk.CTkFrame(right_column)
        status_frame.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        
        status_label = ctk.CTkLabel(status_frame, text="Status:")
        status_label.pack(side="left", padx=5, pady=5)
        
        self.is_active_var = ctk.BooleanVar(value=self.client_data.get('is_active', True))
        status_checkbox = ctk.CTkCheckBox(
            status_frame, 
            text="Active", 
            variable=self.is_active_var,
            state="disabled" if self.readonly else "normal"
        )
        status_checkbox.pack(side="left", padx=5, pady=5)
        
        # Notes field (full width)
        notes_frame = ctk.CTkFrame(container)
        notes_frame.pack(fill="x", padx=10, pady=10)
        
        notes_label = ctk.CTkLabel(notes_frame, text="Notes:")
        notes_label.pack(anchor="w", padx=10, pady=(10, 0))
        
        self.notes_text = ctk.CTkTextbox(notes_frame, height=100)
        self.notes_text.pack(fill="x", padx=10, pady=(0, 10))
        
        # Insert existing notes if any
        if self.client_data.get('notes'):
            self.notes_text.insert("1.0", self.client_data.get('notes'))
        
        if self.readonly:
            self.notes_text.configure(state="disabled")
        
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
        
    def _add_field(self, parent, label_text, field_name, row, required=False, is_text=False):
        """Helper method to add a form field"""
        frame = ctk.CTkFrame(parent)
        frame.grid(row=row, column=0, padx=10, pady=10, sticky="ew")
        
        label = ctk.CTkLabel(frame, text=f"{label_text}:{'*' if required else ''}")
        label.pack(anchor="w", padx=5, pady=(5, 0))
        
        if is_text:
            field = ctk.CTkTextbox(frame, height=50)
            field.pack(fill="x", padx=5, pady=(0, 5))
            
            # Insert existing value if any
            if self.client_data.get(field_name):
                field.insert("1.0", self.client_data.get(field_name))
                
            if self.readonly:
                field.configure(state="disabled")
                
            # Store the field
            setattr(self, f"{field_name}_field", field)
        else:
            field = ctk.CTkEntry(frame, width=200)
            field.pack(fill="x", padx=5, pady=(0, 5))
            
            # Insert existing value if any
            if self.client_data.get(field_name):
                field.insert(0, self.client_data.get(field_name))
                
            if self.readonly:
                field.configure(state="disabled")
                
            # Store the field
            setattr(self, f"{field_name}_field", field)
            
    def _save(self):
        """Save the form data"""
        # Validate required fields
        if not self.name_field.get().strip():
            messagebox.showerror("Validation Error", "Name is required.")
            return
        
        # Collect data from form fields
        self.result = {
            'name': self.name_field.get().strip(),
            'company': self.company_field.get().strip(),
            'email': self.email_field.get().strip(),
            'phone': self.phone_field.get().strip(),
            'address': self.address_field.get("1.0", "end-1c").strip(),
            'city': self.city_field.get().strip(),
            'state': self.state_field.get().strip(),
            'postal_code': self.postal_code_field.get().strip(),
            'country': self.country_field.get().strip(),
            'notes': self.notes_text.get("1.0", "end-1c").strip(),
            'is_active': self.is_active_var.get()
        }
        
        # Close the dialog
        self.destroy()
