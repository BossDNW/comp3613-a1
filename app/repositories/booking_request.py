from datetime import date, datetime

from sqlmodel import Session, select

from app.models.booking_request import BookingRequest
from app.models.listing import Listing
from app.models.user import User


class BookingRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, booking_request: BookingRequest) -> BookingRequest:
        self.db.add(booking_request)
        self.db.commit()
        self.db.refresh(booking_request)
        return booking_request

    def get_for_student(
        self, booking_request_id: int, student_id: int
    ) -> BookingRequest | None:
        statement = select(BookingRequest).where(
            BookingRequest.id == booking_request_id,
            BookingRequest.student_id == student_id,
        )
        return self.db.exec(statement).one_or_none()

    def list_for_student(self, student_id: int) -> list[BookingRequest]:
        statement = (
            select(BookingRequest)
            .where(BookingRequest.student_id == student_id)
            .order_by(BookingRequest.created_at.desc())
        )
        return self.db.exec(statement).all()

    def dashboard_rows(self, student_id: int) -> list[dict[str, object]]:
        statement = (
            select(BookingRequest, Listing, User)
            .join(Listing, BookingRequest.listing_id == Listing.id)
            .join(User, Listing.landlord_id == User.id)
            .where(BookingRequest.student_id == student_id)
            .order_by(BookingRequest.created_at.desc())
        )
        return [
            {"request": booking_request, "listing": listing, "landlord": landlord}
            for booking_request, listing, landlord in self.db.exec(statement).all()
        ]

    def update(
        self,
        booking_request: BookingRequest,
        *,
        move_in_date: date,
        move_out_date: date | None,
        occupants: int,
        message: str,
    ) -> BookingRequest:
        booking_request.move_in_date = move_in_date
        booking_request.move_out_date = move_out_date
        booking_request.occupants = occupants
        booking_request.message = message
        booking_request.updated_at = datetime.utcnow()
        self.db.add(booking_request)
        self.db.commit()
        self.db.refresh(booking_request)
        return booking_request

    def cancel(self, booking_request: BookingRequest) -> BookingRequest:
        booking_request.status = "cancelled"
        booking_request.updated_at = datetime.utcnow()
        self.db.add(booking_request)
        self.db.commit()
        self.db.refresh(booking_request)
        return booking_request
