from unittest.mock import MagicMock

import pytest

from app.models.booking_request import BookingRequest
from app.models.listing import Amenity, Listing
from app.models.user import User
from app.services.landlord_management_service import LandlordManagementService


def landlord_user():
    return User(
        id=2,
        username="landlord",
        email="landlord@test.com",
        password="password",
        role="landlord",
    )


def student_user():
    return User(
        id=1,
        username="bob",
        email="bob@test.com",
        password="password",
        role="user",
    )


def test_non_landlord_is_rejected():
    repo = MagicMock()
    repo.get_user.return_value = student_user()

    service = LandlordManagementService(repo)

    with pytest.raises(PermissionError):
        service.require_landlord(1)


def test_missing_user_is_rejected():
    repo = MagicMock()
    repo.get_user.return_value = None

    service = LandlordManagementService(repo)

    with pytest.raises(PermissionError):
        service.require_landlord(999)


def test_dashboard_calculates_totals():
    repo = MagicMock()
    repo.get_user.return_value = landlord_user()

    listings = [
        Listing(
            id=1,
            landlord_id=2,
            title="Listing One",
            city="Trinidad",
            suburb="St Augustine",
            address="St Augustine",
            price_per_month=2500,
        ),
        Listing(
            id=2,
            landlord_id=2,
            title="Listing Two",
            city="Trinidad",
            suburb="Curepe",
            address="Curepe",
            price_per_month=3000,
        ),
    ]

    requests = [
        BookingRequest(
            id=1,
            listing_id=1,
            student_id=1,
            move_in_date=None,
            occupants=1,
            status="pending",
        ),
        BookingRequest(
            id=2,
            listing_id=2,
            student_id=1,
            move_in_date=None,
            occupants=1,
            status="accepted",
        ),
        BookingRequest(
            id=3,
            listing_id=2,
            student_id=1,
            move_in_date=None,
            occupants=1,
            status="pending",
        ),
    ]

    repo.dashboard_listings.return_value = listings
    repo.booking_requests_for_landlord.return_value = requests
    repo.dashboard_request_rows.return_value = []

    service = LandlordManagementService(repo)

    result = service.dashboard(2)

    assert result["total_listings"] == 2
    assert result["pending_requests"] == 2
    assert result["accepted_requests"] == 1


def test_update_listing_fails_if_listing_not_owned():
    repo = MagicMock()
    repo.get_user.return_value = landlord_user()
    repo.listing_for_landlord.return_value = None

    service = LandlordManagementService(repo)

    with pytest.raises(LookupError):
        service.update_listing(
            2,
            99,
            title="Updated",
            location="St Augustine",
            price_per_month="3000",
            description="Updated description",
            amenity_ids=[1],
            photo_urls=["https://example.com/photo.jpg"],
        )


def test_invalid_booking_decision_is_rejected():
    repo = MagicMock()
    repo.get_user.return_value = landlord_user()

    service = LandlordManagementService(repo)

    with pytest.raises(ValueError):
        service.decide_booking_request(
            2,
            1,
            decision="maybe",
        )


def test_non_pending_booking_request_cannot_be_decided():
    repo = MagicMock()
    repo.get_user.return_value = landlord_user()

    booking_request = BookingRequest(
        id=1,
        listing_id=10,
        student_id=1,
        move_in_date=None,
        occupants=1,
        status="accepted",
    )

    listing = Listing(
        id=10,
        landlord_id=2,
        title="Campus Apartment",
        city="Trinidad",
        suburb="St Augustine",
        address="St Augustine",
        price_per_month=3000,
    )

    repo.booking_request_for_listing_owner.return_value = (
        booking_request,
        listing,
        student_user(),
    )

    service = LandlordManagementService(repo)

    with pytest.raises(ValueError):
        service.decide_booking_request(
            2,
            1,
            decision="rejected",
        )


def test_valid_pending_request_can_be_accepted():
    repo = MagicMock()
    repo.get_user.return_value = landlord_user()

    booking_request = BookingRequest(
        id=1,
        listing_id=10,
        student_id=1,
        move_in_date=None,
        occupants=1,
        status="pending",
    )

    listing = Listing(
        id=10,
        landlord_id=2,
        title="Campus Apartment",
        city="Trinidad",
        suburb="St Augustine",
        address="St Augustine",
        price_per_month=3000,
    )

    repo.booking_request_for_listing_owner.return_value = (
        booking_request,
        listing,
        student_user(),
    )

    accepted_request = BookingRequest(
        id=1,
        listing_id=10,
        student_id=1,
        move_in_date=None,
        occupants=1,
        status="accepted",
    )

    repo.set_booking_request_status.return_value = accepted_request

    service = LandlordManagementService(repo)

    result = service.decide_booking_request(
        2,
        1,
        decision="accepted",
    )

    assert result.status == "accepted"
    repo.set_booking_request_status.assert_called_once()