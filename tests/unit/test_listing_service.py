from datetime import date
from unittest.mock import MagicMock

from app.models.listing import Amenity, Listing, ListingPhoto
from app.models.user import User
from app.services.listing_service import ListingService


def test_search_normalizes_appartment_to_apartment():
    repo = MagicMock()
    service = ListingService(repo)

    service.search_listings(location="St Augustine appartment")

    repo.search.assert_called_once_with(
        location="st augustine apartment",
        max_price=None,
        bedrooms=None,
        exact_bedrooms=None,
        bathrooms=None,
        furnished=None,
        available_from=None,
    )


def test_search_extracts_exact_bedroom_count():
    repo = MagicMock()
    service = ListingService(repo)

    service.search_listings(location="1 bedroom apartment")

    repo.search.assert_called_once_with(
        location="apartment",
        max_price=None,
        bedrooms=None,
        exact_bedrooms=1,
        bathrooms=None,
        furnished=None,
        available_from=None,
    )


def test_search_passes_other_filters_to_repository():
    repo = MagicMock()
    service = ListingService(repo)

    move_in = date(2026, 12, 1)

    service.search_listings(
        location="St Augustine",
        max_price=3000,
        bedrooms=2,
        bathrooms=1,
        furnished=True,
        available_from=move_in,
    )

    repo.search.assert_called_once_with(
        location="st augustine",
        max_price=3000,
        bedrooms=2,
        exact_bedrooms=None,
        bathrooms=1,
        furnished=True,
        available_from=move_in,
    )


def test_listing_details_returns_none_when_listing_missing():
    repo = MagicMock()
    repo.get_available_by_id.return_value = None

    service = ListingService(repo)

    result = service.listing_details(999)

    assert result is None


def test_listing_details_returns_related_data():
    repo = MagicMock()
    service = ListingService(repo)

    listing = Listing(
        id=1,
        landlord_id=2,
        title="Campus Apartment",
        city="Trinidad",
        suburb="St Augustine",
        address="St Augustine",
        price_per_month=3000,
    )

    landlord = User(
        id=2,
        username="landlord",
        email="landlord@test.com",
        password="password",
        role="landlord",
    )

    photos = [
        ListingPhoto(
            id=1,
            listing_id=1,
            image_url="https://example.com/photo.jpg",
        )
    ]

    amenities = [
        Amenity(id=1, name="WiFi")
    ]

    repo.get_available_by_id.return_value = listing
    repo.get_landlord.return_value = landlord
    repo.photos_for_listing.return_value = photos
    repo.amenities_for_listing.return_value = amenities

    result = service.listing_details(1)

    assert result == (listing, landlord, photos, amenities)

    repo.get_landlord.assert_called_once_with(2)
    repo.photos_for_listing.assert_called_once_with(1)
    repo.amenities_for_listing.assert_called_once_with(1)