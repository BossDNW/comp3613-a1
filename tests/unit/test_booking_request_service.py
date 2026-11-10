from datetime import date
from unittest.mock import MagicMock

import pytest

from app.models.booking_request import BookingRequest
from app.models.listing import Listing
from app.models.user import User
from app.services.booking_request_service import BookingRequestService


@pytest.fixture
def repos():
    booking_repo = MagicMock()
    listing_repo = MagicMock()
    user_repo = MagicMock()
    return booking_repo, listing_repo, user_repo


@pytest.fixture
def service(repos):
    booking_repo, listing_repo, user_repo = repos
    return BookingRequestService(
        booking_repo,
        listing_repo,
        user_repo,
    )


def test_landlord_cannot_submit_booking_request(service, repos):
    _, _, user_repo = repos

    user_repo.get_by_id.return_value = User(
        id=2,
        username="landlord",
        email="landlord@test.com",
        password="password",
        role="landlord",
    )

    with pytest.raises(PermissionError):
        service.require_booking_student(2)


def test_missing_user_cannot_submit_booking_request(service, repos):
    _, _, user_repo = repos

    user_repo.get_by_id.return_value = None

    with pytest.raises(PermissionError):
        service.require_booking_student(999)


def test_move_in_before_available_date_is_invalid(service):
    listing = Listing(
        id=1,
        landlord_id=2,
        title="Test Apartment",
        city="Trinidad",
        suburb="St Augustine",
        address="St Augustine",
        price_per_month=2500,
        available_from=date(2026, 12, 1),
    )

    with pytest.raises(ValueError):
        service._validate_request(
            listing,
            move_in_date=date(2026, 11, 20),
            move_out_date=None,
            occupants=1,
        )


def test_move_out_must_be_after_move_in(service):
    listing = Listing(
        id=1,
        landlord_id=2,
        title="Test Apartment",
        city="Trinidad",
        suburb="St Augustine",
        address="St Augustine",
        price_per_month=2500,
        available_from=date(2026, 11, 1),
    )

    with pytest.raises(ValueError):
        service._validate_request(
            listing,
            move_in_date=date(2026, 12, 1),
            move_out_date=date(2026, 12, 1),
            occupants=1,
        )


def test_occupants_must_be_at_least_one(service):
    listing = Listing(
        id=1,
        landlord_id=2,
        title="Test Apartment",
        city="Trinidad",
        suburb="St Augustine",
        address="St Augustine",
        price_per_month=2500,
        available_from=date(2026, 11, 1),
    )

    with pytest.raises(ValueError):
        service._validate_request(
            listing,
            move_in_date=date(2026, 12, 1),
            move_out_date=None,
            occupants=0,
        )


def test_valid_booking_request_is_created(service, repos):
    booking_repo, listing_repo, user_repo = repos

    user_repo.get_by_id.return_value = User(
        id=1,
        username="bob",
        email="bob@test.com",
        password="password",
        role="user",
    )

    listing_repo.get_available_by_id.return_value = Listing(
        id=10,
        landlord_id=2,
        title="Campus Apartment",
        city="Trinidad",
        suburb="St Augustine",
        address="St Augustine",
        price_per_month=3000,
        available_from=date(2026, 11, 1),
    )

    booking_repo.create.side_effect = lambda request: request

    result = service.create_booking_request(
        listing_id=10,
        student_id=1,
        move_in_date=date(2026, 12, 1),
        move_out_date=date(2027, 5, 1),
        occupants=1,
        message="Interested in this apartment",
    )

    assert result.status == "pending"
    assert result.student_id == 1
    assert result.listing_id == 10
    assert result.occupants == 1


def test_non_pending_request_cannot_be_updated(service, repos):
    booking_repo, _, _ = repos

    booking_repo.get_for_student.return_value = BookingRequest(
        id=1,
        listing_id=10,
        student_id=1,
        move_in_date=date(2026, 12, 1),
        occupants=1,
        status="accepted",
    )

    with pytest.raises(ValueError):
        service.update_booking_request(
            booking_request_id=1,
            student_id=1,
            move_in_date=date(2026, 12, 5),
            move_out_date=None,
            occupants=1,
            message="Updated",
        )


def test_pending_request_can_be_cancelled(service, repos):
    booking_repo, _, _ = repos

    request = BookingRequest(
        id=1,
        listing_id=10,
        student_id=1,
        move_in_date=date(2026, 12, 1),
        occupants=1,
        status="pending",
    )

    booking_repo.get_for_student.return_value = request
    booking_repo.cancel.return_value = request

    result = service.cancel_booking_request(1, 1)

    booking_repo.cancel.assert_called_once_with(request)
    assert result == request