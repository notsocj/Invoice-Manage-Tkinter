from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.sql import func
from src.models.database import Base

class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    mobile = Column(String(20))  # Changed from 'phone' to 'mobile' to match requirements
    address = Column(Text)  # This field can be null
    
    # Keep other fields in DB for compatibility but they won't be primary focus in UI
    company = Column(String(100))
    email = Column(String(100))
    city = Column(String(50))
    state = Column(String(50))
    postal_code = Column(String(20))
    country = Column(String(50))
    payment_terms = Column(Integer, default=30)
    credit_limit = Column(Float, default=0.0)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.name}')>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'mobile': self.mobile,  # Changed from 'phone' to 'mobile'
            'address': self.address,
            # Include other fields for database compatibility
            'company': self.company,
            'email': self.email,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
            'payment_terms': self.payment_terms,
            'credit_limit': self.credit_limit,
            'notes': self.notes,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
