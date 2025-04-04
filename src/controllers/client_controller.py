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
    
    def load_clients(self):
        """Load all clients from the database"""
        self.logger.info("Loading clients")
        
        # Use a separate thread for database operations
        def fetch_clients():
            try:
                session = self.db.get_session()
                clients = session.query(Client).order_by(Client.name).all()
                clients_data = [client.to_dict() for client in clients]
                session.close()
                
                # Update UI in the main thread
                self.view.after(0, lambda: self.view.display_clients(clients_data))
                
            except SQLAlchemyError as e:
                self.logger.error(f"Error fetching clients: {str(e)}")
                self.view.after(0, lambda: self.view.show_error("Failed to load clients"))
        
        thread = threading.Thread(target=fetch_clients)
        thread.daemon = True
        thread.start()
    
    def add_client(self, client_data):
        """Add a new client to the database"""
        self.logger.info(f"Adding new client: {client_data['name']}")
        
        try:
            session = self.db.get_session()
            new_client = Client(**client_data)
            session.add(new_client)
            session.commit()
            session.refresh(new_client)
            client_id = new_client.id
            session.close()
            
            self.logger.info(f"Client added successfully with ID: {client_id}")
            self.load_clients()
            return True, client_id
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error adding client: {str(e)}")
            return False, str(e)
    
    def update_client(self, client_id, client_data):
        """Update an existing client"""
        self.logger.info(f"Updating client with ID: {client_id}")
        
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
            self.load_clients()
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
            self.load_clients()
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
