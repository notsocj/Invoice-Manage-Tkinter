import logging
import threading
from sqlalchemy.exc import SQLAlchemyError
from src.models.client_model import Client
from src.views.client_view import ClientView

class ClientController:
    def __init__(self, db, main_view):
        self.db = db
        self.main_view = main_view
        self.view = None
        self.logger = logging.getLogger('invoice_manager')
    
    def load_view(self, parent_frame):
        """Load the client view into the parent frame"""
        self.view = ClientView(parent_frame, self)
        self.load_clients()
    
    def load_clients(self, page=1, per_page=20, search_text=""):
        """Load clients from the database with pagination support"""
        self.logger.info(f"Loading clients page {page}, per_page {per_page}, search '{search_text}'")
        
        # Use a separate thread for database operations
        def fetch_clients():
            try:
                session = self.db.get_session()
                
                # Base query
                query = session.query(Client)
                
                # Apply search filter if provided
                if search_text:
                    search_text_like = f"%{search_text}%"
                    query = query.filter(
                        (Client.name.ilike(search_text_like)) |
                        (Client.company.ilike(search_text_like)) |
                        (Client.email.ilike(search_text_like)) |
                        (Client.phone.ilike(search_text_like)) |
                        (Client.city.ilike(search_text_like))
                    )
                
                # Get total count for pagination
                total_count = query.count()
                
                # Apply pagination
                query = query.order_by(Client.name)
                query = query.limit(per_page).offset((page - 1) * per_page)
                
                # Execute query
                clients = query.all()
                clients_data = [client.to_dict() for client in clients]
                
                session.close()
                
                # Update UI in the main thread
                pagination_info = {
                    'current_page': page,
                    'per_page': per_page,
                    'total_count': total_count,
                    'total_pages': (total_count + per_page - 1) // per_page  # Ceiling division
                }
                
                self.view.after(0, lambda: self.view.display_clients(clients_data, pagination_info))
                
            except SQLAlchemyError as e:
                self.logger.error(f"Error fetching clients: {str(e)}")
                self.view.after(0, lambda: self.view.show_error("Failed to load clients"))
        
        thread = threading.Thread(target=fetch_clients)
        thread.daemon = True
        thread.start()
    
    def add_client(self, client_data):
        """Add a new client to the database"""
        self.logger.info(f"Adding new client: {client_data['name']}")
        
        # Validate client data before saving
        validation_result = self._validate_client_data(client_data)
        if not validation_result[0]:
            return validation_result
        
        try:
            session = self.db.get_session()
            new_client = Client(**client_data)
            session.add(new_client)
            session.commit()
            session.refresh(new_client)
            client_id = new_client.id
            session.close()
            
            self.logger.info(f"Client added successfully with ID: {client_id}")
            self.load_clients(page=self.view.current_page, per_page=self.view.per_page, search_text=self.view.search_var.get())
            return True, client_id
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error adding client: {str(e)}")
            return False, str(e)
    
    def update_client(self, client_id, client_data):
        """Update an existing client"""
        self.logger.info(f"Updating client with ID: {client_id}")
        
        # Validate client data before saving
        validation_result = self._validate_client_data(client_data)
        if not validation_result[0]:
            return validation_result
        
        try:
            session = self.db.get_session()
            client = session.query(Client).filter(Client.id == client_id).first()
            
            if not client:
                session.close()
                self.logger.warning(f"Client with ID {client_id} not found")
                return False, "Client not found"
            
            # Update client attributes
            for key, value in client_data.items():
                setattr(client, key, value)
            
            session.commit()
            session.close()
            
            self.logger.info(f"Client updated successfully: {client_id}")
            self.load_clients(page=self.view.current_page, per_page=self.view.per_page, search_text=self.view.search_var.get())
            return True, client_id
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error updating client: {str(e)}")
            return False, str(e)
    
    def delete_client(self, client_id):
        """Delete a client from the database"""
        self.logger.info(f"Deleting client with ID: {client_id}")
        
        try:
            session = self.db.get_session()
            client = session.query(Client).filter(Client.id == client_id).first()
            
            if not client:
                session.close()
                self.logger.warning(f"Client with ID {client_id} not found")
                return False, "Client not found"
            
            session.delete(client)
            session.commit()
            session.close()
            
            self.logger.info(f"Client deleted successfully: {client_id}")
            self.load_clients(page=self.view.current_page, per_page=self.view.per_page, search_text=self.view.search_var.get())
            return True, None
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error deleting client: {str(e)}")
            return False, str(e)
    
    def get_client(self, client_id):
        """Get a specific client by ID"""
        try:
            session = self.db.get_session()
            client = session.query(Client).filter(Client.id == client_id).first()
            
            if not client:
                session.close()
                return None
            
            client_data = client.to_dict()
            session.close()
            return client_data
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error fetching client: {str(e)}")
            return None
    
    def _validate_client_data(self, client_data):
        """Validate client data before saving to database"""
        errors = []
        
        # Check required fields
        if not client_data.get('name', '').strip():
            errors.append("Name is required")
        
        # Validate mobile number if provided
        mobile = client_data.get('mobile', '').strip()  # Changed from 'phone' to 'mobile'
        if mobile and not self._is_valid_phone(mobile):
            errors.append("Invalid mobile number format")
        
        if errors:
            return False, "\n".join(errors)
        
        return True, None
    
    def _is_valid_email(self, email):
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_valid_phone(self, phone):
        """Validate phone number format (basic validation)"""
        import re
        # Allow digits, spaces, dashes, plus, and parentheses
        pattern = r'^[0-9\s\(\)\-\+]{7,20}$'
        return re.match(pattern, phone) is not None
