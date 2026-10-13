from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette import status

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.user import UserRepository
from app.services.profile_service import ProfileService
from app.utilities.flash import flash
from app.utilities.security import access_token_cookie_kwargs
from . import router, templates


@router.get("/app/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    user: AuthDep,
    db: SessionDep,
):
    profile_service = ProfileService(UserRepository(db))
    profile = profile_service.get_profile(user.id)

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "user": user,
            "profile": profile,
        },
    )


@router.post("/app/profile")
async def update_profile(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    full_name: str = Form(""),
    current_password: str = Form(""),
    new_password: str = Form(""),
    confirm_password: str = Form(""),
):
    profile_service = ProfileService(UserRepository(db))
    try:
        profile = profile_service.update_profile(
            user.id,
            full_name=full_name,
            current_password=current_password,
            new_password=new_password,
            confirm_password=confirm_password,
        )
    except ValueError as exc:
        profile = profile_service.get_profile(user.id)
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found.") from exc
        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={"user": user, "profile": profile, "error": str(exc)},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    flash(request, "Profile updated successfully.")
    return RedirectResponse(
        url=request.url_for("profile_page"),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/app/profile/delete")
async def delete_profile(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    current_password: str = Form(""),
    confirm_delete: str = Form(""),
):
    profile_service = ProfileService(UserRepository(db))
    try:
        profile_service.delete_account(
            user.id,
            current_password=current_password,
            confirm_delete=confirm_delete,
        )
    except ValueError as exc:
        profile = profile_service.get_profile(user.id)
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found.") from exc
        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={"user": user, "profile": profile, "error": str(exc)},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    response = RedirectResponse(
        url=request.url_for("index_view"),
        status_code=status.HTTP_303_SEE_OTHER,
    )
    response.delete_cookie(key="access_token", **access_token_cookie_kwargs())
    flash(request, "Your account and associated accommodation data were deleted.")
    return response
