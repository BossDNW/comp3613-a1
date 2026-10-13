from datetime import date

from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.listing import ListingRepository
from app.services.listing_service import ListingService
from . import router, templates


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    listing_service = ListingService(ListingRepository(db))
    listings = listing_service.search_listings()
    listing_photos = listing_service.photos_for_listings(
        [listing.id for listing in listings if listing.id is not None]
    )
    filters = {
        "location": "",
        "max_price": "",
        "bedrooms": "",
        "bathrooms": "",
        "available_from": "",
        "furnished": "",
    }

    return templates.TemplateResponse(
        request=request,
        name="app.html",
        context={
            "user": user,
            "listings": listings,
            "listing_photos": listing_photos,
            "filters": filters,
        },
    )


@router.get("/app/results", response_class=HTMLResponse)
async def accommodation_results_view(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    filters = {
        "location": request.query_params.get("location", "").strip(),
        "max_price": request.query_params.get("max_price", "").strip(),
        "bedrooms": request.query_params.get("bedrooms", "").strip(),
        "bathrooms": request.query_params.get("bathrooms", "").strip(),
        "available_from": request.query_params.get("available_from", "").strip(),
        "furnished": request.query_params.get("furnished", "").strip().lower(),
    }

    try:
        max_price = float(filters["max_price"]) if filters["max_price"] else None
        bedrooms = int(filters["bedrooms"]) if filters["bedrooms"] else None
        bathrooms = int(filters["bathrooms"]) if filters["bathrooms"] else None
        available_from = (
            date.fromisoformat(filters["available_from"])
            if filters["available_from"]
            else None
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid search filter value.") from exc

    furnished_value = filters["furnished"]
    if furnished_value not in {"", "true", "false"}:
        raise HTTPException(status_code=422, detail="Invalid furnished filter value.")
    furnished = None if furnished_value == "" else furnished_value == "true"

    listing_service = ListingService(ListingRepository(db))
    listings = listing_service.search_listings(
        location=filters["location"] or None,
        max_price=max_price,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        furnished=furnished,
        available_from=available_from,
    )
    listing_photos = listing_service.photos_for_listings(
        [listing.id for listing in listings if listing.id is not None]
    )

    return templates.TemplateResponse(
        request=request,
        name="search-results.html",
        context={
            "user": user,
            "listings": listings,
            "listing_photos": listing_photos,
            "filters": filters,
        },
    )


@router.get("/app/listings/{listing_id}", response_class=HTMLResponse)
async def listing_detail_view(
    listing_id: int,
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    listing_service = ListingService(ListingRepository(db))
    details = listing_service.listing_details(listing_id)
    if details is None:
        raise HTTPException(status_code=404, detail="Accommodation listing not found.")

    listing, landlord, photos, amenities = details
    return_query = request.query_params.get("return_query", "")
    back_url = "/app"
    if request.query_params.get("from") == "results":
        back_url = "/app/results"
        if return_query:
            back_url = f"{back_url}?{return_query}"

    return templates.TemplateResponse(
        request=request,
        name="listing-details.html",
        context={
            "user": user,
            "listing": listing,
            "landlord": landlord,
            "photos": photos,
            "amenities": amenities,
            "back_url": back_url,
        },
    )
