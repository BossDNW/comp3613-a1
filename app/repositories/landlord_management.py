from datetime import datetime

from sqlmodel import Session, delete, select

from app.models.booking_request import BookingRequest
from app.models.listing import Amenity, Listing, ListingAmenity, ListingPhoto
from app.models.user import User


class LandlordManagementRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def dashboard_listings(self, landlord_id: int) -> list[Listing]:
        statement = (
            select(Listing)
            .where(Listing.landlord_id == landlord_id)
            .order_by(Listing.created_at.desc())
        )
        return self.db.exec(statement).all()

    def dashboard_request_rows(self, landlord_id: int) -> list[dict[str, object]]:
        statement = (
            select(BookingRequest, Listing, User)
            .join(Listing, BookingRequest.listing_id == Listing.id)
            .join(User, BookingRequest.student_id == User.id)
            .where(Listing.landlord_id == landlord_id)
            .order_by(BookingRequest.created_at.desc())
            .limit(20)
        )
        return [
            {"request": booking_request, "listing": listing, "student": student}
            for booking_request, listing, student in self.db.exec(statement).all()
        ]

    def booking_requests_for_landlord(
        self, landlord_id: int
    ) -> list[BookingRequest]:
        statement = (
            select(BookingRequest)
            .join(Listing, BookingRequest.listing_id == Listing.id)
            .where(Listing.landlord_id == landlord_id)
        )
        return self.db.exec(statement).all()

    def amenities(self) -> list[Amenity]:
        return self.db.exec(select(Amenity).order_by(Amenity.name)).all()

    def amenities_by_ids(self, amenity_ids: list[int]) -> list[Amenity]:
        if not amenity_ids:
            return []
        statement = select(Amenity).where(Amenity.id.in_(amenity_ids))
        return self.db.exec(statement).all()

    def listing_for_landlord(self, listing_id: int, landlord_id: int) -> Listing | None:
        statement = select(Listing).where(
            Listing.id == listing_id,
            Listing.landlord_id == landlord_id,
        )
        return self.db.exec(statement).one_or_none()

    def listing_photos(self, listing_id: int) -> list[ListingPhoto]:
        statement = (
            select(ListingPhoto)
            .where(ListingPhoto.listing_id == listing_id)
            .order_by(ListingPhoto.id)
        )
        return self.db.exec(statement).all()

    def listing_amenities(self, listing_id: int) -> list[Amenity]:
        statement = (
            select(Amenity)
            .join(ListingAmenity, ListingAmenity.amenity_id == Amenity.id)
            .where(ListingAmenity.listing_id == listing_id)
            .order_by(Amenity.name)
        )
        return self.db.exec(statement).all()

    def create_listing(
        self,
        listing: Listing,
        *,
        amenity_ids: list[int],
        photo_urls: list[str],
    ) -> Listing:
        try:
            self.db.add(listing)
            self.db.flush()
            self._replace_listing_details(listing.id, amenity_ids, photo_urls)
            self.db.commit()
            self.db.refresh(listing)
            return listing
        except Exception:
            self.db.rollback()
            raise

    def update_listing(
        self,
        listing: Listing,
        *,
        amenity_ids: list[int],
        photo_urls: list[str],
    ) -> Listing:
        try:
            self.db.add(listing)
            self._replace_listing_details(listing.id, amenity_ids, photo_urls)
            self.db.commit()
            self.db.refresh(listing)
            return listing
        except Exception:
            self.db.rollback()
            raise

    def _replace_listing_details(
        self,
        listing_id: int | None,
        amenity_ids: list[int],
        photo_urls: list[str],
    ) -> None:
        if listing_id is None:
            raise ValueError("Listing must be saved before its details.")
        self.db.exec(
            delete(ListingAmenity).where(ListingAmenity.listing_id == listing_id)
        )
        self.db.exec(
            delete(ListingPhoto).where(ListingPhoto.listing_id == listing_id)
        )
        self.db.add_all(
            ListingAmenity(listing_id=listing_id, amenity_id=amenity_id)
            for amenity_id in amenity_ids
        )
        self.db.add_all(
            ListingPhoto(listing_id=listing_id, image_url=image_url)
            for image_url in photo_urls
        )

    def set_listing_status(self, listing: Listing, status: str) -> Listing:
        try:
            listing.status = status
            self.db.add(listing)
            self.db.commit()
            self.db.refresh(listing)
            return listing
        except Exception:
            self.db.rollback()
            raise

    def booking_request_for_listing_owner(
        self, booking_request_id: int, landlord_id: int
    ) -> tuple[BookingRequest, Listing, User] | None:
        statement = (
            select(BookingRequest, Listing, User)
            .join(Listing, BookingRequest.listing_id == Listing.id)
            .join(User, BookingRequest.student_id == User.id)
            .where(
                BookingRequest.id == booking_request_id,
                Listing.landlord_id == landlord_id,
            )
        )
        result = self.db.exec(statement).one_or_none()
        if result is None:
            return None
        return result

    def set_booking_request_status(
        self, booking_request: BookingRequest, status: str
    ) -> BookingRequest:
        try:
            booking_request.status = status
            booking_request.updated_at = datetime.utcnow()
            self.db.add(booking_request)
            self.db.commit()
            self.db.refresh(booking_request)
            return booking_request
        except Exception:
            self.db.rollback()
            raise
