from datetime import date

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

import app.models
from app.models.booking_request import BookingRequest
from app.models.listing import Listing
from app.models.user import User
from app.repositories.booking_request import BookingRequestRepository
from app.repositories.listing import ListingRepository
from app.repositories.user import UserRepository
from app.services.booking_request_service import BookingRequestService
from app.services.listing_service import ListingService


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    SQLModel.metadata.drop_all(engine)


def create_test_users(session):
    student = User(
        username="student1",
        email="student1@test.com",
        password="password",
        role="user",
    )

    landlord = User(
        username="landlord1",
        email="landlord1@test.com",
        password="password",
        role="landlord",
    )

    session.add(student)
    session.add(landlord)
    session.commit()

    session.refresh(student)
    session.refresh(landlord)

    return student, landlord


def create_test_listing(session, landlord_id):
    listing = Listing(
        landlord_id=landlord_id,
        title="St Augustine Student Apartment",
        city="Trinidad",
        suburb="St Augustine",
        address="Eastern Main Road",
        price_per_month=3000,
        description="Student apartment near campus",
        bedrooms=2,
        bathrooms=1,
        furnished=True,
        available_from=date(2026, 11, 1),
        status="available",
    )

    session.add(listing)
    session.commit()
    session.refresh(listing)

    return listing


def test_user_is_saved_and_retrieved_from_database(session):
    repo = UserRepository(session)

    user = User(
        username="bobtest",
        email="bobtest@test.com",
        password="password",
        role="user",
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    saved_user = repo.get_by_id(user.id)

    assert saved_user is not None
    assert saved_user.username == "bobtest"
    assert saved_user.email == "bobtest@test.com"


def test_listing_is_saved_and_found_by_search(session):
    student, landlord = create_test_users(session)

    listing = create_test_listing(session, landlord.id)

    repo = ListingRepository(session)
    service = ListingService(repo)

    results = service.search_listings(
        location="St Augustine",
        max_price=3500,
        bedrooms=1,
        furnished=True,
    )

    assert len(results) == 1
    assert results[0].id == listing.id
    assert results[0].title == "St Augustine Student Apartment"


def test_booking_request_is_created_and_persisted(session):
    student, landlord = create_test_users(session)
    listing = create_test_listing(session, landlord.id)

    booking_repo = BookingRequestRepository(session)
    listing_repo = ListingRepository(session)
    user_repo = UserRepository(session)

    service = BookingRequestService(
        booking_repo,
        listing_repo,
        user_repo,
    )

    result = service.create_booking_request(
        listing_id=listing.id,
        student_id=student.id,
        move_in_date=date(2026, 12, 1),
        move_out_date=date(2027, 5, 1),
        occupants=1,
        message="I would like this apartment.",
    )

    assert result.id is not None
    assert result.status == "pending"

    saved_request = session.get(BookingRequest, result.id)

    assert saved_request is not None
    assert saved_request.student_id == student.id
    assert saved_request.listing_id == listing.id
    assert saved_request.message == "I would like this apartment."


def test_booking_request_can_be_cancelled_and_change_persists(session):
    student, landlord = create_test_users(session)
    listing = create_test_listing(session, landlord.id)

    booking_repo = BookingRequestRepository(session)
    listing_repo = ListingRepository(session)
    user_repo = UserRepository(session)

    service = BookingRequestService(
        booking_repo,
        listing_repo,
        user_repo,
    )

    request = service.create_booking_request(
        listing_id=listing.id,
        student_id=student.id,
        move_in_date=date(2026, 12, 1),
        move_out_date=None,
        occupants=1,
        message="Test booking",
    )

    service.cancel_booking_request(
        request.id,
        student.id,
    )

    saved_request = session.get(BookingRequest, request.id)

    assert saved_request is not None
    assert saved_request.status == "cancelled"


def test_student_dashboard_reads_booking_requests_from_database(session):
    student, landlord = create_test_users(session)
    listing = create_test_listing(session, landlord.id)

    booking_repo = BookingRequestRepository(session)
    listing_repo = ListingRepository(session)
    user_repo = UserRepository(session)

    service = BookingRequestService(
        booking_repo,
        listing_repo,
        user_repo,
    )

    service.create_booking_request(
        listing_id=listing.id,
        student_id=student.id,
        move_in_date=date(2026, 12, 1),
        move_out_date=None,
        occupants=1,
        message="Request one",
    )

    service.create_booking_request(
        listing_id=listing.id,
        student_id=student.id,
        move_in_date=date(2027, 1, 1),
        move_out_date=None,
        occupants=2,
        message="Request two",
    )

    dashboard = service.student_dashboard(student.id)

    assert dashboard["total"] == 2
    assert dashboard["pending"] == 2
    assert dashboard["accepted"] == 0
    assert len(dashboard["rows"]) == 2


def test_inactive_listing_is_not_returned_in_student_search(session):
    student, landlord = create_test_users(session)

    listing = create_test_listing(session, landlord.id)

    listing.status = "inactive"
    session.add(listing)
    session.commit()

    repo = ListingRepository(session)
    service = ListingService(repo)

    results = service.search_listings(
        location="St Augustine",
    )

    assert results == []