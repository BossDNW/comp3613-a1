from datetime import date

from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.booking_request import BookingRequestRepository
from app.repositories.listing import ListingRepository
from app.repositories.user import UserRepository
from app.services.booking_request_service import BookingRequestService
from app.services.listing_service import ListingService
from . import router, templates


def _booking_service(db: SessionDep) -> BookingRequestService:
    return BookingRequestService(
        BookingRequestRepository(db),
        ListingRepository(db),
        UserRepository(db),
    )


def _get_available_listing(db: SessionDep, listing_id: int):
    details = ListingService(ListingRepository(db)).listing_details(listing_id)
    if details is None:
        raise HTTPException(status_code=404, detail="Accommodation listing not found.")
    return details


def _student_request_details(
    db: SessionDep, booking_request_id: int, student_id: int
):
    details = _booking_service(db).student_request_details(
        booking_request_id, student_id
    )
    if details is None:
        raise HTTPException(status_code=404, detail="Booking request not found.")
    return details


@router.get("/app/listings/{listing_id}/request", response_class=HTMLResponse)
async def booking_request_form(
    listing_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    booking_request_service = _booking_service(db)
    try:
        booking_request_service.require_booking_student(user.id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    listing, landlord, photos, _amenities = _get_available_listing(db, listing_id)
    return templates.TemplateResponse(
        request=request,
        name="booking-request-form.html",
        context={
            "user": user,
            "listing": listing,
            "landlord": landlord,
            "photos": photos,
            "error": None,
            "booking_request": None,
        },
    )


@router.post("/app/listings/{listing_id}/requests")
async def create_booking_request(
    listing_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
    move_in_date: date = Form(...),
    move_out_date: date | None = Form(None),
    occupants: int = Form(...),
    message: str = Form(""),
):
    booking_request_service = _booking_service(db)
    try:
        booking_request_service.require_booking_student(user.id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    listing, landlord, photos, _amenities = _get_available_listing(db, listing_id)

    try:
        booking_request = booking_request_service.create_booking_request(
            listing_id=listing_id,
            student_id=user.id,
            move_in_date=move_in_date,
            move_out_date=move_out_date,
            occupants=occupants,
            message=message,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        return templates.TemplateResponse(
            request=request,
            name="booking-request-form.html",
            context={
                "user": user,
                "listing": listing,
                "landlord": landlord,
                "photos": photos,
                "error": str(exc),
                "booking_request": None,
            },
            status_code=422,
        )

    if booking_request.id is None:
        raise HTTPException(status_code=500, detail="Booking request was not saved.")
    return RedirectResponse(
        url=f"/app/requests/{booking_request.id}/confirmation",
        status_code=303,
    )


@router.get(
    "/app/requests/{booking_request_id}/confirmation",
    response_class=HTMLResponse,
)
async def booking_request_confirmation(
    booking_request_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    booking_request, listing, _photos = _student_request_details(
        db, booking_request_id, user.id
    )
    return templates.TemplateResponse(
        request=request,
        name="booking-request-confirmation.html",
        context={
            "user": user,
            "booking_request": booking_request,
            "listing": listing,
        },
    )


@router.get("/app/requests", response_class=HTMLResponse)
async def student_booking_requests(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    dashboard = _booking_service(db).student_dashboard(user.id)
    return templates.TemplateResponse(
        request=request,
        name="booking-request-dashboard.html",
        context={
            "user": user,
            **dashboard,
        },
    )


@router.get(
    "/app/requests/{booking_request_id}",
    response_class=HTMLResponse,
)
async def student_booking_request_detail(
    booking_request_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    booking_request, listing, photos = _student_request_details(
        db, booking_request_id, user.id
    )
    return templates.TemplateResponse(
        request=request,
        name="booking-request-detail.html",
        context={
            "user": user,
            "booking_request": booking_request,
            "listing": listing,
            "photos": photos,
            "error": None,
        },
    )


@router.post("/app/requests/{booking_request_id}/update")
async def update_student_booking_request(
    booking_request_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
    move_in_date: date = Form(...),
    move_out_date: date | None = Form(None),
    occupants: int = Form(...),
    message: str = Form(""),
):
    service = _booking_service(db)
    try:
        service.update_booking_request(
            booking_request_id=booking_request_id,
            student_id=user.id,
            move_in_date=move_in_date,
            move_out_date=move_out_date,
            occupants=occupants,
            message=message,
        )
    except ValueError as exc:
        booking_request, listing, photos = _student_request_details(
            db, booking_request_id, user.id
        )
        return templates.TemplateResponse(
            request=request,
            name="booking-request-detail.html",
            context={
                "user": user,
                "booking_request": booking_request,
                "listing": listing,
                "photos": photos,
                "error": str(exc),
            },
            status_code=422,
        )
    return RedirectResponse(url=f"/app/requests/{booking_request_id}", status_code=303)


@router.post("/app/requests/{booking_request_id}/cancel")
async def cancel_student_booking_request(
    booking_request_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    service = _booking_service(db)
    try:
        service.cancel_booking_request(booking_request_id, user.id)
    except ValueError as exc:
        booking_request, listing, photos = _student_request_details(
            db, booking_request_id, user.id
        )
        return templates.TemplateResponse(
            request=request,
            name="booking-request-detail.html",
            context={
                "user": user,
                "booking_request": booking_request,
                "listing": listing,
                "photos": photos,
                "error": str(exc),
            },
            status_code=409,
        )
    return RedirectResponse(url="/app/requests", status_code=303)
