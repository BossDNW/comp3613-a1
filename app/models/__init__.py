"""Database table models.

Import every table model here so ``SQLModel.metadata.create_all`` sees them.
"""

from app.models.booking_request import BookingRequest
from app.models.listing import Amenity, Listing, ListingAmenity, ListingPhoto
from app.models.user import User

__all__ = [
    "User",
    "Listing",
    "ListingPhoto",
    "Amenity",
    "ListingAmenity",
    "BookingRequest",
]
