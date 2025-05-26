from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from auth.hash_password import HashPassword
from auth.jwt_handler import create_jwt_token
from database.connection import get_session
from models.users import User, UserSignIn, UserSignUp
from auth.authenticate import authenticate
import re;


user_router = APIRouter(tags=["User"])
hash_password = HashPassword()

# 회원 가입(등록)
@user_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def sign_new_user(data: UserSignUp, session = Depends(get_session)) -> dict:
    
    # 비밀번호 유효성 검사
    password_pattern = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[!@#$%^&*(),.?\":{}|<>])[A-Za-z\d!@#$%^&*(),.?\":{}|<>]{8,}$"
    if not re.fullmatch(password_pattern, data.password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="비밀번호는 8자 이상이며, 영문자, 숫자, 특수문자를 각각 최소 1개 이상 포함해야 합니다."
        )
    
    # 이메일 중복 검사
    statement = select(User).where(User.email == data.email)
    user = session.exec(statement).first()

    if user:
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="해당 이메일은 탈퇴한 계정입니다. 관리자에게 문의하세요."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="동일한 사용자가 존재합니다."
            )
    
    
    # 새로운 유저 생성
    new_user = User(
        email=data.email,
        password=hash_password.hash_password(data.password),
        username=data.username, 
        events=[]
        # is_active, is_admin -> 기본값 처리
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {
        "message": "회원가입이 완료되었습니다. 로그인 후 서비스를 이용해보세요.",
        "user": new_user
    }

# 로그인
@user_router.post("/signin")
async def sign_in(data: OAuth2PasswordRequestForm = Depends(), session = Depends(get_session)) -> dict:
    statement = select(User).where(User.email == data.username)
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="등록되지 않은 이메일입니다.")
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 이메일은 탈퇴한 계정입니다. 관리자에게 문의하세요."
        )    
    # if user.password != data.password:
    if hash_password.verify_password(data.password, user.password) == False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="패스워드가 일치하지 않습니다.")
    
    return {
        "message": "로그인에 성공했습니다.",
        "username": user.username, 
        "access_token": create_jwt_token(user.email, user.id),
        "is_admin": user.is_admin
    }
   
  
  
 # 회원탈퇴
@user_router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_my_account(
    user_id: int = Depends(authenticate),
    session = Depends(get_session)
    ):
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="이미 탈퇴한 사용자입니다.")

    user.is_active = False
    session.add(user)
    session.commit()

    return { "message": "회원탈퇴가 완료되었습니다." }
