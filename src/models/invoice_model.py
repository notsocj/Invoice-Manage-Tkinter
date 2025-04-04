from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from src.models.database import Base

class InvoiceStatus(enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    PARTIAL = "partial"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class Invoice(Base):
    __tablename__ = 'invoices'
    
    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(20), unique=True, nullable=False)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    issue_date = Column(DateTime, nullable=False, default=func.now())
    due_date = Column(DateTime)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT)
    subtotal = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    commission_rate = Column(Float, default=0.0)
    commission_amount = Column(Float, default=0.0)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", backref="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', client_id={self.client_id})>"
    
    def calculate_totals(self):
        """Calculate and update the invoice totals based on line items"""
        self.subtotal = sum(item.total for item in self.items)
        self.total_amount = self.subtotal + self.tax_amount - self.discount
        self.commission_amount = self.total_amount * self.commission_rate
        return self.total_amount
    
    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'client_id': self.client_id,
            'client_name': self.client.name if self.client else "",
            'issue_date': self.issue_date,
            'due_date': self.due_date,
            'status': self.status.value,
            'subtotal': self.subtotal,
            'tax_amount': self.tax_amount,
            'discount': self.discount,
            'total_amount': self.total_amount,
            'commission_rate': self.commission_rate,
            'commission_amount': self.commission_amount,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class InvoiceItem(Base):
    __tablename__ = 'invoice_items'
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    description = Column(String(200), nullable=False)
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    
    # Relationship
    invoice = relationship("Invoice", back_populates="items")
    
    def __repr__(self):
        return f"<InvoiceItem(id={self.id}, invoice_id={self.invoice_id})>"
    
    def calculate_total(self):
        """Calculate the total for this item"""
        self.total = self.quantity * self.unit_price
        return self.total
    
    def to_dict(self):
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'description': self.description,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total': self.total
        }
