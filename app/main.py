"""
Main FastAPI application with user management endpoints.
"""
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from app.database import get_db, engine, Base
from app.models import User, Calculation
from app.schemas import (
    UserCreate, UserRead, UserUpdate, UserLogin,
    CalculationCreate, CalculationRead, CalculationUpdate, OperationType
)
from app.security import hash_password, verify_password

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Secure FastAPI Application",
    description="User management with secure password hashing and database integration",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Application is running"}

# --- User Endpoints ---

@app.post("/users/register", response_model=UserRead, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    """
    Register a new user.
    
    - **username**: Unique username (3-50 characters)
    - **email**: Valid, unique email address
    - **password**: Password (minimum 8 characters)
    
    Returns the created user without password_hash.
    """
    try:
        # Hash the password before storing
        password_hash = hash_password(user_data.password)
        
        # Create new user instance
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash
        )
        
        # Add to database
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    except IntegrityError as e:
        db.rollback()
        if "username" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists"
            )
        elif "email" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User creation failed due to data conflict"
        )

@app.post("/users/login", tags=["Users"])
async def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Login a user.
    
    Verifies username and password.
    """
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    return {"message": "Login successful", "user_id": str(user.id)}

@app.get("/users/{user_id}", response_model=UserRead, tags=["Users"])
async def get_user(user_id: str, db: Session = Depends(get_db)) -> UserRead:
    """Get a user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@app.get("/users", response_model=List[UserRead], tags=["Users"])
async def list_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)) -> List[UserRead]:
    """
    List all users with pagination.
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@app.put("/users/{user_id}", response_model=UserRead, tags=["Users"])
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
) -> UserRead:
    """Update user information (username or email)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        if user_data.username is not None:
            user.username = user_data.username
        if user_data.email is not None:
            user.email = user_data.email
        
        db.commit()
        db.refresh(user)
        return user
    
    except IntegrityError as e:
        db.rollback()
        if "username" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists"
            )
        elif "email" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Update failed due to data conflict"
        )


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"])
async def delete_user(user_id: str, db: Session = Depends(get_db)):
    """Delete a user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()

# --- Calculation Endpoints ---

def perform_calculation(a: float, b: float, op: OperationType) -> float:
    if op == OperationType.ADD:
        return a + b
    elif op == OperationType.SUBTRACT:
        return a - b
    elif op == OperationType.MULTIPLY:
        return a * b
    elif op == OperationType.DIVIDE:
        if b == 0:
            raise ValueError("Division by zero")
        return a / b
    raise ValueError("Invalid operation")

@app.post("/calculations", response_model=CalculationRead, status_code=status.HTTP_201_CREATED, tags=["Calculations"])
async def create_calculation(calc_data: CalculationCreate, db: Session = Depends(get_db)) -> CalculationRead:
    """Create a new calculation."""
    try:
        result = perform_calculation(calc_data.a, calc_data.b, calc_data.type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    db_calc = Calculation(
        a=calc_data.a,
        b=calc_data.b,
        type=calc_data.type,
        result=result,
        user_id=calc_data.user_id
    )
    db.add(db_calc)
    db.commit()
    db.refresh(db_calc)
    return db_calc

@app.get("/calculations", response_model=List[CalculationRead], tags=["Calculations"])
async def list_calculations(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)) -> List[CalculationRead]:
    """List all calculations."""
    calcs = db.query(Calculation).offset(skip).limit(limit).all()
    return calcs

@app.get("/calculations/{calc_id}", response_model=CalculationRead, tags=["Calculations"])
async def get_calculation(calc_id: str, db: Session = Depends(get_db)) -> CalculationRead:
    """Get a calculation by ID."""
    calc = db.query(Calculation).filter(Calculation.id == calc_id).first()
    if not calc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calculation not found")
    return calc

@app.put("/calculations/{calc_id}", response_model=CalculationRead, tags=["Calculations"])
async def update_calculation(calc_id: str, calc_data: CalculationUpdate, db: Session = Depends(get_db)) -> CalculationRead:
    """Update a calculation."""
    calc = db.query(Calculation).filter(Calculation.id == calc_id).first()
    if not calc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calculation not found")

    # Update fields if provided
    if calc_data.a is not None:
        calc.a = calc_data.a
    if calc_data.b is not None:
        calc.b = calc_data.b
    if calc_data.type is not None:
        calc.type = calc_data.type

    # Recompute result
    try:
        # Use new values if provided, else existing
        a = calc.a
        b = calc.b
        op = OperationType(calc.type) # Ensure it's the enum
        
        if op == OperationType.DIVIDE and b == 0:
             raise ValueError("Division by zero")

        calc.result = perform_calculation(a, b, op)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    db.commit()
    db.refresh(calc)
    return calc

@app.delete("/calculations/{calc_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Calculations"])
async def delete_calculation(calc_id: str, db: Session = Depends(get_db)):
    """Delete a calculation."""
    calc = db.query(Calculation).filter(Calculation.id == calc_id).first()
    if not calc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calculation not found")
    
    db.delete(calc)
    db.commit()
