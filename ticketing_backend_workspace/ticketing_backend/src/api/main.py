from fastapi import FastAPI, Depends, HTTPException, APIRouter, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional
from jose import JWTError, jwt
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .models import Base, User, Ticket, UserRole
from .schemas import (
    UserCreate, UserRead,
    TicketCreate, TicketRead, TicketUpdate,
)

# === CONFIGURATION ===

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

SECRET_KEY = "dev_secret_should_be_env_var"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = FastAPI(
    title="Ticketing Backend API",
    description=(
        "API endpoints for managing users and tickets in "
        "multi-container ticketing system."
    ),
    version="1.0.0",
    openapi_tags=[
        {"name": "users", "description": "User account management"},
        {"name": "tickets", "description": "Ticket CRUD and status management"},
        {"name": "auth", "description": "User authentication"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def fake_hash_password(password: str) -> str:
    """Simulate password hashing for MVP."""
    return "fakehashed_" + password


def verify_password(plain: str, hashed: str) -> bool:
    return fake_hash_password(plain) == hashed


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Generate JWT access token for authenticated user."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


# ===================
#   Auth helpers
# ===================


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Get current active user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    return user


def require_role(
    allowed_roles: List[UserRole]
):
    def role_dependency(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return role_dependency


# ================
# User Endpoints
# ================

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.post(
    "/", response_model=UserRead, status_code=201,
    summary="Create user", description="Register a new user account."
)
# PUBLIC_INTERFACE
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Creates a new user account with the specified role."""
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(
            status_code=409, detail="Username already registered."
        )
    db_user = User(
        username=user.username,
        hashed_password=fake_hash_password(user.password),
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@user_router.get(
    "/", response_model=List[UserRead], summary="List users"
)
# PUBLIC_INTERFACE
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Retrieves all user accounts (admin-only)."""
    return db.query(User).all()


# ================
# AUTH Endpoints
# ================

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post(
    "/register",
    response_model=UserRead,
    status_code=201,
    summary="Register new user",
    description="Registers a new user and returns account info."
)
# PUBLIC_INTERFACE
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register (sign up) a new user account."""
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=409, detail="Username already registered.")
    db_user = User(
        username=user.username,
        hashed_password=fake_hash_password(user.password),
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@auth_router.post(
    "/login",
    summary="User login",
    description="Authenticate user with username & password, returns JWT token."
)
# PUBLIC_INTERFACE
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """User login (returns JWT if successful)"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401, detail="Incorrect username or password."
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id, "role": user.role.value},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ================
# Ticket Endpoints
# ================

ticket_router = APIRouter(prefix="/tickets", tags=["tickets"])


@ticket_router.post(
    "/", response_model=TicketRead, status_code=201, summary="Create ticket"
)
# PUBLIC_INTERFACE
def create_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.USER, UserRole.ADMIN]))
):
    """
    Create a new ticket owned by the logged-in user.
    """
    db_ticket = Ticket(
        title=ticket.title,
        description=ticket.description,
        owner_id=current_user.id,
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@ticket_router.get(
    "/", response_model=List[TicketRead], summary="List tickets"
)
# PUBLIC_INTERFACE
def list_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.USER, UserRole.ADMIN]))
):
    """
    List tickets.
    Regular users see only their own tickets; admins see all.
    """
    if current_user.role == UserRole.ADMIN:
        return db.query(Ticket).all()
    return db.query(Ticket).filter(Ticket.owner_id == current_user.id).all()


@ticket_router.get(
    "/{ticket_id}", response_model=TicketRead, summary="Get ticket"
)
# PUBLIC_INTERFACE
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.USER, UserRole.ADMIN]))
):
    """
    Retrieve a single ticket by ID.
    Access allowed if user is owner or admin.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    if (current_user.role != UserRole.ADMIN and ticket.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not allowed to access this ticket.")
    return ticket


@ticket_router.put(
    "/{ticket_id}", response_model=TicketRead, summary="Update ticket"
)
# PUBLIC_INTERFACE
def update_ticket(
    ticket_id: int,
    update: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.USER, UserRole.ADMIN]))
):
    """
    Update details or status of a ticket.
    Only owner (or admin) may update.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    if (current_user.role != UserRole.ADMIN and ticket.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not allowed to update this ticket.")

    if update.title is not None:
        ticket.title = update.title
    if update.description is not None:
        ticket.description = update.description
    if update.status is not None:
        ticket.status = update.status

    db.commit()
    db.refresh(ticket)
    return ticket


@ticket_router.delete(
    "/{ticket_id}", response_class=JSONResponse, summary="Delete ticket"
)
# PUBLIC_INTERFACE
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """
    Admin only: Delete (close) a ticket.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    db.delete(ticket)
    db.commit()
    return {"detail": "Ticket deleted."}


@app.get("/", summary="Health check")
def health_check():
    """Return the health status of the backend service."""
    return {"message": "Healthy"}


# === ROUTER REGISTRATION ===
app.include_router(user_router)
app.include_router(auth_router)
app.include_router(ticket_router)
