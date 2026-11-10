from datetime import date
from typing import Optional

from fastapi import HTTPException, status
from pydantic import BaseModel

from app.dependencies import SessionDep, AuthDep
from app.repositories.booking_request import BookingRequestRepository
from app.repositories.listing import ListingRepository
from app.repositories.user import UserRepository
from app.services.booking_request_service import BookingRequestService
from app.services.listing_service import ListingService

from . import api_router


class BookingRequestCreate(BaseModel):
    move_in_date: date
    move_out_date: Optional[date] = None
    occupants: int
    message: Optional[str] = None


@api_router.get("/listings")
async def api_listings(
    db: SessionDep,
    location: Optional[str] = None,
    max_price: Optional[float] = None,
    bedrooms: Optional[int] = None,
    bathrooms: Optional[int] = None,
    furnished: Optional[bool] = None,
    available_from: Optional[date] = None,
):
    repo = ListingRepository(db)
    service = ListingService(repo)

    listings = service.search_listings(
        location=location,
        max_price=max_price,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        furnished=furnished,
        available_from=available_from,
    )

    return listings


@api_router.get("/listings/{listing_id}")
async def api_listing_details(
    listing_id: int,
    db: SessionDep,
):
    repo = ListingRepository(db)
    service = ListingService(repo)

    result = service.listing_details(listing_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found",
        )

    listing, landlord, photos, amenities = result

    return {
        "listing": listing,
        "landlord": {
            "id": landlord.id,
            "username": landlord.username,
            "full_name": landlord.full_name,
        },
        "photos": photos,
        "amenities": amenities,
    }


@api_router.post(
    "/listings/{listing_id}/requests",
    status_code=status.HTTP_201_CREATED,
)
async def api_create_booking_request(
    listing_id: int,
    payload: BookingRequestCreate,
    db: SessionDep,
    user: AuthDep,
):
    booking_repo = BookingRequestRepository(db)
    listing_repo = ListingRepository(db)
    user_repo = UserRepository(db)

    service = BookingRequestService(
        booking_repo,
        listing_repo,
        user_repo,
    )

    try:
        booking_request = service.create_booking_request(
            listing_id=listing_id,
            student_id=user.id,
            move_in_date=payload.move_in_date,
            move_out_date=payload.move_out_date,
            occupants=payload.occupants,
            message=payload.message,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return booking_request


@api_router.get("/requests")
async def api_student_requests(
    db: SessionDep,
    user: AuthDep,
):
    booking_repo = BookingRequestRepository(db)
    listing_repo = ListingRepository(db)
    user_repo = UserRepository(db)

    service = BookingRequestService(
        booking_repo,
        listing_repo,
        user_repo,
    )

    try:
        return service.student_dashboard(user.id)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc