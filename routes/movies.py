import json
from typing import List
from pathlib import Path as FilePath

from fastapi import APIRouter, Depends, UploadFile, File, Form, Path, HTTPException, status, Body
from fastapi.responses import FileResponse
from sqlmodel import select
from uuid import uuid4

from auth.authenticate import authenticate
from database.connection import get_session
from models.movie import Movie

movie_router = APIRouter(tags=["Movie"])

# 업로드 디렉토리 설정
BASE_DIR = FilePath(__file__).resolve().parent.parent
FILE_DIR = BASE_DIR / "uploads" / "movie_posters"
FILE_DIR.mkdir(parents=True, exist_ok=True)

# 영화 전체 조회
@movie_router.get("/", response_model=List[Movie])
async def get_all_movies(session=Depends(get_session)) -> List[Movie]:
    statement = select(Movie)
    return session.exec(statement).all()

# 영화 단건 조회
@movie_router.get("/{movie_id}", response_model=Movie)
async def get_movie(movie_id: int, session=Depends(get_session)) -> Movie:
    movie = session.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="해당 영화를 찾을 수 없습니다.")
    return movie

# 영화 등록
@movie_router.post("/", status_code=status.HTTP_201_CREATED, response_model=Movie)
async def create_movie(
    data=Form(...),
    poster: UploadFile = File(...),
    user_id: int = Depends(authenticate),
    session=Depends(get_session)
):
    # JSON 파싱 후 Movie 객체 생성
    data_dict = json.loads(data)
    movie = Movie(**data_dict, user_id=user_id)

    # 포스터 저장
    if poster:
     ext = poster.filename.split('.')[-1]
     unique_filename = f"{uuid4().hex}.{ext}"
     file_path = FILE_DIR / unique_filename

     with open(file_path, "wb") as f:
        f.write(poster.file.read())
    
    movie.poster_path = unique_filename # ✅ 경로 X, 파일명만

    session.add(movie)
    session.commit()
    session.refresh(movie)
    return movie

# 영화 수정
from fastapi import UploadFile, File, Form
from models.users import User

@movie_router.put("/{movie_id}", response_model=Movie)
async def update_movie(
    movie_id: int,
    data: str = Form(...),
    poster: UploadFile = File(None),
    user_id: int = Depends(authenticate),
    session=Depends(get_session)
):
    parsed_data = json.loads(data)
    movie = session.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="해당 영화를 찾을 수 없습니다.")

    # 관리자 또는 작성자만 수정 가능
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="유저 정보를 찾을 수 없습니다.")
    if not user.is_admin and movie.user_id != user_id:
        raise HTTPException(status_code=403, detail="수정 권한이 없습니다.")

    for key, value in parsed_data.items():
        if hasattr(movie, key):
            setattr(movie, key, value)

    if poster:
        ext = poster.filename.split('.')[-1]
        unique_filename = f"{uuid4().hex}.{ext}"
        file_path = FILE_DIR / unique_filename
        with open(file_path, "wb") as f:
            f.write(poster.file.read())
        movie.poster_path = unique_filename

    session.add(movie)
    session.commit()
    session.refresh(movie)
    return movie


# 영화 삭제
@movie_router.delete("/{movie_id}")
async def delete_movie(movie_id: int, user_id: int = Depends(authenticate), session=Depends(get_session)):
    movie = session.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="해당 영화를 찾을 수 없습니다.")

    # 관리자 또는 작성자만 삭제 가능
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="유저 정보를 찾을 수 없습니다.")
    if not user.is_admin and movie.user_id != user_id:
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")

    session.delete(movie)
    session.commit()
    return {"message": "영화가 삭제되었습니다."}

# 포스터 다운로드
@movie_router.get("/download/{movie_id}")
async def download_poster(movie_id: int, session=Depends(get_session)):
    movie = session.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="해당 영화를 찾을 수 없습니다.")

    file_path = FILE_DIR / movie.poster_path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="포스터 파일을 찾을 수 없습니다.")

    return FileResponse(file_path, media_type="application/octet-stream", filename=file_path.name)
