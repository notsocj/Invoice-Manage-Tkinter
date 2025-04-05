from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.models.database import Base

class Invoice(Base):
    __tablename__ = 'invoices'
    
    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(20), unique=True)
    date = Column(String(20), nullable=False)
    customer_name = Column(String(100), nullable=False)
    customer_address = Column(Text)
    total_amount = Column(Float, default=0.0)
    mode_of_payment = Column(String(50))  # Added field to match database schema
    payment_status = Column(String(20), default='pending')  # Added with default value
    
    # Relationships
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', customer='{self.customer_name}')>"
    
    def calculate_total(self):
        """Calculate and update the invoice total based on line items"""
        self.total_amount = sum(item.price * item.quantity for item in self.items)
        return self.total_amount
    
    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'date': self.date,
            'customer_name': self.customer_name,
            'customer_address': self.customer_address,
            'total_amount': self.total_amount,
            'mode_of_payment': self.mode_of_payment,
            'payment_status': self.payment_status
        }

class InvoiceItem(Base):
    __tablename__ = 'invoice_items'
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    item_id = Column(Integer, nullable=False)
    description = Column(Text)
    quantity = Column(Integer, default=1)
    price = Column(Float, default=0.0)
    
    # Relationship
    invoice = relationship("Invoice", back_populates="items")
    
    def __repr__(self):
        return f"<InvoiceItem(id={self.id}, invoice_id={self.invoice_id}, description='{self.description}')>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'item_id': self.item_id,
            'description': self.description,
            'quantity': self.quantity,
            'price': self.price,
            'total': self.quantity * self.price
        }
