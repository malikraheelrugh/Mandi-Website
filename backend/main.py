from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .auth import create_access_token, get_current_user, get_password_hash, require_role, verify_password
from .database import Base, engine, get_db
from .models import AuditLog, Sale, SaleItem, Stock, User
from .schemas import (
    LoginRequest,
    SaleCreate,
    SaleOut,
    StockCreate,
    StockOut,
    StockUpdate,
    TokenResponse,
    UserCreate,
    UserOut,
)

app = FastAPI(title="Mandi Broker Management System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


def log_action(db: Session, user_id: int, action: str):
    db.add(AuditLog(user_id=user_id, action=action))


def bootstrap_admin(db: Session):
    if db.query(User).count() == 0:
        db.add(
            User(
                name="System Admin",
                email="admin@mandi.local",
                password=get_password_hash("admin123"),
                role="admin",
            )
        )
        db.commit()


@app.on_event("startup")
def init_data():
    db = next(get_db())
    bootstrap_admin(db)


@app.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token)


@app.get("/users", response_model=list[UserOut])
def get_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    return db.query(User).all()


@app.post("/users", response_model=UserOut)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    if payload.role not in {"buyer", "clerk", "admin"}:
        raise HTTPException(status_code=400, detail="Invalid role")
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already exists")

    user = User(
        name=payload.name,
        email=payload.email,
        password=get_password_hash(payload.password),
        role=payload.role,
    )
    db.add(user)
    log_action(db, current_user.id, f"Created user {payload.email}")
    db.commit()
    db.refresh(user)
    return user


@app.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    log_action(db, current_user.id, f"Deleted user {user.email}")
    db.commit()
    return {"message": "User deleted"}


@app.get("/stock", response_model=list[StockOut])
def get_stock(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin", "clerk", "buyer")),
):
    return db.query(Stock).all()


@app.post("/stock", response_model=StockOut)
def create_stock(
    payload: StockCreate,
    db: Session = Depends(get_db),
    clerk: User = Depends(require_role("clerk", "admin")),
):
    if payload.quantity < 0 or payload.price_per_unit < 0:
        raise HTTPException(status_code=400, detail="Quantity and price must be positive")
    stock = Stock(
        item_name=payload.item_name,
        quantity=payload.quantity,
        price_per_unit=payload.price_per_unit,
        added_by=clerk.id,
    )
    db.add(stock)
    log_action(db, clerk.id, f"Added stock {payload.item_name}")
    db.commit()
    db.refresh(stock)
    return stock


@app.put("/stock/{stock_id}", response_model=StockOut)
def update_stock(
    stock_id: int,
    payload: StockUpdate,
    db: Session = Depends(get_db),
    clerk: User = Depends(require_role("clerk", "admin")),
):
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    if payload.quantity < 0:
        raise HTTPException(status_code=400, detail="Stock cannot be negative")

    stock.item_name = payload.item_name
    stock.quantity = payload.quantity
    stock.price_per_unit = payload.price_per_unit
    log_action(db, clerk.id, f"Updated stock {stock.id}")
    db.commit()
    db.refresh(stock)
    return stock


@app.delete("/stock/{stock_id}")
def delete_stock(
    stock_id: int,
    db: Session = Depends(get_db),
    clerk: User = Depends(require_role("clerk", "admin")),
):
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    db.delete(stock)
    log_action(db, clerk.id, f"Deleted stock {stock.id}")
    db.commit()
    return {"message": "Stock deleted"}


@app.post("/sales", response_model=SaleOut)
def create_sale(
    payload: SaleCreate,
    db: Session = Depends(get_db),
    clerk: User = Depends(require_role("clerk", "admin")),
):
    buyer = db.query(User).filter(User.id == payload.buyer_id, User.role == "buyer").first()
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")

    sale = Sale(buyer_id=payload.buyer_id, sold_by=clerk.id, total_amount=0)
    total = 0.0

    for line in payload.items:
        stock = db.query(Stock).filter(Stock.id == line.stock_id).first()
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock {line.stock_id} not found")
        if line.quantity <= 0 or stock.quantity < line.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {stock.item_name}")

        stock.quantity -= line.quantity
        line_total = line.quantity * stock.price_per_unit
        total += line_total
        sale.items.append(
            SaleItem(item_name=stock.item_name, quantity=line.quantity, price=stock.price_per_unit)
        )

    sale.total_amount = total
    db.add(sale)
    log_action(db, clerk.id, f"Created sale for buyer {payload.buyer_id}")
    db.commit()
    db.refresh(sale)
    return sale


@app.get("/sales", response_model=list[SaleOut])
def get_sales(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "clerk", "buyer")),
):
    query = db.query(Sale)
    if current_user.role == "buyer":
        query = query.filter(Sale.buyer_id == current_user.id)
    elif current_user.role == "clerk":
        query = query.filter(Sale.sold_by == current_user.id)
    return query.order_by(Sale.created_at.desc()).all()


@app.get("/sales/buyer/{buyer_id}", response_model=list[SaleOut])
def get_buyer_sales(
    buyer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "buyer")),
):
    if current_user.role == "buyer" and current_user.id != buyer_id:
        raise HTTPException(status_code=403, detail="Cannot view other buyer data")
    return db.query(Sale).filter(Sale.buyer_id == buyer_id).order_by(Sale.created_at.desc()).all()


@app.get("/dashboard/admin")
def admin_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    total_sales = db.query(Sale).count()
    total_stock = sum([row.quantity for row in db.query(Stock).all()])
    revenue = sum([row.total_amount for row in db.query(Sale).all()])
    return {
        "total_sales": total_sales,
        "total_stock": total_stock,
        "revenue": revenue,
        "transactions": db.query(Sale).order_by(Sale.created_at.desc()).all(),
    }


@app.get("/reports/{period}")
def reports(
    period: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    now = datetime.utcnow()
    if period == "daily":
        start = now - timedelta(days=1)
    elif period == "weekly":
        start = now - timedelta(weeks=1)
    elif period == "monthly":
        start = now - timedelta(days=30)
    else:
        raise HTTPException(status_code=400, detail="Period must be daily/weekly/monthly")

    sales = db.query(Sale).filter(Sale.created_at >= start).all()
    return {
        "period": period,
        "from": start,
        "to": now,
        "total_transactions": len(sales),
        "total_amount": sum([s.total_amount for s in sales]),
    }


@app.get("/audit-logs")
def audit_logs(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).all()
