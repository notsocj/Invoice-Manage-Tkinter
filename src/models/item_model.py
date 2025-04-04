from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from src.models.database import Base

class Item(Base):
    __tablename__ = 'items'
    
    id = Column(Integer, primary_key=True)
    item_code = Column(String(20), unique=True, nullable=False)  # TKW-001 format
    name = Column(String(100), nullable=False)
    price = Column(Float, default=0.0)
    date_added = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Item(id={self.id}, code='{self.item_code}', name='{self.name}')>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_code': self.item_code,
            'name': self.name,
            'price': self.price,
            'date_added': self.date_added,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
