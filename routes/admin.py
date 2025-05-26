
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from models.users import User
from database.connection import get_session
from auth.authenticate import authenticate
from typing import List

admin_router = APIRouter(tags=["Admin"])

# 탈퇴된 사용자 목록 조회
@admin_router.get("/", response_model=List[User])
async def get_inactive_users(
    admin_id: int = Depends(authenticate),
    session: Session = Depends(get_session)
):
    admin_user = session.get(User, admin_id)
    if not admin_user or not admin_user.is_admin:
        raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다.")

    return session.exec(select(User).where(User.is_active == False)).all()

# 특정 사용자 복구
@admin_router.put("/{user_id}")
async def restore_user(
    user_id: int,
    admin_id: int = Depends(authenticate),
    session: Session = Depends(get_session)
):
    admin_user = session.get(User, admin_id)
    if not admin_user or not admin_user.is_admin:
        raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다.")

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    if user.is_active:
        raise HTTPException(status_code=400, detail="이미 활성화된 계정입니다.")

    user.is_active = True
    session.add(user)
    session.commit()
    return {"message": f"{user.email} 계정이 복구되었습니다."}
