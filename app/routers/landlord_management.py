from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette import status

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.landlord_management import LandlordManagementRepository
from app.services.landlord_management_service import LandlordManagementService
from app.utilities.flash import flash
from . import router, templates


def _landlord_service(db: SessionDep) -> LandlordManagementService:
    return LandlordManagementService(LandlordManagementRepository(db))


def _require_landlord(service: LandlordManagementService, user: AuthDep) -> None:
    try:
        service.require_landlord(user.id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


def _listing_form_values(
    *,
    title: str = "",
    location: str = "",
    price_per_month: str = "",
    description: str = "",
    amenity_ids: list[int] | None = None,
    photo_urls: list[str] | None = None,
) -> dict[str, object]:
    return {
        "title": title,
        "location": location,
        "price_per_month": price_per_month,
        "description": description,
        "amenity_ids": set(amenity_ids or []),
        "photo_urls": photo_urls or [],
    }


def _render_listing_form(
    request: Request,
    user: AuthDep,
    service: LandlordManagementService,
    *,
    listing_id: int | None = None,
    error: str | None = None,
    values: dict[str, object] | None = None,
    status_code: int = 200,
):
    try:
        form_data = service.listing_form_data(user.id, listing_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    listing = form_data["listing"]
    photos = form_data["photos"]
    default_values = _listing_form_values()
    if listing is not None:
        default_values = _listing_form_values(
            title=listing.title,
            location=listing.suburb,
            price_per_month=str(listing.price_per_month),
            description=listing.description,
            amenity_ids=list(form_data["selected_amenity_ids"]),
            photo_urls=[photo.image_url for photo in photos],
        )
    context = {
        "user": user,
        **form_data,
        "values": values if values is not None else default_values,
        "error": error,
        "is_edit": listing_id is not None,
    }
    return templates.TemplateResponse(
        request=request,
        name="landlord-listing-form.html",
        context=context,
        status_code=status_code,
    )


@router.get("/app/landlord", response_class=HTMLResponse)
async def landlord_dashboard(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    landlord_service = _landlord_service(db)
    _require_landlord(landlord_service, user)
    dashboard_data = landlord_service.dashboard(user.id)

    return templates.TemplateResponse(
        request=request,
        name="landlord-dashboard.html",
        context={
            "user": user,
            **dashboard_data,
        },
    )


@router.get(
    "/app/landlord/listings/new",
    response_class=HTMLResponse,
    name="new_landlord_listing",
)
async def new_landlord_listing(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    return _render_listing_form(request, user, _landlord_service(db))


@router.post("/app/landlord/listings")
async def create_landlord_listing(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    title: str = Form(""),
    location: str = Form(""),
    price_per_month: str = Form(""),
    description: str = Form(""),
    amenity_ids: list[int] = Form([]),
    photo_urls: list[str] = Form([]),
):
    service = _landlord_service(db)
    _require_landlord(service, user)
    try:
        service.create_listing(
            user.id,
            title=title,
            location=location,
            price_per_month=price_per_month,
            description=description,
            amenity_ids=amenity_ids,
            photo_urls=photo_urls,
        )
    except ValueError as exc:
        return _render_listing_form(
            request,
            user,
            service,
            error=str(exc),
            values=_listing_form_values(
                title=title,
                location=location,
                price_per_month=price_per_month,
                description=description,
                amenity_ids=amenity_ids,
                photo_urls=photo_urls,
            ),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    flash(request, "Accommodation listing added.")
    return RedirectResponse("/app/landlord", status_code=303)


@router.get(
    "/app/landlord/listings/{listing_id}/edit",
    response_class=HTMLResponse,
    name="edit_landlord_listing",
)
async def edit_landlord_listing(
    listing_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    return _render_listing_form(
        request,
        user,
        _landlord_service(db),
        listing_id=listing_id,
    )


@router.post("/app/landlord/listings/{listing_id}/edit")
async def update_landlord_listing(
    listing_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
    title: str = Form(""),
    location: str = Form(""),
    price_per_month: str = Form(""),
    description: str = Form(""),
    amenity_ids: list[int] = Form([]),
    photo_urls: list[str] = Form([]),
):
    service = _landlord_service(db)
    _require_landlord(service, user)
    try:
        service.update_listing(
            user.id,
            listing_id,
            title=title,
            location=location,
            price_per_month=price_per_month,
            description=description,
            amenity_ids=amenity_ids,
            photo_urls=photo_urls,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        return _render_listing_form(
            request,
            user,
            service,
            listing_id=listing_id,
            error=str(exc),
            values=_listing_form_values(
                title=title,
                location=location,
                price_per_month=price_per_month,
                description=description,
                amenity_ids=amenity_ids,
                photo_urls=photo_urls,
            ),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    flash(request, "Accommodation listing updated.")
    return RedirectResponse("/app/landlord", status_code=303)


@router.post("/app/landlord/listings/{listing_id}/status")
async def change_landlord_listing_status(
    listing_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
    active: bool = Form(...),
):
    service = _landlord_service(db)
    try:
        service.change_listing_status(user.id, listing_id, active=active)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    flash(
        request,
        "Listing status updated.",
    )
    return RedirectResponse("/app/landlord", status_code=303)


@router.get(
    "/app/landlord/requests/{booking_request_id}",
    response_class=HTMLResponse,
    name="landlord_booking_request",
)
async def landlord_booking_request(
    booking_request_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    service = _landlord_service(db)
    try:
        details = service.booking_request_details(user.id, booking_request_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return templates.TemplateResponse(
        request=request,
        name="landlord-booking-request.html",
        context={"user": user, **details},
    )


@router.post("/app/landlord/requests/{booking_request_id}/decision")
async def decide_landlord_booking_request(
    booking_request_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
    decision: str = Form(""),
):
    service = _landlord_service(db)
    try:
        service.decide_booking_request(
            user.id,
            booking_request_id,
            decision=decision,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        details = service.booking_request_details(user.id, booking_request_id)
        return templates.TemplateResponse(
            request=request,
            name="landlord-booking-request.html",
            context={"user": user, "error": str(exc), **details},
            status_code=status.HTTP_409_CONFLICT,
        )
    flash(request, f"Booking request {decision}.")
    return RedirectResponse(
        f"/app/landlord/requests/{booking_request_id}",
        status_code=303,
    )
