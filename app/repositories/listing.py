from __future__ import annotations

from datetime import date
from typing import Optional

from sqlmodel import Session, or_, select

from app.models.listing import Amenity, Listing, ListingAmenity, ListingPhoto
from app.models.user import User


class ListingRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[Listing]:
        return self.db.exec(select(Listing).where(Listing.status == "available")).all()

    def search(
        self,
        *,
        location: str | None = None,
        max_price: float | None = None,
        bedrooms: int | None = None,
        exact_bedrooms: int | None = None,
        bathrooms: int | None = None,
        furnished: bool | None = None,
        available_from: date | None = None,
    ) -> list[Listing]:
        statement = select(Listing).where(Listing.status == "available")

        if location:
            search_terms = location.split()
            for term in search_terms:
                term_match = f"%{term}%"
                statement = statement.where(
                    or_(
                        Listing.title.ilike(term_match),
                        Listing.city.ilike(term_match),
                        Listing.suburb.ilike(term_match),
                        Listing.address.ilike(term_match),
                        Listing.description.ilike(term_match),
                    )
                )
        if max_price is not None:
            statement = statement.where(Listing.price_per_month <= float(max_price))
        if bedrooms is not None:
            statement = statement.where(Listing.bedrooms >= int(bedrooms))
        if exact_bedrooms is not None:
            statement = statement.where(Listing.bedrooms == int(exact_bedrooms))
        if bathrooms is not None:
            statement = statement.where(Listing.bathrooms >= int(bathrooms))
        if furnished is not None:
            statement = statement.where(Listing.furnished == bool(furnished))
        if available_from is not None:
            statement = statement.where(Listing.available_from <= available_from)

        return self.db.exec(statement).all()

    def get_available_by_id(self, listing_id: int) -> Listing | None:
        return self.db.exec(
            select(Listing)
            .where(Listing.id == listing_id)
            .where(Listing.status == "available")
        ).one_or_none()

    def get_by_id(self, listing_id: int) -> Listing | None:
        return self.db.get(Listing, listing_id)

    def get_landlord(self, landlord_id: int) -> User | None:
        return self.db.get(User, landlord_id)

    def photos_for_listing(self, listing_id: int) -> list[ListingPhoto]:
        statement = (
            select(ListingPhoto)
            .where(ListingPhoto.listing_id == listing_id)
            .order_by(ListingPhoto.id)
        )
        return self.db.exec(statement).all()

    def photos_for_listings(self, listing_ids: list[int]) -> dict[int, list[ListingPhoto]]:
        if not listing_ids:
            return {}

        statement = (
            select(ListingPhoto)
            .where(ListingPhoto.listing_id.in_(listing_ids))
            .order_by(ListingPhoto.id)
        )
        photos_by_listing: dict[int, list[ListingPhoto]] = {}
        for photo in self.db.exec(statement).all():
            photos_by_listing.setdefault(photo.listing_id, []).append(photo)
        return photos_by_listing

    def amenities_for_listing(self, listing_id: int) -> list[Amenity]:
        statement = (
            select(Amenity)
            .join(ListingAmenity, ListingAmenity.amenity_id == Amenity.id)
            .where(ListingAmenity.listing_id == listing_id)
            .order_by(Amenity.name)
        )
        return self.db.exec(statement).all()

    def create(self, listing: Listing) -> Listing:
        self.db.add(listing)
        self.db.commit()
        self.db.refresh(listing)
        return listing
