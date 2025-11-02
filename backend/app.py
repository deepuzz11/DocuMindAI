from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

import models
import schemas
from database import engine, get_db
from categorizer import categorizer

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SmartBudget API")

# CORS - Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize default categories
@app.on_event("startup")
def startup_event():
    db = next(get_db())
    
    # Add default categories if none exist
    if db.query(models.Category).count() == 0:
        default_categories = [
            {"name": "Food & Dining", "icon": "🍔", "type": "expense"},
            {"name": "Transportation", "icon": "🚗", "type": "expense"},
            {"name": "Shopping", "icon": "🛍️", "type": "expense"},
            {"name": "Bills & Utilities", "icon": "📄", "type": "expense"},
            {"name": "Entertainment", "icon": "🎬", "type": "expense"},
            {"name": "Healthcare", "icon": "🏥", "type": "expense"},
            {"name": "Salary", "icon": "💰", "type": "income"},
            {"name": "Other Income", "icon": "💵", "type": "income"},
        ]
        
        for cat in default_categories:
            db.add(models.Category(**cat))
        db.commit()
    
    # Create default user if none exist
    if db.query(models.User).count() == 0:
        default_user = models.User(email="user@example.com", name="Demo User")
        db.add(default_user)
        db.commit()

# ============ ROUTES ============

@app.get("/")
def root():
    return {"message": "SmartBudget API is running!"}

# Categories
@app.get("/api/categories", response_model=List[schemas.Category])
def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()

# Transactions
@app.get("/api/transactions", response_model=List[schemas.Transaction])
def get_transactions(
    user_id: int = 1,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    transactions = db.query(models.Transaction)\
        .filter(models.Transaction.user_id == user_id)\
        .order_by(models.Transaction.date.desc())\
        .offset(skip).limit(limit).all()
    
    # Add category name to response
    result = []
    for t in transactions:
        t_dict = {
            "id": t.id,
            "user_id": t.user_id,
            "amount": t.amount,
            "description": t.description,
            "date": t.date,
            "type": t.type,
            "created_at": t.created_at,
            "category_id": t.category_id,
            "category_name": t.category.name if t.category else None
        }
        result.append(t_dict)
    
    return result

@app.post("/api/transactions", response_model=schemas.Transaction)
def create_transaction(
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db)
):
    # Auto-categorize if category not provided
    if not transaction.category_id:
        prediction = categorizer.predict(transaction.description)
        category = db.query(models.Category)\
            .filter(models.Category.name == prediction['category'])\
            .first()
        if category:
            transaction.category_id = category.id
    
    db_transaction = models.Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@app.put("/api/transactions/{transaction_id}")
def update_transaction(
    transaction_id: int,
    amount: float = None,
    description: str = None,
    category_id: int = None,
    db: Session = Depends(get_db)
):
    transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if amount: transaction.amount = amount
    if description: transaction.description = description
    if category_id: transaction.category_id = category_id
    
    db.commit()
    return {"message": "Updated successfully"}

@app.delete("/api/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    db.delete(transaction)
    db.commit()
    return {"message": "Deleted successfully"}

# Auto-categorize endpoint
@app.post("/api/categorize")
def categorize_description(description: str):
    return categorizer.predict(description)

# Analytics
@app.get("/api/analytics/spending-by-category")
def get_spending_by_category(
    user_id: int = 1,
    days: int = 30,
    db: Session = Depends(get_db)
):
    start_date = datetime.now() - timedelta(days=days)
    
    transactions = db.query(models.Transaction)\
        .filter(
            models.Transaction.user_id == user_id,
            models.Transaction.type == 'expense',
            models.Transaction.date >= start_date
        ).all()
    
    spending = {}
    total = 0
    
    for t in transactions:
        category_name = t.category.name if t.category else 'Other'
        spending[category_name] = spending.get(category_name, 0) + t.amount
        total += t.amount
    
    # Calculate percentages
    result = [
        {
            "category": cat,
            "amount": amount,
            "percentage": round((amount / total * 100) if total > 0 else 0, 2)
        }
        for cat, amount in spending.items()
    ]
    
    return {"data": result, "total": total}

@app.get("/api/analytics/monthly-trend")
def get_monthly_trend(
    user_id: int = 1,
    months: int = 6,
    db: Session = Depends(get_db)
):
    # Get transactions for last N months
    monthly_data = []
    
    for i in range(months - 1, -1, -1):
        month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        
        transactions = db.query(models.Transaction)\
            .filter(
                models.Transaction.user_id == user_id,
                models.Transaction.date >= month_start,
                models.Transaction.date < month_end
            ).all()
        
        income = sum(t.amount for t in transactions if t.type == 'income')
        expense = sum(t.amount for t in transactions if t.type == 'expense')
        
        monthly_data.append({
            "month": month_start.strftime("%b %Y"),
            "income": income,
            "expense": expense,
            "savings": income - expense
        })
    
    return monthly_data

# Run with: uvicorn app:app --reload