from __future__ import annotations

from datetime import date
import re

from app.models.listing import Amenity, Listing, ListingPhoto
from app.models.user import User
from app.repositories.listing import ListingRepository


class ListingService:
    def __init__(self, listing_repo: ListingRepository):
        self.listing_repo = listing_repo

    def search_listings(
        self,
        *,
        location: str | None = None,
        max_price: float | None = None,
        bedrooms: int | None = None,
        exact_bedrooms: int | None = None,
        bathrooms: int | None = None,
        furnished: bool | None = None,
        available_from: date | None = None,
    ):
        search_text = (location or "").strip().lower()
        search_text = re.sub(r"\bappartment\b", "apartment", search_text)
        bedroom_match = re.search(
            r"\b(?P<count>\d+)\s*[- ]?\s*bed(?:room)?s?\b",
            search_text,
        )
        inferred_bedrooms = None
        if bedroom_match:
            inferred_bedrooms = int(bedroom_match.group("count"))
            search_text = search_text[: bedroom_match.start()] + search_text[bedroom_match.end() :]
            search_text = " ".join(search_text.split())

        if inferred_bedrooms is not None:
            exact_bedrooms = inferred_bedrooms

        return self.listing_repo.search(
            location=search_text or None,
            max_price=max_price,
            bedrooms=bedrooms,
            exact_bedrooms=exact_bedrooms,
            bathrooms=bathrooms,
            furnished=furnished,
            available_from=available_from,
        )

    def photos_for_listings(self, listing_ids: list[int]) -> dict[int, list[ListingPhoto]]:
        return self.listing_repo.photos_for_listings(listing_ids)

    def listing_details(
        self, listing_id: int
    ) -> tuple[Listing, User | None, list[ListingPhoto], list[Amenity]] | None:
        listing = self.listing_repo.get_available_by_id(listing_id)
        if listing is None:
            return None

        return (
            listing,
            self.listing_repo.get_landlord(listing.landlord_id),
            self.listing_repo.photos_for_listing(listing_id),
            self.listing_repo.amenities_for_listing(listing_id),
        )
