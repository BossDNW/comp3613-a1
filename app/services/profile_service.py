from app.repositories.user import UserRepository
from app.utilities.security import encrypt_password, verify_password


class ProfileService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def get_profile(self, user_id: int):
        return self.user_repo.get_by_id(user_id)

    def update_profile(
        self,
        user_id: int,
        *,
        full_name: str,
        current_password: str,
        new_password: str,
        confirm_password: str,
    ):
        normalized_name = full_name.strip()
        if not normalized_name:
            raise ValueError("Full name cannot be empty.")

        password_hash = None
        if new_password:
            user = self.user_repo.get_by_id(user_id)
            if user is None:
                raise ValueError("Profile not found.")
            if not current_password or not verify_password(
                plaintext_password=current_password,
                encrypted_password=user.password,
            ):
                raise ValueError("Current password is incorrect.")
            if len(new_password) < 8:
                raise ValueError("New password must be at least 8 characters.")
            if new_password != confirm_password:
                raise ValueError("New password confirmation does not match.")
            password_hash = encrypt_password(new_password)
        elif current_password or confirm_password:
            raise ValueError("Enter a new password to change your password.")

        profile = self.user_repo.update_profile(
            user_id,
            full_name=normalized_name,
            password_hash=password_hash,
        )
        if profile is None:
            raise ValueError("Profile not found.")
        return profile

    def delete_account(
        self,
        user_id: int,
        *,
        current_password: str,
        confirm_delete: str,
    ) -> None:
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise ValueError("Profile not found.")
        if not verify_password(
            plaintext_password=current_password,
            encrypted_password=user.password,
        ):
            raise ValueError("Current password is incorrect.")
        if confirm_delete != "yes":
            raise ValueError("Confirm account deletion to continue.")
        if not self.user_repo.delete_account(user_id):
            raise ValueError("Profile not found.")

    def get_profile(self, user_id: int):
        return self.user_repo.get_by_id(user_id)