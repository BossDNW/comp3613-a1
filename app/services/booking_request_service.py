from datetime import date

from app.models.booking_request import BookingRequest
from app.models.listing import Listing, ListingPhoto
from app.repositories.booking_request import BookingRequestRepository
from app.repositories.listing import ListingRepository
from app.repositories.user import UserRepository


class BookingRequestService:
    def __init__(
        self,
        booking_request_repo: BookingRequestRepository,
        listing_repo: ListingRepository,
        user_repo: UserRepository,
    ):
        self.booking_request_repo = booking_request_repo
        self.listing_repo = listing_repo
        self.user_repo = user_repo

    def require_booking_student(self, user_id: int) -> None:
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise PermissionError("Your account could not be found.")
        if user.role == "landlord":
            raise PermissionError("Landlord accounts cannot submit booking requests.")

    def _validate_request(
        self,
        listing: Listing,
        *,
        move_in_date: date,
        move_out_date: date | None,
        occupants: int,
    ) -> None:
        if listing.available_from and move_in_date < listing.available_from:
            raise ValueError("Move-in date must be on or after the listing availability date.")
        if move_out_date and move_out_date <= move_in_date:
            raise ValueError("Move-out date must be after the move-in date.")
        if occupants < 1:
            raise ValueError("Number of occupants must be at least one.")

    def create_booking_request(
        self,
        *,
        listing_id: int,
        student_id: int,
        move_in_date: date,
        move_out_date: date | None,
        occupants: int,
        message: str,
    ) -> BookingRequest:
        self.require_booking_student(student_id)
        listing = self.listing_repo.get_available_by_id(listing_id)
        if listing is None:
            raise ValueError("This accommodation is no longer available.")

        self._validate_request(
            listing,
            move_in_date=move_in_date,
            move_out_date=move_out_date,
            occupants=occupants,
        )
        return self.booking_request_repo.create(
            BookingRequest(
                listing_id=listing_id,
                student_id=student_id,
                move_in_date=move_in_date,
                move_out_date=move_out_date,
                occupants=occupants,
                message=message.strip(),
                status="pending",
            )
        )

    def student_dashboard(self, student_id: int) -> dict[str, object]:
        requests = self.booking_request_repo.list_for_student(student_id)

        return {
            "rows": self.booking_request_repo.dashboard_rows(student_id),
            "total": len(requests),
            "pending": sum(item.status == "pending" for item in requests),
            "accepted": sum(item.status == "accepted" for item in requests),
        }

    def student_request_details(
        self, booking_request_id: int, student_id: int
    ) -> tuple[BookingRequest, Listing, list[ListingPhoto]] | None:
        booking_request = self.booking_request_repo.get_for_student(
            booking_request_id, student_id
        )
        if booking_request is None:
            return None

        listing = self.listing_repo.get_by_id(booking_request.listing_id)
        if listing is None:
            return None

        return (
            booking_request,
            listing,
            self.listing_repo.photos_for_listing(listing.id),
        )

    def update_booking_request(
        self,
        *,
        booking_request_id: int,
        student_id: int,
        move_in_date: date,
        move_out_date: date | None,
        occupants: int,
        message: str,
    ) -> BookingRequest:
        booking_request = self.booking_request_repo.get_for_student(
            booking_request_id, student_id
        )
        if booking_request is None:
            raise ValueError("Booking request not found.")
        if booking_request.status != "pending":
            raise ValueError("Only pending requests can be updated.")

        listing = self.listing_repo.get_available_by_id(booking_request.listing_id)
        if listing is None:
            raise ValueError("This accommodation is no longer available.")
        self._validate_request(
            listing,
            move_in_date=move_in_date,
            move_out_date=move_out_date,
            occupants=occupants,
        )
        return self.booking_request_repo.update(
            booking_request,
            move_in_date=move_in_date,
            move_out_date=move_out_date,
            occupants=occupants,
            message=message.strip(),
        )

    def cancel_booking_request(
        self, booking_request_id: int, student_id: int
    ) -> BookingRequest:
        booking_request = self.booking_request_repo.get_for_student(
            booking_request_id, student_id
        )
        if booking_request is None:
            raise ValueError("Booking request not found.")
        if booking_request.status != "pending":
            raise ValueError("Only pending requests can be cancelled.")
        return self.booking_request_repo.cancel(booking_request)
