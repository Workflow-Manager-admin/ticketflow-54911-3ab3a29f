from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .models import UserRole, TicketStatus


# PUBLIC_INTERFACE
class UserCreate(BaseModel):
    """Schema for creating a user account."""
    username: str = Field(..., description="Unique username")
    password: str = Field(..., description="Password for user account")
    role: UserRole = Field(default=UserRole.USER, description="User role")


# PUBLIC_INTERFACE


class UserRead(BaseModel):
    """Schema for returning a user."""
    id: int
    username: str
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True


# PUBLIC_INTERFACE


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


# PUBLIC_INTERFACE


class TicketCreate(BaseModel):
    """Schema for creating a ticket."""
    title: str = Field(..., description="Ticket title")
    description: Optional[str] = Field(None, description="Detailed description")


# PUBLIC_INTERFACE


class TicketUpdate(BaseModel):
    """Schema for updating a ticket."""
    title: Optional[str] = Field(None, description="Ticket title")
    description: Optional[str] = Field(None, description="Description")
    status: Optional[TicketStatus] = Field(None, description="Ticket status")


# PUBLIC_INTERFACE


class TicketRead(BaseModel):
    """Schema for returning ticket info."""
    id: int
    title: str
    description: Optional[str]
    status: TicketStatus
    created_at: datetime
    updated_at: datetime
    owner_id: int

    class Config:
        from_attributes = True
