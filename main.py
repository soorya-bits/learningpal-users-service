from fastapi import FastAPI, HTTPException, Depends, Header, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from passlib.hash import bcrypt
from jose import jwt, JWTError
from pydantic import BaseModel
from datetime import datetime, timedelta
from database import SessionLocal, engine, get_db
from models import Base, User
from starlette.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI(
    title="LibraryPal User Service",
    description="API for user registration and authentication",
    version="1.0.0"
)
security = HTTPBearer()

# Add CORSMiddleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Pydantic Schemas
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

# JWT Secret Key
SECRET_KEY = "bookstore123"
ALGORITHM = "HS256"

# Healthcheck
@app.get("/health", tags=["Health"])
def healthcheck():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except SQLAlchemyError as e:
        return {"status": "error", "db": "unreachable", "detail": str(e)}
    finally:
        db.close()

# Verify JWT Token
def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # you can inspect or use this if needed
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Sign-up User
@app.post("/signup", tags=["Users"])
def signup(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username or email already exists
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    # Hash password and create user
    hashed_password = bcrypt.hash(user.password)
    new_user = User(username=user.username, email=user.email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Sign-up successful"}

# Login User
@app.post("/login", tags=["Users"])
def login(user: UserLogin, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user.username).first()
    if not existing_user or not bcrypt.verify(user.password, existing_user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Generate JWT token
    token_data = {"sub": existing_user.username, "exp": datetime.utcnow() + timedelta(days=30)}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    return {"id": existing_user.id, "token": token}

# Get User Info Route
@app.get("/get-user-info", tags=["Users"])
def get_user_info(
    id: int = Header(...), 
    db: Session = Depends(get_db),
    _: dict = Depends(verify_jwt_token)  # token must be valid to reach here
):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "username": user.username, "email": user.email}


# Get All Users Route
@app.get("/users", tags=["Users"])
def get_all_users(
    db: Session = Depends(get_db),
    _: dict = Depends(verify_jwt_token)  # Require valid JWT
):
    users = db.query(User).all()
    return [
        {"id": user.id, "username": user.username, "email": user.email}
        for user in users
    ]

# Token Verification for External Services
@app.get("/verify-token", tags=["Auth"])
def verify_token_endpoint(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "valid": True,
            "username": payload.get("sub"),
            "expires": payload.get("exp")
        }
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
