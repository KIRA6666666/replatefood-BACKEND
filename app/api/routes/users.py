from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.core.security import verify_password
from app.crud import user as user_crud
from app.schemas.user import ChangePassword, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def read_me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(payload: ChangePassword, current_user: CurrentUser, db: DbSession) -> None:
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mot de passe actuel incorrect")
    await user_crud.change_password(db, current_user, payload.new_password)
