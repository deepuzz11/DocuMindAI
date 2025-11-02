from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TransactionBase(BaseModel):
    amount: float
    description: str
    date: datetime
    type: str  # 'income' or 'expense'
    category_id: Optional[int] = None

class TransactionCreate(TransactionBase):
    user_id: int

class Transaction(TransactionBase):
    id: int
    user_id: int
    created_at: datetime
    category_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    name: str
    icon: str
    type: str

class Category(CategoryBase):
    id: int
    
    class Config:
        from_attributes = True

class BudgetCreate(BaseModel):
    category_id: int
    limit: float
    period: str

class SpendingInsight(BaseModel):
    category: str
    amount: float
    percentage: float
    comparison: str  # "above/below average"