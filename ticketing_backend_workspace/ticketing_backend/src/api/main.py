from fastapi import FastAPI, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .models import Base, User, Ticket
from .schemas import (
    UserCreate, UserRead, UserLogin,
    TicketCreate, TicketRead, TicketUpdate,
)

# Simple in-memory SQLite for MVP; easy refactor for production DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


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
def list_users(db: Session = Depends(get_db)):
    """Retrieves all user accounts."""
    return db.query(User).all()


auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post(
    "/login", summary="User login",
    description="Authenticate user and return basic result (no JWT for MVP)."
)
# PUBLIC_INTERFACE
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticates a user by username and password and returns user info.
    (For production, use secure hashing/JWT tokens. This is a stub.)
    """
    user = db.query(User).filter(
        User.username == login_data.username
    ).first()
    if not user or user.hashed_password != fake_hash_password(login_data.password):
        raise HTTPException(
            status_code=401, detail="Incorrect username or password."
        )
    return UserRead.model_validate(user)


ticket_router = APIRouter(prefix="/tickets", tags=["tickets"])


@ticket_router.post(
    "/", response_model=TicketRead, status_code=201, summary="Create ticket"
)
# PUBLIC_INTERFACE
def create_ticket(ticket: TicketCreate, db: Session = Depends(get_db)):
    """
    Create a new ticket (owned by hardcoded user for MVP).
    TODO: Replace owner logic with real user from session/auth.
    """
    owner = db.query(User).first()
    if not owner:
        raise HTTPException(status_code=400, detail="No users registered.")
    db_ticket = Ticket(
        title=ticket.title,
        description=ticket.description,
        owner_id=owner.id,
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@ticket_router.get(
    "/", response_model=List[TicketRead], summary="List tickets"
)
# PUBLIC_INTERFACE
def list_tickets(db: Session = Depends(get_db)):
    """Return all tickets."""
    return db.query(Ticket).all()


@ticket_router.get(
    "/{ticket_id}", response_model=TicketRead, summary="Get ticket"
)
# PUBLIC_INTERFACE
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Retrieve a single ticket by ID."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    return ticket


@ticket_router.put(
    "/{ticket_id}", response_model=TicketRead, summary="Update ticket"
)
# PUBLIC_INTERFACE
def update_ticket(ticket_id: int, update: TicketUpdate, db: Session = Depends(get_db)):
    """Update details or status of a ticket."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")

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
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Delete (close) a ticket."""
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


app.include_router(user_router)
app.include_router(auth_router)
app.include_router(ticket_router)
