from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class BookingRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    listing_id: int = Field(foreign_key="listing.id", index=True)
    student_id: int = Field(foreign_key="user.id", index=True)

    move_in_date: date
    move_out_date: Optional[date] = None

    occupants: int = Field(default=1)

    status: str = Field(default="pending", index=True)
    message: str = ""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)