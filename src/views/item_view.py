import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import logging
from datetime import datetime

class ItemView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.logger = logging.getLogger('invoice_manager')
        self.pack(fill="both", expand=True)
        
        # Store currently selected item ID
        self.selected_item_id = None
        
        # Pagination settings
        self.current_page = 1
        self.per_page = 20
        self.total_pages = 1
        self.total_count = 0
        
        # Create UI elements
        self._create_widgets()
        
    def _create_widgets(self):
        """Create all UI elements for the item view"""
        # Title and button frame
        title_frame = ctk.CTkFrame(self)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text="Item Management", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left", padx=10, pady=10)
        
        add_button = ctk.CTkButton(
            title_frame, 
            text="Add New Item", 
            command=self._show_add_item_dialog,
            hover_color=("gray70", "gray30")
        )
        add_button.pack(side="right", padx=10, pady=10)
        
        refresh_button = ctk.CTkButton(
            title_frame, 
            text="Refresh", 
            command=self._refresh_items,
            hover_color=("gray70", "gray30")
        )
        refresh_button.pack(side="right", padx=10, pady=10)
        
        # Search and filter frame
        search_frame = ctk.CTkFrame(self)
        search_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        search_label = ctk.CTkLabel(search_frame, text="Search:")
        search_label.pack(side="left", padx=10, pady=10)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self._handle_search())
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, width=300)
        search_entry.pack(side="left", padx=10, pady=10)
        
        # Page size selector
        page_size_label = ctk.CTkLabel(search_frame, text="Items per page:")
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
        
        # Items list frame
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Treeview for items
        treeview_frame = ctk.CTkFrame(list_frame)
        treeview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Use a regular Treeview (ttk) as CustomTkinter doesn't have a Treeview widget
        self.tree = tk.ttk.Treeview(
            treeview_frame, 
            columns=("ID", "Item Code", "Name", "Price", "Date Added"),
            show="headings",
            selectmode="browse"
        )
        
        # Configure the treeview style to match CustomTkinter aesthetics
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
        self.tree.heading("Item Code", text="Item Code", command=lambda: self._sort_by_column("Item Code", False))
        self.tree.heading("Name", text="Name", command=lambda: self._sort_by_column("Name", False))
        self.tree.heading("Price", text="Price", command=lambda: self._sort_by_column("Price", False))
        self.tree.heading("Date Added", text="Date Added", command=lambda: self._sort_by_column("Date Added", False))
        
        # Configure column widths and alignment
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Item Code", width=100, anchor="center")
        self.tree.column("Name", width=300)
        self.tree.column("Price", width=100, anchor="e")
        self.tree.column("Date Added", width=150, anchor="center")
        
        # Bind select event
        self.tree.bind("<<TreeviewSelect>>", self._on_item_select)
        self.tree.bind("<Double-1>", self._on_item_double_click)
        
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
        
        # Action buttons for the selected item
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        self.view_button = ctk.CTkButton(
            action_frame, 
            text="View Item", 
            state="disabled", 
            command=self._show_view_item_dialog,
            hover_color=("gray70", "gray30")
        )
        self.view_button.pack(side="left", padx=10, pady=10)
        
        self.edit_button = ctk.CTkButton(
            action_frame, 
            text="Edit Item", 
            state="disabled", 
            command=self._show_edit_item_dialog,
            hover_color=("gray70", "gray30")
        )
        self.edit_button.pack(side="left", padx=10, pady=10)
        
        self.delete_button = ctk.CTkButton(
            action_frame, 
            text="Delete Item", 
            state="disabled",
            fg_color="red",
            hover_color="darkred",
            command=self._confirm_delete_item
        )
        self.delete_button.pack(side="right", padx=10, pady=10)
        
        # Store items data
        self.items_data = []
        self.sorted_column = None
        self.sort_ascending = True
        
    def display_items(self, items_data, pagination_info=None):
        """Display the list of items in the treeview"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Store the full data for later use
        self.items_data = items_data
        
        # Update pagination information
        if pagination_info:
            self.current_page = pagination_info['current_page']
            self.per_page = pagination_info['per_page']
            self.total_count = pagination_info['total_count']
            self.total_pages = pagination_info['total_pages']
            self._update_pagination_controls()
        
        # Add items to the treeview
        for item in items_data:
            # Format date
            date_added = item['date_added'].strftime('%Y-%m-%d') if item['date_added'] else ""
            
            # Format price with peso symbol
            price = f"₱{item['price']:.2f}"
            
            self.tree.insert(
                "", 
                "end", 
                values=(
                    item['id'],
                    item['item_code'],
                    item['name'],
                    price,
                    date_added
                )
            )
            
        # Reset selection
        self.selected_item_id = None
        self._update_action_buttons()
        
        # Update status message
        start_record = (self.current_page - 1) * self.per_page + 1 if self.items_data else 0
        end_record = start_record + len(self.items_data) - 1 if self.items_data else 0
        
        message = f"Showing {start_record} to {end_record} of {self.total_count} items"
        if self.search_var.get():
            message += f" (filtered by '{self.search_var.get()}')"
        
        self.logger.info(message)
        
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
            self.controller.load_items(
                page=self.current_page, 
                per_page=self.per_page,
                search_text=self.search_var.get()
            )
    
    def _next_page(self):
        """Go to the next page"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.controller.load_items(
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
                self.controller.load_items(
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
            self.controller.load_items(
                page=self.current_page, 
                per_page=self.per_page,
                search_text=self.search_var.get()
            )
        except ValueError:
            self.show_error("Invalid page size")
    
    def _handle_search(self):
        """Handle search input with debounce"""
        self.after_cancel(getattr(self, '_search_after_id', None))
        self._search_after_id = self.after(300, self._perform_search)
    
    def _perform_search(self):
        """Perform the actual search"""
        search_text = self.search_var.get()
        self.current_page = 1  # Reset to first page
        self.controller.load_items(
            page=self.current_page, 
            per_page=self.per_page,
            search_text=search_text
        )
    
    def _refresh_items(self):
        """Refresh the item list"""
        self.controller.load_items(
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
        
        # Special handling for price (remove ₱ sign for sorting)
        if column == "Price":
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
        
    def _on_item_select(self, event):
        """Handle item selection"""
        selected_items = self.tree.selection()
        if selected_items:
            item = selected_items[0]
            self.selected_item_id = int(self.tree.item(item, "values")[0])
            self._update_action_buttons()
        else:
            self.selected_item_id = None
            self._update_action_buttons()
    
    def _on_item_double_click(self, event):
        """Handle double-click on an item (view details)"""
        if self.selected_item_id:
            self._show_view_item_dialog()
            
    def _update_action_buttons(self):
        """Update the state of action buttons based on item selection"""
        if self.selected_item_id:
            self.view_button.configure(state="normal")
            self.edit_button.configure(state="normal")
            self.delete_button.configure(state="normal")
        else:
            self.view_button.configure(state="disabled")
            self.edit_button.configure(state="disabled")
            self.delete_button.configure(state="disabled")
            
    def _show_add_item_dialog(self):
        """Show dialog to add a new item"""
        # Generate a new item code
        item_code = self.controller.generate_item_code()
        item_data = {'item_code': item_code}
        
        dialog = ItemDialog(self, "Add New Item", item_data)
        dialog.grab_set()  # Make it modal
        self.wait_window(dialog)  # Wait until the dialog is closed
        
        if dialog.result:
            # Process the form data
            success, result = self.controller.add_item(dialog.result)
            if success:
                self.show_info(f"Item added successfully with code: {result}")
            else:
                self.show_error(f"Failed to add item: {result}")
                
    def _show_edit_item_dialog(self):
        """Show dialog to edit an existing item"""
        # Get the item data
        item_data = self.controller.get_item(self.selected_item_id)
        if not item_data:
            self.show_error("Failed to load item data")
            return
            
        dialog = ItemDialog(self, "Edit Item", item_data)
        dialog.grab_set()  # Make it modal
        self.wait_window(dialog)  # Wait until the dialog is closed
        
        if dialog.result:
            # Process the form data
            success, result = self.controller.update_item(self.selected_item_id, dialog.result)
            if success:
                self.show_info(f"Item updated successfully")
            else:
                self.show_error(f"Failed to update item: {result}")
                
    def _show_view_item_dialog(self):
        """Show dialog to view item details"""
        # Get the item data
        item_data = self.controller.get_item(self.selected_item_id)
        if not item_data:
            self.show_error("Failed to load item data")
            return
            
        dialog = ItemDialog(self, "View Item", item_data, readonly=True)
        dialog.grab_set()  # Make it modal
        dialog.wait_window()  # Wait until the dialog is closed
            
    def _confirm_delete_item(self):
        """Show confirmation dialog before deleting an item"""
        if not self.selected_item_id:
            return
            
        # Show confirmation dialog
        if messagebox.askyesno("Confirm Delete", 
                              "Are you sure you want to delete this item?\nThis action cannot be undone."):
            success, result = self.controller.delete_item(self.selected_item_id)
            if success:
                self.show_info("Item deleted successfully")
            else:
                self.show_error(f"Failed to delete item: {result}")
    
    def show_error(self, message):
        """Show error message"""
        messagebox.showerror("Error", message)
        
    def show_info(self, message):
        """Show info message"""
        messagebox.showinfo("Information", message)


class ItemDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, item_data=None, readonly=False):
        super().__init__(parent)
        self.title(title)
        self.geometry("500x350")
        self.resizable(False, False)
        
        # Set up variables
        self.item_data = item_data or {}
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
        """Create all UI elements for the item dialog"""
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
        
        # Item Code
        code_label = ctk.CTkLabel(form, text="Item Code:")
        code_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        self.item_code_var = ctk.StringVar(value=self.item_data.get('item_code', ''))
        item_code_entry = ctk.CTkEntry(form, textvariable=self.item_code_var, width=150)
        item_code_entry.grid(row=0, column=1, padx=10, pady=(10, 5), sticky="w")
        
        if self.readonly or 'item_code' in self.item_data:
            item_code_entry.configure(state="disabled")
        
        # Name (required)
        name_label = ctk.CTkLabel(form, text="Name:*")
        name_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.name_var = ctk.StringVar(value=self.item_data.get('name', ''))
        name_entry = ctk.CTkEntry(form, textvariable=self.name_var, width=300)
        name_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        
        if self.readonly:
            name_entry.configure(state="disabled")
        
        # Price
        price_label = ctk.CTkLabel(form, text="Price:*")
        price_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        
        # Create a price frame with a ₱ sign label and entry
        price_frame = ctk.CTkFrame(form)
        price_frame.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        
        peso_label = ctk.CTkLabel(price_frame, text="₱")
        peso_label.pack(side="left", padx=(0, 2))
        
        self.price_var = ctk.StringVar(value=f"{self.item_data.get('price', 0.0):.2f}")
        price_entry = ctk.CTkEntry(price_frame, textvariable=self.price_var, width=100)
        price_entry.pack(side="left")
        
        if self.readonly:
            price_entry.configure(state="disabled")
        
        # Date Added
        date_added_label = ctk.CTkLabel(form, text="Date Added:")
        date_added_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        
        date_added = self.item_data.get('date_added', datetime.now())
        date_str = date_added.strftime('%Y-%m-%d') if date_added else "Not specified"
        
        date_added_field = ctk.CTkLabel(form, text=date_str)
        date_added_field.grid(row=3, column=1, padx=10, pady=10, sticky="w")
        
        # Button frame
        button_frame = ctk.CTkFrame(container)
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
            'item_code': self.item_code_var.get().strip(),
            'name': self.name_var.get().strip(),
            'price': float(self.price_var.get()) if self.price_var.get() else 0.0
        }
        
        # If this is an edit, preserve the existing date_added
        if 'date_added' in self.item_data:
            self.result['date_added'] = self.item_data['date_added']
        
        # Close the dialog
        self.destroy()
    
    def _validate_form(self):
        """Validate form data"""
        errors = []
        
        # Validate required fields
        if not self.name_var.get().strip():
            errors.append("Item name is required")
        
        # Validate price
        try:
            price = float(self.price_var.get()) if self.price_var.get() else 0.0
            if price < 0:
                errors.append("Price cannot be negative")
        except ValueError:
            errors.append("Price must be a valid number")
        
        return errors
