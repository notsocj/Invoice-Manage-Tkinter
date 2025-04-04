from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from src.models.database import Base

class PaymentMethod(enum.Enum):
    CASH = "cash"
    CHECK = "check" 
    BANK_TRANSFER = "bank_transfer"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    OTHER = "other"

class Payment(Base):
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, nullable=False, default=func.now())
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.BANK_TRANSFER)
    reference_number = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationship
    invoice = relationship("Invoice", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, invoice_id={self.invoice_id}, amount={self.amount})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'invoice_number': self.invoice.invoice_number if self.invoice else "",
            'amount': self.amount,
            'payment_date': self.payment_date,
            'payment_method': self.payment_method.value,
            'reference_number': self.reference_number,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
