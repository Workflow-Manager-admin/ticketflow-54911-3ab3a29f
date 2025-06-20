from fastapi import FastAPI, HTTPException, APIRouter, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .models import Base, Ticket, TicketStatus
from .schemas import TicketCreate, TicketRead, TicketUpdate

# === CONFIGURATION ===

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Ticketing Backend API",
    description=(
        "API endpoints for managing tickets in the multi-container ticketing system."
    ),
    version="1.0.0",
    openapi_tags=[
        {"name": "tickets", "description": "Ticket CRUD and status management"},
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


# ================
# Ticket Endpoints
# ================

ticket_router = APIRouter(prefix="/tickets", tags=["tickets"])


@ticket_router.post(
    "/",
    response_model=TicketRead,
    status_code=201,
    summary="Create ticket",
    description="Create a new ticket.",
)
# PUBLIC_INTERFACE
def create_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db),
):
    """Create a new ticket."""
    db_ticket = Ticket(
        title=ticket.title,
        description=ticket.description,
        # In no-auth mode, we do not track user, use fixed owner_id (e.g., 1)
        owner_id=1,
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


@ticket_router.get(
    "/",
    response_model=List[TicketRead],
    summary="List tickets",
    description="List all tickets.",
)
# PUBLIC_INTERFACE
def list_tickets(
    db: Session = Depends(get_db),
):
    """Return all tickets in the system."""
    return db.query(Ticket).all()


@ticket_router.get(
    "/{ticket_id}",
    response_model=TicketRead,
    summary="Get ticket",
    description="Get a single ticket by ID.",
)
# PUBLIC_INTERFACE
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve a ticket by its unique ID."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    return ticket


@ticket_router.put(
    "/{ticket_id}",
    response_model=TicketRead,
    summary="Update ticket",
    description="Update ticket details.",
)
# PUBLIC_INTERFACE
def update_ticket(
    ticket_id: int,
    update: TicketUpdate,
    db: Session = Depends(get_db),
):
    """Update ticket details (title, description, and/or status)."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")

    if update.title is not None:
        ticket.title = update.title
    if update.description is not None:
        ticket.description = update.description
    if update.status is not None:
        # Validate status
        if update.status not in TicketStatus.__members__.values():
            raise HTTPException(status_code=400, detail="Invalid status value.")
        ticket.status = update.status

    db.commit()
    db.refresh(ticket)
    return ticket


@ticket_router.delete(
    "/{ticket_id}",
    response_class=JSONResponse,
    summary="Delete ticket",
    description="Delete a ticket.",
)
# PUBLIC_INTERFACE
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
):
    """Delete a ticket by its ID."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    db.delete(ticket)
    db.commit()
    return {"detail": "Ticket deleted."}


@ticket_router.patch(
    "/{ticket_id}/status",
    response_model=TicketRead,
    summary="Update ticket status",
    description="Update only the status of a ticket.",
)
# PUBLIC_INTERFACE
def update_ticket_status(
    ticket_id: int,
    ticket_status: TicketStatus,
    db: Session = Depends(get_db),
):
    """Directly update the status of a ticket."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    ticket.status = ticket_status
    db.commit()
    db.refresh(ticket)
    return ticket


@app.get("/", summary="Health check")
def health_check():
    """Return the health status of the backend service."""
    return {"message": "Healthy"}


# === ROUTER REGISTRATION ===
app.include_router(ticket_router)
