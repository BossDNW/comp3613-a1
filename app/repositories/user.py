from sqlmodel import Session, delete, func, or_, select
from app.models.booking_request import BookingRequest
from app.models.listing import Listing, ListingAmenity, ListingPhoto
from app.models.user import UserBase, User
from typing import Optional, Tuple
from app.utilities.pagination import Pagination
from app.schemas.user import UserUpdate
import logging

logger = logging.getLogger(__name__)

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_data: UserBase) -> Optional[User]:
        try:
            user_db = User.model_validate(user_data)
            self.db.add(user_db)
            self.db.commit()
            self.db.refresh(user_db)
            return user_db
        except Exception as e:
            logger.error(f"An error occurred while saving user: {e}")
            self.db.rollback()
            raise

    def search_users(self, query: str, page:int=1, limit:int=10) -> Tuple[list[User], Pagination]:
        offset = (page - 1) * limit
        db_qry = select(User)
        if query:
            db_qry = db_qry.where(
                User.username.ilike(f"%{query}%") | User.email.ilike(f"%{query}%")
            )
        count_qry = select(func.count()).select_from(db_qry.subquery())
        count_todos = self.db.exec(count_qry).one()

        users = self.db.exec(db_qry.offset(offset).limit(limit)).all()
        pagination = Pagination(total_count=count_todos, current_page=page, limit=limit)

        return users, pagination

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.exec(select(User).where(User.username == username)).one_or_none()

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_all_users(self) -> list[User]:
        return self.db.exec(select(User)).all()

    def update_user(self, user_id:int, user_data: UserUpdate)->User:
        user = self.db.get(User, user_id)
        if not user:
            raise Exception("Invalid user id given")
        if user_data.username:
            user.username = user_data.username
        if user_data.email:
            user.email = user_data.email
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            logger.error(f"An error occurred while updating user: {e}")
            self.db.rollback()
            raise

    def update_profile(
        self,
        user_id: int,
        *,
        full_name: str,
        password_hash: str | None = None,
    ) -> User | None:
        user = self.db.get(User, user_id)
        if user is None:
            return None

        user.full_name = full_name
        if password_hash is not None:
            user.password = password_hash
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as exc:
            logger.error("An error occurred while updating profile: %s", exc)
            self.db.rollback()
            raise

    def delete_account(self, user_id: int) -> bool:
        user = self.db.get(User, user_id)
        if user is None:
            return False

        listing_ids = self.db.exec(
            select(Listing.id).where(Listing.landlord_id == user_id)
        ).all()
        try:
            self.db.exec(
                delete(BookingRequest).where(
                    or_(
                        BookingRequest.student_id == user_id,
                        BookingRequest.listing_id.in_(listing_ids),
                    )
                )
            )
            self.db.exec(
                delete(ListingPhoto).where(ListingPhoto.listing_id.in_(listing_ids))
            )
            self.db.exec(
                delete(ListingAmenity).where(
                    ListingAmenity.listing_id.in_(listing_ids)
                )
            )
            self.db.exec(delete(Listing).where(Listing.id.in_(listing_ids)))
            self.db.delete(user)
            self.db.commit()
            return True
        except Exception as exc:
            logger.error("An error occurred while deleting account: %s", exc)
            self.db.rollback()
            raise

    def delete_user(self, user_id: int):
        user = self.db.get(User, user_id)
        if not user:
            raise Exception("User doesn't exist")
        try:
            self.db.delete(user)
            self.db.commit()
        except Exception as e:
            logger.error(f"An error occurred while deleting user: {e}")
            self.db.rollback()
            raise
