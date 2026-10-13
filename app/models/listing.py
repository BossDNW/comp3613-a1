from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Listing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    landlord_id: int = Field(foreign_key="user.id", index=True)
    title: str = Field(index=True)
    city: str = Field(index=True)
    suburb: str = Field(index=True)
    address: str
    price_per_month: float = Field(default=0.0, index=True)
    description: str = ""
    bedrooms: int = Field(default=1, index=True)
    bathrooms: int = Field(default=1, index=True)
    furnished: bool = Field(default=False, index=True)
    available_from: Optional[date] = None
    status: str = Field(default="available", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ListingPhoto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    listing_id: int = Field(foreign_key="listing.id", index=True)
    image_url: str


class Amenity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)


class ListingAmenity(SQLModel, table=True):
    listing_id: int = Field(foreign_key="listing.id", primary_key=True)
    amenity_id: int = Field(foreign_key="amenity.id", primary_key=True)