import math
from typing import TypedDict
from urllib.parse import urlsplit

from app.models.booking_request import BookingRequest
from app.models.listing import Listing, ListingPhoto
from app.models.user import User
from app.repositories.landlord_management import LandlordManagementRepository


class ListingValues(TypedDict):
    title: str
    location: str
    price: float
    description: str
    amenity_ids: list[int]
    photo_urls: list[str]


class LandlordManagementService:
    def __init__(self, landlord_repo: LandlordManagementRepository):
        self.landlord_repo = landlord_repo

    def require_landlord(self, landlord_id: int) -> User:
        user = self.landlord_repo.get_user(landlord_id)
        if user is None or user.role != "landlord":
            raise PermissionError("Only landlord accounts can manage listings.")
        return user

    def dashboard(self, landlord_id: int) -> dict[str, object]:
        self.require_landlord(landlord_id)
        listings = self.landlord_repo.dashboard_listings(landlord_id)
        requests = self.landlord_repo.booking_requests_for_landlord(landlord_id)
        return {
            "listings": listings,
            "rows": self.landlord_repo.dashboard_request_rows(landlord_id),
            "total_listings": len(listings),
            "pending_requests": sum(item.status == "pending" for item in requests),
            "accepted_requests": sum(item.status == "accepted" for item in requests),
        }

    def listing_form_data(
        self, landlord_id: int, listing_id: int | None = None
    ) -> dict[str, object]:
        self.require_landlord(landlord_id)
        listing = None
        photos: list[ListingPhoto] = []
        selected_amenity_ids: set[int] = set()
        if listing_id is not None:
            listing = self.landlord_repo.listing_for_landlord(
                listing_id, landlord_id
            )
            if listing is None:
                raise LookupError("Listing not found.")
            assert listing.id is not None
            photos = self.landlord_repo.listing_photos(listing_id)
            selected_amenity_ids = {
                amenity.id
                for amenity in self.landlord_repo.listing_amenities(listing_id)
                if amenity.id is not None
            }
        return {
            "listing": listing,
            "photos": photos,
            "amenities": self.landlord_repo.amenities(),
            "selected_amenity_ids": selected_amenity_ids,
        }

    def create_listing(
        self,
        landlord_id: int,
        *,
        title: str,
        location: str,
        price_per_month: str,
        description: str,
        amenity_ids: list[int],
        photo_urls: list[str],
    ) -> Listing:
        self.require_landlord(landlord_id)
        values = self._validate_listing_values(
            title=title,
            location=location,
            price_per_month=price_per_month,
            description=description,
            amenity_ids=amenity_ids,
            photo_urls=photo_urls,
        )
        listing = Listing(
            landlord_id=landlord_id,
            title=values["title"],
            city="Trinidad",
            suburb=values["location"],
            address=values["location"],
            price_per_month=values["price"],
            description=values["description"],
            status="available",
        )
        return self.landlord_repo.create_listing(
            listing,
            amenity_ids=values["amenity_ids"],
            photo_urls=values["photo_urls"],
        )

    def update_listing(
        self,
        landlord_id: int,
        listing_id: int,
        *,
        title: str,
        location: str,
        price_per_month: str,
        description: str,
        amenity_ids: list[int],
        photo_urls: list[str],
    ) -> Listing:
        self.require_landlord(landlord_id)
        listing = self.landlord_repo.listing_for_landlord(
            listing_id, landlord_id
        )
        if listing is None:
            raise LookupError("Listing not found.")
        values = self._validate_listing_values(
            title=title,
            location=location,
            price_per_month=price_per_month,
            description=description,
            amenity_ids=amenity_ids,
            photo_urls=photo_urls,
        )
        listing.title = values["title"]
        listing.city = "Trinidad"
        listing.suburb = values["location"]
        listing.address = values["location"]
        listing.price_per_month = values["price"]
        listing.description = values["description"]
        return self.landlord_repo.update_listing(
            listing,
            amenity_ids=values["amenity_ids"],
            photo_urls=values["photo_urls"],
        )

    def change_listing_status(
        self, landlord_id: int, listing_id: int, *, active: bool
    ) -> Listing:
        self.require_landlord(landlord_id)
        listing = self.landlord_repo.listing_for_landlord(
            listing_id, landlord_id
        )
        if listing is None:
            raise LookupError("Listing not found.")
        return self.landlord_repo.set_listing_status(
            listing, "available" if active else "inactive"
        )

    def booking_request_details(
        self, landlord_id: int, booking_request_id: int
    ) -> dict[str, object]:
        self.require_landlord(landlord_id)
        details = self.landlord_repo.booking_request_for_listing_owner(
            booking_request_id, landlord_id
        )
        if details is None:
            raise LookupError("Booking request not found.")
        booking_request, listing, student = details
        assert listing.id is not None
        return {
            "booking_request": booking_request,
            "listing": listing,
            "student": student,
            "photos": self.landlord_repo.listing_photos(listing.id),
            "amenities": self.landlord_repo.listing_amenities(listing.id),
        }

    def decide_booking_request(
        self,
        landlord_id: int,
        booking_request_id: int,
        *,
        decision: str,
    ) -> BookingRequest:
        self.require_landlord(landlord_id)
        if decision not in {"accepted", "rejected"}:
            raise ValueError("Choose accept or reject for this request.")
        details = self.landlord_repo.booking_request_for_listing_owner(
            booking_request_id, landlord_id
        )
        if details is None:
            raise LookupError("Booking request not found.")
        booking_request = details[0]
        if booking_request.status != "pending":
            raise ValueError("Only pending requests can be accepted or rejected.")
        return self.landlord_repo.set_booking_request_status(
            booking_request, decision
        )

    def _validate_listing_values(
        self,
        *,
        title: str,
        location: str,
        price_per_month: str,
        description: str,
        amenity_ids: list[int],
        photo_urls: list[str],
    ) -> ListingValues:
        title = title.strip()
        location = location.strip()
        description = description.strip()
        if not title or len(title) > 150:
            raise ValueError("Enter a listing title up to 150 characters.")
        if not location or len(location) > 120:
            raise ValueError("Enter a Trinidad location up to 120 characters.")
        if len(description) > 2000:
            raise ValueError("Description must be 2,000 characters or fewer.")
        try:
            price = float(price_per_month)
        except (TypeError, ValueError) as exc:
            raise ValueError("Enter a valid monthly price.") from exc
        if not math.isfinite(price) or price <= 0:
            raise ValueError("Monthly price must be greater than zero.")

        clean_amenity_ids = sorted(set(amenity_ids))
        if not clean_amenity_ids:
            raise ValueError("Select at least one amenity.")
        amenities = self.landlord_repo.amenities_by_ids(clean_amenity_ids)
        if len(amenities) != len(clean_amenity_ids):
            raise ValueError("One or more selected amenities are not available.")

        clean_photo_urls: list[str] = []
        for raw_url in photo_urls:
            image_url = raw_url.strip()
            if not image_url:
                continue
            try:
                parsed_url = urlsplit(image_url)
            except ValueError as exc:
                raise ValueError("Enter a valid photo URL.") from exc
            if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
                raise ValueError("Enter photo URLs that start with http:// or https://.")
            clean_photo_urls.append(image_url)
        if not clean_photo_urls:
            raise ValueError("Add at least one photo URL.")
        if len(clean_photo_urls) > 8:
            raise ValueError("A listing can have up to eight photos.")

        return {
            "title": title,
            "location": location,
            "price": price,
            "description": description,
            "amenity_ids": clean_amenity_ids,
            "photo_urls": clean_photo_urls,
        }
