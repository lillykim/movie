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

import boto3
from botocore.exceptions import NoCredentialsError

import os
from dotenv import load_dotenv

# 이미지만 저장하는 S3버킷에 대한 설정 새로 추가
load_dotenv()

S3_BUCKET = os.getenv("S3_BUCKET")
S3_REGION = os.getenv("S3_REGION")
CLOUDFRONT_URL = os.getenv("CLOUDFRONT_URL") 
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

s3 = boto3.client(
    "s3",
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=S3_REGION
)
# 이미지만 저장하는 S3버킷에 대한 설정 새로 추가

# 이미지만 저장하는 S3버킷에 대한 설정 새로 추가
# S3_BUCKET = "my-pic-saving-bucket"
# S3_REGION = "ap-northeast-2"
# s3 = boto3.client(
#     "s3",
#     "키ID를 직접 변수에 하드코딩해서 넣음",
#     "시크릿액세스키를 직접 변수에 하드코딩해서 넣음",
#     region_name=S3_REGION
# )
# 이미지만 저장하는 S3버킷에 대한 설정 새로 추가

movie_router = APIRouter(tags=["Movie"])

# 로컬 업로드 디렉토리 설정
# BASE_DIR = FilePath(__file__).resolve().parent.parent
# FILE_DIR = BASE_DIR / "uploads" / "movie_posters"
# FILE_DIR.mkdir(parents=True, exist_ok=True)

# 영화 전체 조회
def build_poster_url(poster_path):
    if not poster_path:
        return None
    if poster_path.startswith("http://") or poster_path.startswith("https://"):
        return poster_path
    return f"{CLOUDFRONT_URL}/{poster_path}"
# @movie_router.get("/", response_model=List[Movie])
# async def get_all_movies(session=Depends(get_session)) -> List[Movie]:
#     statement = select(Movie)
#     return session.exec(statement).all()
@movie_router.get("/", response_model=List[Movie])
async def get_all_movies(session=Depends(get_session)) -> List[Movie]:
    statement = select(Movie)
    movies = session.exec(statement).all()
    result = [] # url 중복 문제 해결용
    for movie in movies:
        movie_dict = movie.dict()
        movie_dict["poster_url"] = build_poster_url(movie.poster_path)
        result.append(movie_dict)
        # if movie.poster_path:
        #     movie.poster_path = f"{CLOUDFRONT_URL}/{movie.poster_path}"  # CloudFront URL로 반환
            # presigned_url = s3.generate_presigned_url( # presigned URL 생성 로직 제거
            #     ClientMethod='get_object',
            #     Params={
            #         'Bucket': S3_BUCKET,
            #         'Key': movie.poster_path
            #     },
            #     ExpiresIn=3600
            # )
            # movie.poster_path = presigned_url          # presigned URL 생성 로직 제거
    # return movies
    return result

# 영화 단건 조회
# @movie_router.get("/{movie_id}", response_model=Movie)
# async def get_movie(movie_id: int, session=Depends(get_session)) -> Movie:
#     movie = session.get(Movie, movie_id)
#     if not movie:
#         raise HTTPException(status_code=404, detail="해당 영화를 찾을 수 없습니다.") #url 중복 문제 해결용으로 일단 삭제
@movie_router.get("/{movie_id}")
async def get_movie(movie_id: int, session=Depends(get_session)):
    movie = session.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="해당 영화를 찾을 수 없습니다.")
    movie_dict = movie.dict()
    movie_dict["poster_url"] = build_poster_url(movie.poster_path)
    return movie_dict

    if movie.poster_path:
        movie.poster_path = f"{CLOUDFRONT_URL}/{movie.poster_path}"  # CloudFront URL로 반환
    # if movie.poster_path:                              # 프리사인드 URL 생성 로직 제거
    #     presigned_url = s3.generate_presigned_url(
    #         ClientMethod='get_object',
    #         Params={
    #             'Bucket': S3_BUCKET,
    #             'Key': movie.poster_path
    #         },
    #         ExpiresIn=3600  # 1시간 유효
    #     )
    #     movie.poster_path = presigned_url              # 프리사인드 URL 생성 로직 제거

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
    # if poster:
    #  ext = poster.filename.split('.')[-1]
    #  unique_filename = f"{uuid4().hex}.{ext}"
    #  file_path = FILE_DIR / unique_filename

    #  with open(file_path, "wb") as f:
    #     f.write(poster.file.read())
    
    # movie.poster_path = unique_filename # ✅ 경로 X, 파일명만

    # session.add(movie)
    # session.commit()
    # session.refresh(movie)
    # return movie
    if poster:
        ext = poster.filename.split('.')[-1]
        unique_filename = f"{uuid4().hex}.{ext}"
        s3_key = f"movie_posters/{unique_filename}"

        # S3에 업로드
        poster.file.seek(0)
        s3.upload_fileobj(
            poster.file,
            S3_BUCKET,
            s3_key,
            ExtraArgs={
                "ACL": "public-read", 
                "ContentType": poster.content_type,
                "ContentDisposition": "attachment"
            }
        )

    movie.poster_path = s3_key  # ✅ S3 key만 DB에 저장

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
    # print("data:", data)         # 프론트에서 온 data 파라미터 값 출력
    # print("poster:", poster)     # 프론트에서 온 poster 파일 정보 출력
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

    # 포스터 저장
    # if poster:
    #     ext = poster.filename.split('.')[-1]
    #     unique_filename = f"{uuid4().hex}.{ext}"
    #     file_path = FILE_DIR / unique_filename
    #     with open(file_path, "wb") as f:
    #         f.write(poster.file.read())
    #     movie.poster_path = unique_filename
    if poster:
        ext = poster.filename.split('.')[-1]
        unique_filename = f"{uuid4().hex}.{ext}"
        s3_key = f"movie_posters/{unique_filename}"

        poster.file.seek(0)
        s3.upload_fileobj(
            poster.file,
            S3_BUCKET,
            s3_key,
            ExtraArgs={
                "ACL": "public-read",
                "ContentType": poster.content_type,
                "ContentDisposition": "attachment"
            }
        )
    movie.poster_path = s3_key  # S3 key만 DB에 저장

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
# @movie_router.get("/download/{movie_id}")
# async def download_poster(movie_id: int, session=Depends(get_session)):
#     movie = session.get(Movie, movie_id)
#     if not movie:
#         raise HTTPException(status_code=404, detail="해당 영화를 찾을 수 없습니다.")

#     file_path = FILE_DIR / movie.poster_path
#     if not file_path.exists():
#         raise HTTPException(status_code=404, detail="포스터 파일을 찾을 수 없습니다.")

#     return FileResponse(file_path, media_type="application/octet-stream", filename=file_path.name)