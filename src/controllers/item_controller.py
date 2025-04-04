import logging
import threading
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from src.models.item_model import Item
from src.views.item_view import ItemView

class ItemController:
    def __init__(self, db, main_view):
        self.db = db
        self.main_view = main_view
        self.view = None
        self.logger = logging.getLogger('invoice_manager')
    
    def load_view(self, parent_frame):
        """Load the item view into the parent frame"""
        self.view = ItemView(parent_frame, self)
        self.load_items()
    
    def load_items(self, page=1, per_page=20, search_text=""):
        """Load items from the database with pagination support"""
        self.logger.info(f"Loading items page {page}, per_page {per_page}, search '{search_text}'")
        
        # Use a separate thread for database operations
        def fetch_items():
            try:
                session = self.db.get_session()
                
                # Base query
                query = session.query(Item)
                
                # Apply search filter if provided
                if search_text:
                    search_text_like = f"%{search_text}%"
                    query = query.filter(
                        (Item.item_code.ilike(search_text_like)) |
                        (Item.name.ilike(search_text_like))
                    )
                
                # Get total count for pagination
                total_count = query.count()
                
                # Apply pagination
                query = query.order_by(Item.date_added.desc())
                query = query.limit(per_page).offset((page - 1) * per_page)
                
                # Execute query
                items = query.all()
                items_data = [item.to_dict() for item in items]
                
                session.close()
                
                # Update UI in the main thread
                pagination_info = {
                    'current_page': page,
                    'per_page': per_page,
                    'total_count': total_count,
                    'total_pages': (total_count + per_page - 1) // per_page  # Ceiling division
                }
                
                self.view.after(0, lambda: self.view.display_items(items_data, pagination_info))
                
            except SQLAlchemyError as e:
                self.logger.error(f"Error fetching items: {str(e)}")
                self.view.after(0, lambda: self.view.show_error("Failed to load items"))
        
        thread = threading.Thread(target=fetch_items)
        thread.daemon = True
        thread.start()
    
    def generate_item_code(self):
        """Generate a unique item code with TKW prefix"""
        try:
            session = self.db.get_session()
            # Get the highest item code
            last_item = session.query(Item).order_by(Item.id.desc()).first()
            session.close()
            
            if last_item and last_item.item_code.startswith('TKW-'):
                # Extract the number part
                try:
                    last_num = int(last_item.item_code.split('-')[1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
                
            # Format: TKW-XXX (e.g., TKW-001)
            item_code = f"TKW-{new_num:03d}"
            
            return item_code
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error generating item code: {str(e)}")
            # Fallback item code
            return f"TKW-{datetime.now().strftime('%H%M%S')}"
    
    def add_item(self, item_data):
        """Add a new item to the database"""
        self.logger.info(f"Adding new item: {item_data['name']}")
        
        # Validate item data before saving
        validation_result = self._validate_item_data(item_data)
        if not validation_result[0]:
            return validation_result
            
        # Generate a unique item code if not provided
        if not item_data.get('item_code'):
            item_data['item_code'] = self.generate_item_code()
        
        try:
            session = self.db.get_session()
            new_item = Item(**item_data)
            session.add(new_item)
            session.commit()
            session.refresh(new_item)
            item_id = new_item.id
            item_code = new_item.item_code
            session.close()
            
            self.logger.info(f"Item added successfully with ID: {item_id}, Code: {item_code}")
            self.load_items(page=self.view.current_page, per_page=self.view.per_page, search_text=self.view.search_var.get())
            return True, item_code
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error adding item: {str(e)}")
            return False, str(e)
    
    def update_item(self, item_id, item_data):
        """Update an existing item"""
        self.logger.info(f"Updating item with ID: {item_id}")
        
        # Validate item data before saving
        validation_result = self._validate_item_data(item_data)
        if not validation_result[0]:
            return validation_result
        
        try:
            session = self.db.get_session()
            item = session.query(Item).filter(Item.id == item_id).first()
            
            if not item:
                session.close()
                self.logger.warning(f"Item with ID {item_id} not found")
                return False, "Item not found"
            
            # Update item attributes
            for key, value in item_data.items():
                setattr(item, key, value)
            
            session.commit()
            session.close()
            
            self.logger.info(f"Item updated successfully: {item_id}")
            self.load_items(page=self.view.current_page, per_page=self.view.per_page, search_text=self.view.search_var.get())
            return True, item_id
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating item: {str(e)}")
            return False, str(e)
    
    def delete_item(self, item_id):
        """Delete an item from the database"""
        self.logger.info(f"Deleting item with ID: {item_id}")
        
        try:
            session = self.db.get_session()
            item = session.query(Item).filter(Item.id == item_id).first()
            
            if not item:
                session.close()
                self.logger.warning(f"Item with ID {item_id} not found")
                return False, "Item not found"
            
            session.delete(item)
            session.commit()
            session.close()
            
            self.logger.info(f"Item deleted successfully: {item_id}")
            self.load_items(page=self.view.current_page, per_page=self.view.per_page, search_text=self.view.search_var.get())
            return True, None
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error deleting item: {str(e)}")
            return False, str(e)
    
    def get_item(self, item_id):
        """Get a specific item by ID"""
        try:
            session = self.db.get_session()
            item = session.query(Item).filter(Item.id == item_id).first()
            
            if not item:
                session.close()
                return None
            
            item_data = item.to_dict()
            session.close()
            return item_data
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching item: {str(e)}")
            return None
    
    def _validate_item_data(self, item_data):
        """Validate item data before saving to database"""
        errors = []
        
        # Check required fields
        if not item_data.get('name', '').strip():
            errors.append("Item name is required")
        
        # Validate price if provided
        try:
            price = float(item_data.get('price', 0))
            if price < 0:
                errors.append("Price cannot be negative")
        except (ValueError, TypeError):
            errors.append("Price must be a valid number")
        
        if errors:
            return False, "\n".join(errors)
        
        return True, None
